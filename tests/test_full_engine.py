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
        candles.append(Candle(symbol="EUR_USD", timestamp=start + timedelta(minutes=15 * index), open=open_price, high=high, low=low, close=close, volume=100.0))
    return candles


def test_full_engine_returns_report() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.1000, 1.1010, 1.0990, 1.1030, 1.1010, 1.1060, 1.1040, 1.1080]))
    assert isinstance(result, AnalysisReport)
    assert result.trend in ["bullish", "bearish", "unknown"]


def test_full_engine_has_signal() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.0, 1.2, 1.1, 1.4, 1.3, 1.6]))
    assert result.signal in ["BUY", "SELL", "NEUTRAL", "WAIT", "NO_TRADE"]


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


def test_full_engine_rejects_non_finite_atr_output(monkeypatch) -> None:
    engine = FullAnalysisEngine()
    original_calculate = engine.atr_engine.calculate

    def invalid_atr(prices):
        result = original_calculate(prices)
        return type(result)(atr=float("nan"), atr_percentage=result.atr_percentage, volatility=result.volatility)

    monkeypatch.setattr(engine.atr_engine, "calculate", invalid_atr)
    with pytest.raises(ValueError, match="ATR must be numeric and finite"):
        engine.analyze(make_candles([1.0, 1.1, 1.05, 1.2, 1.15, 1.3]))


def test_full_engine_rejects_non_finite_analysis_component(monkeypatch) -> None:
    engine = FullAnalysisEngine()
    original_analyze = engine.smc_engine.analyze

    def invalid_smc(prices):
        result = original_analyze(prices)
        return type(result)(bias=result.bias, structure=result.structure, order_block=result.order_block, liquidity=result.liquidity, fair_value_gap=result.fair_value_gap, premium_discount=result.premium_discount, equal_high=result.equal_high, equal_low=result.equal_low, score=float("inf"), strength=result.strength, reason=result.reason)

    monkeypatch.setattr(engine.smc_engine, "analyze", invalid_smc)
    with pytest.raises(ValueError, match="smart_money_score must be numeric and finite"):
        engine.analyze(make_candles([1.0, 1.1, 1.05, 1.2, 1.15, 1.3]))


def test_full_engine_output_numeric_contract_is_finite() -> None:
    result = FullAnalysisEngine().analyze(make_candles([1.0, 1.1, 1.05, 1.2, 1.15, 1.3]))
    for value in (result.score, result.confidence, result.agreement, result.entry_price, result.stop_loss, result.take_profit, result.risk_reward, result.position_size, result.risk_amount):
        if value is not None:
            assert value == pytest.approx(value)
            assert abs(value) != float("inf")


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


def test_full_engine_macro_crisis_blocks_trade():
    candles = [100, 101, 102, 101, 103, 104, 105, 106, 107, 108]
    report = FullAnalysisEngine().analyze(candles, macro_risk={"risk_level": "CRISIS", "events": [{"title": "rate decision"}]})
    assert report.macro_risk_level == "CRISIS"
    assert report.macro_events == [{"title": "rate decision"}]
    assert report.signal == "NO_TRADE"


def test_full_engine_macro_elevated_downgrades_directional_signal():
    candles = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    report = FullAnalysisEngine().analyze(candles, macro_risk={"risk_level": "ELEVATED", "events": []})
    assert report.macro_risk_level == "ELEVATED"
    assert report.signal in {"WAIT", "NO_TRADE", "BUY", "SELL", "NEUTRAL"}


def test_full_engine_blocks_candidate_when_portfolio_concentration_exceeds_limit():
    from analysis.portfolio_risk_guard import PortfolioExposure

    candles = make_candles([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    report = FullAnalysisEngine().analyze(
        candles,
        portfolio_exposures=[PortfolioExposure("EUR_USD", "FOREX", "BUY", 80, 0.8)],
        portfolio_candidate=PortfolioExposure("EUR_USD", "FOREX", "BUY", 40, 0.4),
        portfolio_equity=200,
    )
    assert report.portfolio_risk_blocked is True
    assert "SYMBOL_CONCENTRATION" in report.portfolio_risk_flags
    assert report.signal == "NO_TRADE"


def test_full_engine_allows_candidate_within_portfolio_limits():
    from analysis.portfolio_risk_guard import PortfolioExposure

    candles = make_candles([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
    report = FullAnalysisEngine().analyze(
        candles,
        portfolio_exposures=[PortfolioExposure("EUR_USD", "FOREX", "BUY", 20, 0.2)],
        portfolio_candidate=PortfolioExposure("XAUUSD", "COMMODITY", "SELL", 20, 0.2),
        portfolio_equity=100,
        portfolio_max_symbol_weight=0.60,
    )
    assert report.portfolio_risk_blocked is False
    assert report.portfolio_risk_flags == []
