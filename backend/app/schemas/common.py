from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class APIMessage(BaseModel):
    message: str


class RunStatus(BaseModel):
    run_id: str
    status: Literal["queued", "running", "completed", "failed"]
    updated_at: datetime


class IntegrationStatus(BaseModel):
    provider: str
    connected: bool
    scopes: list[str] = Field(default_factory=list)
    connected_at: datetime | None = None
