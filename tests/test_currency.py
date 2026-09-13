import pytest

from analysis.currency import get_forex_currency_pair


def test_forex_currency_pair_extracts_base_and_quote():
    assert get_forex_currency_pair("EURUSD") == (
        get_forex_currency_pair("EUR/USD")
    )
    pair = get_forex_currency_pair("EURUSD")
    assert pair.symbol == "EURUSD"
    assert pair.base_currency == "EUR"
    assert pair.quote_currency == "USD"


def test_forex_currency_pair_supports_non_usd_quote_pairs():
    pair = get_forex_currency_pair("EURJPY")
    assert pair.base_currency == "EUR"
    assert pair.quote_currency == "JPY"


def test_forex_currency_pair_rejects_non_forex_symbols():
    for symbol in ("BTCUSDT", "AAPL", "SPX", "XAUUSD", "UNKNOWN"):
        with pytest.raises(ValueError, match="Unsupported forex symbol"):
            get_forex_currency_pair(symbol)
