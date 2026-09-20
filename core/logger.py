from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from config.settings import Settings
from observability.redaction import redact_value

LOG_DIR = Path("logs")
_LOGGER_NAME = "forex-signal-bot"
_CORRELATION_ID = os.getenv("OBSERVABILITY_CORRELATION_ID") or str(uuid.uuid4())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname.lower(),
            "message": redact_value(record.getMessage()),
            "service": _LOGGER_NAME,
            "logger": record.name,
            "event": getattr(record, "event", "log"),
            "correlation_id": getattr(record, "correlation_id", None) or _CORRELATION_ID,
        }
        for key in ("symbol", "timeframe", "outcome", "cycle_id", "deployment_id", "commit_sha"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = redact_value(value)
        if record.exc_info:
            payload["exception"] = redact_value(self.formatException(record.exc_info))
        return json.dumps(redact_value(payload), ensure_ascii=False, separators=(",", ":"))


def setup_logger() -> logging.Logger:
    """Configure the single application logging pipeline.

    Production logs go to stdout/stderr so Railway and other runtimes can
    collect them centrally. A local file is opt-in via LOG_TO_FILE=true.
    """

    logger = logging.getLogger(_LOGGER_NAME)
    root = logging.getLogger()
    level = getattr(logging, Settings.load().log_level.upper(), logging.INFO)

    root.setLevel(level)
    logger.setLevel(level)

    formatter = JsonFormatter()

    if not any(getattr(handler, "_forex_signal_bot_console", False) for handler in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console._forex_signal_bot_console = True
        root.addHandler(console)

    if os.getenv("LOG_TO_FILE", "").strip().lower() in {"1", "true", "yes", "on"}:
        LOG_DIR.mkdir(exist_ok=True)
        if not any(getattr(handler, "_forex_signal_bot_file", False) for handler in root.handlers):
            file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler._forex_signal_bot_file = True
            root.addHandler(file_handler)

    return logger
