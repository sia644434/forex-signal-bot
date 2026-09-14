import asyncio
import math

import pytest

from worker.contracts import JobRequest, WorkerCapabilities
from worker.runtime import WorkerRuntime


def test_runtime_rejects_non_finite_timeout():
    runtime = WorkerRuntime("worker", WorkerCapabilities(), {})
    runtime.register("backtest", lambda payload: {"ok": True})
    for timeout in (math.nan, math.inf, -math.inf):
        result = asyncio.run(runtime.execute(JobRequest("non-finite", "backtest", timeout_seconds=timeout)))
        assert result.status == "INVALID"


def test_runtime_completion_cache_is_bounded():
    async def run():
        runtime = WorkerRuntime("worker", WorkerCapabilities(), {}, max_completed_jobs=2)
        runtime.register("backtest", lambda payload: {"job": payload["job"]})
        for index in range(3):
            result = await runtime.execute(
                JobRequest(f"job-{index}", "backtest", {"job": index}, timeout_seconds=1)
            )
            assert result.status == "COMPLETED"
        assert len(runtime._completed_jobs) == 2
        assert "job-0" not in runtime._completed_jobs
        assert set(runtime._completed_jobs) == {"job-1", "job-2"}

    asyncio.run(run())


def test_runtime_rejects_invalid_completion_cache_size():
    with pytest.raises(ValueError):
        WorkerRuntime("worker", WorkerCapabilities(), {}, max_completed_jobs=0)
