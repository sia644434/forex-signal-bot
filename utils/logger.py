from __future__ import annotations

import logging

from core.logger import setup_logger


def get_logger(name: str) -> logging.Logger:
    """Backward-compatible access to the single central logging pipeline."""
    setup_logger()
    return logging.getLogger(name)
