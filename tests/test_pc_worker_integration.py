import asyncio

from worker.client import PCWorkerClient
from worker.contracts import JobRequest
from worker.dispatcher import WorkerDispatcher
from worker.handlers import register_default_handlers
from worker.queue import WorkerQueue
from worker.runtime import WorkerRuntime


def test_all_declared_workloads_have_runtime_handlers():
    runtime = WorkerRuntime.create()
    register_default_handlers(runtime)
    assert runtime.capabilities.supported_jobs <= runtime.handlers.keys()


def test_dispatcher_accepts_declared_heavy_job():
    async def submit(request):
        return type("Result", (), {"status": "COMPLETED", "job_id": request.job_id})()

    result = asyncio.run(WorkerDispatcher(submit).submit(JobRequest("j1", "backtest")))
    assert result.status == "COMPLETED"


def test_dispatcher_uses_queue_before_transport_and_records_completion(tmp_path):
    async def submit(request):
        return type("Result", (), {
            "status": "COMPLETED",
            "job_id": request.job_id,
            "output": {"rows": 10},
            "error": None,
        })()

    queue = WorkerQueue(str(tmp_path / "queue.sqlite3"))
    dispatcher = WorkerDispatcher(submit, queue)
    result = asyncio.run(dispatcher.submit(JobRequest("queued", "backtest")))

    assert result.status == "COMPLETED"
    record = queue.get("queued")
    assert record is not None
    assert record.status == "COMPLETED"
    assert record.result == {"rows": 10}
    queue.close()


def test_dispatcher_records_transport_failure_in_queue():
    async def submit(request):
        raise RuntimeError("worker unavailable")

    queue = WorkerQueue()
    dispatcher = WorkerDispatcher(submit, queue)

    try:
        asyncio.run(dispatcher.submit(JobRequest("failed", "backtest")))
    except RuntimeError as exc:
        assert str(exc) == "worker unavailable"
    else:
        raise AssertionError("transport failure must propagate")

    record = queue.get("failed")
    assert record is not None
    assert record.status == "FAILED"
    assert record.error == "worker unavailable"
    queue.close()


def test_client_offline_is_controlled():
    result = PCWorkerClient("http://127.0.0.1:1", "test", timeout=1).submit(JobRequest("j2", "backtest"))
    assert result.status == "WORKER_OFFLINE"
