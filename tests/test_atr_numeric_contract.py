import math

import pytest

from analysis.atr_engine import ATREngine


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, 0.0, -1.0])
def test_close_only_atr_rejects_invalid_price_instead_of_dropping_it(value):
    engine = ATREngine(period=2)
    with pytest.raises(ValueError, match="ATR prices"):
        engine.calculate([100.0, value, 101.0])


def test_close_only_atr_rejects_non_sequence_input():
    with pytest.raises(TypeError, match="numeric sequence"):
        ATREngine().calculate("100,101,102")


def test_true_range_helper_rejects_arithmetic_overflow():
    with pytest.raises(ValueError, match="true range"):
        ATREngine.true_range([1e308, -1e308])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_atr_constructor_rejects_non_finite_thresholds(value):
    with pytest.raises(ValueError, match="finite"):
        ATREngine(low_volatility_threshold=value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_atr_percentage_rejects_non_finite_inputs(value):
    with pytest.raises(ValueError, match="finite"):
        ATREngine.calculate_atr_percentage(value, 100.0)


def test_normal_atr_result_remains_finite():
    result = ATREngine(period=2).calculate(
        [100.0, 101.0, 100.5, 102.0]
    )
    assert math.isfinite(result.atr)
    assert math.isfinite(result.atr_percentage)
