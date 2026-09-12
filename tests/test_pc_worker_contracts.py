import asyncio

from worker.contracts import HEAVY_JOB_TYPES, JobRequest, WorkerCapabilities
from worker.dispatcher import WorkerDispatcher
from worker.runtime import WorkerRuntime


def test_requested_workloads_are_worker_owned():
    expected = {
        "backtest", "walk_forward", "monte_carlo", "hyperparameter_optimization",
        "feature_engineering", "multitimeframe_analysis", "heavy_market_scan",
        "ml_training", "xgboost_training", "lightgbm_training", "random_forest_training",
        "timeseries_training", "ensemble_training", "candle_batch_analysis", "dataset_build",
        "model_evaluation", "deep_learning_training", "transformer_training", "lstm_training",
        "gru_training", "medium_model_training", "multi_agent_analysis",
    }
    assert expected <= HEAVY_JOB_TYPES
    assert "coding_agent" not in HEAVY_JOB_TYPES


def test_worker_hardware_capabilities():
    capabilities = WorkerCapabilities()
    assert capabilities.cpu is True
    assert capabilities.gpu is True
    assert capabilities.max_ram_gb == 16
    assert capabilities.limited_jobs
    assert "coding_agent" not in capabilities.limited_jobs


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
