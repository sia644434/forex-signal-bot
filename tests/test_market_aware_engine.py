from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from analysis.market_aware_engine import MarketAwareAnalysisEngine
from analysis.report import AnalysisReport
from config.settings import Settings
from data.models import Candle
from services.market_data.service import MarketDataService


class FakeMarketDataService(MarketDataService):
    def __init__(self, conversion_symbol: str, conversion_price: float) -> None:
        self.conversion_symbol = conversion_symbol
        self.conversion_price = conversion_price
        self.requests: list[tuple[str, str, int]] = []

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> list[Candle]:
        self.requests.append((symbol, timeframe, limit))
        if symbol != self.conversion_symbol:
            return []
        now = datetime.now(timezone.utc)
        return [
            Candle(
                symbol=symbol,
                timestamp=now,
                open=self.conversion_price,
                high=self.conversion_price,
                low=self.conversion_price,
                close=self.conversion_price,
                volume=1.0,
            )
        ]


def _price_candles(symbol: str, price: float = 150.0) -> list[Candle]:
    now = datetime.now(timezone.utc)
    return [
        Candle(
            symbol=symbol,
            timestamp=now,
            open=price,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=1.0,
        )
    ]


@pytest.mark.parametrize(
    ("symbol", "conversion_symbol", "conversion_price", "expected_rate", "expected_position_size"),
    [
        ("USDJPY", "USDJPY", 150.0, 1.0 / 150.0, 900.0),
        ("EURJPY", "USDJPY", 150.0, 1.0 / 150.0, 900.0),
    ],
)
def test_market_aware_engine_uses_configured_risk_policy_for_jpy_quotes(
    monkeypatch: pytest.MonkeyPatch,
    symbol: str,
    conversion_symbol: str,
    conversion_price: float,
    expected_rate: float,
    expected_position_size: float,
) -> None:
    market_data = FakeMarketDataService(conversion_symbol, conversion_price)
    settings = Settings(account_currency="USD", risk_per_trade=0.01)
    engine = MarketAwareAnalysisEngine(market_data=market_data, settings=settings)

    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(
            score=100.0,
            signal="BUY",
            confidence=0.90,
        ),
    )
    monkeypatch.setattr(
        "analysis.market_aware_engine.ATREngine.calculate",
        lambda self, candles: type("ATRResult", (), {"atr": 1.0})(),
    )

    report = __import__("asyncio").run(
        engine.analyze(
            _price_candles(symbol, conversion_price),
            symbol=symbol,
            timeframe="1h",
        )
    )

    assert market_data.requests == [(conversion_symbol, "1m", 1)]
    assert report.position_size is not None
    assert report.lot_size is not None
    assert report.risk_percent == pytest.approx(1.0)
    assert report.risk_amount == pytest.approx(10.0)
    assert report.position_size == pytest.approx(expected_position_size)
    assert report.position_size <= 10.0 / (1.5 * expected_rate)
    assert report.lot_size == pytest.approx(report.position_size / 100000, abs=0.0005)
    assert f"via {conversion_symbol}" in report.reasons[-1]


def test_market_aware_engine_uses_configured_account_balance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    settings = Settings(account_currency="USD", account_balance=25000.0, risk_per_trade=0.02)
    engine = MarketAwareAnalysisEngine(market_data=market_data, settings=settings)
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )
    monkeypatch.setattr(
        "analysis.market_aware_engine.ATREngine.calculate",
        lambda self, candles: type("ATRResult", (), {"atr": 1.0})(),
    )

    report = __import__("asyncio").run(
        engine.analyze(_price_candles("USDJPY"), symbol="USDJPY", timeframe="1h")
    )

    assert report.risk_percent == pytest.approx(2.0)
    assert report.risk_amount == pytest.approx(500.0)
    assert report.position_size == pytest.approx(49900.0)


def test_market_aware_engine_honors_non_default_risk_per_trade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    settings = Settings(account_currency="USD", risk_per_trade=0.05)
    engine = MarketAwareAnalysisEngine(market_data=market_data, settings=settings)
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )
    monkeypatch.setattr(
        "analysis.market_aware_engine.ATREngine.calculate",
        lambda self, candles: type("ATRResult", (), {"atr": 1.0})(),
    )

    report = __import__("asyncio").run(
        engine.analyze(_price_candles("USDJPY"), symbol="USDJPY", timeframe="1h")
    )

    assert report.risk_percent == pytest.approx(5.0)
    assert report.risk_amount == pytest.approx(50.0)


def test_market_aware_engine_does_not_mutate_shared_risk_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD", risk_per_trade=0.01),
    )
    original_risk_engine = engine.analysis_engine.risk_engine
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )
    monkeypatch.setattr(
        "analysis.market_aware_engine.ATREngine.calculate",
        lambda self, candles: type("ATRResult", (), {"atr": 1.0})(),
    )

    __import__("asyncio").run(
        engine.analyze(_price_candles("USDJPY"), symbol="USDJPY", timeframe="1h")
    )

    assert engine.analysis_engine.risk_engine is original_risk_engine


def test_market_aware_engine_fails_closed_when_atr_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD"),
    )
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )
    monkeypatch.setattr(
        "analysis.market_aware_engine.ATREngine.calculate",
        lambda self, candles: type("ATRResult", (), {"atr": None})(),
    )

    with pytest.raises(ValueError, match="ATR is required for market-aware risk sizing"):
        __import__("asyncio").run(
            engine.analyze(_price_candles("USDJPY"), symbol="USDJPY", timeframe="1h")
        )


def test_market_aware_engine_fails_closed_without_account_currency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency=None),
    )
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )

    report = __import__("asyncio").run(
        engine.analyze(
            _price_candles("USDJPY"),
            symbol="USDJPY",
            timeframe="1h",
        )
    )

    assert report.position_size is None
    assert report.lot_size is None
    assert market_data.requests == []


def test_market_aware_engine_propagates_conversion_failure_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("EURUSD", 1.1)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD"),
    )
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )

    with pytest.raises(ValueError, match="Unable to resolve fresh currency conversion"):
        __import__("asyncio").run(
            engine.analyze(
                _price_candles("USDJPY"),
                symbol="USDJPY",
                timeframe="1h",
            )
        )


def test_market_aware_engine_rejects_candle_symbol_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD"),
    )
    monkeypatch.setattr(
        engine.analysis_engine,
        "analyze",
        lambda candles: AnalysisReport(score=100.0, signal="BUY", confidence=0.90),
    )

    with pytest.raises(ValueError, match="Candle symbol mismatch"):
        __import__("asyncio").run(
            engine.analyze(
                _price_candles("EURUSD"),
                symbol="USDJPY",
                timeframe="1h",
            )
        )

    assert market_data.requests == []


def test_market_aware_engine_rejects_stale_input_before_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD"),
    )
    stale = _price_candles("USDJPY")
    stale[0] = Candle(
        symbol="USDJPY",
        timestamp=datetime.now(timezone.utc) - timedelta(hours=7),
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.0,
        volume=1.0,
    )
    analyze = monkeypatch.spy(engine.analysis_engine, "analyze")

    with pytest.raises(ValueError, match="not fresh enough"):
        __import__("asyncio").run(
            engine.analyze(stale, symbol="USDJPY", timeframe="1h")
        )

    assert analyze.call_count == 0
    assert market_data.requests == []


def test_market_aware_engine_rejects_future_input_before_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    market_data = FakeMarketDataService("USDJPY", 150.0)
    engine = MarketAwareAnalysisEngine(
        market_data=market_data,
        settings=Settings(account_currency="USD"),
    )
    future = _price_candles("USDJPY")
    future[0] = Candle(
        symbol="USDJPY",
        timestamp=datetime.now(timezone.utc) + timedelta(minutes=1),
        open=150.0,
        high=151.0,
        low=149.0,
        close=150.0,
        volume=1.0,
    )

    with pytest.raises(ValueError, match="timestamp cannot be in the future"):
        __import__("asyncio").run(
            engine.analyze(future, symbol="USDJPY", timeframe="1h")
        )

    assert market_data.requests == []
