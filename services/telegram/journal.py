from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from .journal_store import JournalStore, JournalStoreError


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
_ENTRY_FIELDS = {
    "symbol",
    "side",
    "entry",
    "stop_loss",
    "take_profit",
    "notes",
    "status",
    "result",
    "created_at",
}
_REQUIRED_ENTRY_FIELDS = {"symbol", "side", "entry", "stop_loss", "take_profit"}


def _to_entry(item: dict) -> JournalEntry:
    """Validate persisted entry data before constructing the domain object."""
    if not isinstance(item, dict):
        raise JournalStoreError("invalid journal entry structure")

    if not _REQUIRED_ENTRY_FIELDS.issubset(item) or set(item) - _ENTRY_FIELDS:
        raise JournalStoreError("invalid journal entry structure")

    normalized = dict(item)
    normalized.setdefault("notes", "")
    normalized.setdefault("status", "OPEN")
    normalized.setdefault("result", None)
    normalized.setdefault("created_at", "")

    if not isinstance(normalized["symbol"], str) or not isinstance(normalized["side"], str):
        raise JournalStoreError("invalid journal entry structure")
    if any(
        value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)))
        for value in (normalized["entry"], normalized["stop_loss"], normalized["take_profit"])
    ):
        raise JournalStoreError("invalid journal entry structure")
    if not isinstance(normalized["notes"], str) or not isinstance(normalized["status"], str):
        raise JournalStoreError("invalid journal entry structure")
    if normalized["result"] is not None and not isinstance(normalized["result"], str):
        raise JournalStoreError("invalid journal entry structure")
    if not isinstance(normalized["created_at"], str):
        raise JournalStoreError("invalid journal entry structure")

    return JournalEntry(**normalized)


def _load(user_id: int) -> list[JournalEntry]:
    # JournalStore.list() returns newest-first at its public boundary. Keep the
    # journal module's internal representation chronological so append and
    # persistence operations remain stable.
    return [
        _to_entry(item)
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
    return _to_entry(item)


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
