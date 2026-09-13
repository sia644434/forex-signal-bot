from __future__ import annotations

import asyncio
from dataclasses import dataclass

import services.telegram.tracker as tracker_module
from services.telegram.tracker import (
    ACTIVE_TRACKS,
    list_tracking,
    refresh_tracking,
    stop_tracking,
    track_report,
)


@dataclass
class Report:
    signal: str
    entry_price: float | None = 100.0
    stop_loss: float | None = 95.0
    take_profit_1: float | None = 105.0
    take_profit_2: float | None = 110.0
    take_profit_3: float | None = 115.0


@dataclass
class Candle:
    high: float
    low: float
    close: float


class FakeMarketData:
    def __init__(self, candles: list[Candle]) -> None:
        self.candles = candles

    async def get_candles_list(self, symbol: str, timeframe: str, limit: int):
        return self.candles


def setup_function() -> None:
    ACTIVE_TRACKS.clear()


def teardown_function() -> None:
    ACTIVE_TRACKS.clear()


async def collect_notification(notifications: list[str], message: str) -> None:
    notifications.append(message)


def test_track_report_replaces_same_user_symbol_timeframe_and_lists_it() -> None:
    first = track_report(1, "EURUSD", "M15", Report("BUY"))
    second = track_report(1, "EURUSD", "M15", Report("SELL"))

    assert first is not second
    assert list_tracking(1) == [second]
    assert list_tracking(2) == []


def test_stop_tracking_removes_existing_track_and_is_idempotent() -> None:
    track_report(1, "EURUSD", "M15", Report("BUY"))

    assert stop_tracking(1, "EURUSD", "M15") is True
    assert stop_tracking(1, "EURUSD", "M15") is False
    assert list_tracking(1) == []


def test_refresh_tracking_stops_buy_when_stop_loss_is_touched() -> None:
    item = track_report(1, "EURUSD", "M15", Report("BUY"))
    notifications: list[str] = []

    result = asyncio.run(
        refresh_tracking(
            item,
            lambda message: collect_notification(notifications, message),
            FakeMarketData([Candle(high=101.0, low=94.0, close=96.0)]),
        )
    )

    assert result.status == "STOPPED"
    assert notifications and "حد ضرر لمس شد" in notifications[0]
    assert list_tracking(1) == []


def test_refresh_tracking_marks_buy_target_and_removes_track() -> None:
    item = track_report(1, "EURUSD", "M15", Report("BUY"))
    notifications: list[str] = []

    result = asyncio.run(
        refresh_tracking(
            item,
            lambda message: collect_notification(notifications, message),
            FakeMarketData([Candle(high=106.0, low=99.0, close=104.0)]),
        )
    )

    assert result.status == "TARGET_REACHED"
    assert notifications and "TP1 لمس شد" in notifications[0]
    assert list_tracking(1) == []


def test_refresh_tracking_records_signal_change_and_updates_timestamp(monkeypatch) -> None:
    item = track_report(1, "EURUSD", "M15", Report("BUY"))
    notifications: list[str] = []

    class FakeEngine:
        async def analyze(self, candles, *, symbol: str, timeframe: str):
            return Report("SELL")

    monkeypatch.setattr(tracker_module, "MarketAwareAnalysisEngine", FakeEngine)

    result = asyncio.run(
        refresh_tracking(
            item,
            lambda message: collect_notification(notifications, message),
            FakeMarketData([Candle(high=101.0, low=99.0, close=100.5)]),
        )
    )

    assert result.last_signal == "SELL"
    assert result.status == "CHANGED"
    assert result.updated_at
    assert notifications and "سیگنال فعلی" in notifications[0]
    assert list_tracking(1) == [item]
