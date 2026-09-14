from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from analysis import FullAnalysisEngine, AnalysisReport
from data.models import Candle


def make_candles(closes: list[float]) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    for index, close in enumerate(closes):
        previous_close = closes[index - 1] if index > 0 else close
        open_price = previous_close
        high = max(open_price, close) * 1.001
        low = min(open_price, close) * 0.999
        candles.append(Candle(
            symbol="EUR_USD",
            timestamp=start + timedelta(minutes=15 * index),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=100.0,
        ))
    return candles


def test_full_engine_returns_report() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.1000, 1.1010, 1.0990, 1.1030, 1.1010, 1.1060, 1.1040, 1.1080]))
    assert isinstance(result, AnalysisReport)
    assert result.trend in ["bullish", "bearish", "unknown"]


def test_full_engine_has_signal() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.0, 1.2, 1.1, 1.4, 1.3, 1.6]))
    assert result.signal in ["BUY", "SELL", "NEUTRAL"]


def test_full_engine_confidence_range() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.0, 1.2, 1.1, 1.5, 1.3, 1.7]))
    assert 0 <= result.confidence <= 1


def test_full_engine_invalid_input() -> None:
    with pytest.raises(ValueError):
        FullAnalysisEngine().analyze([])


@pytest.mark.parametrize("invalid_input", [None, 123, object()])
def test_full_engine_rejects_invalid_collection_boundary(invalid_input) -> None:
    with pytest.raises((TypeError, ValueError)):
        FullAnalysisEngine().analyze(invalid_input)


@pytest.mark.parametrize("invalid_price", [float("nan"), float("inf"), float("-inf"), 0.0, -1.0])
def test_full_engine_rejects_non_finite_or_nonpositive_price_lists(invalid_price: float) -> None:
    with pytest.raises(ValueError, match="finite and greater than zero"):
        FullAnalysisEngine().analyze([1.0, invalid_price, 1.1])


def test_full_engine_supports_legacy_price_list_input() -> None:
    result = FullAnalysisEngine().analyze([1.0, 1.1, 1.05, 1.2, 1.15, 1.3])
    assert isinstance(result, AnalysisReport)


def test_full_engine_rejects_mixed_candle_collection() -> None:
    candles = make_candles([1.0, 1.1, 1.05, 1.2, 1.15, 1.3])
    with pytest.raises(TypeError, match="only Candle objects"):
        FullAnalysisEngine().analyze([*candles, 1.4])


def test_full_engine_uses_canonical_candle_model() -> None:
    candles = make_candles([1.0, 1.1, 1.05, 1.2, 1.15, 1.3])
    result = FullAnalysisEngine().analyze(candles)
    assert result is not None
    assert all(isinstance(candle, Candle) for candle in candles)
    assert candles[0].symbol == "EUR_USD"
    assert candles[0].timestamp.tzinfo is not None


def test_full_engine_directional_strength_is_symmetric() -> None:
    assert FullAnalysisEngine._directional_strength(0) == 100
    assert FullAnalysisEngine._directional_strength(100) == 100
    assert FullAnalysisEngine._directional_strength(25) == 50
    assert FullAnalysisEngine._directional_strength(75) == 50
    assert FullAnalysisEngine._directional_strength(50) == 0


@pytest.mark.parametrize("invalid_score", [float("nan"), float("inf"), float("-inf"), "bad", None])
def test_full_engine_directional_strength_rejects_invalid_scores(invalid_score) -> None:
    with pytest.raises(ValueError, match="numeric and finite"):
        FullAnalysisEngine._directional_strength(invalid_score)


def test_full_engine_wires_supply_demand_score_to_analysis_contract(monkeypatch) -> None:
    engine = FullAnalysisEngine()
    captured = {}
    original_evaluate = engine.confidence_engine.evaluate

    def capture(analysis):
        captured["analysis"] = analysis
        return original_evaluate(analysis)

    monkeypatch.setattr(engine.confidence_engine, "evaluate", capture)
    engine.analyze(make_candles([1.0, 1.1, 1.2, 1.3, 1.4, 1.5]))
    assert captured["analysis"].supply_demand_score == 20
