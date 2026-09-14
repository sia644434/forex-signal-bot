from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock


class TrackerStoreError(RuntimeError):
    """Raised when persisted Telegram tracking state cannot be read safely."""


class TrackerStore:
    """Small atomic JSON store for durable active Telegram signal tracking."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("TELEGRAM_TRACKER_FILE", "data/telegram_tracker.json"))
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise TrackerStoreError(f"unable to read Telegram tracker store: {self.path}") from error
        if not isinstance(data, dict) or not all(
            isinstance(key, str) and isinstance(item, dict)
            for key, item in data.items()
        ):
            raise TrackerStoreError(f"invalid Telegram tracker store structure: {self.path}")
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def load_all(self) -> dict[str, dict]:
        with self._lock:
            return self._read()

    def save_all(self, items: dict[str, dict]) -> None:
        with self._lock:
            self._write(items)


__all__ = ["TrackerStore", "TrackerStoreError"]
