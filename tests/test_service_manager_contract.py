import asyncio

import pytest

from core.errors import CriticalServiceError
from core.service import ServiceManager
from services.base import BaseService


class FakeService(BaseService):
    def __init__(self, name, *, critical=False, fail_start=False, fail_stop=False, fail_health=False):
        self.name = name
        self.critical = critical
        self.fail_start = fail_start
        self.fail_stop = fail_stop
        self.fail_health = fail_health
        self.events = []

    def start(self):
        self.events.append("start")
        if self.fail_start:
            raise RuntimeError(f"start failed: {self.name}")

    def stop(self):
        self.events.append("stop")
        if self.fail_stop:
            raise RuntimeError(f"stop failed: {self.name}")

    def health(self):
        if self.fail_health:
            raise RuntimeError(f"health failed: {self.name}")
        return {"service": self.name, "status": "ok", "critical": self.critical}


def run(coro):
    return asyncio.run(coro)


def test_register_rejects_duplicate_service_names():
    manager = ServiceManager()
    manager.register(FakeService("telegram"))

    with pytest.raises(ValueError, match="Service already registered: telegram"):
        manager.register(FakeService("telegram"))


def test_start_all_stops_already_started_services_when_critical_service_fails():
    manager = ServiceManager()
    first = FakeService("first")
    failing = FakeService("critical", critical=True, fail_start=True)
    manager.register(first)
    manager.register(failing)

    with pytest.raises(CriticalServiceError, match="Critical service failed to start: critical"):
        run(manager.start_all())

    assert first.events == ["start", "stop"]
    assert failing.events == ["start"]


def test_start_all_continues_when_noncritical_service_fails():
    manager = ServiceManager()
    failing = FakeService("optional", fail_start=True)
    healthy = FakeService("healthy")
    manager.register(failing)
    manager.register(healthy)

    run(manager.start_all())

    assert failing.events == ["start"]
    assert healthy.events == ["start"]


def test_stop_all_stops_services_in_reverse_registration_order():
    manager = ServiceManager()
    first = FakeService("first")
    second = FakeService("second")
    manager.register(first)
    manager.register(second)

    run(manager.stop_all())

    assert second.events == ["stop"]
    assert first.events == ["stop"]


def test_stop_all_isolates_stop_failures_and_continues_cleanup():
    manager = ServiceManager()
    first = FakeService("first")
    failing = FakeService("failing", fail_stop=True)
    manager.register(first)
    manager.register(failing)

    run(manager.stop_all())

    assert failing.events == ["stop"]
    assert first.events == ["stop"]


def test_health_isolates_service_health_failure():
    manager = ServiceManager()
    healthy = FakeService("healthy")
    failing = FakeService("failing", critical=True, fail_health=True)
    manager.register(healthy)
    manager.register(failing)

    result = manager.health()

    assert result["healthy"] == {
        "service": "healthy",
        "status": "ok",
        "critical": False,
    }
    assert result["failing"] == {
        "service": "failing",
        "status": "error",
        "critical": True,
    }
