from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.models import Candle
from services.market_data.currency_conversion import CurrencyConversionService
from services.market_data.service import MarketDataService


class FakeMarketDataEngine:
    def __init__(self, candles: list[Candle] | None = None, error: Exception | None = None) -> None:
        self.candles = candles or []
        self.error = error
        self.requests: list[tuple[str, str, int]] = []

    async def get_candles_list(self, symbol: str, timeframe: str, limit: int) -> list[Candle]:
        self.requests.append((symbol, timeframe, limit))
        if self.error is not None:
            raise self.error
        return list(self.candles)


def candle(symbol: str, close: float) -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc),
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1.0,
    )


@pytest.mark.asyncio
async def test_identity_conversion_is_exact_without_market_request() -> None:
    engine = FakeMarketDataEngine()
    service = CurrencyConversionService(MarketDataService(engine=engine))

    result = await service.get_conversion(source_currency="usd", target_currency="USD")

    assert result.rate == 1.0
    assert result.pair_symbol == "USDUSD"
    assert result.inverted is False
    assert engine.requests == []


@pytest.mark.asyncio
async def test_direct_conversion_uses_quote_to_account_pair() -> None:
    engine = FakeMarketDataEngine([candle("EURUSD", 1.25)])
    service = CurrencyConversionService(MarketDataService(engine=engine))

    result = await service.get_conversion(source_currency="EUR", target_currency="USD")

    assert result.rate == 1.25
    assert result.pair_symbol == "EURUSD"
    assert result.inverted is False
    assert engine.requests == [("EURUSD", "1m", 1)]


@pytest.mark.asyncio
async def test_inverse_conversion_inverts_account_quote_pair() -> None:
    engine = FakeMarketDataEngine([candle("USDJPY", 150.0)])
    service = CurrencyConversionService(MarketDataService(engine=engine))

    result = await service.get_conversion(source_currency="JPY", target_currency="USD")

    assert result.rate == pytest.approx(1 / 150.0)
    assert result.pair_symbol == "USDJPY"
    assert result.inverted is True
    assert engine.requests == [("USDJPY", "1m", 1)]


@pytest.mark.asyncio
async def test_missing_market_data_fails_closed() -> None:
    engine = FakeMarketDataEngine([])
    service = CurrencyConversionService(MarketDataService(engine=engine))

    with pytest.raises(ValueError, match="Unable to resolve fresh currency conversion JPY->USD"):
        await service.get_conversion(source_currency="JPY", target_currency="USD")


@pytest.mark.asyncio
async def test_invalid_market_price_fails_closed() -> None:
    engine = FakeMarketDataEngine([candle("USDJPY", 0.0)])
    service = CurrencyConversionService(MarketDataService(engine=engine))

    with pytest.raises(ValueError, match="Unable to resolve fresh currency conversion JPY->USD"):
        await service.get_conversion(source_currency="JPY", target_currency="USD")


@pytest.mark.asyncio
async def test_unsupported_conversion_pair_fails_closed() -> None:
    engine = FakeMarketDataEngine()
    service = CurrencyConversionService(MarketDataService(engine=engine))

    with pytest.raises(ValueError, match="No supported Forex conversion pair"):
        await service.get_conversion(source_currency="XAU", target_currency="USD")
