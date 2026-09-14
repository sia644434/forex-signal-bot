from types import SimpleNamespace

from services.telegram.scanner import DEFAULT_SCAN_SYMBOLS
from services.telegram.tracker import TrackedSignal, _apply_report


def _report(signal: str, base: float = 1.1):
    return SimpleNamespace(
        signal=signal,
        entry_price=base,
        stop_loss=base - 0.01,
        take_profit_1=base + 0.01,
        take_profit_2=base + 0.02,
        take_profit_3=base + 0.03,
    )


def test_telegram_scanner_defaults_are_forex_only():
    assert DEFAULT_SCAN_SYMBOLS == ("EURUSD", "GBPUSD", "USDJPY", "EURJPY")
    assert all(len(symbol) == 6 for symbol in DEFAULT_SCAN_SYMBOLS)
    assert "XAUUSD" not in DEFAULT_SCAN_SYMBOLS


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
