from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from .journal_store import JournalStore


@dataclass
class JournalEntry:
    symbol: str
    side: str
    entry: float | None
    stop_loss: float | None
    take_profit: float | None
    notes: str = ""
    status: str = "OPEN"
    result: str | None = None
    created_at: str = ""


_STORE = JournalStore()


def _load(user_id: int) -> list[JournalEntry]:
    # JournalStore.list() returns newest-first at its public boundary. Keep the
    # journal module's internal representation chronological so append and
    # persistence operations remain stable.
    return [
        JournalEntry(**item)
        for item in reversed(_STORE.list(user_id, limit=1000))
    ]


def _save(user_id: int, entries: list[JournalEntry]) -> None:
    # The journal module stores entries chronologically; JournalStore.list()
    # reverses that persisted representation when reading it publicly.
    _STORE.replace(user_id, [asdict(item) for item in entries])


def add_entry(user_id: int, entry: JournalEntry) -> JournalEntry:
    if not entry.created_at:
        entry.created_at = datetime.now(timezone.utc).isoformat()
    # JournalStore.add() performs the read/append/write while holding the
    # store lock, so concurrent Telegram callbacks cannot overwrite each
    # other's newly appended journal entry.
    _STORE.add(user_id, asdict(entry))
    return entry


def list_entries(user_id: int, limit: int = 10) -> list[JournalEntry]:
    entries = _load(user_id)
    return list(reversed(entries))[:limit]


def close_entry(user_id: int, index: int, result: str) -> JournalEntry:
    def _close(item: dict) -> dict:
        item["status"] = "CLOSED"
        item["result"] = result
        return item

    # The public close_entry index contract is chronological, matching the
    # journal module's persisted representation. JournalStore.update_at()
    # performs selection and mutation atomically under the store lock.
    item = _STORE.update_at(user_id, index, _close)
    return JournalEntry(**item)


def format_journal(user_id: int, limit: int = 10) -> str:
    entries = list_entries(user_id, limit)
    if not entries:
        return "📒 <b>ژورنال معاملات</b>\n\nهنوز معامله‌ای ثبت نشده است."
    lines = ["📒 <b>ژورنال معاملات</b>", ""]
    for number, entry in enumerate(entries, 1):
        result = entry.result or entry.status
        lines.append(
            f"{number}. <b>{entry.symbol}</b> {entry.side} | "
            f"ورود {entry.entry if entry.entry is not None else '—'} | "
            f"SL {entry.stop_loss if entry.stop_loss is not None else '—'} | "
            f"TP {entry.take_profit if entry.take_profit is not None else '—'} | {result}"
        )
    return "\n".join(lines)


def export_entries(user_id: int) -> list[dict[str, Any]]:
    return [asdict(entry) for entry in _load(user_id)]


__all__ = ["JournalEntry", "add_entry", "list_entries", "close_entry", "format_journal", "export_entries"]
