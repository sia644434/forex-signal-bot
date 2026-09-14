import math

import pytest

from analysis.risk_engine import RiskEngine


@pytest.mark.parametrize("signal", ["BUY", "SELL"])
def test_setup_rejects_arithmetic_overflow_before_emitting_non_finite_levels(signal: str) -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")
    with pytest.raises(ValueError, match="risk plan output must be finite"):
        engine.calculate(signal=signal, current_price=1e308, risk_distance=1e308, confidence=0.90, score=100.0 if signal == "BUY" else 0.0, symbol="EURUSD")


@pytest.mark.parametrize("signal", ["BUY", "SELL"])
def test_setup_rejects_risk_distance_that_crosses_zero(signal: str) -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")
    with pytest.raises(ValueError, match="risk plan levels must be greater than zero"):
        engine.calculate(signal=signal, current_price=1.0, risk_distance=1.01, confidence=0.90, score=100.0 if signal == "BUY" else 0.0, symbol="EURUSD")


def test_sell_setup_rejects_generated_take_profit_below_zero() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")
    with pytest.raises(ValueError, match="risk plan levels must be greater than zero"):
        engine.calculate(signal="SELL", current_price=1.0, risk_distance=0.34, confidence=0.90, score=0.0, symbol="EURUSD")


def test_normal_risk_plan_output_remains_finite_and_directional() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")
    result = engine.calculate(signal="BUY", current_price=1.1000, risk_distance=0.015, confidence=0.90, score=100.0, symbol="EURUSD")
    for value in (result.entry_price, result.stop_loss, result.take_profit, result.take_profit_1, result.take_profit_2, result.take_profit_3, result.risk_reward, result.position_size, result.lot_size, result.risk_amount, result.risk_percent, result.trailing_stop, result.trade_quality):
        if value is not None:
            assert math.isfinite(value)
    assert result.stop_loss < result.entry_price
    assert result.entry_price < result.take_profit_1 <= result.take_profit_2 <= result.take_profit_3
