from __future__ import annotations

import json
import logging

from openai import OpenAI

from utils.config import settings
from utils.server_logger import get_logger, setup_server_logging

setup_server_logging(logging.DEBUG)
LOGGER = get_logger("agent.analyst")


class CompetitorAnalyst:
    def __init__(self) -> None:
        self.client = None
        if settings.openrouter_api_key:
            self.client = OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)

    def analyze(self, own_brand: dict, competitor_payload: dict, debug_callback=None) -> dict:
        if not self.client:
            if debug_callback:
                debug_callback("CI_ANALYST_FALLBACK_USED reason=no_openrouter_client")
            return self._fallback(competitor_payload)

        system = (
            "You are a senior competitive intelligence analyst. Analyze this competitor signal pack relative "
            "to the user's brand and return compact JSON with keys: what_changed, strategic_interpretation, "
            "speed_of_movement, threat_level, recommended_response, key_signals."
        )
        user = {
            "own_brand": own_brand,
            "competitor_signals": competitor_payload,
        }
        if debug_callback:
            debug_callback(
                f"CI_ANALYST_LLM_CALL model={settings.openrouter_model} system_prompt={system} "
                f"user_prompt={json.dumps(user)}"
            )

        try:
            LOGGER.debug(
                "CI_ANALYST_LLM_CALL_START model=%s competitor=%s",
                settings.openrouter_model,
                competitor_payload.get("competitor_name"),
            )
            completion = self.client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(user)},
                ],
                temperature=0.2,
            )
            content = completion.choices[0].message.content or "{}"
            LOGGER.debug(
                "CI_ANALYST_LLM_CALL_END model=%s competitor=%s response_len=%s",
                settings.openrouter_model,
                competitor_payload.get("competitor_name"),
                len(content),
            )
            if debug_callback:
                debug_callback(f"CI_ANALYST_LLM_RESPONSE raw={content}")
            parsed = json.loads(content)
            if isinstance(parsed, dict) and parsed:
                if debug_callback:
                    debug_callback("CI_ANALYST_LLM_PARSED success=true")
                return parsed
        except Exception as exc:
            LOGGER.exception(
                "CI_ANALYST_LLM_CALL_ERROR model=%s competitor=%s error=%s",
                settings.openrouter_model,
                competitor_payload.get("competitor_name"),
                exc,
            )
            if debug_callback:
                debug_callback(f"CI_ANALYST_LLM_FAILED error={exc}")

        if debug_callback:
            debug_callback("CI_ANALYST_FALLBACK_USED reason=llm_parse_or_call_failure")
        return self._fallback(competitor_payload)

    def _fallback(self, competitor_payload: dict) -> dict:
        diff_items = competitor_payload.get("web_diffs", [])
        major = sum(1 for item in diff_items if item.get("change_magnitude") in {"major", "moderate"})
        threat = "high" if major >= 2 else "medium" if major == 1 else "low"
        speed = "aggressive" if major >= 3 else "fast" if major >= 2 else "moderate"
        competitor = competitor_payload.get("competitor_name", "Competitor")

        return {
            "what_changed": f"{competitor} changed {len(diff_items)} monitored pages this cycle.",
            "strategic_interpretation": "Signals a messaging refresh with stronger emphasis on conversion-oriented copy.",
            "speed_of_movement": speed,
            "threat_level": threat,
            "recommended_response": "Launch a counter-positioning page with clearer differentiation and proof points.",
            "key_signals": [
                "Website copy updates detected",
                "Ad messaging signal monitored",
                "Public signal scan completed",
            ],
        }
