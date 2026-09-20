from __future__ import annotations

import logging
from pathlib import Path

import pytest

from core.logger import JsonFormatter, setup_logger
from utils.logger import get_logger


def _reset_root_logger() -> None:
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()


def test_logger_creation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOG_TO_FILE", raising=False)
    _reset_root_logger()

    logger = get_logger("test")

    assert logger.name == "test"
    assert any(getattr(handler, "_forex_signal_bot_console", False) for handler in logging.getLogger().handlers)


def test_legacy_logger_uses_central_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.delenv("LOG_TO_FILE", raising=False)
    _reset_root_logger()

    logger = get_logger("settings-contract-logger")

    assert logger.level == logging.WARNING


def test_core_logger_uses_central_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.delenv("LOG_TO_FILE", raising=False)
    _reset_root_logger()

    configured = setup_logger()

    assert configured.level == logging.ERROR
    assert logging.getLogger().level == logging.ERROR


def test_file_logging_is_opt_in(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOG_TO_FILE", "true")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    _reset_root_logger()

    logger = setup_logger()
    logger.info("file logging contract")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert (Path("logs") / "app.log").exists()


def test_log_output_redacts_bearer_tokens() -> None:
    record = logging.LogRecord(
        name="security-test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Authorization: Bearer %s",
        args=("super-secret-token",),
        exc_info=None,
    )

    rendered = JsonFormatter().format(record)

    assert "super-secret-token" not in rendered
    assert "[REDACTED]" in rendered
