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

    def __init__(self, dispatcher: WorkerDispatcher, configured: bool) -> None:
        if dispatcher is None:
            raise TypeError("dispatcher cannot be None")
        self.dispatcher = dispatcher
        self.configured = configured

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
        return cls(dispatcher=dispatcher, configured=client is not None)

    async def submit(self, request: JobRequest) -> JobResult:
        return await self.dispatcher.submit(request)

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await self.dispatcher.submit_many(requests)

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def health(self) -> dict[str, Any]:
        return {
            "service": self.name,
            "status": "ok",
            "critical": self.critical,
            "configured": self.configured,
        }


__all__ = ["WorkerProcessingService"]
