from __future__ import annotations

import asyncio
import signal

from core.shutdown import ShutdownManager


class FakeLoop:
    def __init__(self) -> None:
        self.handlers: dict[signal.Signals, object] = {}

    def add_signal_handler(self, sig: signal.Signals, callback) -> None:
        self.handlers[sig] = callback


def run(coro):
    return asyncio.run(coro)


def test_setup_registers_sigint_and_sigterm(monkeypatch) -> None:
    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    manager = ShutdownManager()
    manager.setup()

    assert loop.handlers == {
        signal.SIGINT: manager.trigger,
        signal.SIGTERM: manager.trigger,
    }


def test_trigger_sets_shutdown_event() -> None:
    manager = ShutdownManager()

    assert not manager.event.is_set()

    manager.trigger()

    assert manager.event.is_set()


def test_wait_returns_after_shutdown_trigger() -> None:
    async def scenario() -> None:
        manager = ShutdownManager()
        waiter = asyncio.create_task(manager.wait())

        await asyncio.sleep(0)
        assert not waiter.done()

        manager.trigger()
        await asyncio.wait_for(waiter, timeout=1)

    run(scenario())


def test_trigger_is_idempotent() -> None:
    manager = ShutdownManager()

    manager.trigger()
    manager.trigger()

    assert manager.event.is_set()
