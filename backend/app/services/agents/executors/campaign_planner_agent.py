from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    return {
        "campaign_thesis": "Own a clear problem-solution narrative with proof in every channel.",
        "channel_plan": [
            {"channel": "Meta", "role": "Demand capture", "kpi": "CPL"},
            {"channel": "Search", "role": "High-intent conversion", "kpi": "CPA"},
            {"channel": "Email", "role": "Nurture and retention", "kpi": "CVR"},
        ],
        "message_house": ["Problem framing", "Differentiator", "Proof", "CTA"],
        "90_day_plan": ["Weeks 1-2 setup", "Weeks 3-6 scale winners", "Weeks 7-12 optimize funnel"],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for campaign planning")
        parsed = run_llm_json(
            "You are a growth marketing planner. Return strict JSON only.",
            (
                "Return JSON keys: campaign_thesis, "
                "channel_plan[{channel,role,kpi}], message_house[], 90_day_plan[]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.4,
            max_tokens=900,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)
    return {**base_output("campaign_planner_agent", payload), "dashboard": parsed}, logs
