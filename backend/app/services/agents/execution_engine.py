from __future__ import annotations

from uuid import uuid4

from app.schemas.agents import AgentRunResult
from app.services.agents.executors import EXECUTORS


def execute_agent(agent_id: str, payload: dict) -> AgentRunResult:
    run_id = str(uuid4())
    fn = EXECUTORS.get(agent_id)
    logs = [f"Executor completed for {agent_id}"]
    if fn:
        result = fn(payload)
        if isinstance(result, tuple) and len(result) == 2:
            output, run_logs = result
            if isinstance(run_logs, list):
                logs = [str(item) for item in run_logs]
        else:
            output = result
    else:
        output = {"message": f"No executor found for {agent_id}", "input_echo": payload}
        logs = [f"No executor found for {agent_id}"]

    return AgentRunResult(
        run_id=run_id,
        agent_id=agent_id,
        workspace_id=payload.get("workspace_id", "unknown"),
        status="completed",
        output=output,
        logs=logs,
    )
