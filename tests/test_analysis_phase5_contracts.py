from __future__ import annotations

import math

import pytest

from analysis.indicator_engine import IndicatorEngine
from analysis.market_structure import MarketStructureDetector


def test_market_structure_detector_comes_from_canonical_package() -> None:
    assert MarketStructureDetector.__module__ == "analysis.market_structure.detector"


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


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, 0.0, -1.0, "bad"])
def test_market_structure_rejects_invalid_prices(value) -> None:
    with pytest.raises(ValueError, match="finite and greater than zero"):
        MarketStructureDetector().analyze([1.0, value, 1.1])


@pytest.mark.parametrize("validator_module", ["analysis.indicators.base", "analysis.indicators.moving_average", "analysis.indicators.momentum"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_indicator_primitives_reject_non_finite_values(validator_module, value) -> None:
    import importlib

    module = importlib.import_module(validator_module)
    validator = getattr(module, "validate_series", None) or getattr(module, "_validate_values")
    with pytest.raises((ValueError, TypeError), match="finite"):
        validator([1.0, value, 2.0])
