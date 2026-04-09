from __future__ import annotations

from datetime import datetime


def base_output(agent_id: str, payload: dict) -> dict:
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "agent_id": agent_id,
        "input_echo": payload,
    }
