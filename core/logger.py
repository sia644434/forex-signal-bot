from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from config.settings import Settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "service": "forex-signal-bot",
            "logger": record.name,
            "event": getattr(record, "event", "log"),
            "correlation_id": getattr(record, "correlation_id", None) or os.getenv("OBSERVABILITY_CORRELATION_ID") or str(uuid.uuid4()),
        }
        for key in ("symbol", "timeframe", "outcome", "cycle_id", "deployment_id", "commit_sha"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("forex-signal-bot")
    if logger.handlers:
        return logger
    level = Settings.load().log_level.upper()
    logger.setLevel(getattr(logging, level, logging.INFO))
    formatter = JsonFormatter()
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
