import asyncio
from datetime import datetime, timezone

from config.settings import Settings
from services.worker.service import WorkerProcessingService
from worker.contracts import JobRequest
from worker.dispatcher import WorkerDispatcher
from worker.queue import WorkerQueue


def test_worker_service_without_transport_is_non_critical_and_controlled():
    settings = Settings(worker_queue_database_path=":memory:")
    service = WorkerProcessingService.from_settings(settings)

    result = asyncio.run(service.submit(JobRequest("offline", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is False
    assert service.health()["readiness"] == "UNCONFIGURED"
    assert service.health()["dispatcher"]["queue_configured"] is True
    assert service.health()["dispatcher"]["queue"]["total"] == 0


def test_worker_service_stop_closes_dispatcher_queue():
    service = WorkerProcessingService.from_settings(Settings(worker_queue_database_path=":memory:"))

    assert service.health()["dispatcher"]["queue_configured"] is True

    asyncio.run(service.stop())

    assert service.health()["dispatcher"] == {"queue_configured": False}


def test_worker_dispatcher_close_is_idempotent_and_releases_queue():
    queue = WorkerQueue(":memory:")
    dispatcher = WorkerDispatcher(queue=queue)

    dispatcher.close()
    dispatcher.close()

    assert dispatcher.health() == {"queue_configured": False}


def test_worker_service_uses_configured_transport(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_timeout=12,
        pc_worker_heartbeat_max_age=120,
    )
    captured = {}

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            captured.update(base_url=base_url, token=token, timeout=timeout)

        def submit(self, request):
            return type("Result", (), {
                "job_id": request.job_id,
                "status": "COMPLETED",
                "job_type": request.job_type,
                "output": {"ok": True},
                "error": None,
                "worker_id": "worker-1",
            })()

        def heartbeat(self):
            return {"status": "READY", "worker_id": "worker-1", "timestamp": datetime.now(timezone.utc).isoformat()}

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "UNKNOWN"
    assert service.health()["dispatcher"]["queue"]["total"] == 0

    result_before_heartbeat = asyncio.run(service.submit(JobRequest("blocked", "backtest")))
    assert result_before_heartbeat.status == "WORKER_OFFLINE"
    assert "UNKNOWN" in (result_before_heartbeat.error or "")

    heartbeat = asyncio.run(service.heartbeat())
    result = asyncio.run(service.submit(JobRequest("online", "backtest")))

    assert result.status == "COMPLETED"
    assert result.output == {"ok": True}
    assert heartbeat["status"] == "READY"
    assert heartbeat["worker_id"] == "worker-1"
    assert service.health()["readiness"] == "READY"
    assert service.health()["worker_id"] == "worker-1"
    assert service.health()["timestamp"] == heartbeat["timestamp"]
    assert captured == {
        "base_url": "http://worker.example",
        "token": "secret",
        "timeout": 12,
    }
    assert service.health()["configured"] is True
    assert service.health()["dispatcher"]["queue"]["completed"] == 1
    assert service.health()["dispatcher"]["queue"]["total"] == 1


def test_worker_service_blocks_dispatch_when_heartbeat_is_stale(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_heartbeat_max_age=60,
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def submit(self, request):
            raise AssertionError("stale worker must not receive a job")

        def heartbeat(self):
            return {
                "status": "READY",
                "worker_id": "worker-1",
                "timestamp": "2020-01-01T00:00:00+00:00",
            }

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    asyncio.run(service.heartbeat())
    result = asyncio.run(service.submit(JobRequest("stale", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert "STALE" in (result.error or "")
    assert service.health()["readiness"] == "STALE"
    assert service.health()["dispatcher"]["queue"]["total"] == 0


def test_worker_service_blocks_dispatch_when_heartbeat_reports_offline(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_timeout=12,
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def submit(self, request):
            raise AssertionError("offline worker must not receive a job")

        def heartbeat(self):
            return {"status": "WORKER_OFFLINE", "configured": True, "error": "connection refused"}

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    asyncio.run(service.heartbeat())
    result = asyncio.run(service.submit(JobRequest("offline", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert "WORKER_OFFLINE" in (result.error or "")
    assert service.health()["readiness"] == "WORKER_OFFLINE"
    assert service.health()["dispatcher"]["queue"]["total"] == 0


def test_worker_service_blocks_dispatch_when_heartbeat_timestamp_is_in_the_future(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_heartbeat_max_age=60,
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def submit(self, request):
            raise AssertionError("future-dated heartbeat must not receive a job")

        def heartbeat(self):
            return {
                "status": "READY",
                "worker_id": "worker-1",
                "timestamp": "2099-01-01T00:00:00+00:00",
            }

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    asyncio.run(service.heartbeat())
    result = asyncio.run(service.submit(JobRequest("future", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert "STALE" in (result.error or "")
    assert service.health()["readiness"] == "STALE"
    assert service.health()["dispatcher"]["queue"]["total"] == 0


def test_worker_service_blocks_dispatch_when_heartbeat_identity_is_missing(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def submit(self, request):
            raise AssertionError("malformed heartbeat must not receive a job")

        def heartbeat(self):
            return {
                "status": "READY",
                "timestamp": "2099-01-01T00:00:00+00:00",
            }

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    asyncio.run(service.heartbeat())
    result = asyncio.run(service.submit(JobRequest("missing-identity", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert "STALE" in (result.error or "")
    assert service.health()["readiness"] == "STALE"


def test_worker_service_health_marks_stale_ready_heartbeat(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_heartbeat_max_age=60,
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def heartbeat(self):
            return {
                "status": "READY",
                "worker_id": "worker-1",
                "timestamp": "2020-01-01T00:00:00+00:00",
            }

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    asyncio.run(service.heartbeat())

    assert service.health()["status"] == "degraded"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "STALE"


def test_worker_service_health_reflects_offline_heartbeat(monkeypatch):
    settings = Settings(
        worker_queue_database_path=":memory:",
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_timeout=12,
    )

    class FakeClient:
        def __init__(self, base_url, token, timeout):
            pass

        def submit(self, request):
            raise AssertionError("submit is not part of this test")

        def heartbeat(self):
            return {"status": "WORKER_OFFLINE", "configured": True, "error": "connection refused"}

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    heartbeat = asyncio.run(service.heartbeat())

    assert heartbeat["status"] == "WORKER_OFFLINE"
    assert service.health()["status"] == "degraded"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "WORKER_OFFLINE"


def test_worker_service_heartbeat_is_controlled_when_unconfigured():
    service = WorkerProcessingService.from_settings(Settings(worker_queue_database_path=":memory:"))

    heartbeat = asyncio.run(service.heartbeat())

    assert heartbeat == {"status": "WORKER_OFFLINE", "configured": False}
    assert service.health()["readiness"] == "UNCONFIGURED"



def test_worker_dispatcher_shutdown_waits_for_active_submission_before_closing_queue():
    queue = WorkerQueue(":memory:")
    started = asyncio.Event()
    release = asyncio.Event()

    async def submit(_request):
        started.set()
        await release.wait()
        return type("Result", (), {
            "job_id": "drain-1",
            "status": "COMPLETED",
            "job_type": "backtest",
            "output": {"ok": True},
            "error": None,
        })()

    dispatcher = WorkerDispatcher(submit=submit, queue=queue)

    async def scenario():
        task = asyncio.create_task(dispatcher.submit(JobRequest("drain-1", "backtest")))
        await started.wait()
        shutdown = asyncio.create_task(dispatcher.close_async(timeout_seconds=1))
        await asyncio.sleep(0)
        assert not shutdown.done()
        release.set()
        await task
        await shutdown

    asyncio.run(scenario())
    assert dispatcher.health() == {"queue_configured": False}
