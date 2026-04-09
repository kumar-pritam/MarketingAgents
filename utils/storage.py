from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "data" / "results"
AUDIT_LOG = ROOT / "data" / "audit_log.json"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def save_audit_payload(audit_id: str, payload: dict[str, Any]) -> Path:
    target = RESULTS_DIR / f"{audit_id}.json"
    _write_json(target, payload)
    return target


def append_audit_log(entry: dict[str, Any]) -> None:
    logs = _read_json(AUDIT_LOG, default=[])
    logs.append({"logged_at": datetime.utcnow().isoformat(), **entry})
    _write_json(AUDIT_LOG, logs)


def load_audit_history() -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for item in sorted(RESULTS_DIR.glob("*.json"), reverse=True):
        history.append(_read_json(item, default={}))
    return history
