import math

import pytest

from analysis.risk_engine import RiskEngine


def test_non_string_account_currency_fails_closed() -> None:
    with pytest.raises(TypeError, match="account_currency"):
        RiskEngine(account_currency=123)  # type: ignore[arg-type]


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
