from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    return {
        "objective": payload.get("goal_metric", "Improve conversion rate"),
        "hypotheses": [
            "Benefit-first headline improves CTR vs feature-first copy.",
            "Proof block before CTA improves CVR.",
        ],
        "experiment_plan": [
            {"test": "Hero headline", "control": "Feature-led", "variant": "Outcome-led"},
            {"test": "Proof placement", "control": "Below fold", "variant": "Above CTA"},
        ],
        "decision_rule": "Choose winner at 95% confidence and >=7% relative lift.",
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    context = {"workspace": repo.get_workspace(payload.get("workspace_id", "")) or {}, "payload": payload}
    try:
        logs.append("Calling LLM for experimentation roadmap")
        parsed = run_llm_json(
            "You are a growth experimentation lead. Return strict JSON only.",
            (
                "Return JSON keys: objective, hypotheses[], "
                "experiment_plan[{test,control,variant}], decision_rule. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.35,
            max_tokens=850,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)

    return {**base_output("experimentation_agent", payload), "dashboard": parsed}, logs
