import math

import pytest

from analysis.confidence_engine import ConfidenceEngine


class MockAnalysis:
    smart_money_score = 80
    structure_score = 75
    price_action_score = 70
    momentum_score = 65
    elliott_score = 60
    harmonic_score = 55
    wyckoff_score = 50


def test_confidence_engine_returns_result():
    result = ConfidenceEngine().evaluate(MockAnalysis())
    assert 0 <= result.confidence <= 1


def test_confidence_engine_counts_votes():
    result = ConfidenceEngine().evaluate(MockAnalysis())
    assert result.bullish_votes >= 1


def test_confidence_engine_detects_conflict():
    class ConflictAnalysis:
        smart_money_score = 80
        structure_score = 70
        price_action_score = 60
        momentum_score = 50
        elliott_score = -20
        harmonic_score = -30
        wyckoff_score = -40

    result = ConfidenceEngine().evaluate(ConflictAnalysis())
    assert result.warnings


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_normalizers_reject_non_finite_values(value):
    engine = ConfidenceEngine()
    with pytest.raises(ValueError, match="finite"):
        engine.normalize(value)
    with pytest.raises(ValueError, match="finite"):
        engine.normalize_signed_score(value)
    with pytest.raises(ValueError, match="finite"):
        engine.normalize_confidence(value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_present_non_finite_engine_score_fails_closed(value):
    class InvalidAnalysis:
        smart_money_score = value

    with pytest.raises(ValueError, match="finite"):
        ConfidenceEngine().evaluate(InvalidAnalysis())


def test_missing_engine_score_remains_neutral():
    class SparseAnalysis:
        pass

    result = ConfidenceEngine().evaluate(SparseAnalysis())
    assert result.neutral_votes == 10
    assert result.data_quality == 0.0


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_volatility_fails_closed(value):
    class InvalidVolatility:
        volatility_score = value

    with pytest.raises(ValueError, match="volatility_score.*finite"):
        ConfidenceEngine().evaluate(InvalidVolatility())


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_weight_is_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        ConfidenceEngine(weights={"smart_money": value})


def test_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        ConfidenceEngine(weights={"smart_money": -1})


def test_final_result_metrics_are_finite():
    result = ConfidenceEngine().evaluate(MockAnalysis())
    values = [
        result.confidence,
        result.agreement,
        result.weighted_bullish,
        result.weighted_bearish,
        result.weighted_neutral,
        result.data_quality,
        result.market_uncertainty,
        result.conflict_score,
    ]
    assert all(math.isfinite(value) for value in values)
