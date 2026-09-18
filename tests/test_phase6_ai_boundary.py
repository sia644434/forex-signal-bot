from __future__ import annotations

import math

import pytest

from ai.parser import AIResponseParser
from config.settings import Settings


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_settings_reject_non_finite_ai_temperature(value) -> None:
    with pytest.raises(ValueError, match="AI_TEMPERATURE"):
        Settings(ai_temperature=value)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_ai_parser_rejects_non_finite_confidence(value) -> None:
    response = AIResponseParser().parse(
        '{"direction":"bullish","confidence":null}',
        provider="test",
        model="test",
    )
    assert response.confidence == 0.0

    assert AIResponseParser._normalize_confidence(value) == 0.0
