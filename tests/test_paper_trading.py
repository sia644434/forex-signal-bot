import pytest

from services.paper_trading import PaperTradingEngine, compare_shadow_decision


def test_paper_trading_round_trip():
    engine = PaperTradingEngine()
    position = engine.open("BTCUSDT", "BUY", 2, 100, "2026-09-19T09:00:00Z", position_id="p1")
    trade = engine.close(position.position_id, 110, "2026-09-19T10:00:00Z")
    assert trade.pnl == 20
    assert engine.snapshot()["realized_pnl"] == 20


def test_paper_trading_rejects_invalid_side():
    with pytest.raises(ValueError):
        PaperTradingEngine().open("EURUSD", "NO_TRADE", 1, 100, "now")


def test_shadow_comparison_is_explicit():
    result = compare_shadow_decision("BUY", "SELL")
    assert result.agreement is False


def test_paper_trading_marks_open_positions_and_combines_equity():
    engine = PaperTradingEngine()
    engine.open("BTCUSDT", "BUY", 2, 100, "2026-09-19T09:00:00Z", position_id="p1")
    snapshot = engine.snapshot({"BTCUSDT": 105})
    assert snapshot["equity"]["unrealized_pnl"] == 10
    assert snapshot["equity"]["equity_pnl"] == 10


def test_paper_trading_rejects_missing_mark_price():
    engine = PaperTradingEngine()
    engine.open("EURUSD", "SELL", 1, 100, "now", position_id="p2")
    with pytest.raises(ValueError):
        engine.mark_to_market({})
