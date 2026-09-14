import math

import pytest

from analysis.decision_engine import DecisionEngine


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "bad"])
def test_present_component_rejects_non_finite_or_non_numeric_value(value):
    class Analysis:
        smart_money_score = value

    with pytest.raises(ValueError, match="smart_money_score"):
        DecisionEngine().decide(Analysis())


def test_missing_component_keeps_neutral_default():
    class Analysis:
        pass

    result = DecisionEngine().decide(Analysis())
    assert math.isfinite(result.score)
    assert math.isfinite(result.confidence)
