from __future__ import annotations

import logging

from config.settings import Settings
from core.logger import setup_logger


def get_logger(name: str) -> logging.Logger:
    """Backward-compatible access to the single central logging pipeline."""
    setup_logger()
    logger = logging.getLogger(name)
    level = getattr(logging, Settings.load().log_level.upper(), logging.INFO)
    logger.setLevel(level)
    return logger
