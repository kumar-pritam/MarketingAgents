from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo

LOGGER = logging.getLogger("app.agent.brand_equity")


def _filter_workspace_context(workspace: dict[str, Any]) -> dict[str, Any]:
    return {
        "brand_name": workspace.get("brand_name", ""),
        "website": workspace.get("website", ""),
        "industry": workspace.get("industry", ""),
        "geography": workspace.get("geography", ""),
        "category": workspace.get("category", ""),
        "positioning": workspace.get("positioning", ""),
    }


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif value is not None and value != "" and value != []:
            result[key] = value
    return result


def _extract_json_from_text(text: str) -> dict | None:
    """Extract JSON from LLM response text, handling various formats."""
    if not text:
        return None

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object pattern { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    return None


def run(payload: dict) -> tuple[dict, list[str]]:
    logs: list[str] = []
    debug_info: dict[str, Any] = {}
    agent_id = "brand_equity_tracker_agent"
    workspace_id = payload.get("workspace_id", "")
    workspace = repo.get_workspace(workspace_id) or {}

    brand_name = str(
        payload.get("brand_name") or workspace.get("brand_name") or "Your Brand"
    )
    brand_context = str(
        payload.get("brand_context") or workspace.get("brand_summary") or ""
    )

    competitors_list = payload.get("competitors") or []
    category_keywords_list = payload.get("category_keywords") or []
    time_window = payload.get("time_window", "Last 90 days")
    primary_concern = payload.get("primary_concern", "All")

    logs.append(f"Starting Brand Equity analysis for {brand_name}")
    logs.append(
        f"Competitors: {', '.join(competitors_list) if competitors_list else 'None'}"
    )
    logs.append(f"Time window: {time_window}")
    logs.append(f"Primary concern: {primary_concern}")

    # Simplified, clearer system prompt
    system_prompt = """You are a brand strategist. Return ONLY valid JSON matching this exact structure:

{
  "brand_health_score": {
    "overall_score": 65,
    "rating": "Moderate (50-74)",
    "verdict": "Brand shows moderate awareness but needs stronger differentiation in AI visibility.",
    "dimensions": [
      {"label": "Awareness", "score": 13},
      {"label": "Sentiment", "score": 12},
      {"label": "Share of Voice", "score": 14},
      {"label": "AI Visibility", "score": 10},
      {"label": "Competitive Position", "score": 16}
    ]
  },
  "pulse_summary": [
    "Brand mentions growing on Reddit → Opportunity to amplify positive sentiment",
    "Competitor X increasing ad spend → Share of voice at risk",
    "AI platforms partially mention the brand → Need better GEO strategy",
    "Pricing concerns in reviews → Sentiment trending down"
  ],
  "biggest_risk": {
    "what": "Low AI visibility in LLM responses",
    "evidence": "Brand rarely cited when competitors are mentioned in AI searches",
    "severity": "High",
    "action": "Publish authoritative content on key topics to improve AI citations"
  },
  "biggest_opportunity": {
    "what": "Own the sustainability narrative",
    "why_now": "No competitor has claimed this positioning yet in public discourse",
    "action": "Release brand story content around sustainability by end of month"
  },
  "ai_visibility_snapshot": {
    "status": "Partial",
    "context_line": "Brand appears in product comparisons but not in category recommendations",
    "leader_vs_competitors": "Competitor Y leads AI visibility with 3x more citations"
  },
  "brand_associations": {
    "owned": ["innovation", "quality", "reliability", "value", "trust"],
    "intended": ["sustainability", "innovation", "community", "premium", "trust"],
    "gap_line": "Brand perceived as traditional; sustainability positioning not resonating"
  },
  "top_3_actions": [
    "Publish thought leadership on sustainability → Own differentiated positioning",
    "Optimize key pages for AI discovery → Improve GEO visibility by 40%",
    "Address pricing concerns in reviews → Shift sentiment from neutral to positive"
  ]
}

Rules:
- Return ONLY the JSON, no markdown, no explanation
- If you cannot find data for a field, provide reasonable estimates based on brand context
- Fill in realistic values - do not leave arrays empty or strings blank
- scores should be 0-20 for dimensions, overall 0-100"""

    user_prompt = f"""Conduct a brand health audit for {brand_name}.

Brand context: {brand_context}
Competitors: {", ".join(competitors_list) if competitors_list else "None specified"}
Category keywords: {", ".join(category_keywords_list) if category_keywords_list else "None specified"}
Time window: {time_window}
Primary concern: {primary_concern}

Search for: news, social signals, reviews, and AI recommendations for {brand_name} vs competitors.

Return ONLY the JSON matching the schema provided. Fill in realistic values."""

    parsed = None
    raw_response = None

    try:
        raw_response = run_llm_json(
            system_prompt, user_prompt, temperature=0.4, max_tokens=2500
        )
        logs.append(f"LLM response type: {type(raw_response)}")

        if raw_response:
            debug_info["llm_raw"] = str(raw_response)[:500] if raw_response else None
            parsed = (
                _extract_json_from_text(raw_response)
                if isinstance(raw_response, str)
                else raw_response
            )
            if parsed:
                logs.append(
                    f"Successfully parsed JSON with {len(parsed)} top-level keys"
                )
            else:
                logs.append("WARNING: Could not extract valid JSON from LLM response")
        else:
            logs.append("WARNING: LLM returned empty response")

    except Exception as exc:
        LOGGER.exception("BRAND_EQUITY_LLM_ERROR error=%s", exc)
        logs.append(f"LLM call failed: {exc}")
        debug_info["error"] = str(exc)

    fallback = _get_fallback_equity_report(brand_name, competitors_list, time_window)

    if parsed:
        report = _deep_merge(fallback, parsed)

        # Check which fields were actually filled by LLM
        required_sections = [
            "brand_health_score",
            "pulse_summary",
            "biggest_risk",
            "biggest_opportunity",
            "ai_visibility_snapshot",
            "brand_associations",
            "top_3_actions",
        ]
        filled_sections = [k for k in required_sections if k in parsed and parsed[k]]
        missing_sections = [
            k for k in required_sections if k not in parsed or not parsed[k]
        ]

        logs.append(
            f"LLM filled {len(filled_sections)}/{len(required_sections)} sections"
        )
        if missing_sections:
            logs.append(f"Missing sections: {', '.join(missing_sections)}")

        debug_info["source"] = "llm"
        debug_info["filled_sections"] = filled_sections
        debug_info["missing_sections"] = missing_sections
    else:
        logs.append("Using fallback - LLM returned no valid data")
        report = fallback
        debug_info["source"] = "fallback"

    output = {
        **base_output(agent_id, payload),
        "brand_equity_data": report,
        "_debug": debug_info,
    }
    return output, logs


def _get_fallback_equity_report(
    brand_name: str, competitors: list[str], time_window: str
) -> dict:
    return {
        "brand_health_score": {
            "overall_score": 55,
            "rating": "Moderate (50-74)",
            "verdict": f"Brand health baseline established for {brand_name}. Run with more context for actionable insights.",
            "dimensions": [
                {"label": "Awareness", "score": 11},
                {"label": "Sentiment", "score": 10},
                {"label": "Share of Voice", "score": 11},
                {"label": "AI Visibility", "score": 12},
                {"label": "Competitive Position", "score": 11},
            ],
        },
        "pulse_summary": [
            "No live data available → Run with workspace context for signals",
            "No sentiment data → Add brand details to the workspace",
            "No share of voice data → Specify competitors for comparison",
            "No AI visibility data → Connect integrations for live data",
        ],
        "biggest_risk": {
            "what": "Insufficient brand context",
            "evidence": f"Minimal input data provided for {time_window}",
            "severity": "Medium",
            "action": "Add brand positioning, competitors, and keywords to workspace for richer analysis",
        },
        "biggest_opportunity": {
            "what": "Workspace enrichment",
            "why_now": "More context = more accurate brand health assessment",
            "action": "Fill in brand details, add competitors, and define category keywords",
        },
        "ai_visibility_snapshot": {
            "status": "Unknown",
            "context_line": "No AI visibility data available without live search",
            "leader_vs_competitors": "Unable to determine without competitor analysis",
        },
        "brand_associations": {
            "owned": [
                "[Add context]",
                "[Add context]",
                "[Add context]",
                "[Add context]",
                "[Add context]",
            ],
            "intended": ["[From positioning]"],
            "gap_line": "Add brand positioning to see association gaps",
        },
        "top_3_actions": [
            "Add brand context to workspace → Enable deeper signal analysis",
            "Specify competitors → Enable share of voice comparison",
            "Define category keywords → Improve report accuracy",
        ],
    }
