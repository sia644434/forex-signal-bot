from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock

class PaperTradingStoreError(RuntimeError):
    """Raised when persisted paper-trading state is invalid or unavailable."""

class PaperTradingStore:
    """Atomic JSON persistence for the paper-trading ledger."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("PAPER_TRADING_FILE", "data/paper_trading.json"))
        self._lock = Lock()

    def load(self) -> dict:
        if not self.path.exists():
            return {"open": [], "closed": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise PaperTradingStoreError(f"unable to read paper trading store: {self.path}") from error
        if not isinstance(payload, dict) or not isinstance(payload.get("open", []), list) or not isinstance(payload.get("closed", []), list):
            raise PaperTradingStoreError("invalid paper trading store structure")
        return {"open": payload.get("open", []), "closed": payload.get("closed", [])}

    def save(self, snapshot: dict) -> None:
        if not isinstance(snapshot, dict):
            raise PaperTradingStoreError("paper trading snapshot must be an object")
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(snapshot, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, self.path)
            except OSError as error:
                raise PaperTradingStoreError(f"unable to write paper trading store: {self.path}") from error
            finally:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass

__all__ = ["PaperTradingStore", "PaperTradingStoreError"]