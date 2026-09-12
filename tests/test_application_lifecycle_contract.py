from __future__ import annotations

import asyncio

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
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def start(self) -> None:
        self.events.append("health.start")

    def stop(self) -> None:
        self.events.append("health.stop")


def run(coro):
    return asyncio.run(coro)


def test_application_start_starts_services_before_health_server() -> None:
    events: list[str] = []
    app = Application()
    app.services = FakeServiceManager(events)
    app.health_server = FakeHealthServer(events)

    run(app.start())

    assert events == ["services.start", "health.start"]


def test_application_stop_stops_health_server_before_services() -> None:
    events: list[str] = []
    app = Application()
    app.services = FakeServiceManager(events)
    app.health_server = FakeHealthServer(events)

    run(app.stop())

    assert events == ["health.stop", "services.stop"]


def test_application_health_marks_critical_service_failure_as_degraded() -> None:
    events: list[str] = []
    app = Application()
    app.services = FakeServiceManager(
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
    app = Application()
    app.services = FakeServiceManager(
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


def test_create_app_registers_telegram_service(monkeypatch) -> None:
    import core.application as application_module

    class FakeTelegramService:
        name = "telegram"
        critical = True

    monkeypatch.setattr(application_module, "TelegramService", FakeTelegramService)

    app = application_module.create_app()

    assert list(app.services.services) == ["telegram"]
    assert isinstance(app.services.services["telegram"], FakeTelegramService)


def test_app_factory_wrapper_delegates_to_application_factory(monkeypatch) -> None:
    import app as app_module

    sentinel = object()
    monkeypatch.setattr(app_module, "application_factory", lambda: sentinel)

    assert app_module.create_app() is sentinel
