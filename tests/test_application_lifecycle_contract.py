from __future__ import annotations

import asyncio

import pytest

from core.application import Application


class FakeServiceManager:
    def __init__(self, events: list[str], health_result: dict | None = None) -> None:
        self.events = events
        self.health_result = health_result or {}

    async def start_all(self) -> None:
        self.events.append("services.start")

    async def stop_all(self) -> None:
        self.events.append("services.stop")

    def health(self) -> dict:
        return self.health_result


class FakeHealthServer:
    def __init__(
        self,
        events: list[str],
        fail_on_start: bool = False,
        fail_on_stop: bool = False,
    ) -> None:
        self.events = events
        self.fail_on_start = fail_on_start
        self.fail_on_stop = fail_on_stop

    def start(self) -> None:
        self.events.append("health.start")
        if self.fail_on_start:
            raise RuntimeError("health server failed to start")

    def stop(self) -> None:
        self.events.append("health.stop")
        if self.fail_on_stop:
            raise RuntimeError("health server failed to stop")


def run(coro):
    return asyncio.run(coro)


def make_application(
    events: list[str],
    health_result: dict | None = None,
    health_start_fails: bool = False,
    health_stop_fails: bool = False,
) -> Application:
    app = object.__new__(Application)
    app.name = "forex-signal-bot"
    app.services = FakeServiceManager(events, health_result)
    app.health_server = FakeHealthServer(
        events,
        fail_on_start=health_start_fails,
        fail_on_stop=health_stop_fails,
    )
    return app


def test_application_start_starts_services_before_health_server() -> None:
    events: list[str] = []
    app = make_application(events)

    run(app.start())

    assert events == ["services.start", "health.start"]


def test_application_start_rolls_back_services_when_health_server_fails() -> None:
    events: list[str] = []
    app = make_application(events, health_start_fails=True)

    with pytest.raises(RuntimeError, match="health server failed to start"):
        run(app.start())

    assert events == ["services.start", "health.start", "services.stop"]


def test_application_stop_stops_health_server_before_services() -> None:
    events: list[str] = []
    app = make_application(events)

    run(app.stop())

    assert events == ["health.stop", "services.stop"]


def test_application_stop_stops_services_when_health_server_fails() -> None:
    events: list[str] = []
    app = make_application(events, health_stop_fails=True)

    with pytest.raises(RuntimeError, match="health server failed to stop"):
        run(app.stop())

    assert events == ["health.stop", "services.stop"]


def test_application_health_marks_critical_service_failure_as_degraded() -> None:
    events: list[str] = []
    app = make_application(
        events,
        {
            "telegram": {
                "service": "telegram",
                "status": "error",
                "critical": True,
            }
        },
    )

    result = app.health()

    assert result["application"]["status"] == "degraded"
    assert result["application"]["critical_failures"] == ["telegram"]
    assert result["services"]["telegram"]["status"] == "error"


def test_application_health_preserves_healthy_application_status() -> None:
    events: list[str] = []
    app = make_application(
        events,
        {
            "telegram": {
                "service": "telegram",
                "status": "ok",
                "critical": True,
            }
        },
    )

    result = app.health()

    assert result["application"]["status"] == "ok"
    assert "critical_failures" not in result["application"]


def test_create_app_registers_application_services(monkeypatch) -> None:
    import core.application as application_module

    class FakeTelegramService:
        name = "telegram"
        critical = True

    class FakeWorkerProcessingService:
        name = "worker_processing"
        critical = False

        @classmethod
        def from_settings(cls):
            return cls()

    class FakeServer:
        def __init__(self, *args, **kwargs) -> None:
            pass

    monkeypatch.setattr(application_module, "TelegramService", FakeTelegramService)
    monkeypatch.setattr(application_module, "WorkerProcessingService", FakeWorkerProcessingService)
    monkeypatch.setattr(application_module, "HealthServer", FakeServer)

    app = application_module.create_app()

    assert list(app.services.services) == ["telegram", "worker_processing"]
    assert isinstance(app.services.services["telegram"], FakeTelegramService)
    assert isinstance(app.services.services["worker_processing"], FakeWorkerProcessingService)


def test_app_factory_wrapper_delegates_to_application_factory(monkeypatch) -> None:
    import app as app_module

    sentinel = object()
    monkeypatch.setattr(app_module, "application_factory", lambda: sentinel)

    assert app_module.create_app() is sentinel
