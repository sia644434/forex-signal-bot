import sys

import pytest

from analysis.decision_engine import DecisionEngine


class OverflowAnalysis:
    structure_score = sys.float_info.max
    trend_score = sys.float_info.max


def test_structure_score_arithmetic_overflow_fails_closed() -> None:
    with pytest.raises(ValueError, match="Market Structure score became non-finite"):
        DecisionEngine().decide(OverflowAnalysis())


def test_normal_structure_combination_remains_valid() -> None:
    class NormalAnalysis:
        structure_score = 80.0
        trend_score = 60.0

    result = DecisionEngine().decide(NormalAnalysis())

    assert 0.0 <= result.score <= 100.0
    assert result.signal in {"BUY", "SELL", "NEUTRAL"}
