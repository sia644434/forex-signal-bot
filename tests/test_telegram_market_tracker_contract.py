from types import SimpleNamespace

import pytest

from services.telegram.scanner import DEFAULT_SCAN_SYMBOLS
from services.telegram.tracker import TrackedSignal, _apply_report, refresh_tracking


def _report(signal: str, base: float = 1.1):
    return SimpleNamespace(
        signal=signal,
        entry_price=base,
        stop_loss=base - 0.01,
        take_profit_1=base + 0.01,
        take_profit_2=base + 0.02,
        take_profit_3=base + 0.03,
    )


def test_telegram_scanner_defaults_cover_multiple_asset_classes():
    from config.symbols import get_all_symbols

    assert DEFAULT_SCAN_SYMBOLS == get_all_symbols()
    assert len(DEFAULT_SCAN_SYMBOLS) == 63
    assert "EURUSD" in DEFAULT_SCAN_SYMBOLS
    assert "BTCUSDT" in DEFAULT_SCAN_SYMBOLS
    assert "AAPL" in DEFAULT_SCAN_SYMBOLS
    assert "SPX" in DEFAULT_SCAN_SYMBOLS
    assert "XAUUSD" in DEFAULT_SCAN_SYMBOLS
    assert "WTI" in DEFAULT_SCAN_SYMBOLS


def test_tracker_updates_direction_and_risk_levels_after_signal_flip():
    item = TrackedSignal(
        user_id=1,
        symbol="EURUSD",
        timeframe="M15",
        signal="BUY",
        entry=1.10,
        stop_loss=1.09,
        take_profit_1=1.11,
        take_profit_2=1.12,
        take_profit_3=1.13,
        last_signal="BUY",
    )
    old_signal, new_signal = _apply_report(item, _report("SELL", 1.20))
    assert (old_signal, new_signal) == ("BUY", "SELL")
    assert item.signal == "SELL"
    assert item.entry == 1.20
    assert item.stop_loss == 1.19
    assert item.take_profit_1 == 1.21
    assert item.take_profit_2 == 1.22
    assert item.take_profit_3 == 1.23
    assert item.status == "CHANGED"


def test_tracker_clears_executable_levels_when_analysis_becomes_no_trade():
    item = TrackedSignal(
        user_id=1,
        symbol="EURUSD",
        timeframe="M15",
        signal="BUY",
        entry=1.10,
        stop_loss=1.09,
        take_profit_1=1.11,
        take_profit_2=1.12,
        take_profit_3=1.13,
        last_signal="BUY",
    )
    old_signal, new_signal = _apply_report(item, _report("NO_TRADE"))
    assert (old_signal, new_signal) == ("BUY", "NO_TRADE")
    assert item.signal == "NO_TRADE"
    assert item.entry is None
    assert item.stop_loss is None
    assert item.take_profit_1 is None
    assert item.take_profit_2 is None
    assert item.take_profit_3 is None
    assert item.status == "INVALIDATED"


@pytest.mark.asyncio
async def test_tracker_does_not_apply_old_target_before_current_analysis(monkeypatch):
    item = TrackedSignal(
        user_id=1,
        symbol="EURUSD",
        timeframe="M15",
        signal="BUY",
        entry=1.10,
        stop_loss=1.09,
        take_profit_1=1.11,
        take_profit_2=1.12,
        take_profit_3=1.13,
        last_signal="BUY",
    )

    class MarketData:
        async def get_candles_list(self, symbol, timeframe, limit):
            return [SimpleNamespace(high=1.11, low=1.09, close=1.10)]

    class Engine:
        def __init__(self, *, market_data):
            self.market_data = market_data

        async def analyze(self, candles, *, symbol, timeframe):
            return _report("SELL", 1.20)

    notifications = []

    async def notify(message: str):
        notifications.append(message)

    monkeypatch.setattr("services.telegram.tracker.MarketAwareAnalysisEngine", Engine)
    result = await refresh_tracking(item, notify, MarketData())

    assert result.status == "CHANGED"
    assert result.signal == "SELL"
    assert result.entry == 1.20
    assert result.take_profit_1 == 1.21
    assert notifications == [
        "📢 <b>به‌روزرسانی EURUSD</b>\n\nسیگنال قبلی: <b>BUY</b>\nسیگنال فعلی: <b>SELL</b>\nقیمت: <b>1.1</b>"
    ]
