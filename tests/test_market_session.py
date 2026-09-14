from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data.models import Candle
from services.telegram.market_session import CLOSED, NO_DATA, OPEN, STALE, evaluate_market_status


NOW = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)


def candle(timestamp: datetime) -> Candle:
    return Candle(
        symbol="EURUSD",
        timestamp=timestamp,
        open=1.1,
        high=1.11,
        low=1.09,
        close=1.105,
        volume=1.0,
    )


def test_empty_candles_return_no_data() -> None:
    assert evaluate_market_status([], now=NOW).status == NO_DATA


def test_naive_timestamp_is_rejected_at_canonical_candle_boundary() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        candle(datetime(2026, 9, 14, 11, 0))


def test_invalid_timestamp_string_returns_no_data() -> None:
    result = evaluate_market_status(
        [type("CandleLike", (), {"timestamp": "not-a-timestamp"})()],
        now=NOW,
    )
    assert result.status == NO_DATA


def test_future_timestamp_returns_no_data() -> None:
    result = evaluate_market_status(
        [candle(NOW + timedelta(minutes=1))],
        now=NOW,
    )
    assert result.status == NO_DATA


def test_stale_threshold_scales_with_timeframe() -> None:
    result = evaluate_market_status(
        [candle(NOW - timedelta(minutes=91))],
        "M15",
        symbol="EURUSD",
        now=NOW,
    )
    assert result.status == STALE


def test_fresh_data_is_open_on_weekday() -> None:
    result = evaluate_market_status(
        [candle(NOW - timedelta(minutes=10))],
        "M15",
        symbol="EURUSD",
        now=NOW,
    )
    assert result.status == OPEN


def test_forex_is_closed_on_weekend() -> None:
    saturday = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    result = evaluate_market_status(
        [candle(saturday - timedelta(minutes=10))],
        "M15",
        symbol="EURUSD",
        now=saturday,
    )
    assert result.status == CLOSED


def test_crypto_is_not_closed_only_because_it_is_weekend() -> None:
    saturday = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    result = evaluate_market_status(
        [candle(saturday - timedelta(minutes=10))],
        "M15",
        symbol="BTCUSDT",
        market_type="crypto",
        now=saturday,
    )
    assert result.status == OPEN


def test_invalid_now_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        evaluate_market_status(
            [candle(NOW)],
            now=datetime(2026, 9, 14, 12, 0),
        )
