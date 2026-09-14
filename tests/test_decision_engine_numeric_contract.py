import math

import pytest

from analysis.decision_engine import DecisionEngine


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_safe_float_rejects_non_finite_values(value):
    assert DecisionEngine._safe_float(value, 7.0) == 7.0


@pytest.mark.parametrize("field", [
    "buy_threshold",
    "sell_threshold",
    "strong_buy_threshold",
    "strong_sell_threshold",
])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_thresholds_reject_non_finite_values(field, value):
    kwargs = {field: value}
    with pytest.raises(ValueError, match="finite"):
        DecisionEngine(**kwargs)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_custom_weight_rejects_non_finite_values(value):
    with pytest.raises(ValueError, match="finite"):
        DecisionEngine(weights={"smart_money": value})


def test_weight_normalization_remains_finite():
    engine = DecisionEngine(weights={"smart_money": 1.0, "structure": 2.0})

    assert all(math.isfinite(weight) for weight in engine.weights.values())
    assert math.isclose(sum(engine.weights.values()), 1.0)


class NonFiniteAnalysis:
    smart_money_score = math.inf
    structure_score = -math.inf
    price_action_score = math.nan
    trend_score = 0.0
    momentum_score = 0.0


def test_non_finite_analysis_components_fail_closed_to_neutral_defaults():
    result = DecisionEngine().decide(NonFiniteAnalysis())

    assert math.isfinite(result.score)
    assert 0.0 <= result.score <= 100.0
    assert math.isfinite(result.confidence)
    assert 0.0 <= result.confidence <= 1.0
