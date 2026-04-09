from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    return {
        "executive_finding": "Landing page has message clarity gaps that suppress conversion intent.",
        "diagnostics": [
            "Hero section does not convey clear value in first 3 seconds.",
            "Proof and trust signals are too late in the scroll.",
            "Primary CTA lacks urgency and specificity.",
        ],
        "fixes": [
            {"priority": "p1", "fix": "Rewrite hero with quantified outcome + clearer CTA."},
            {"priority": "p1", "fix": "Move trust proof directly under hero."},
            {"priority": "p2", "fix": "Add objection-handling FAQ near CTA."},
        ],
        "expected_impact": "Potential CVR lift: 8-18% with clean implementation and A/B validation.",
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for landing page CRO audit")
        parsed = run_llm_json(
            "You are a CRO consultant. Return strict JSON only.",
            (
                "Return JSON keys: executive_finding, diagnostics[], "
                "fixes[{priority,fix}], expected_impact. "
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

    return {**base_output("landing_page_optimization_agent", payload), "dashboard": parsed}, logs
