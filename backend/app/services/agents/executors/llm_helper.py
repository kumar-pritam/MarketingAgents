from __future__ import annotations

import json
from typing import Any

from app.services.llm.openrouter_client import call_openrouter


def extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    raw = text[start : end + 1]
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def run_llm_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.4, max_tokens: int = 1200) -> dict[str, Any]:
    text = call_openrouter(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return extract_json_object(text)
