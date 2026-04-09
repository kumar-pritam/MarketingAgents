from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FileBackedRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state_file = Path(__file__).resolve().parents[2] / "data" / "platform_state.json"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        self.workspaces: dict[str, dict[str, Any]] = {}
        self.integrations: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self.runs: dict[str, dict[str, Any]] = {}
        self.workspace_runs: dict[str, list[str]] = defaultdict(list)
        self._load()

    def _load(self) -> None:
        if not self._state_file.exists():
            return
        try:
            raw = json.loads(self._state_file.read_text(encoding="utf-8"))
            self.workspaces = raw.get("workspaces", {})
            self.integrations = defaultdict(dict, raw.get("integrations", {}))
            self.runs = raw.get("runs", {})
            self.workspace_runs = defaultdict(list, raw.get("workspace_runs", {}))
        except Exception:
            # Keep startup resilient if the file is malformed.
            self.workspaces = {}
            self.integrations = defaultdict(dict)
            self.runs = {}
            self.workspace_runs = defaultdict(list)

    def _save(self) -> None:
        payload = {
            "workspaces": self.workspaces,
            "integrations": dict(self.integrations),
            "runs": self.runs,
            "workspace_runs": dict(self.workspace_runs),
        }
        tmp_file = self._state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_file.replace(self._state_file)

    def upsert_workspace(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            payload["updated_at"] = utc_now_iso()
            self.workspaces[payload["workspace_id"]] = payload
            self._save()
            return payload

    def get_workspace(self, workspace_id: str) -> dict[str, Any] | None:
        return self.workspaces.get(workspace_id)

    def list_workspaces(self) -> list[dict[str, Any]]:
        rows = list(self.workspaces.values())
        rows.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return rows

    def add_workspace_asset(self, workspace_id: str, asset: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                raise KeyError(workspace_id)
            assets = workspace.setdefault("assets", [])
            assets.append(asset)
            workspace["updated_at"] = utc_now_iso()
            self.workspaces[workspace_id] = workspace
            self._save()
            return workspace

    def set_integration(self, workspace_id: str, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.integrations[workspace_id][provider] = payload
            self._save()
            return payload

    def get_integrations(self, workspace_id: str) -> dict[str, dict[str, Any]]:
        return self.integrations.get(workspace_id, {})

    def add_run(self, run_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self.runs[run_id] = payload
            self.workspace_runs[payload["workspace_id"]].append(run_id)
            self._save()

    def update_run(self, run_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self.runs[run_id] = payload
            self._save()

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.runs.get(run_id)

    def list_runs(self, workspace_id: str) -> list[dict[str, Any]]:
        ids = self.workspace_runs.get(workspace_id, [])
        return [self.runs[rid] for rid in reversed(ids) if rid in self.runs]


repo = FileBackedRepository()
