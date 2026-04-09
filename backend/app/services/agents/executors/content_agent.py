from __future__ import annotations

import json
import logging
from typing import Any

from app.services.agents.executors.common import base_output
from app.services.llm.openrouter_client import call_openrouter
from app.storage.repository import repo

LOGGER = logging.getLogger("app.agent.content")


def _extract_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    raw = text[start : end + 1]
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _fallback_output(payload: dict[str, Any], workspace: dict[str, Any]) -> dict[str, Any]:
    brand_name = workspace.get("brand_name", "Your brand")
    goal = str(payload.get("campaign_goal", "Drive qualified conversions"))
    offer = str(payload.get("product_or_offer", "Core product"))
    audience = payload.get("audience_segments") or ["High-intent prospects"]
    cta = str(payload.get("primary_cta", "Shop Now"))
    return {
        "campaign_summary": {
            "brand_name": brand_name,
            "campaign_goal": goal,
            "product_or_offer": offer,
            "primary_audience": audience[0],
            "angle": f"{brand_name} should emphasize a clear value proposition tied to {goal.lower()}.",
        },
        "email_variants": [
            {
                "variant_name": "Value-first",
                "subject": f"{brand_name}: Better results with {offer}",
                "preheader": "See why customers are switching.",
                "body": f"Discover how {offer} helps {audience[0].lower()} achieve better outcomes with less friction.",
                "cta": cta,
            },
            {
                "variant_name": "Proof-first",
                "subject": f"Why {audience[0]} choose {brand_name}",
                "preheader": "Real proof and real outcomes.",
                "body": f"See key proof points, customer trust signals, and practical reasons to choose {brand_name}.",
                "cta": cta,
            },
        ],
        "push_notifications": [
            {"segment": audience[0], "message": f"{offer} from {brand_name} is now live.", "cta": cta},
            {"segment": audience[0], "message": f"Your next best step starts with {brand_name}.", "cta": cta},
        ],
        "ad_headlines": [
            f"{brand_name} for {audience[0]}",
            f"Upgrade to {offer} today",
            f"Proven value from {brand_name}",
            f"{offer} that actually converts",
        ],
        "ad_primary_texts": [
            f"{brand_name} helps {audience[0].lower()} with a clear, outcome-led approach.",
            f"Make the smarter switch to {offer} with confidence and proof.",
        ],
        "creative_brief": {
            "visual_direction": "Clean product-led visuals with social proof and single CTA focus.",
            "hooks": [
                "Outcome in first 3 seconds",
                "Trust signal above the fold",
                "Single conversion action",
            ],
        },
        "recommended_next_steps": [
            "Run A/B test between value-first and proof-first copy angles.",
            "Align landing page hero with top-performing headline.",
            "Retarget non-converters with proof-led email follow-up.",
        ],
    }


def run(payload: dict) -> tuple[dict, list[str]]:
    logs: list[str] = []
    workspace_id = payload.get("workspace_id", "")
    workspace = repo.get_workspace(workspace_id) or {}
    logs.append(f"Loaded workspace context for {workspace_id}")

    prompt_payload = {
        "brand_context": {
            "brand_name": workspace.get("brand_name", ""),
            "website": workspace.get("website", ""),
            "industry": workspace.get("industry", ""),
            "positioning": workspace.get("positioning", ""),
            "additional_details": workspace.get("additional_details", ""),
            "key_pages": workspace.get("key_pages", []),
            "assets": workspace.get("assets", []),
        },
        "campaign_input": payload,
    }

    system = (
        "You are a senior marketing strategist and copywriter. "
        "Return ONLY valid JSON with marketer-friendly, actionable content."
    )
    user = (
        "Generate a campaign-ready content pack.\n"
        "JSON keys required: campaign_summary, email_variants (2-3), push_notifications (2-4), "
        "ad_headlines (6-10), ad_primary_texts (2-4), creative_brief, recommended_next_steps (3-5).\n"
        f"Use this context:\n{json.dumps(prompt_payload)}"
    )

    try:
        logs.append("Calling OpenRouter LLM for content generation")
        LOGGER.info("CONTENT_AGENT_LLM_CALL workspace_id=%s payload=%s", workspace_id, prompt_payload)
        response_text = call_openrouter(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.5,
            max_tokens=1400,
        )
        logs.append("Received LLM response")
        parsed = _extract_json(response_text)
        if not parsed:
            logs.append("LLM response JSON parse failed. Using fallback output.")
            output = _fallback_output(payload, workspace)
        else:
            output = parsed
            logs.append("Parsed LLM JSON output successfully")
    except Exception as exc:
        logs.append(f"LLM call failed: {exc}. Using fallback output.")
        LOGGER.exception("CONTENT_AGENT_LLM_ERROR workspace_id=%s error=%s", workspace_id, exc)
        output = _fallback_output(payload, workspace)

    return {
        **base_output("content_agent", payload),
        "content_pack": output,
    }, logs
