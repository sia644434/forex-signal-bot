from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services.market_data.service import MarketDataService


@pytest.mark.asyncio
async def test_service_uses_canonical_engine_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = AsyncMock()
    engine.get_candles_list.return_value = []
    monkeypatch.setattr(
        "services.market_data.service.MarketDataEngine",
        lambda: engine,
    )

    service = MarketDataService()
    result = await service.get_candles_list("EURUSD", "M15", 10)

    assert result == []
    engine.get_candles_list.assert_awaited_once_with("EURUSD", "M15", 10)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "symbol,timeframe,limit",
    [
        ("", "M15", 10),
        ("EURUSD", "", 10),
        ("EURUSD", "M15", 0),
    ],
)
async def test_service_does_not_replace_engine_validation(
    symbol: str, timeframe: str, limit: int
) -> None:
    engine = AsyncMock()
    engine.get_candles_list.side_effect = ValueError("invalid request")
    service = MarketDataService(engine=engine)

    with pytest.raises(ValueError, match="invalid request"):
        await service.get_candles_list(symbol, timeframe, limit)


@pytest.mark.asyncio
async def test_service_preserves_engine_result_identity() -> None:
    candles = [object(), object()]
    engine = AsyncMock()
    engine.get_candles_list.return_value = candles
    service = MarketDataService(engine=engine)

    result = await service.get_candles_list("EURUSD", "M15", 2)

    assert result is candles
