from __future__ import annotations

from services.telegram.handlers.callbacks import ALLOWED_CALLBACKS, _apply_setting
from services.telegram.handlers.signal import _EXECUTABLE_SIGNALS, _setting_value
from services.telegram.journal import JournalEntry, add_entry, format_journal
from services.telegram.scanner import ScanResult, format_scan
from services.telegram.state import TelegramUserState


def test_callback_contract_allows_only_canonical_values() -> None:
    assert "market_EURUSD" in ALLOWED_CALLBACKS
    assert "timeframe_M15" in ALLOWED_CALLBACKS
    assert "market_injected" not in ALLOWED_CALLBACKS
    assert "timeframe_1D" not in ALLOWED_CALLBACKS


def test_apply_setting_rejects_untrusted_callback_values() -> None:
    state = TelegramUserState(user_id=1)
    state.settings["market_symbol"] = "EURUSD"
    assert _apply_setting(state, "market_injected") is None
    assert state.settings["market_symbol"] == "EURUSD"
    assert _apply_setting(state, "timeframe_1D") is None


def test_apply_setting_accepts_only_supported_market_and_timeframe() -> None:
    state = TelegramUserState(user_id=1)
    assert _apply_setting(state, "market_GBPUSD") == "Market GBPUSD"
    assert state.settings["market_symbol"] == "GBPUSD"
    assert _apply_setting(state, "timeframe_H1") == "Timeframe H1"
    assert state.settings["timeframe"] == "H1"


def test_signal_setting_falls_back_when_state_value_is_not_a_nonempty_string() -> None:
    state = TelegramUserState(user_id=1)
    state.settings["market_symbol"] = None
    assert _setting_value(state, "market_symbol", "EURUSD") == "EURUSD"
    state.settings["market_symbol"] = "   "
    assert _setting_value(state, "market_symbol", "EURUSD") == "EURUSD"


def test_executable_signal_contract_includes_strong_directional_signals() -> None:
    assert {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"} <= _EXECUTABLE_SIGNALS
    assert "NEUTRAL" not in _EXECUTABLE_SIGNALS
    assert "NO_TRADE" not in _EXECUTABLE_SIGNALS


def test_scanner_html_escapes_dynamic_symbol_fields() -> None:
    result = ScanResult(
        symbol="EURUSD<&",
        signal="BUY",
        confidence=0.8,
        score=75.0,
        trade_quality=80.0,
        trade_grade="A",
        trend="up",
        risk_reward=2.0,
    )
    rendered = format_scan([result], "M15")
    assert "EURUSD<&" not in rendered
    assert "EURUSD&lt;&amp;" in rendered


def test_journal_html_escapes_persisted_dynamic_fields(tmp_path, monkeypatch) -> None:
    from services.telegram import journal

    class Store:
        def list(self, user_id, limit=1000):
            return [{
                "symbol": "EURUSD<&",
                "side": "BUY<b>",
                "entry": 1.1,
                "stop_loss": 1.0,
                "take_profit": 1.2,
                "notes": "",
                "status": "OPEN",
                "result": "OK<&",
                "created_at": "",
            }]

    monkeypatch.setattr(journal, "_STORE", Store())
    rendered = format_journal(1)
    assert "EURUSD<&" not in rendered
    assert "BUY<b>" not in rendered
    assert "OK<&" not in rendered
    assert "EURUSD&lt;&amp;" in rendered
