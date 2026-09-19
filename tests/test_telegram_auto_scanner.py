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


def test_auto_scanner_session_filter_skips_closed_non_crypto_markets():
    from config.symbols import get_market_type

    symbols = ("EURUSD", "BTCUSDT", "AAPL")
    saturday = datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc)
    monday = datetime(2026, 9, 21, 12, 0, tzinfo=timezone.utc)

    assert ContinuousMarketScanner._eligible_symbols_for_session(symbols, saturday) == ("BTCUSDT",)
    assert ContinuousMarketScanner._eligible_symbols_for_session(symbols, monday) == symbols
    assert get_market_type("BTCUSDT") == "crypto"


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
    assert len(DEFAULT_SCAN_SYMBOLS) == 63


def test_scanner_env_override_accepts_complete_supported_universe(monkeypatch):
    from config.symbols import get_all_symbols
    from services.telegram.scanner import _configured_scan_symbols

    monkeypatch.setenv("TELEGRAM_SCANNER_SYMBOLS", ",".join(get_all_symbols()))
    assert _configured_scan_symbols() == get_all_symbols()


def test_notification_key_is_recipient_and_signal_specific():
    scanner = ContinuousMarketScanner()
    assert scanner._notification_key("BTCUSDT", "M15", "2026-09-19T12:00:00+00:00", "BUY", 123) != (
        scanner._notification_key("BTCUSDT", "M15", "2026-09-19T12:00:00+00:00", "BUY", 456)
    )
    assert scanner._notification_key("BTCUSDT", "M15", "2026-09-19T12:00:00+00:00", "BUY", 123) != (
        scanner._notification_key("BTCUSDT", "M15", "2026-09-19T12:15:00+00:00", "BUY", 123)
    )


@pytest.mark.asyncio
async def test_notification_retry_skips_already_delivered_recipient(monkeypatch):
    from types import SimpleNamespace
    import services.telegram.auto_scanner as auto_scanner_module

    scanner = ContinuousMarketScanner()
    monkeypatch.setattr(auto_scanner_module, "_chat_ids", lambda: (101, 202))
    monkeypatch.setattr(
        auto_scanner_module,
        "get_user_state",
        lambda chat_id: SimpleNamespace(
            settings={"notifications_enabled": True},
            language="fa",
        ),
    )
    monkeypatch.setattr(auto_scanner_module, "_format_signal", lambda *args: "signal")

    class FakeBot:
        def __init__(self):
            self.calls = []
            self.fail_202 = True

        async def send_message(self, *, chat_id, text, parse_mode):
            self.calls.append(chat_id)
            if chat_id == 202 and self.fail_202:
                raise RuntimeError("temporary Telegram failure")

    decision = SimpleNamespace(
        symbol="BTCUSDT",
        setup_timeframe="M15",
        direction="BUY",
        setup_report=SimpleNamespace(),
        alignment_score=80.0,
        lower_timeframe_score=70.0,
        reasons=[],
    )
    bot = FakeBot()

    first_sent, first_eligible = await scanner._notify(
        bot, decision, "2026-09-19T12:00:00+00:00"
    )
    assert (first_sent, first_eligible) == (1, 2)
    assert bot.calls == [101, 202]

    bot.fail_202 = False
    second_sent, second_eligible = await scanner._notify(
        bot, decision, "2026-09-19T12:00:00+00:00"
    )
    assert (second_sent, second_eligible) == (2, 2)
    assert bot.calls == [101, 202, 202]


def test_scanner_scheduler_event_logs_for_expected_job(monkeypatch):
    import services.telegram.client as client_module
    from types import SimpleNamespace
    from apscheduler.events import EVENT_JOB_EXECUTED

    messages = []
    monkeypatch.setattr(client_module.logger, "info", lambda *args, **kwargs: messages.append(args))

    event = SimpleNamespace(
        code=EVENT_JOB_EXECUTED,
        job_id=client_module.AUTO_SCANNER_JOB_NAME,
        scheduled_run_time=datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),
    )
    client_module._log_scanner_scheduler_event(event)

    assert messages
    assert "Automatic scanner scheduler event: executed" in messages[0][0]


@pytest.mark.asyncio
async def test_continuous_scan_wrapper_logs_and_reraises_job_failure(monkeypatch):
    import services.telegram.auto_scanner as auto_scanner_module
    from types import SimpleNamespace

    class FailingScanner:
        async def run_once(self, bot, application):
            raise RuntimeError("scanner boom")

    monkeypatch.setattr(auto_scanner_module, "_SCANNER", FailingScanner())

    errors = []
    monkeypatch.setattr(auto_scanner_module.logger, "exception", lambda *args, **kwargs: errors.append(args))

    context = SimpleNamespace(bot=object(), application=object())
    with pytest.raises(RuntimeError, match="scanner boom"):
        await auto_scanner_module.run_continuous_market_scan(context)

    assert errors
    assert "Automatic scanner job crashed" in errors[0][0]
