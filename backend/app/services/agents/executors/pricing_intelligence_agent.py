from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    return {
        "pricing_position": "Premium-mass with room for clearer value laddering.",
        "competitor_price_map": [
            {"segment": "entry", "your_brand": "₹999", "competitor_avg": "₹899"},
            {"segment": "core", "your_brand": "₹1499", "competitor_avg": "₹1399"},
        ],
        "elasticity_hypotheses": [
            "Entry segment is highly price sensitive.",
            "Core segment responds better to bundles than discounts.",
        ],
        "recommended_actions": [
            "Test bundle-led value framing before flat discounting.",
            "Introduce tiered anchor pricing on top 2 SKUs.",
        ],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for pricing intelligence")
        parsed = run_llm_json(
            "You are a pricing strategy consultant. Return strict JSON only.",
            (
                "Return JSON keys: pricing_position, "
                "competitor_price_map[{segment,your_brand,competitor_avg}], "
                "elasticity_hypotheses[], recommended_actions[]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.3,
            max_tokens=800,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)
    return {**base_output("pricing_intelligence_agent", payload), "dashboard": parsed}, logs
