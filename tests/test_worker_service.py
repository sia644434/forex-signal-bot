import asyncio

from config.settings import Settings
from services.worker.service import WorkerProcessingService
from worker.contracts import JobRequest


def test_worker_service_without_transport_is_non_critical_and_controlled():
    settings = Settings()
    service = WorkerProcessingService.from_settings(settings)

    result = asyncio.run(service.submit(JobRequest("offline", "backtest")))

    assert result.status == "WORKER_OFFLINE"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is False
    assert service.health()["readiness"] == "UNCONFIGURED"


def test_worker_service_uses_configured_transport():
    settings = Settings(
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
            return {"status": "READY", "worker_id": "worker-1", "timestamp": "2099-09-12T00:00:00+00:00"}

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "UNKNOWN"

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
    assert service.health()["timestamp"] == "2099-09-12T00:00:00+00:00"
    assert captured == {
        "base_url": "http://worker.example",
        "token": "secret",
        "timeout": 12,
    }
    assert service.health()["configured"] is True


def test_worker_service_blocks_dispatch_when_heartbeat_is_stale(monkeypatch):
    settings = Settings(
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


def test_worker_service_blocks_dispatch_when_heartbeat_reports_offline(monkeypatch):
    settings = Settings(
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


def test_worker_service_health_marks_stale_ready_heartbeat(monkeypatch):
    settings = Settings(
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

    assert service.health()["status"] == "ok"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "STALE"


def test_worker_service_health_reflects_offline_heartbeat(monkeypatch):
    settings = Settings(
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
    assert service.health()["status"] == "ok"
    assert service.health()["critical"] is False
    assert service.health()["configured"] is True
    assert service.health()["readiness"] == "WORKER_OFFLINE"


def test_worker_service_heartbeat_is_controlled_when_unconfigured():
    service = WorkerProcessingService.from_settings(Settings())

    heartbeat = asyncio.run(service.heartbeat())

    assert heartbeat == {"status": "WORKER_OFFLINE", "configured": False}
    assert service.health()["readiness"] == "UNCONFIGURED"
