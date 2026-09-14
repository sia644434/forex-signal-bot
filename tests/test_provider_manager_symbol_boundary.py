from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.provider_manager import ProviderManager


def candle(symbol: str) -> Candle:
    timestamp = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    return Candle(
        symbol=symbol,
        timestamp=timestamp,
        open=1.0,
        high=1.1,
        low=0.9,
        close=1.05,
        volume=1.0,
    )


@pytest.mark.parametrize(
    ("requested", "returned"),
    [
        ("EUR/USD", "EUR_USD"),
        ("EUR/USD", "EURUSD"),
        ("EUR_USD", "EUR/USD"),
        ("eur-usd", "EUR_USD"),
    ],
)
def test_provider_result_symbol_validation_accepts_equivalent_formatting(
    requested: str, returned: str
) -> None:
    result = ProviderManager._validate_result("test", [candle(returned)], requested)
    assert len(result) == 1
    assert result[0].symbol == returned


def test_provider_result_symbol_validation_still_rejects_different_symbol() -> None:
    with pytest.raises(Exception, match="unexpected symbol"):
        ProviderManager._validate_result("test", [candle("GBPUSD")], "EUR/USD")
