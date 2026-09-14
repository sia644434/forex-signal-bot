from __future__ import annotations

from data.factory import ProviderFactory
from data.provider_manager import ProviderManager


class NamedProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    async def get_candles(self, symbol: str, timeframe: str, limit: int):
        return []


def test_set_providers_removes_inactive_injected_provider_objects() -> None:
    old = NamedProvider("oanda")
    manager = ProviderManager(providers=[old])

    manager.set_providers(["finnhub"])

    assert manager.providers == ("finnhub",)
    assert manager.status()["injected_instances"] == []


def test_set_providers_does_not_resurrect_removed_injected_object(monkeypatch) -> None:
    old = NamedProvider("oanda")
    created = NamedProvider("oanda")
    manager = ProviderManager(providers=[old])

    manager.set_providers(["finnhub"])
    manager.set_providers(["oanda"])
    monkeypatch.setattr(ProviderFactory, "create", lambda name: created)

    assert manager._get_provider("oanda") is created
    assert manager._get_provider("oanda") is not old


def test_set_providers_keeps_active_factory_cache() -> None:
    created = NamedProvider("finnhub")
    manager = ProviderManager(providers=["finnhub"])
    manager._provider_instances["finnhub"] = created

    manager.set_providers(["finnhub"])

    assert manager._get_provider("finnhub") is created
