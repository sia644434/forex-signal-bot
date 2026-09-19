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


def test_settings_market_keyboard_exposes_all_supported_market_families():
    from services.telegram.handlers.callbacks import settings_keyboard, market_symbols_keyboard
    assert {button.callback_data for row in settings_keyboard("settings_market").inline_keyboard for button in row} >= {"market_forex", "market_crypto", "market_stock", "market_index", "market_commodity", "settings"}
    for market in ("forex", "crypto", "stock", "index", "commodity"):
        callbacks = {button.callback_data for row in market_symbols_keyboard(market).inline_keyboard for button in row}
        assert callbacks
        assert all(value.startswith("market_") or value == "settings_market" for value in callbacks)


def test_apply_setting_accepts_canonical_multi_asset_symbols():
    state = TelegramUserState(user_id=1)
    assert _apply_setting(state, "market_BTCUSDT") == "Market BTCUSDT"
    assert state.settings["market_symbol"] == "BTCUSDT"
    assert _apply_setting(state, "market_AAPL") == "Market AAPL"
    assert state.settings["market_symbol"] == "AAPL"
    assert _apply_setting(state, "market_SPX") == "Market SPX"
    assert state.settings["market_symbol"] == "SPX"
    assert _apply_setting(state, "market_XAUUSD") == "Market XAUUSD"
    assert state.settings["market_symbol"] == "XAUUSD"


def test_market_category_callbacks_are_accepted_by_menu_handler_contract():
    from services.telegram.handlers.callbacks import ALLOWED_CALLBACKS
    assert {"market_forex", "market_crypto", "market_stock", "market_index", "market_commodity"}.issubset(ALLOWED_CALLBACKS)


def test_signal_failure_includes_safe_provider_diagnostics():
    from core.errors import ApplicationError
    from services.telegram.handlers.signal import _format_signal_failure

    error = ApplicationError(
        "All market data providers failed.",
        {
            "failures": [
                {"provider": "finnhub", "attempt": 3, "error_type": "RuntimeError", "message": "status=error: symbol not found"},
                {"provider": "twelvedata", "attempt": 3, "error_type": "ApplicationError", "message": "Twelve Data API error for BTC/USDT: symbol not found"},
            ]
        },
    )
    rendered = _format_signal_failure(error, "BTCUSDT", "M15")
    assert "finnhub" in rendered
    assert "twelvedata" in rendered
    assert "symbol not found" in rendered
    assert "All market data providers failed" not in rendered



def test_signal_failure_surfaces_nested_provider_reason():
    from core.errors import ApplicationError
    from services.telegram.handlers.signal import _format_signal_failure

    error = ApplicationError(
        "All market data providers failed.",
        {
            "failures": [
                {
                    "provider": "twelvedata",
                    "attempt": 3,
                    "error_type": "ApplicationError",
                    "message": "Failed to fetch Twelve Data candles.",
                    "details": {"reason": "Twelve Data API error for BTC/USDT: symbol not found"},
                }
            ]
        },
    )
    rendered = _format_signal_failure(error, "BTCUSDT", "M15")
    assert "Twelve Data API error for BTC/USDT: symbol not found" in rendered
