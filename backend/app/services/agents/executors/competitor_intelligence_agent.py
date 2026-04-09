from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    rows = payload.get("competitors") or []
    names = [c.get("name", "Competitor") if isinstance(c, dict) else str(c) for c in rows][:3]
    while len(names) < 3:
        names.append(f"Competitor {chr(65 + len(names))}")
    return {
        "executive_summary": "Competitive threat is rising from sharper positioning and increased campaign velocity.",
        "scorecard": [
            {"competitor": names[0], "threat": "high", "momentum": "+", "message_fit": 78},
            {"competitor": names[1], "threat": "medium", "momentum": "+", "message_fit": 64},
            {"competitor": names[2], "threat": "medium", "momentum": "-", "message_fit": 57},
        ],
        "where_you_win": ["Distribution scale", "Trust familiarity"],
        "where_you_lose": ["Distinctive point-of-view", "Proof-led creative"],
        "recommended_actions": [
            {"urgency": "this_week", "action": "Launch counter-positioning landing page with proof assets."},
            {"urgency": "this_week", "action": "Deploy rapid response ad set against top competitor claim."},
            {"urgency": "this_month", "action": "Build monthly signal tracker for campaigns, pricing, and partnerships."},
        ],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    workspace = repo.get_workspace(payload.get("workspace_id", "")) or {}
    context = {"workspace": workspace, "payload": payload}
    try:
        logs.append("Calling LLM for competitor intelligence dashboard")
        parsed = run_llm_json(
            "You are a competitive intelligence strategist. Return strict JSON only.",
            (
                "Return JSON keys: executive_summary, scorecard[{competitor,threat,momentum,message_fit}], "
                "where_you_win[], where_you_lose[], recommended_actions[{urgency,action}]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.35,
            max_tokens=900,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)

    return {**base_output("competitor_intelligence_agent", payload), "dashboard": parsed}, logs
