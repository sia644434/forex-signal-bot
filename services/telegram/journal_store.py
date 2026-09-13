from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Callable


class JournalStoreError(RuntimeError):
    """Raised when the persisted journal cannot be read safely."""


class JournalStore:
    """Small dependency-free persistent journal store suitable for Railway volumes."""

    def __init__(self, path: str = "data/journal.json"):
        self.path = Path(path)
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            # Never treat a read failure or corrupted JSON as an empty journal:
            # a subsequent write would otherwise silently discard persisted data.
            raise JournalStoreError(f"unable to read journal store: {self.path}") from error

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def add(self, user_id: int, entry: dict) -> None:
        with self._lock:
            data = self._read()
            data.setdefault(str(user_id), []).append(entry)
            self._write(data)

    def list(self, user_id: int, limit: int = 20) -> list[dict]:
        with self._lock:
            data = self._read()
            return list(reversed(data.get(str(user_id), [])))[:limit]

    def replace(self, user_id: int, entries: list[dict]) -> None:
        with self._lock:
            data = self._read()
            data[str(user_id)] = entries
            self._write(data)

    def update_at(self, user_id: int, index: int, updater: Callable[[dict], dict]) -> dict:
        """Atomically update one chronological entry and return the stored value."""
        with self._lock:
            data = self._read()
            entries = data.get(str(user_id), [])
            if index < 0 or index >= len(entries):
                raise IndexError("journal entry not found")
            updated = updater(dict(entries[index]))
            entries[index] = updated
            data[str(user_id)] = entries
            self._write(data)
            return dict(updated)
