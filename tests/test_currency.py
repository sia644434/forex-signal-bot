import pytest

from analysis.currency import get_contract_size, get_forex_currency_pair, get_quote_currency


def test_forex_currency_pair_extracts_base_and_quote():
    assert get_forex_currency_pair("EURUSD") == get_forex_currency_pair("EUR/USD")
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


def test_quote_currency_covers_all_supported_asset_classes():
    assert get_quote_currency("EURJPY") == "JPY"
    assert get_quote_currency("BTCUSDT") == "USDT"
    assert get_quote_currency("AAPL") == "USD"
    assert get_quote_currency("SPX") == "USD"
    assert get_quote_currency("XAUUSD") == "USD"


def test_contract_size_does_not_apply_forex_lot_size_to_other_assets():
    assert get_contract_size("EURUSD") == 100000.0
    assert get_contract_size("BTCUSDT") == 1.0
    assert get_contract_size("AAPL") == 1.0
    assert get_contract_size("SPX") == 1.0
    assert get_contract_size("XAUUSD") == 1.0


def test_quote_currency_and_contract_size_reject_unknown_symbols():
    with pytest.raises(ValueError, match="Unsupported symbol"):
        get_quote_currency("UNKNOWN")
    with pytest.raises(ValueError, match="Unsupported symbol"):
        get_contract_size("UNKNOWN")
