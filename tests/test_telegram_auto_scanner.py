from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.telegram.auto_scan_state import AutoScannerStateStore
from services.telegram.auto_scanner import ContinuousMarketScanner, auto_scanner_interval_seconds


def test_auto_scanner_triggers_only_at_quarter_hour_windows():
    assert ContinuousMarketScanner._should_scan_now(datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc))
    assert ContinuousMarketScanner._should_scan_now(datetime(2026, 9, 19, 12, 1, tzinfo=timezone.utc))
    assert not ContinuousMarketScanner._should_scan_now(datetime(2026, 9, 19, 12, 2, tzinfo=timezone.utc))
    assert not ContinuousMarketScanner._should_scan_now(datetime(2026, 9, 19, 12, 14, tzinfo=timezone.utc))


def test_auto_scanner_interval_is_bounded(monkeypatch):
    monkeypatch.setenv("TELEGRAM_AUTO_SCAN_INTERVAL_SECONDS", "60")
    assert auto_scanner_interval_seconds() == 60
    monkeypatch.setenv("TELEGRAM_AUTO_SCAN_INTERVAL_SECONDS", "10")
    with pytest.raises(ValueError):
        auto_scanner_interval_seconds()


def test_auto_scanner_state_store_round_trip(tmp_path):
    store = AutoScannerStateStore(str(tmp_path / "state.json"))
    assert store.get("processed:BTCUSDT:M15") is None
    store.put("processed:BTCUSDT:M15", "2026-09-19T12:00:00+00:00")
    assert store.get("processed:BTCUSDT:M15") == "2026-09-19T12:00:00+00:00"


def test_default_scanner_universe_covers_every_supported_market():
    from config.symbols import get_all_symbols
    from services.telegram.scanner import DEFAULT_SCAN_SYMBOLS

    assert DEFAULT_SCAN_SYMBOLS == get_all_symbols()
    assert len(DEFAULT_SCAN_SYMBOLS) > 20
