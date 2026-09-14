import math

import pytest

from analysis.risk_engine import RiskEngine


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_current_price_rejects_non_finite(value: float) -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="current_price"):
        engine.calculate(
            signal="BUY",
            current_price=value,
            risk_distance=1.0,
            confidence=0.90,
            score=100.0,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_risk_distance_rejects_non_finite(value: float) -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="risk distance"):
        engine.calculate(
            signal="BUY",
            current_price=100.0,
            risk_distance=value,
            confidence=0.90,
            score=100.0,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_atr_rejects_non_finite(value: float) -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="atr"):
        engine.calculate(
            signal="BUY",
            current_price=100.0,
            atr=value,
            confidence=0.90,
            score=100.0,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_confidence_rejects_non_finite(value: float) -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="confidence"):
        engine.calculate(
            signal="BUY",
            current_price=100.0,
            risk_distance=1.0,
            confidence=value,
            score=100.0,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_score_rejects_non_finite(value: float) -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="score"):
        engine.calculate(
            signal="BUY",
            current_price=100.0,
            risk_distance=1.0,
            confidence=0.90,
            score=value,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("risk_reward_target", math.nan),
        ("risk_reward_target", math.inf),
        ("risk_reward_target", -math.inf),
        ("atr_multiplier", math.nan),
        ("atr_multiplier", math.inf),
        ("atr_multiplier", -math.inf),
        ("account_balance", math.nan),
        ("account_balance", math.inf),
        ("account_balance", -math.inf),
        ("risk_percent", math.nan),
        ("risk_percent", math.inf),
        ("risk_percent", -math.inf),
        ("contract_size", math.nan),
        ("contract_size", math.inf),
        ("contract_size", -math.inf),
    ],
)
def test_constructor_rejects_non_finite_numeric_configuration(field: str, value: float) -> None:
    with pytest.raises(ValueError, match=field):
        RiskEngine(**{field: value})


def test_non_finite_conversion_rate_remains_fail_closed() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")
    for rate in (math.nan, math.inf, -math.inf):
        result = engine.calculate(
            signal="BUY",
            current_price=150.0,
            risk_distance=1.0,
            confidence=0.90,
            score=100.0,
            symbol="USDJPY",
            quote_to_account_rate=rate,
        )
        assert result.position_size is None
        assert result.lot_size is None
        assert result.risk_amount is None
        assert "Position sizing unavailable" in result.reason
