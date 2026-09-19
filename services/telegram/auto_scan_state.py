from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock


class AutoScannerStateStore:
    """Durable deduplication state for the continuous Telegram scanner."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("TELEGRAM_AUTO_SCAN_STATE_FILE", "data/telegram_auto_scan_state.json"))
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RuntimeError(f"Unable to read auto-scanner state: {self.path}") from error
        if not isinstance(payload, dict):
            raise RuntimeError("Auto-scanner state must be a JSON object.")
        return payload

    def _write(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    def get(self, key: str) -> str | None:
        with self._lock:
            value = self._read().get(key)
            return value if isinstance(value, str) else None

    def put(self, key: str, value: str) -> None:
        with self._lock:
            payload = self._read()
            payload[key] = value
            self._write(payload)


__all__ = ["AutoScannerStateStore"]
