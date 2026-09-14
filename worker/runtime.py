from __future__ import annotations

import asyncio
import logging
import math
import os
import platform
import socket
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .contracts import JobRequest, JobResult, WorkerCapabilities

logger = logging.getLogger(__name__)
Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


@dataclass
class WorkerRuntime:
    worker_id: str
    capabilities: WorkerCapabilities
    handlers: dict[str, Handler]
    max_completed_jobs: int = 1024
    _active_jobs: dict[str, asyncio.Task[JobResult]] = field(default_factory=dict, init=False, repr=False)
    _completed_jobs: dict[str, JobResult] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if isinstance(self.max_completed_jobs, bool) or not isinstance(self.max_completed_jobs, int) or self.max_completed_jobs < 1:
            raise ValueError("max_completed_jobs must be a positive integer")

    @classmethod
    def create(cls) -> "WorkerRuntime":
        worker_id = os.getenv("PC_WORKER_ID") or f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        gpu = os.getenv("PC_WORKER_GPU", "1").lower() not in {"0", "false", "no"}
        capabilities = WorkerCapabilities(gpu=gpu, max_ram_gb=int(os.getenv("PC_WORKER_RAM_GB", "16")))
        cache_size = int(os.getenv("PC_WORKER_COMPLETED_CACHE_SIZE", "1024"))
        return cls(worker_id=worker_id, capabilities=capabilities, handlers={}, max_completed_jobs=cache_size)

    def register(self, job_type: str, handler: Handler) -> None:
        if job_type not in self.capabilities.supported_jobs:
            raise ValueError(f"Unsupported worker job type: {job_type}")
        self.handlers[job_type] = handler

    def health(self) -> dict[str, Any]:
        return {"worker_id": self.worker_id, "status": "READY", "hostname": socket.gethostname(), "platform": platform.platform(), "python": platform.python_version(), "cpu": self.capabilities.cpu, "gpu": self.capabilities.gpu, "max_ram_gb": self.capabilities.max_ram_gb, "registered_jobs": sorted(self.handlers), "active_jobs": sorted(self._active_jobs), "completed_jobs": len(self._completed_jobs), "limited_jobs": sorted(self.capabilities.limited_jobs)}

    async def execute(self, request: JobRequest) -> JobResult:
        if not isinstance(request.job_id, str) or not request.job_id.strip():
            return JobResult(request.job_id, "INVALID", request.job_type, error="Job ID must not be empty", worker_id=self.worker_id)
        if not isinstance(request.timeout_seconds, (int, float)) or isinstance(request.timeout_seconds, bool) or not math.isfinite(float(request.timeout_seconds)) or request.timeout_seconds <= 0:
            return JobResult(request.job_id, "INVALID", request.job_type, error="Job timeout must be a finite number greater than zero", worker_id=self.worker_id)
        if request.job_type not in self.capabilities.supported_jobs:
            return JobResult(request.job_id, "UNSUPPORTED", request.job_type, error="Unsupported job type", worker_id=self.worker_id)
        handler = self.handlers.get(request.job_type)
        if handler is None:
            return JobResult(request.job_id, "UNSUPPORTED", request.job_type, error="No handler registered", worker_id=self.worker_id)

        cached = self._completed_jobs.get(request.job_id)
        if cached is not None:
            return cached
        active = self._active_jobs.get(request.job_id)
        if active is not None:
            return JobResult(request.job_id, "RUNNING", request.job_type, worker_id=self.worker_id)

        task = asyncio.create_task(self._run_job(request, handler))
        self._active_jobs[request.job_id] = task
        try:
            return await task
        finally:
            self._active_jobs.pop(request.job_id, None)

    async def _run_job(self, request: JobRequest, handler: Handler) -> JobResult:
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(handler(request.payload), timeout=request.timeout_seconds)
            else:
                result = await asyncio.wait_for(asyncio.to_thread(handler, request.payload), timeout=request.timeout_seconds)
            if not isinstance(result, dict):
                raise TypeError("Worker handler must return a dictionary.")
            completed = JobResult(request.job_id, "COMPLETED", request.job_type, output=result, worker_id=self.worker_id)
            self._completed_jobs[request.job_id] = completed
            while len(self._completed_jobs) > self.max_completed_jobs:
                oldest_job_id = next(iter(self._completed_jobs))
                self._completed_jobs.pop(oldest_job_id, None)
            return completed
        except asyncio.TimeoutError:
            return JobResult(request.job_id, "TIMEOUT", request.job_type, error="Worker job timeout", worker_id=self.worker_id)
        except asyncio.CancelledError:
            logger.warning("Worker job cancelled: %s", request.job_id)
            raise
        except Exception as exc:
            logger.exception("Worker job failed: %s", request.job_id)
            return JobResult(request.job_id, "FAILED", request.job_type, error=f"{type(exc).__name__}: {exc}", worker_id=self.worker_id)


__all__ = ["WorkerRuntime"]
