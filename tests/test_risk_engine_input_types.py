import math

import pytest

from analysis.risk_engine import RiskEngine


def test_non_string_account_currency_fails_closed() -> None:
    with pytest.raises(TypeError, match="account_currency"):
        RiskEngine(account_currency=123)  # type: ignore[arg-type]


def test_malformed_account_currency_fails_closed() -> None:
    for currency in ("US", "USDX", "U$D"):
        with pytest.raises(ValueError, match="3-letter ISO currency code"):
            RiskEngine(account_currency=currency)


def test_risk_engine_rejects_risk_policy_above_100_percent() -> None:
    with pytest.raises(ValueError, match="at most 100"):
        RiskEngine(risk_percent=100.0001)


@pytest.mark.parametrize("score", [math.nan, math.inf, -math.inf])
def test_directional_strength_rejects_non_finite_score(score: float) -> None:
    with pytest.raises(ValueError, match="score"):
        RiskEngine._directional_strength(score)


def test_non_string_signal_fails_closed() -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="signal"):
        engine.calculate(
            signal=123,  # type: ignore[arg-type]
            current_price=100.0,
            risk_distance=1.0,
            confidence=0.90,
            score=100.0,
        )


def test_risk_policy_override_above_100_percent_fails_closed() -> None:
    engine = RiskEngine()
    with pytest.raises(ValueError, match="at most 100"):
        engine.calculate(
            signal="BUY",
            current_price=100.0,
            risk_distance=1.0,
            confidence=0.90,
            score=100.0,
            risk_percent=100.0001,
        )
