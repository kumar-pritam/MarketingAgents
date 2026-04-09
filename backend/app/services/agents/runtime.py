from __future__ import annotations

import logging
from queue import Queue
from threading import Thread
from uuid import uuid4

from app.services.agents.execution_engine import execute_agent
from app.storage.repository import repo, utc_now_iso

LOGGER = logging.getLogger("app.runtime")


class AgentRuntime:
    def __init__(self) -> None:
        self._queue: Queue[tuple[str, str, dict]] = Queue()
        self._worker = Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def run_sync(self, workspace_id: str, agent_id: str, payload: dict):
        LOGGER.info("AGENT_RUN_SYNC_START workspace_id=%s agent_id=%s", workspace_id, agent_id)
        result = execute_agent(agent_id, {**payload, "workspace_id": workspace_id})
        run_record = {
            "run_id": result.run_id,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "status": result.status,
            "input_payload": payload,
            "output": result.output,
            "logs": result.logs,
            "updated_at": utc_now_iso(),
        }
        repo.add_run(result.run_id, run_record)
        LOGGER.info("AGENT_RUN_SYNC_END run_id=%s status=%s", result.run_id, result.status)
        return result

    def run_async(self, workspace_id: str, agent_id: str, payload: dict) -> str:
        run_id = str(uuid4())
        run_record = {
            "run_id": run_id,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "status": "queued",
            "input_payload": payload,
            "output": {},
            "logs": ["Queued"],
            "updated_at": utc_now_iso(),
        }
        repo.add_run(run_id, run_record)
        self._queue.put((run_id, agent_id, payload))
        LOGGER.info("AGENT_RUN_ASYNC_QUEUED run_id=%s agent_id=%s", run_id, agent_id)
        return run_id

    def _worker_loop(self) -> None:
        while True:
            run_id, agent_id, payload = self._queue.get()
            run = repo.get_run(run_id)
            if not run:
                continue
            run["status"] = "running"
            run["updated_at"] = utc_now_iso()
            run["logs"].append("Running")
            repo.update_run(run_id, run)
            LOGGER.info("AGENT_RUN_ASYNC_START run_id=%s", run_id)
            try:
                result = execute_agent(agent_id, {**payload, "workspace_id": run["workspace_id"]})
                run["status"] = "completed"
                run["output"] = result.output
                run["logs"].extend(result.logs)
            except Exception as exc:
                run["status"] = "failed"
                run["logs"].append(f"Failure: {exc}")
                LOGGER.exception("AGENT_RUN_ASYNC_FAILED run_id=%s error=%s", run_id, exc)
            run["updated_at"] = utc_now_iso()
            repo.update_run(run_id, run)
            LOGGER.info("AGENT_RUN_ASYNC_END run_id=%s status=%s", run_id, run["status"])


runtime = AgentRuntime()
