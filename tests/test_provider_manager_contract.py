from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from core.errors import ApplicationError
from data.models import Candle
from data.provider_manager import ProviderManager


class FakeProvider:
    def __init__(self, name: str, result=None, error: Exception | None = None):
        self.name = name
        self.get_candles = AsyncMock()
        if error is not None:
            self.get_candles.side_effect = error
        else:
            self.get_candles.return_value = result


def candle(minute: int, close: float = 1.1005) -> Candle:
    return Candle(symbol="EURUSD", timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * minute), open=1.1000, high=1.1010, low=1.0990, close=close, volume=100.0)


@pytest.mark.asyncio
async def test_manager_uses_provider_priority_and_forwards_request():
    first = FakeProvider("first", [candle(1)])
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=0)
    result = await manager.get_candles(" eurusd ", " 15m ", limit=1)
    assert result == [candle(1)]
    first.get_candles.assert_awaited_once_with(symbol="EURUSD", timeframe="15M", limit=1)
    second.get_candles.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_falls_back_after_provider_failure():
    first = FakeProvider("first", error=TimeoutError("timeout"))
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=0)
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(2)]
    first.get_candles.assert_awaited_once()
    second.get_candles.assert_awaited_once()
    assert manager.last_failures[0].provider == "first"
    assert manager.last_failures[0].error_type == "TimeoutError"


@pytest.mark.asyncio
async def test_manager_retries_before_fallback():
    first = FakeProvider("first")
    first.get_candles.side_effect = [TimeoutError("temporary"), [candle(1)]]
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=1, retry_delay=0, cooldown_seconds=0)
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(1)]
    assert first.get_candles.await_count == 2
    second.get_candles.assert_not_awaited()
    assert len(manager.last_failures) == 1


@pytest.mark.asyncio
async def test_manager_rejects_invalid_provider_result_and_falls_back():
    first = FakeProvider("first", ["not-a-candle"])
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=0)
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(2)]
    assert manager.last_failures[0].error_type == "ApplicationError"


@pytest.mark.asyncio
async def test_manager_raises_application_error_when_all_providers_fail():
    first = FakeProvider("first", error=TimeoutError("first timeout"))
    second = FakeProvider("second", error=ConnectionError("second down"))
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=0)
    with pytest.raises(ApplicationError) as exc_info:
        await manager.get_candles("EURUSD", "15m", limit=5)
    assert exc_info.value.details["symbol"] == "EURUSD"
    assert exc_info.value.details["timeframe"] == "15M"
    assert exc_info.value.details["limit"] == 5
    assert exc_info.value.details["attempted_providers"] == 2
    assert [item["provider"] for item in exc_info.value.details["failures"]] == ["first", "second"]


@pytest.mark.asyncio
async def test_manager_skips_provider_in_cooldown():
    first = FakeProvider("first", error=TimeoutError("down"))
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=60)
    await manager.get_candles("EURUSD", "15m", limit=1)
    first.get_candles.reset_mock()
    second.get_candles.reset_mock()
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(2)]
    first.get_candles.assert_not_awaited()
    second.get_candles.assert_awaited_once()
    assert manager.status()["cooldowns"]["first"] > 0


@pytest.mark.asyncio
async def test_set_providers_removes_cooldown_for_removed_provider():
    first = FakeProvider("first", error=TimeoutError("down"))
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=60)
    await manager.get_candles("EURUSD", "15m", limit=1)
    assert manager.status()["cooldowns"]["first"] > 0
    manager.set_providers([second])
    assert "first" not in manager.status()["cooldowns"]


@pytest.mark.asyncio
async def test_removed_provider_restarts_without_stale_cooldown_when_readded():
    first = FakeProvider("first", error=TimeoutError("down"))
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second], retries=0, retry_delay=0, cooldown_seconds=60)
    await manager.get_candles("EURUSD", "15m", limit=1)
    first.get_candles.reset_mock()
    manager.set_providers([second])
    manager.set_providers([first, second])
    first.get_candles.side_effect = None
    first.get_candles.return_value = [candle(1)]
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(1)]
    first.get_candles.assert_awaited_once()


@pytest.mark.parametrize("field", ["retry_delay", "cooldown_seconds"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_manager_rejects_non_finite_provider_timing_configuration(field, value):
    kwargs = {field: value}
    with pytest.raises(ValueError, match=f"{field} must be finite"):
        ProviderManager(providers=[FakeProvider("first", [candle(1)])], **kwargs)


def test_manager_accepts_zero_provider_timing_configuration():
    manager = ProviderManager(providers=[FakeProvider("first", [candle(1)])], retry_delay=0, cooldown_seconds=0)
    assert manager.retry_delay == 0.0
    assert manager.cooldown_seconds == 0.0


def test_manager_rejects_empty_provider_configuration():
    with pytest.raises(ValueError):
        ProviderManager(providers=[])


def test_manager_rejects_unknown_provider_name():
    with pytest.raises(ApplicationError) as exc_info:
        ProviderManager(providers=["definitely-unknown-provider"])
    assert exc_info.value.details["provider"] == "definitely-unknown-provider"


def test_manager_rejects_duplicate_provider_identity():
    first = FakeProvider("first", [candle(1)])
    with pytest.raises(ValueError, match="Duplicate provider identity: first"):
        ProviderManager(providers=[first, first])


def test_manager_rejects_duplicate_normalized_provider_names():
    with pytest.raises(ValueError, match="Duplicate provider identity: oanda"):
        ProviderManager(providers=["OANDA", "oanda"])


def test_set_providers_rejects_duplicate_provider_identity():
    first = FakeProvider("first", [candle(1)])
    manager = ProviderManager(providers=[first])
    with pytest.raises(ValueError, match="Duplicate provider identity: first"):
        manager.set_providers([first, first])


def test_set_providers_replaces_active_priority_and_prunes_removed_instances():
    first = FakeProvider("first", [candle(1)])
    second = FakeProvider("second", [candle(2)])
    manager = ProviderManager(providers=[first, second])
    manager.set_providers([second])
    assert manager.providers == ("second",)
    assert manager.status()["injected_instances"] == ["second"]
    manager.set_providers([first])
    assert manager.providers == ("first",)
    assert manager.status()["injected_instances"] == ["first"]
    assert "second" not in manager._provider_objects
    assert "second" not in manager._provider_instances


def test_set_providers_replaces_injected_instance_when_same_provider_name_is_rebound():
    original = FakeProvider("first", [candle(1)])
    replacement = FakeProvider("first", [candle(2)])
    manager = ProviderManager(providers=[original])
    manager.set_providers([replacement])
    assert manager.providers == ("first",)
    assert manager.status()["injected_instances"] == ["first"]
    assert manager._get_provider("first") is replacement


@pytest.mark.asyncio
async def test_manager_skips_provider_when_declared_symbol_capability_does_not_match():
    unsupported = FakeProvider("unsupported", [candle(1)])
    unsupported.supports_symbol = lambda _symbol: False
    fallback = FakeProvider("fallback", [candle(2)])
    manager = ProviderManager(providers=[unsupported, fallback], retries=0, retry_delay=0, cooldown_seconds=0)
    result = await manager.get_candles("EURUSD", "15m", limit=1)
    assert result == [candle(2)]
    unsupported.get_candles.assert_not_awaited()
    fallback.get_candles.assert_awaited_once()
    assert manager.last_failures[0].error_type == "UnsupportedSymbol"
    assert manager.last_failures[0].attempt == 0
