from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock


class TelegramStateStoreError(RuntimeError):
    """Raised when persisted Telegram user state cannot be read safely."""


class TelegramStateStore:
    """Small atomic JSON store for durable per-user Telegram preferences."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("TELEGRAM_STATE_FILE", "data/telegram_state.json"))
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise TelegramStateStoreError(f"unable to read Telegram state store: {self.path}") from error
        if not isinstance(data, dict) or not all(
            isinstance(user_id, str) and isinstance(state, dict)
            for user_id, state in data.items()
        ):
            raise TelegramStateStoreError(f"invalid Telegram state store structure: {self.path}")
        return data

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def load(self, user_id: int) -> dict | None:
        with self._lock:
            return self._read().get(str(user_id))

    def save(self, user_id: int, state: dict) -> None:
        with self._lock:
            data = self._read()
            data[str(user_id)] = state
            self._write(data)


__all__ = ["TelegramStateStore", "TelegramStateStoreError"]
