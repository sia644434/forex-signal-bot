import json

import json

import pytest

from services.paper_store import PaperTradingStore, PaperTradingStoreError
from services.paper_trading import PaperTradingEngine, ShadowComparisonLedger, compare_shadow_decision
from services.shadow_store import ShadowComparisonStore, ShadowComparisonStoreError


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


def test_shadow_comparison_ledger_tracks_agreement_rate():
    ledger = ShadowComparisonLedger()
    ledger.record("BUY", "BUY", "2026-09-19T10:00:00Z")
    ledger.record("BUY", "SELL", "2026-09-19T10:01:00Z")
    summary = ledger.summary()
    assert summary["total"] == 2
    assert summary["agreements"] == 1
    assert summary["disagreements"] == 1
    assert summary["agreement_rate"] == 0.5


def test_shadow_comparison_ledger_clear_resets_history():
    ledger = ShadowComparisonLedger()
    ledger.record("SELL", "SELL", "2026-09-19T10:00:00Z")
    ledger.clear()
    assert ledger.summary()["total"] == 0


def test_shadow_comparison_ledger_persists_and_reloads(tmp_path):
    path = tmp_path / "shadow.json"
    first = ShadowComparisonLedger(ShadowComparisonStore(str(path)))
    first.record("BUY", "BUY", "2026-09-19T10:00:00Z")
    first.record("BUY", "SELL", "2026-09-19T10:01:00Z")

    second = ShadowComparisonLedger(ShadowComparisonStore(str(path)))
    summary = second.summary()
    assert summary["total"] == 2
    assert summary["agreements"] == 1
    assert summary["disagreements"] == 1


def test_shadow_comparison_store_rejects_invalid_structure(tmp_path):
    path = tmp_path / "shadow.json"
    path.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
    with pytest.raises(ShadowComparisonStoreError):
        ShadowComparisonStore(str(path)).load_all()


def test_shadow_comparison_store_writes_atomically(tmp_path):
    path = tmp_path / "nested" / "shadow.json"
    store = ShadowComparisonStore(str(path))
    store.save_all([{"timestamp": "now", "paper_decision": "BUY", "reference_decision": "BUY", "agreement": True}])
    assert json.loads(path.read_text(encoding="utf-8"))[0]["agreement"] is True


def test_paper_trading_persists_and_reloads(tmp_path):
    path = tmp_path / "paper.json"
    first = PaperTradingEngine(PaperTradingStore(str(path)))
    first.open("BTCUSDT", "BUY", 2, 100, "2026-09-19T09:00:00Z", position_id="p1")
    second = PaperTradingEngine(PaperTradingStore(str(path)))
    assert second.snapshot()["open"][0]["position_id"] == "p1"
    trade = second.close("p1", 110, "2026-09-19T10:00:00Z")
    assert trade.pnl == 20
    third = PaperTradingEngine(PaperTradingStore(str(path)))
    assert third.snapshot()["realized_pnl"] == 20
    assert third.snapshot()["open"] == []


def test_paper_trading_store_rejects_invalid_structure(tmp_path):
    path = tmp_path / "paper.json"
    path.write_text(json.dumps({"open": "bad", "closed": []}), encoding="utf-8")
    with pytest.raises(PaperTradingStoreError):
        PaperTradingStore(str(path)).load()
