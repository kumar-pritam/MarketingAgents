from __future__ import annotations

import json

from app.services.agents.executors.common import base_output
from app.services.agents.executors.llm_helper import run_llm_json
from app.storage.repository import repo


def _fallback(payload: dict) -> dict:
    competitors = payload.get("competitors") or []
    return {
        "summary": "Your brand has mid-tier AI discoverability and can improve proof-based content coverage.",
        "ai_sov": {"your_brand": 34, "competitors": [{"name": c, "sov": 22} for c in competitors[:3]]},
        "visibility_score": 61,
        "cep_gaps": ["best-for comparisons", "pricing intent content", "trust/proof snippets"],
        "recommended_actions": [
            {"priority": "this_week", "action": "Publish 3 comparison pages with structured FAQ blocks."},
            {"priority": "this_week", "action": "Add pricing rationale + proof to high-intent pages."},
            {"priority": "this_month", "action": "Create LLM-friendly glossary and category explainer hub."},
        ],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs = []
    workspace = repo.get_workspace(payload.get("workspace_id", "")) or {}
    context = {
        "brand": workspace.get("brand_name"),
        "industry": workspace.get("industry"),
        "positioning": workspace.get("positioning"),
        "payload": payload,
    }
    try:
        logs.append("Calling LLM for GEO visibility diagnostics")
        parsed = run_llm_json(
            "You are a GEO strategist. Return strict JSON only.",
            (
                "Generate a marketer-friendly GEO dashboard JSON with keys: "
                "summary, ai_sov{your_brand,competitors[{name,sov}]}, visibility_score, "
                "cep_gaps[], recommended_actions[{priority,action}]. "
                f"Context: {json.dumps(context)}"
            ),
            temperature=0.3,
            max_tokens=900,
        )
        if not parsed:
            logs.append("LLM parsing failed. Using fallback.")
            parsed = _fallback(payload)
    except Exception as exc:
        logs.append(f"LLM failed: {exc}. Using fallback.")
        parsed = _fallback(payload)

    return {**base_output("geo_agent", payload), "dashboard": parsed}, logs
