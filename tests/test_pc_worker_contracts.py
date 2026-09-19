import asyncio
import threading

from worker.contracts import HEAVY_JOB_TYPES, JobRequest, WorkerCapabilities
from worker.dispatcher import WorkerDispatcher
from worker.queue import WorkerQueue
from worker.runtime import WorkerRuntime


def test_requested_workloads_are_worker_owned():
    expected = {
        "backtest", "walk_forward", "monte_carlo", "hyperparameter_optimization",
        "feature_engineering", "multitimeframe_analysis", "heavy_market_scan",
        "ml_training", "xgboost_training", "lightgbm_training", "random_forest_training",
        "timeseries_training", "ensemble_training", "candle_batch_analysis", "dataset_build",
        "model_evaluation", "deep_learning_training", "transformer_training", "lstm_training",
        "gru_training", "medium_model_training", "correlation_matrix", "portfolio_stress", "stress_sensitivity", "counterfactual_batch", "market_replay", "time_machine", "strategy_evaluation",
    }
    assert expected <= HEAVY_JOB_TYPES
    assert "coding_agent" not in HEAVY_JOB_TYPES
    assert "multi_agent_analysis" not in HEAVY_JOB_TYPES


def test_worker_hardware_capabilities():
    capabilities = WorkerCapabilities()
    assert capabilities.cpu is True
    assert capabilities.gpu is True
    assert capabilities.max_ram_gb == 16
    assert capabilities.limited_jobs
    assert "coding_agent" not in capabilities.limited_jobs
    assert "multi_agent_analysis" not in capabilities.limited_jobs


def test_offline_worker_does_not_block_railway():
    request = JobRequest("test-1", "backtest", {"symbol": "EURUSD"})
    result = asyncio.run(WorkerDispatcher().submit(request))
    assert result.status == "WORKER_OFFLINE"
    assert result.job_id == "test-1"


def test_duplicate_job_id_does_not_execute_completed_work_twice():
    calls = 0

    async def handler(_payload):
        nonlocal calls
        calls += 1
        return {"ok": True}

    runtime = WorkerRuntime("worker-1", WorkerCapabilities(), {})
    runtime.register("backtest", handler)
    request = JobRequest("job-1", "backtest", timeout_seconds=5)

    first = asyncio.run(runtime.execute(request))
    second = asyncio.run(runtime.execute(request))

    assert first.status == "COMPLETED"
    assert second == first
    assert calls == 1


def test_sync_handler_is_bounded_by_timeout_without_blocking_event_loop():
    async def run():
        started = asyncio.Event()

        def handler(_payload):
            import time
            started.set()
            time.sleep(0.2)
            return {"ok": True}

        runtime = WorkerRuntime("worker-1", WorkerCapabilities(), {})
        runtime.register("backtest", handler)
        task = asyncio.create_task(runtime.execute(JobRequest("job-sync-timeout", "backtest", timeout_seconds=0.05)))
        await started.wait()
        result = await task
        assert result.status == "TIMEOUT"
        assert "job-sync-timeout" not in runtime._completed_jobs

    asyncio.run(run())


def test_timed_out_sync_job_stays_inflight_until_underlying_thread_finishes():
    async def run():
        finished = threading.Event()
        calls = 0

        def handler(_payload):
            nonlocal calls
            import time
            calls += 1
            time.sleep(0.08)
            finished.set()
            return {"ok": True}

        runtime = WorkerRuntime("worker-1", WorkerCapabilities(), {})
        runtime.register("backtest", handler)
        request = JobRequest("job-sync-fenced", "backtest", timeout_seconds=0.01)
        first = await runtime.execute(request)
        assert first.status == "TIMEOUT"

        duplicate = await runtime.execute(request)
        assert duplicate.status == "RUNNING"
        assert calls == 1

        await asyncio.to_thread(finished.wait)
        await asyncio.sleep(0)
        cached = await runtime.execute(request)
        assert cached.status == "COMPLETED"
        assert cached.output == {"ok": True}
        assert calls == 1

    asyncio.run(run())


def test_invalid_job_timeout_is_rejected_before_execution():
    calls = 0

    def handler(_payload):
        nonlocal calls
        calls += 1
        return {"ok": True}

    runtime = WorkerRuntime("worker-1", WorkerCapabilities(), {})
    runtime.register("backtest", handler)

    result = asyncio.run(runtime.execute(JobRequest("job-2", "backtest", timeout_seconds=0)))

    assert result.status == "INVALID"
    assert calls == 0


def test_cancelled_job_is_not_cached_as_completed():
    started = asyncio.Event()

    async def handler(_payload):
        started.set()
        await asyncio.sleep(60)
        return {"ok": True}

    async def run():
        runtime = WorkerRuntime("worker-1", WorkerCapabilities(), {})
        runtime.register("backtest", handler)
        task = asyncio.create_task(runtime.execute(JobRequest("job-3", "backtest", timeout_seconds=120)))
        await started.wait()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert "job-3" not in runtime._completed_jobs

    asyncio.run(run())


def test_concurrent_dispatches_execute_their_own_jobs():
    calls: list[str] = []

    async def submit(request: JobRequest):
        calls.append(request.job_id)
        await asyncio.sleep(0)
        return type("Result", (), {
            "status": "COMPLETED",
            "error": None,
            "output": {"job_id": request.job_id},
        })()

    async def run():
        queue = WorkerQueue()
        dispatcher = WorkerDispatcher(submit=submit, queue=queue)
        low = JobRequest("low", "backtest", priority=10)
        high = JobRequest("high", "backtest", priority=90)
        results = await asyncio.gather(dispatcher.submit(low), dispatcher.submit(high))
        assert [result.status for result in results] == ["COMPLETED", "COMPLETED"]
        assert set(calls) == {"low", "high"}
        assert queue.get("low").status == "COMPLETED"
        assert queue.get("high").status == "COMPLETED"
        dispatcher.close()


    asyncio.run(run())


def test_dispatcher_cancellation_does_not_strand_running_job():
    started = asyncio.Event()

    async def submit(_request: JobRequest):
        started.set()
        await asyncio.sleep(60)
        return type("Result", (), {"status": "COMPLETED", "error": None, "output": {}})()

    async def run():
        queue = WorkerQueue()
        dispatcher = WorkerDispatcher(submit=submit, queue=queue)
        task = asyncio.create_task(dispatcher.submit(JobRequest("cancelled", "backtest")))
        await started.wait()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        record = queue.get("cancelled")
        assert record is not None
        assert record.status == "CANCELLED"
        dispatcher.close()

    asyncio.run(run())


def test_robustness_research_is_worker_owned():
    from worker.contracts import HEAVY_JOB_TYPES
    assert "robustness_analysis" in HEAVY_JOB_TYPES
