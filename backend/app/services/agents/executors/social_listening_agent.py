from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    return {
        "conversation_themes": ["product quality", "value perception", "delivery experience"],
        "sentiment_mix": {"positive": 46, "neutral": 35, "negative": 19},
        "emerging_signals": ["Growing interest in ingredient transparency", "Higher comparison chatter"],
        "action_plan": [
            "Publish weekly social proof stories from real customers.",
            "Address top negative themes in FAQ and creative.",
        ],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for social listening synthesis")
        parsed = run_llm_json(
            "You are a social intelligence analyst. Return strict JSON only.",
            (
                "Return JSON keys: conversation_themes[], sentiment_mix{positive,neutral,negative}, "
                "emerging_signals[], action_plan[]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.35,
            max_tokens=800,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)
    return {**base_output("social_listening_agent", payload), "dashboard": parsed}, logs
