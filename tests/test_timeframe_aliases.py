from __future__ import annotations

from config.symbols import normalize_timeframe


def test_normalize_timeframe_accepts_analysis_aliases():
    assert normalize_timeframe("D1") == "1d"
    assert normalize_timeframe("W1") == "1w"
    assert normalize_timeframe("d1") == "1d"
    assert normalize_timeframe("w1") == "1w"
