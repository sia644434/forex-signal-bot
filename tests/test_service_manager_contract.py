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


def test_start_all_stops_partially_started_critical_service_and_already_started_services():
    manager = ServiceManager()
    first = FakeService("first")
    failing = FakeService("critical", critical=True, fail_start=True)
    manager.register(first)
    manager.register(failing)

    with pytest.raises(CriticalServiceError, match="Critical service failed to start: critical"):
        run(manager.start_all())

    assert first.events == ["start", "stop"]
    assert failing.events == ["start", "stop"]


def test_start_all_cleans_up_failed_noncritical_service_before_continuing():
    manager = ServiceManager()
    failing = FakeService("optional", fail_start=True)
    healthy = FakeService("healthy")
    manager.register(failing)
    manager.register(healthy)

    run(manager.start_all())

    assert failing.events == ["start", "stop"]
    assert healthy.events == ["start"]


def test_failed_start_cleanup_failure_is_retained_for_shutdown_retry():
    manager = ServiceManager()
    failing = FakeService("optional", fail_start=True, fail_stop=True)
    healthy = FakeService("healthy")
    manager.register(failing)
    manager.register(healthy)

    run(manager.start_all())
    assert failing.events == ["start", "stop"]
    assert healthy.events == ["start"]

    failing.fail_stop = False
    run(manager.stop_all())

    assert failing.events == ["start", "stop", "stop"]
    assert healthy.events == ["start", "stop"]


def test_stop_all_stops_only_started_services_in_reverse_start_order():
    manager = ServiceManager()
    first = FakeService("first")
    failing = FakeService("failing", fail_start=True)
    second = FakeService("second")
    manager.register(first)
    manager.register(failing)
    manager.register(second)

    run(manager.start_all())
    run(manager.stop_all())

    assert first.events == ["start", "stop"]
    assert failing.events == ["start", "stop"]
    assert second.events == ["start", "stop"]


def test_stop_all_does_not_stop_services_that_never_started_after_critical_failure():
    manager = ServiceManager()
    first = FakeService("first")
    failing = FakeService("critical", critical=True, fail_start=True)
    never_started = FakeService("never-started")
    manager.register(first)
    manager.register(failing)
    manager.register(never_started)

    with pytest.raises(CriticalServiceError):
        run(manager.start_all())

    run(manager.stop_all())

    assert first.events == ["start", "stop"]
    assert failing.events == ["start", "stop"]
    assert never_started.events == []


def test_stop_all_retries_services_whose_stop_failed():
    manager = ServiceManager()
    failing = FakeService("failing", fail_stop=True)
    manager.register(failing)

    run(manager.start_all())
    run(manager.stop_all())
    assert failing.events == ["start", "stop"]

    failing.fail_stop = False
    run(manager.stop_all())
    assert failing.events == ["start", "stop", "stop"]


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
