from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.agents import AgentCard, AgentRunRequest, AgentRunResult, AgentSpec
from app.schemas.common import RunStatus
from app.services.agents.registry import registry
from app.services.agents.runtime import runtime
from app.storage.repository import repo

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentCard])
def list_agents(q: str | None = Query(default=None)) -> list[AgentCard]:
    specs = registry.list_agents(q=q)
    return [
        AgentCard(
            id=item.id,
            name=item.name,
            category=item.category,
            summary=item.summary,
            tags=item.tags,
        )
        for item in specs
    ]


@router.get("/{agent_id}", response_model=AgentSpec)
def agent_details(agent_id: str) -> AgentSpec:
    item = registry.get_agent(agent_id)
    if not item:
        raise HTTPException(status_code=404, detail="Agent not found")
    return item


@router.post("/run", response_model=AgentRunResult | RunStatus)
def run_agent(req: AgentRunRequest):
    if not registry.get_agent(req.agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

    if req.run_async:
        run_id = runtime.run_async(req.workspace_id, req.agent_id, req.input_payload)
        run = repo.get_run(run_id)
        return RunStatus(run_id=run_id, status="queued", updated_at=run["updated_at"])

    return runtime.run_sync(req.workspace_id, req.agent_id, req.input_payload)


@router.get("/runs/{run_id}", response_model=AgentRunResult | RunStatus)
def get_run(run_id: str):
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run["status"] != "completed":
        return RunStatus(run_id=run_id, status=run["status"], updated_at=run["updated_at"])

    return AgentRunResult(
        run_id=run_id,
        agent_id=run["agent_id"],
        workspace_id=run["workspace_id"],
        status=run["status"],
        output=run["output"],
        logs=run["logs"],
    )


@router.get("/history/{workspace_id}", response_model=list[AgentRunResult])
def run_history(workspace_id: str, agent_id: str | None = Query(default=None)) -> list[AgentRunResult]:
    rows = repo.list_runs(workspace_id)
    if agent_id:
        rows = [row for row in rows if row["agent_id"] == agent_id]
    completed = [
        AgentRunResult(
            run_id=row["run_id"],
            agent_id=row["agent_id"],
            workspace_id=row["workspace_id"],
            status=row["status"],
            output=row["output"],
            logs=row["logs"],
        )
        for row in rows
    ]
    return completed
