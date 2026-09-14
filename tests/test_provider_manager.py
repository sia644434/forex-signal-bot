from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.errors import ApplicationError
from data.models import Candle
from data.provider_manager import ProviderManager


def make_candle(
    timestamp: int,
    *,
    symbol: str = "EUR_USD",
    open_price: float = 1.1000,
    high: float = 1.1200,
    low: float = 1.0900,
    close: float = 1.1100,
    volume: float = 100.0,
) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def get_candles(self, symbol: str, timeframe: str, limit: int):
        self.calls += 1
        if not self.responses:
            return []
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.asyncio
async def test_manager_uses_first_provider(monkeypatch) -> None:
    candles = [make_candle(1), make_candle(2), make_candle(3)]
    first = FakeProvider([candles])
    second = FakeProvider([[]])
    manager = ProviderManager(providers=[first, second])
    result = await manager.get_candles(symbol="EUR_USD", timeframe="M15", limit=10)
    assert result == candles
    assert first.calls == 1
    assert second.calls == 0


@pytest.mark.asyncio
async def test_manager_accepts_tuple_provider_result() -> None:
    candles = (make_candle(1), make_candle(2))
    provider = FakeProvider([candles])
    manager = ProviderManager(providers=[provider], retries=0, retry_delay=0)
    result = await manager.get_candles("EUR_USD", "M15", 10)
    assert result == list(candles)
    assert isinstance(result, list)
    assert provider.calls == 1


def test_validate_result_accepts_tuple_directly() -> None:
    candles = (make_candle(1),)
    result = ProviderManager._validate_result("fake", candles, "EUR_USD")
    assert result == list(candles)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_manager_retries_failed_provider(monkeypatch) -> None:
    candles = [make_candle(1)]
    first = FakeProvider([RuntimeError("temporary failure"), candles])
    manager = ProviderManager(providers=[first])
    result = await manager.get_candles(symbol="EUR_USD", timeframe="M15", limit=10)
    assert result == candles
    assert first.calls == 2


@pytest.mark.asyncio
async def test_manager_falls_back_after_retries(monkeypatch) -> None:
    candles = [make_candle(1), make_candle(2)]
    first = FakeProvider([RuntimeError("provider unavailable")] * 3)
    second = FakeProvider([candles])
    manager = ProviderManager(providers=[first, second])
    result = await manager.get_candles(symbol="EUR_USD", timeframe="M15", limit=10)
    assert result == candles
    assert first.calls >= 1
    assert second.calls == 1


@pytest.mark.asyncio
async def test_manager_skips_provider_in_cooldown(monkeypatch) -> None:
    first = FakeProvider([RuntimeError("provider unavailable")])
    second_candles = [make_candle(1)]
    second = FakeProvider([second_candles])
    manager = ProviderManager(providers=[first, second])
    result = await manager.get_candles(symbol="EUR_USD", timeframe="M15", limit=10)
    assert result == second_candles
    assert second.calls == 1


@pytest.mark.asyncio
async def test_manager_rejects_non_chronological_provider_output() -> None:
    candles = [make_candle(3), make_candle(1), make_candle(2)]
    provider = FakeProvider([candles])
    manager = ProviderManager(providers=[provider], retries=0, retry_delay=0)

    with pytest.raises(ApplicationError, match="All market data providers failed"):
        await manager.get_candles("EUR_USD", "M15", 10)

    assert any(
        failure.error_type == "ApplicationError"
        and "non-chronological or duplicate" in failure.message
        for failure in manager.last_failures
    )


@pytest.mark.asyncio
async def test_manager_rejects_duplicate_provider_timestamps() -> None:
    candles = [make_candle(1), make_candle(2), make_candle(2), make_candle(3)]
    provider = FakeProvider([candles])
    manager = ProviderManager(providers=[provider], retries=0, retry_delay=0)

    with pytest.raises(ApplicationError, match="All market data providers failed"):
        await manager.get_candles("EUR_USD", "M15", 10)

    assert any(
        failure.error_type == "ApplicationError"
        and "non-chronological or duplicate" in failure.message
        for failure in manager.last_failures
    )


@pytest.mark.asyncio
async def test_manager_respects_limit(monkeypatch) -> None:
    candles = [make_candle(1), make_candle(2), make_candle(3), make_candle(4), make_candle(5)]
    provider = FakeProvider([candles])
    manager = ProviderManager(providers=[provider])
    result = await manager.get_candles(symbol="EUR_USD", timeframe="M15", limit=3)
    assert len(result) == 3
    assert [int(candle.timestamp.timestamp()) for candle in result] == [3, 4, 5]
