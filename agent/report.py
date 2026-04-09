from __future__ import annotations

import json
import logging

from openai import OpenAI

from utils.config import settings
from utils.models import AuditScore, BrandContext, GapItem
from utils.server_logger import get_logger, setup_server_logging

setup_server_logging(logging.DEBUG)
LOGGER = get_logger("agent.report")


class ReportGenerator:
    def __init__(self) -> None:
        self.client = None
        if settings.openrouter_api_key:
            self.client = OpenAI(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
            )

    def _fallback_recommendations(
        self,
        context: BrandContext,
        gaps: list[GapItem],
        gsc_insights: list[dict[str, str | int | float]] | None = None,
    ) -> list[dict[str, str]]:
        recommendations: list[dict[str, str]] = []
        insight_topics = [str(item.get("query", "")).strip() for item in (gsc_insights or []) if item.get("query")]

        for idx, gap in enumerate(gaps[:8], start=1):
            urgency = "Act Now" if gap.gap_score >= 3 else "Watch"
            format_type = (
                "Comparison landing page"
                if idx % 3 == 0
                else "Thought-leadership article"
                if idx % 2 == 0
                else "SEO blog + FAQ"
            )
            why = "Targets high-intent LLM prompts where competitors are currently cited."
            if insight_topics:
                why += f" Align with owned-search demand around '{insight_topics[(idx - 1) % len(insight_topics)]}'."
            recommendations.append(
                {
                    "topic": gap.topic,
                    "content_format": format_type,
                    "why_this_works": why,
                    "urgency": urgency,
                    "competitor_to_displace": gap.dominant_competitor,
                }
            )

        while len(recommendations) < 5:
            seed_topic = insight_topics[(len(recommendations) - 1) % len(insight_topics)] if insight_topics else context.category
            recommendations.append(
                {
                    "topic": f"{seed_topic} trust and proof content",
                    "content_format": "Customer proof page",
                    "why_this_works": "Improves authority-seeking and evaluative query performance.",
                    "urgency": "Watch",
                    "competitor_to_displace": context.competitors[0] if context.competitors else "N/A",
                }
            )

        return recommendations[:10]

    def generate(
        self,
        context: BrandContext,
        score: AuditScore,
        gsc_insights: list[dict[str, str | int | float]] | None = None,
        debug_callback=None,
    ) -> list[dict[str, str]]:
        if not self.client:
            if debug_callback:
                debug_callback("GEO_REPORT_FALLBACK_USED reason=no_openrouter_client")
            return self._fallback_recommendations(context, score.gaps, gsc_insights=gsc_insights)

        prompt = {
            "brand": context.brand_name,
            "category": context.category,
            "industry": context.industry,
            "region": context.region,
            "competitors": context.competitors,
            "ai_sov_pct": score.ai_sov_pct,
            "visibility_score": score.visibility_score,
            "gaps": [gap.to_dict() for gap in score.gaps],
            "gsc_top_queries": gsc_insights or [],
        }

        system = (
            "You are a senior growth marketing strategist. Create a concise action plan for improving "
            "brand visibility in LLM answers. Use the GSC data to align with high-demand search terms when present. "
            "Return valid JSON list with 5-10 items and keys: "
            "topic, content_format, why_this_works, urgency, competitor_to_displace."
        )
        if debug_callback:
            debug_callback(
                f"GEO_REPORT_LLM_CALL model={settings.openrouter_model} system_prompt={system} user_prompt={json.dumps(prompt)}"
            )

        try:
            LOGGER.debug("REPORT_LLM_CALL_START model=%s brand=%s", settings.openrouter_model, context.brand_name)
            completion = self.client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                temperature=0.2,
            )
            text = completion.choices[0].message.content or "[]"
            LOGGER.debug("REPORT_LLM_CALL_END model=%s response_len=%s", settings.openrouter_model, len(text))
            if debug_callback:
                debug_callback(f"GEO_REPORT_LLM_RESPONSE raw={text}")
            parsed = json.loads(text)
            if isinstance(parsed, list) and parsed:
                if debug_callback:
                    debug_callback(f"GEO_REPORT_LLM_PARSED recommendations_count={len(parsed[:10])}")
                return parsed[:10]
        except Exception as exc:
            LOGGER.exception("REPORT_LLM_CALL_ERROR model=%s error=%s", settings.openrouter_model, exc)
            if debug_callback:
                debug_callback(f"GEO_REPORT_LLM_FAILED error={exc}")

        if debug_callback:
            debug_callback("GEO_REPORT_FALLBACK_USED reason=llm_parse_or_call_failure")
        return self._fallback_recommendations(context, score.gaps, gsc_insights=gsc_insights)
