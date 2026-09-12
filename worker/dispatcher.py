from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from config.settings import Settings
from .contracts import HEAVY_JOB_TYPES, JobRequest, JobResult
from .queue import WorkerQueue

JobHandler = Callable[[dict[str, Any]], Any]


class WorkerDispatcher:
    """Queue-backed dispatcher for heavy Forex worker jobs."""

    def __init__(
        self,
        submit: Callable[[JobRequest], Awaitable[JobResult]] | None = None,
        queue: WorkerQueue | None = None,
        recovery_grace_seconds: int = 30,
    ):
        self._submit = submit
        self._queue = queue
        if recovery_grace_seconds < 0:
            raise ValueError("Recovery grace must not be negative")
        if self._queue is not None:
            self._queue.recover_expired_running(recovery_grace_seconds)

    @classmethod
    def from_settings(
        cls,
        submit: Callable[[JobRequest], Awaitable[JobResult]] | None = None,
        settings: Settings | None = None,
    ) -> "WorkerDispatcher":
        """Build a queue-backed dispatcher from the central Forex settings boundary."""
        resolved = settings or Settings.load()
        queue = WorkerQueue(resolved.worker_queue_database_path)
        return cls(
            submit=submit,
            queue=queue,
            recovery_grace_seconds=resolved.worker_queue_recovery_grace_seconds,
        )

    async def submit(self, request: JobRequest) -> JobResult:
        if request.job_type not in HEAVY_JOB_TYPES:
            raise ValueError(f"Unsupported PC worker job type: {request.job_type}")
        if self._queue is None:
            if self._submit is None:
                return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="PC worker transport is not configured")
            return await self._submit(request)

        record = self._queue.enqueue(request)
        if record.status == "COMPLETED":
            return JobResult(request.job_id, "COMPLETED", request.job_type, output=record.result or {})
        if record.status in {"FAILED", "CANCELLED", "TIMEOUT"}:
            return JobResult(request.job_id, record.status, request.job_type, error=record.error)
        if record.status == "RUNNING":
            return JobResult(request.job_id, "RUNNING", request.job_type)

        claimed = self._queue.claim_next()
        if claimed is None or claimed.job_id != request.job_id:
            current = self._queue.get(request.job_id)
            return JobResult(request.job_id, current.status if current else "PENDING", request.job_type)

        if self._submit is None:
            self._queue.fail(request.job_id, "PC worker transport is not configured")
            return JobResult(request.job_id, "WORKER_OFFLINE", request.job_type, error="PC worker transport is not configured")

        try:
            result = await self._submit(request)
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError as exc:
            self._queue.timeout(request.job_id, str(exc) or "Worker job timeout")
            raise
        except Exception as exc:
            self._queue.fail(request.job_id, str(exc))
            raise

        if result.status == "COMPLETED":
            self._queue.finish(request.job_id, result=result.output)
        elif result.status == "TIMEOUT":
            self._queue.timeout(request.job_id, result.error or "Worker job timeout")
        elif result.status == "CANCELLED":
            self._queue.cancel(request.job_id)
        elif result.status == "FAILED":
            self._queue.fail(request.job_id, result.error or "Worker job failed")
        return result

    async def submit_many(self, requests: list[JobRequest]) -> list[JobResult]:
        return await asyncio.gather(*(self.submit(request) for request in requests))


__all__ = ["WorkerDispatcher"]
