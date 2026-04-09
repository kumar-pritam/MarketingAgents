from __future__ import annotations

from app.schemas.agents import AgentSpec
from app.specs.catalog import get_agent_specs


class AgentRegistry:
    def __init__(self) -> None:
        self._agents = {item.id: item for item in get_agent_specs()}

    def list_agents(self, q: str | None = None) -> list[AgentSpec]:
        values = list(self._agents.values())
        if not q:
            return values
        term = q.lower().strip()
        return [
            item
            for item in values
            if term in item.name.lower() or term in item.summary.lower() or any(term in t.lower() for t in item.tags)
        ]

    def get_agent(self, agent_id: str) -> AgentSpec | None:
        return self._agents.get(agent_id)


registry = AgentRegistry()
