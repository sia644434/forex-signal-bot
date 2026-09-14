from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data.models import Candle
from data.quality import DataQuality


def candle(timestamp: datetime) -> Candle:
    return Candle(
        symbol="EURUSD",
        timestamp=timestamp,
        open=1.1000,
        high=1.1010,
        low=1.0990,
        close=1.1005,
        volume=100.0,
    )


def test_friday_to_monday_gap_is_treated_as_expected_market_closure():
    friday = candle(datetime(2026, 1, 2, 21, 59, tzinfo=timezone.utc))
    monday = candle(datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc))

    report = DataQuality.inspect(
        [friday, monday],
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
        gap_tolerance=1,
    )

    assert report.valid is True
    assert report.gaps == 0
    assert report.suspicious_gaps == 0


def test_large_intraday_friday_gap_is_not_hidden_by_weekend_exception():
    friday_open = candle(datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc))
    friday_later = candle(datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc))

    report = DataQuality.inspect(
        [friday_open, friday_later],
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
        gap_tolerance=1,
    )

    assert report.valid is False
    assert report.gaps == 1
    assert report.suspicious_gaps == 1


def test_large_intraday_monday_gap_is_not_hidden_by_weekend_exception():
    monday_open = candle(datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc))
    monday_later = candle(datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc))

    report = DataQuality.inspect(
        [monday_open, monday_later],
        expected_symbol="EURUSD",
        expected_interval=timedelta(minutes=1),
        gap_tolerance=1,
    )

    assert report.valid is False
    assert report.gaps == 1
    assert report.suspicious_gaps == 1
