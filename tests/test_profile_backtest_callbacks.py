from services.telegram.profile_backtest_callbacks import _PERIODS, _TIMEFRAMES, _result_text


class _Profile:
    name = "Scalping"
    version = 3


def test_profile_backtest_contract_uses_supported_timeframes_and_ranges():
    assert set(_PERIODS) == {"300", "1000", "3000"}
    assert _TIMEFRAMES == ("M5", "M15", "H1", "H4", "D1")


def test_profile_backtest_result_is_localized():
    result = {
        "profile_id": "scalping",
        "profile_version": 3,
        "bars": 1000,
        "trades": 20,
        "wins": 12,
        "losses": 8,
        "win_rate": 0.6,
        "total_return": 0.125,
        "final_equity": 1.125,
    }
    fa = _result_text(result, _Profile(), "fa")
    en = _result_text(result, _Profile(), "en")
    assert "نتیجه بک‌تست" in fa
    assert "نرخ برد" in fa
    assert "Backtest Result" in en
    assert "Win rate" in en
