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


def test_worker_service_uses_configured_transport(monkeypatch):
    settings = Settings(
        pc_worker_url="http://worker.example",
        pc_worker_token="secret",
        pc_worker_timeout=12,
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

    monkeypatch.setattr("services.worker.service.PCWorkerClient", FakeClient)
    service = WorkerProcessingService.from_settings(settings)

    result = asyncio.run(service.submit(JobRequest("online", "backtest")))

    assert result.status == "COMPLETED"
    assert result.output == {"ok": True}
    assert captured == {
        "base_url": "http://worker.example",
        "token": "secret",
        "timeout": 12,
    }
    assert service.health()["configured"] is True
