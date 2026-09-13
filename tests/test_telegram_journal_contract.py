from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from services.telegram import journal as journal_module
from services.telegram.journal import JournalEntry
from services.telegram.journal_store import JournalStore


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

    try:
        journal_module.close_entry(14, 0, "TP1")
    except IndexError as error:
        assert str(error) == "journal entry not found"
    else:
        raise AssertionError("expected close_entry to reject an invalid index")


def test_concurrent_adds_do_not_lose_journal_entries(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(journal_module, "_STORE", JournalStore(str(tmp_path / "journal.json")))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(lambda index: journal_module.add_entry(15, _entry(f"PAIR{index}")), range(40)))

    entries = journal_module.list_entries(15, limit=100)
    assert len(entries) == 40
    assert {entry.symbol for entry in entries} == {f"PAIR{index}" for index in range(40)}
