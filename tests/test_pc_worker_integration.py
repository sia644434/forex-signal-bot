import asyncio
import sqlite3
import time

from config.settings import Settings
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


def test_dispatcher_recovers_expired_jobs_on_initialization(tmp_path):
    database = tmp_path / "queue.sqlite3"
    queue = WorkerQueue(str(database))
    queue.enqueue(JobRequest("crashed", "backtest", timeout_seconds=1))
    claimed = queue.claim_next()
    assert claimed is not None
    queue.close()

    connection = sqlite3.connect(database)
    connection.execute("UPDATE worker_jobs SET claimed_at = ? WHERE job_id = ?", (time.time() - 10, "crashed"))
    connection.commit()
    connection.close()

    recovered_queue = WorkerQueue(str(database))
    WorkerDispatcher(queue=recovered_queue)
    record = recovered_queue.get("crashed")

    assert record is not None
    assert record.status == "PENDING"
    assert record.claimed_at is None
    recovered_queue.close()


def test_dispatcher_from_settings_uses_configured_queue(tmp_path):
    database = tmp_path / "configured-queue.sqlite3"
    settings = Settings(worker_queue_database_path=str(database), worker_queue_recovery_grace_seconds=12)
    dispatcher = WorkerDispatcher.from_settings(settings=settings)

    assert database.exists()
    result = asyncio.run(dispatcher.submit(JobRequest("offline", "backtest")))
    assert result.status == "WORKER_OFFLINE"
    dispatcher._queue.close()


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
