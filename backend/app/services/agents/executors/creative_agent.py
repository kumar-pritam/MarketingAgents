from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    theme = payload.get("creative_theme", "Performance-led simplicity")
    channels = payload.get("channels") or ["meta", "google", "landing page"]
    return {
        "creative_direction": f"{theme} with clear proof and single-CTA framing.",
        "visual_system": ["Bold product focal point", "Trust badge strip", "High-contrast CTA buttons"],
        "channel_variants": [{"channel": c, "variant": f"{c}-hero-v1"} for c in channels[:4]],
        "production_notes": ["Keep headline under 8 words", "Use one proof metric per asset"],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for creative system generation")
        parsed = run_llm_json(
            "You are a creative strategy lead. Return strict JSON only.",
            (
                "Return JSON keys: creative_direction, visual_system[], "
                "channel_variants[{channel,variant}], production_notes[]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.5,
            max_tokens=850,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)

    return {**base_output("creative_agent", payload), "dashboard": parsed}, logs
