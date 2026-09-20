from __future__ import annotations

import re
from typing import Any

_SECRET_KEY = re.compile(
    r"(token|secret|password|api[_-]?key|authorization|cookie|credential|private[_-]?key)",
    re.IGNORECASE,
)
_BEARER = re.compile(r"(bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE)
_AUTHORIZATION = re.compile(r"(authorization\s*:\s*)([^\s,;]+)", re.IGNORECASE)
_TELEGRAM_BOT_URL = re.compile(r"(api[.]telegram[.]org/bot)[A-Za-z0-9_-]+:[A-Za-z0-9_-]+", re.IGNORECASE)
_KEY_VALUE_SECRET = re.compile(
    r"((?:token|secret|password|api[_-]?key|access[_-]?token|refresh[_-]?token)\s*[=:]\s*)([^\s,;]+)",
    re.IGNORECASE,
)


def _redact_text(value: str) -> str:
    value = _BEARER.sub(r"\1[REDACTED]", value)
    value = _AUTHORIZATION.sub(r"\1[REDACTED]", value)
    value = _TELEGRAM_BOT_URL.sub(r"\1[REDACTED]", value)
    return _KEY_VALUE_SECRET.sub(r"\1[REDACTED]", value)


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("[REDACTED]" if _SECRET_KEY.search(str(key)) else redact_value(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value
