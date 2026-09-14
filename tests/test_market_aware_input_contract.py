from __future__ import annotations

import asyncio

import pytest

from analysis.market_aware_engine import MarketAwareAnalysisEngine
from config.settings import Settings
from services.market_data.service import MarketDataService


class FakeMarketDataService(MarketDataService):
    pass


@pytest.mark.parametrize("symbol", [None, 123, object()])
def test_market_aware_engine_rejects_non_string_symbol(symbol) -> None:
    engine = MarketAwareAnalysisEngine(
        market_data=FakeMarketDataService(),
        settings=Settings(account_currency="USD"),
    )

    with pytest.raises(TypeError, match="symbol must be a string"):
        asyncio.run(engine.analyze([], symbol=symbol, timeframe="1h"))


@pytest.mark.parametrize("timeframe", [None, 60, object()])
def test_market_aware_engine_rejects_non_string_timeframe(timeframe) -> None:
    engine = MarketAwareAnalysisEngine(
        market_data=FakeMarketDataService(),
        settings=Settings(account_currency="USD"),
    )

    with pytest.raises(TypeError, match="timeframe must be a string"):
        asyncio.run(engine.analyze([], symbol="EURUSD", timeframe=timeframe))


@pytest.mark.parametrize("candles", [None, 123, object()])
def test_market_aware_engine_rejects_invalid_candle_collection(candles) -> None:
    engine = MarketAwareAnalysisEngine(
        market_data=FakeMarketDataService(),
        settings=Settings(account_currency="USD"),
    )

    with pytest.raises((TypeError, ValueError)):
        asyncio.run(engine.analyze(candles, symbol="EURUSD", timeframe="1h"))


def test_market_aware_engine_normalizes_symbol_and_timeframe() -> None:
    engine = MarketAwareAnalysisEngine(
        market_data=FakeMarketDataService(),
        settings=Settings(account_currency=None),
    )

    class FakeAnalysisEngine:
        def analyze(self, candles):
            from analysis.report import AnalysisReport

            return AnalysisReport(score=50.0, signal="NEUTRAL", confidence=0.5)

    engine.analysis_engine = FakeAnalysisEngine()
    candles = [object()]

    report = asyncio.run(
        engine.analyze(candles, symbol=" eurusd ", timeframe=" 1H ")
    )

    assert report.symbol == "EURUSD"
    assert report.timeframe == "1H"
