import pytest

from services.telegram.scanner import DEFAULT_SCAN_SYMBOLS, _configured_scan_symbols


def test_default_scanner_universe_covers_multiple_market_families(monkeypatch):
    monkeypatch.delenv("TELEGRAM_SCANNER_SYMBOLS", raising=False)

    symbols = _configured_scan_symbols()

    assert symbols == DEFAULT_SCAN_SYMBOLS
    assert "EURUSD" in symbols
    assert "BTCUSDT" in symbols
    assert "AAPL" in symbols
    assert "SPX" in symbols
    assert "XAUUSD" in symbols


def test_scanner_universe_env_override_is_normalized_and_deduplicated(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SCANNER_SYMBOLS", " eur/usd, BTC/USDT, eurusd ")

    assert _configured_scan_symbols() == ("EURUSD", "BTCUSDT")


def test_scanner_universe_accepts_full_supported_universe(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SCANNER_SYMBOLS", ",".join(DEFAULT_SCAN_SYMBOLS))

    assert _configured_scan_symbols() == DEFAULT_SCAN_SYMBOLS

def test_scanner_universe_rejects_unsupported_symbols(monkeypatch):
    monkeypatch.setenv("TELEGRAM_SCANNER_SYMBOLS", "EURUSD,NOTAREALASSET")

    with pytest.raises(ValueError, match="unsupported symbols"):
        _configured_scan_symbols()

