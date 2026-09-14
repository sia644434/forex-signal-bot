from types import SimpleNamespace

import pytest

from services.telegram import tracker as tracker_module
from services.telegram.tracker_store import TrackerStore, TrackerStoreError


def _report(signal="BUY"):
    return SimpleNamespace(
        signal=signal,
        entry_price=1.1,
        stop_loss=1.09,
        take_profit_1=1.11,
        take_profit_2=1.12,
        take_profit_3=1.13,
    )


def test_track_report_persists_and_restores_across_restart(tmp_path, monkeypatch) -> None:
    store = TrackerStore(str(tmp_path / "telegram_tracker.json"))
    monkeypatch.setattr(tracker_module, "_STORE", store)
    tracker_module.ACTIVE_TRACKS.clear()

    item = tracker_module.track_report(1001, "EURUSD", "M15", _report("STRONG_BUY"))
    assert item.signal == "STRONG_BUY"

    tracker_module.ACTIVE_TRACKS.clear()
    restored = tracker_module._load_tracks()

    assert list(restored) == [(1001, "EURUSD", "M15")]
    assert restored[(1001, "EURUSD", "M15")].signal == "STRONG_BUY"
    assert restored[(1001, "EURUSD", "M15")].take_profit_3 == 1.13


def test_stop_tracking_removes_persisted_track(tmp_path, monkeypatch) -> None:
    store = TrackerStore(str(tmp_path / "telegram_tracker.json"))
    monkeypatch.setattr(tracker_module, "_STORE", store)
    tracker_module.ACTIVE_TRACKS.clear()

    tracker_module.track_report(1002, "GBPUSD", "H1", _report())
    assert tracker_module.stop_tracking(1002, "GBPUSD", "H1") is True
    assert store.load_all() == {}
    assert tracker_module.stop_tracking(1002, "GBPUSD", "H1") is False


def test_tracker_store_corruption_fails_closed(tmp_path) -> None:
    path = tmp_path / "telegram_tracker.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(TrackerStoreError):
        TrackerStore(str(path)).load_all()


def test_tracker_store_rejects_mismatched_identity(tmp_path, monkeypatch) -> None:
    store = TrackerStore(str(tmp_path / "telegram_tracker.json"))
    store.save_all({"1003:EURUSD:M15": {"user_id": 1003, "symbol": "GBPUSD", "timeframe": "M15", "signal": "BUY"}})
    monkeypatch.setattr(tracker_module, "_STORE", store)

    with pytest.raises(TrackerStoreError):
        tracker_module._load_tracks()
