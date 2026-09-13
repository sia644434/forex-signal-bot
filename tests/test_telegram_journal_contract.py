from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from services.telegram import journal as journal_module
from services.telegram.journal import JournalEntry
from services.telegram.journal_store import JournalStore, JournalStoreError


def _entry(symbol: str) -> JournalEntry:
    return JournalEntry(
        symbol=symbol,
        side="BUY",
        entry=100.0,
        stop_loss=95.0,
        take_profit=105.0,
    )


def test_add_and_list_preserve_newest_first_order(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(journal_module, "_STORE", JournalStore(str(tmp_path / "journal.json")))

    journal_module.add_entry(11, _entry("EURUSD"))
    journal_module.add_entry(11, _entry("GBPUSD"))

    entries = journal_module.list_entries(11)
    assert [entry.symbol for entry in entries] == ["GBPUSD", "EURUSD"]


def test_journal_order_survives_reload_between_store_instances(tmp_path, monkeypatch) -> None:
    path = str(tmp_path / "journal.json")
    first = JournalStore(path)
    monkeypatch.setattr(journal_module, "_STORE", first)

    journal_module.add_entry(12, _entry("EURUSD"))
    journal_module.add_entry(12, _entry("USDJPY"))

    monkeypatch.setattr(journal_module, "_STORE", JournalStore(path))
    assert [entry.symbol for entry in journal_module.list_entries(12)] == ["USDJPY", "EURUSD"]


def test_close_entry_updates_selected_entry_without_reordering(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(journal_module, "_STORE", JournalStore(str(tmp_path / "journal.json")))

    journal_module.add_entry(13, _entry("EURUSD"))
    journal_module.add_entry(13, _entry("GBPUSD"))

    closed = journal_module.close_entry(13, 0, "TP1")
    entries = journal_module.list_entries(13)

    assert closed.symbol == "EURUSD"
    assert closed.status == "CLOSED"
    assert closed.result == "TP1"
    assert [entry.symbol for entry in entries] == ["GBPUSD", "EURUSD"]
    assert entries[1].status == "CLOSED"
    assert entries[1].result == "TP1"


def test_close_entry_rejects_invalid_index(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(journal_module, "_STORE", JournalStore(str(tmp_path / "journal.json")))

    with pytest.raises(IndexError, match="journal entry not found"):
        journal_module.close_entry(14, 0, "TP1")


def test_concurrent_adds_do_not_lose_journal_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(journal_module, "_STORE", JournalStore(str(tmp_path / "journal.json")))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda index: journal_module.add_entry(15, _entry(f"PAIR{index}")), range(40)))

    entries = journal_module.list_entries(15, limit=100)
    assert len(entries) == 40
    assert {entry.symbol for entry in entries} == {f"PAIR{index}" for index in range(40)}


def test_corrupt_store_fails_closed_without_overwriting_data(tmp_path) -> None:
    path = tmp_path / "journal.json"
    original = "{not-valid-json"
    path.write_text(original, encoding="utf-8")
    store = JournalStore(str(path))

    with pytest.raises(JournalStoreError, match="unable to read journal store"):
        store.add(16, {"symbol": "EURUSD"})

    assert path.read_text(encoding="utf-8") == original


def test_corrupt_store_is_not_reported_as_empty(tmp_path) -> None:
    path = tmp_path / "journal.json"
    path.write_text("[broken", encoding="utf-8")
    store = JournalStore(str(path))

    with pytest.raises(JournalStoreError, match="unable to read journal store"):
        store.list(17)


@pytest.mark.parametrize(
    "payload",
    [
        "[]",
        "null",
        '{"16": "not-a-list"}',
        '{"16": ["not-an-entry-object"]}',
    ],
)
def test_structurally_invalid_store_fails_closed(tmp_path, payload) -> None:
    path = tmp_path / "journal.json"
    path.write_text(payload, encoding="utf-8")
    store = JournalStore(str(path))

    with pytest.raises(JournalStoreError, match="invalid journal store structure"):
        store.list(16)

    assert path.read_text(encoding="utf-8") == payload
