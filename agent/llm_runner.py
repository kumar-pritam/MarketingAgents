from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Callable

from openai import OpenAI

from utils.config import settings
from utils.models import LLMResponse, QueryItem
from utils.server_logger import get_logger, setup_server_logging

setup_server_logging(logging.DEBUG)
LOGGER = get_logger("agent.llm_runner")


@dataclass(slots=True)
class RunnerStats:
    total_tokens: int = 0
    completed: int = 0
    failed: int = 0
    requests_used_today: int = 0
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


class LLMRunner:
    def __init__(self, usage_store: Path | None = None) -> None:
        self.client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )
        self.usage_store = usage_store

    def _system_prompt(self) -> str:
        return (
            "You are a neutral business buyer conducting independent market research. "
            "Answer directly and objectively with concrete brand options and rationale. "
            "Do not optimize for any specific brand."
        )

    def _get_request_count(self) -> int:
        if not self.usage_store or not self.usage_store.exists():
            return 0
        try:
            payload = self.usage_store.read_text(encoding="utf-8").strip().splitlines()
            today = datetime.now(timezone.utc).date().isoformat()
            return sum(1 for row in payload if row.startswith(today))
        except OSError:
            return 0

    def _log_request(self) -> int:
        current = self._get_request_count()
        if not self.usage_store:
            return current + 1
        self.usage_store.parent.mkdir(parents=True, exist_ok=True)
        with self.usage_store.open("a", encoding="utf-8") as file:
            file.write(f"{datetime.now(timezone.utc).date().isoformat()}|1\n")
        return current + 1

    def run_queries(
        self,
        queries: list[QueryItem],
        progress_callback: Callable[[int, int, str], None] | None = None,
        debug_callback: Callable[[str], None] | None = None,
        model: str | None = None,
    ) -> tuple[list[LLMResponse], RunnerStats]:
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        target_model = model or settings.openrouter_model
        responses: list[LLMResponse] = []
        stats = RunnerStats(requests_used_today=self._get_request_count())

        for idx, query in enumerate(queries, start=1):
            if progress_callback:
                progress_callback(idx, len(queries), query.text)
            if debug_callback:
                debug_callback(
                    f"GEO_LLM_CALL_START query_id={query.query_id} model={target_model} "
                    f"prompt_system={self._system_prompt()} prompt_user={query.text}"
                )

            response_text = ""
            tokens_used = 0
            success = False

            for attempt in range(settings.max_retries):
                try:
                    LOGGER.debug(
                        "LLM_CALL_START query_id=%s model=%s attempt=%s",
                        query.query_id,
                        target_model,
                        attempt + 1,
                    )
                    if debug_callback:
                        debug_callback(f"GEO_LLM_ATTEMPT query_id={query.query_id} attempt={attempt + 1}")
                    completion = self.client.chat.completions.create(
                        model=target_model,
                        messages=[
                            {"role": "system", "content": self._system_prompt()},
                            {"role": "user", "content": query.text},
                        ],
                    )
                    response_text = completion.choices[0].message.content or ""
                    tokens_used = completion.usage.total_tokens if completion.usage else 0
                    LOGGER.debug(
                        "LLM_CALL_END query_id=%s model=%s tokens=%s success=true",
                        query.query_id,
                        target_model,
                        tokens_used,
                    )
                    if debug_callback:
                        debug_callback(
                            f"GEO_LLM_CALL_SUCCESS query_id={query.query_id} model={target_model} "
                            f"tokens={tokens_used} response={response_text}"
                        )
                    success = True
                    break
                except Exception as exc:
                    LOGGER.exception(
                        "LLM_CALL_ERROR query_id=%s model=%s attempt=%s error=%s",
                        query.query_id,
                        target_model,
                        attempt + 1,
                        exc,
                    )
                    if debug_callback:
                        debug_callback(
                            f"GEO_LLM_ATTEMPT_FAILED query_id={query.query_id} attempt={attempt + 1} error={exc}"
                        )
                    if attempt >= settings.max_retries - 1:
                        break
                    time.sleep(2**attempt)

            if not success and target_model != settings.openrouter_fallback_model:
                try:
                    LOGGER.debug(
                        "LLM_FALLBACK_CALL_START query_id=%s model=%s",
                        query.query_id,
                        settings.openrouter_fallback_model,
                    )
                    if debug_callback:
                        debug_callback(
                            f"GEO_LLM_FALLBACK_CALL query_id={query.query_id} model={settings.openrouter_fallback_model}"
                        )
                    completion = self.client.chat.completions.create(
                        model=settings.openrouter_fallback_model,
                        messages=[
                            {"role": "system", "content": self._system_prompt()},
                            {"role": "user", "content": query.text},
                        ],
                    )
                    response_text = completion.choices[0].message.content or ""
                    tokens_used = completion.usage.total_tokens if completion.usage else 0
                    LOGGER.debug(
                        "LLM_FALLBACK_CALL_END query_id=%s model=%s tokens=%s success=true",
                        query.query_id,
                        settings.openrouter_fallback_model,
                        tokens_used,
                    )
                    if debug_callback:
                        debug_callback(
                            f"GEO_LLM_FALLBACK_SUCCESS query_id={query.query_id} "
                            f"model={settings.openrouter_fallback_model} tokens={tokens_used} response={response_text}"
                        )
                    success = True
                except Exception as exc:
                    LOGGER.exception(
                        "LLM_FALLBACK_CALL_ERROR query_id=%s model=%s error=%s",
                        query.query_id,
                        settings.openrouter_fallback_model,
                        exc,
                    )
                    if debug_callback:
                        debug_callback(f"GEO_LLM_FALLBACK_FAILED query_id={query.query_id} error={exc}")
                    success = False

            if success:
                responses.append(
                    LLMResponse(
                        query_id=query.query_id,
                        raw_response=response_text,
                        model=target_model,
                        tokens_used=tokens_used,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )
                stats.total_tokens += tokens_used
                stats.completed += 1
            else:
                stats.failed += 1
                responses.append(
                    LLMResponse(
                        query_id=query.query_id,
                        raw_response="",
                        model=target_model,
                        tokens_used=0,
                        timestamp=datetime.now(timezone.utc).isoformat(),
                    )
                )

            stats.requests_used_today = self._log_request()
            if debug_callback:
                debug_callback(
                    f"GEO_LLM_QUOTA requests_used_today={stats.requests_used_today} "
                    f"daily_limit={settings.quota_daily_limit}"
                )
            if stats.requests_used_today >= settings.quota_warn_threshold:
                warning = (
                    f"OpenRouter free-tier usage warning: {stats.requests_used_today}/"
                    f"{settings.quota_daily_limit} requests used today."
                )
                if warning not in stats.warnings:
                    stats.warnings.append(warning)

        return responses, stats
