from services.telegram.handlers.callbacks import _parse_tracking_callback, _tracking_callback


def test_tracking_callback_binds_exact_symbol_and_timeframe():
    data = _tracking_callback("BTCUSDT", "H1")

    assert data == "signal_untrack:BTCUSDT:H1"
    assert _parse_tracking_callback(data) == ("BTCUSDT", "H1")


def test_malformed_tracking_callback_is_rejected():
    assert _parse_tracking_callback("signal_untrack") is None
    assert _parse_tracking_callback("signal_untrack:BTCUSDT") is None
    assert _parse_tracking_callback("signal_untrack::H1") is None
    assert _parse_tracking_callback("signal_untrack:BTCUSDT:H1:extra") is None
