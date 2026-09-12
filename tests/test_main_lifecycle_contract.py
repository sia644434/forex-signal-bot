from __future__ import annotations

import asyncio

import pytest

import main as main_module


class FakeApplication:
    def __init__(self, events: list[str], fail_on_start: bool = False) -> None:
        self.events = events
        self.fail_on_start = fail_on_start

    async def start(self) -> None:
        self.events.append("app.start")
        if self.fail_on_start:
            raise RuntimeError("application failed to start")

    async def stop(self) -> None:
        self.events.append("app.stop")


class FakeShutdownManager:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def setup(self) -> None:
        self.events.append("shutdown.setup")

    async def wait(self) -> None:
        self.events.append("shutdown.wait")


class FakeLogger:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def info(self, message: str) -> None:
        self.events.append(message)


def run(coro):
    return asyncio.run(coro)


def test_main_runs_application_to_shutdown_in_order(monkeypatch) -> None:
    events: list[str] = []
    app = FakeApplication(events)

    monkeypatch.setattr(main_module, "create_app", lambda: app)
    monkeypatch.setattr(main_module, "ShutdownManager", lambda: FakeShutdownManager(events))
    monkeypatch.setattr(main_module, "logger", FakeLogger(events))

    run(main_module.main())

    assert events == [
        "shutdown.setup",
        "app.start",
        "Application running.",
        "shutdown.wait",
        "Stopping application...",
        "app.stop",
    ]


def test_main_does_not_wait_or_stop_when_application_start_fails(monkeypatch) -> None:
    events: list[str] = []
    app = FakeApplication(events, fail_on_start=True)

    monkeypatch.setattr(main_module, "create_app", lambda: app)
    monkeypatch.setattr(main_module, "ShutdownManager", lambda: FakeShutdownManager(events))
    monkeypatch.setattr(main_module, "logger", FakeLogger(events))

    with pytest.raises(RuntimeError, match="application failed to start"):
        run(main_module.main())

    assert events == [
        "shutdown.setup",
        "app.start",
    ]
