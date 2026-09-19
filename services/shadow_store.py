from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from threading import Lock


class ShadowComparisonStoreError(RuntimeError):
    """Raised when persisted shadow-comparison state cannot be read or written safely."""


class ShadowComparisonStore:
    """Atomic JSON persistence for shadow-comparison observations."""

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(
            path or os.getenv("SHADOW_COMPARISON_FILE", "data/shadow_comparison.json")
        )
        self._lock = Lock()

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ShadowComparisonStoreError(
                f"unable to read shadow comparison store: {self.path}"
            ) from error
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise ShadowComparisonStoreError(
                f"invalid shadow comparison store structure: {self.path}"
            )
        return payload

    def _write(self, observations: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(observations, ensure_ascii=False, indent=2)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=self.path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except OSError as error:
            raise ShadowComparisonStoreError(
                f"unable to write shadow comparison store: {self.path}"
            ) from error
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def load_all(self) -> list[dict]:
        with self._lock:
            return self._read()

    def save_all(self, observations: list[dict]) -> None:
        with self._lock:
            self._write(observations)


__all__ = ["ShadowComparisonStore", "ShadowComparisonStoreError"]
