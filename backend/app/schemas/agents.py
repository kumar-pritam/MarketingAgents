from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    id: str
    name: str
    category: str
    summary: str
    tags: list[str] = Field(default_factory=list)


class AgentField(BaseModel):
    key: str
    label: str
    type: str
    required: bool = True
    placeholder: str | None = None


class AgentSpec(BaseModel):
    id: str
    name: str
    category: str
    summary: str
    description: str
    tags: list[str] = Field(default_factory=list)
    inputs: list[AgentField]
    outputs: list[str]
    helps_with: list[str]


class AgentRunRequest(BaseModel):
    workspace_id: str
    agent_id: str
    input_payload: dict[str, Any]
    run_async: bool = False


class AgentRunResult(BaseModel):
    run_id: str
    agent_id: str
    workspace_id: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
