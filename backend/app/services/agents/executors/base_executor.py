from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.services.agents.executors.common import base_output
from app.storage.repository import repo

LOGGER = logging.getLogger("app.agent.base")


def _extract_json(text: str) -> dict | None:
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


def _build_base_payload(payload: dict, workspace_id: str) -> dict:
    """Build common payload with workspace context."""
    workspace = repo.get_workspace(workspace_id) or {}
    return {
        **payload,
        "brand_name": payload.get("brand_name") or workspace.get("brand_name") or "",
        "brand_context": payload.get("brand_context")
        or workspace.get("brand_summary")
        or workspace.get("positioning")
        or "",
        "workspace_website": workspace.get("website", ""),
        "workspace_industry": workspace.get("industry", ""),
        "workspace_geography": workspace.get("geography", ""),
    }


def _call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> dict | None:
    """Call LLM and extract JSON response. Returns None if parsing fails."""
    try:
        from app.services.llm.openrouter_client import call_openrouter

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = call_openrouter(
            messages, temperature=temperature, max_tokens=max_tokens
        )
        return _extract_json(response)
    except Exception as exc:
        LOGGER.warning("LLM call failed: %s", exc)
        return None


def run_agent(
    agent_id: str,
    agent_title: str,
    system_prompt: str,
    user_prompt_template: str,
    payload: dict,
    required_fields: list[str] | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> tuple[dict, list[str]]:
    """
    Unified agent executor with proper JSON handling.

    Args:
        agent_id: Unique identifier for the agent
        agent_title: Display title for the agent
        system_prompt: System prompt for the LLM
        user_prompt_template: User prompt with {{variable}} placeholders
        payload: Input payload from the request
        required_fields: List of required output fields (for fallback)
        temperature: LLM temperature
        max_tokens: Max tokens for LLM response

    Returns:
        Tuple of (output dict, logs list)
    """
    logs: list[str] = []
    debug_info: dict[str, Any] = {}
    workspace_id = payload.get("workspace_id", "")

    base_payload = _build_base_payload(payload, workspace_id)

    # Replace template variables
    def apply_template(text: str) -> str:
        for key, value in base_payload.items():
            if value is not None:
                # Handle list values - join with comma
                if isinstance(value, list):
                    text = text.replace(
                        f"{{{{{key}}}}}", ", ".join(str(v) for v in value if v)
                    )
                else:
                    text = text.replace(f"{{{{{key}}}}}", str(value))
        # Remove any remaining {{variable}} placeholders
        text = re.sub(r"\{\{[^}]+\}\}", "", text)
        return text

    user_prompt = apply_template(user_prompt_template)

    logs.append(
        f"Starting {agent_title} for {base_payload.get('brand_name', 'unknown')}"
    )

    # Call LLM
    parsed = _call_llm(
        system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens
    )

    if parsed:
        debug_info["source"] = "llm"
        debug_info["fields_returned"] = list(parsed.keys())
        logs.append(f"LLM returned {len(parsed)} fields")

        # Check required fields
        if required_fields:
            missing = [f for f in required_fields if f not in parsed or not parsed[f]]
            if missing:
                logs.append(f"Missing fields: {', '.join(missing)}")
                debug_info["missing_fields"] = missing
    else:
        debug_info["source"] = "fallback"
        logs.append("LLM returned no valid JSON - using fallback")
        parsed = {}

    # Build output
    output = {
        **base_output(agent_id, payload),
        "agent_title": agent_title,
        "result": parsed,
        "_debug": debug_info,
    }

    logs.append(f"{agent_id} completed")
    return output, logs
