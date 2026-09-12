from __future__ import annotations

import asyncio
from typing import Any

from config.settings import Settings
from services.base import BaseService
from worker.client import PCWorkerClient
from worker.contracts import JobRequest, JobResult
from worker.dispatcher import WorkerDispatcher


class WorkerProcessingService(BaseService):
    """Application boundary for optional heavy Forex PC-worker processing."""

    name = "worker_processing"
    critical = False

    def __init__(self, dispatcher: WorkerDispatcher, configured: bool, client: PCWorkerClient | None = None) -> None:
        if dispatcher is None:
            raise TypeError("dispatcher cannot be None")
        self.dispatcher = dispatcher
        self.configured = configured
        self._client = client
        self._last_heartbeat: dict[str, Any] | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "WorkerProcessingService":
        resolved = settings or Settings.load()
        client: PCWorkerClient | None = None
        if resolved.pc_worker_url:
            client = PCWorkerClient(
                resolved.pc_worker_url,
                resolved.pc_worker_token or "",
                timeout=resolved.pc_worker_timeout,
            )

        async def submit(request: JobRequest) -> JobResult:
            if client is None:
                return JobResult(
                    request.job_id,
                    "WORKER_OFFLINE",
                    request.job_type,
                    error="PC worker transport is not configured",
                )
            return await asyncio.to_thread(client.submit, request)

        dispatcher = WorkerDispatcher.from_settings(
            settings=resolved,
            submit=submit,
        )
        return cls(dispatcher=dispatcher, configured=client is not None, client=client)

    async def submit(self, request: JobRequest) -> JobResult:
        return await self.dispatcher.submit(request)

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await self.dispatcher.submit_many(requests)

    async def heartbeat(self) -> dict[str, Any]:
        """Verify authenticated PC-worker readiness through the application boundary."""
        if self._client is None:
            result = {"status": "WORKER_OFFLINE", "configured": False}
        else:
            result = await asyncio.to_thread(self._client.heartbeat)
        self._last_heartbeat = result
        return result

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def health(self) -> dict[str, Any]:
        readiness = "UNCONFIGURED" if not self.configured else "UNKNOWN"
        if self._last_heartbeat is not None:
            readiness = str(self._last_heartbeat.get("status", "UNKNOWN"))

        health: dict[str, Any] = {
            "service": self.name,
            "status": "ok",
            "critical": self.critical,
            "configured": self.configured,
            "readiness": readiness,
        }
        if self._last_heartbeat is not None:
            for key in ("worker_id", "timestamp"):
                if key in self._last_heartbeat:
                    health[key] = self._last_heartbeat[key]
        return health


__all__ = ["WorkerProcessingService"]
