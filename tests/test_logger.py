from __future__ import annotations

import logging

import pytest

from core.logger import setup_logger
from utils.logger import get_logger


def test_logger_creation():
    logger = get_logger(
        "test"
    )

    assert logger.name == "test"


def test_legacy_logger_uses_central_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    logger = get_logger("settings-contract-logger")

    assert logger.level == logging.WARNING


def test_core_logger_uses_central_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

    logger = logging.getLogger("forex-signal-bot")
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)

    configured = setup_logger()

    assert configured.level == logging.ERROR
