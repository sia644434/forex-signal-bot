from __future__ import annotations

import math

import pytest

from analysis.indicator_engine import IndicatorEngine
from analysis.market_structure import MarketStructureAnalyzer, MarketStructureDetector


def test_market_structure_analyzer_alias_matches_detector() -> None:
    assert MarketStructureAnalyzer is MarketStructureDetector


@pytest.mark.parametrize("value", [None, math.nan, math.inf, -math.inf, 0.0, -1.0])
def test_indicator_engine_rejects_invalid_close_values(value) -> None:
    with pytest.raises(ValueError, match="finite and greater than zero"):
        IndicatorEngine().calculate([1.0, value, 1.1])


def test_indicator_engine_rejects_non_numeric_sequence() -> None:
    with pytest.raises(TypeError, match="numeric sequence"):
        IndicatorEngine().calculate("1,2,3")  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, "bad"])
def test_indicator_engine_score_normalization_fails_closed(value) -> None:
    with pytest.raises(ValueError, match="indicator score must be numeric and finite"):
        IndicatorEngine._normalize_score(value)
