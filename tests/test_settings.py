import math

import pytest

from config.settings import Settings


def test_settings_without_token(
    monkeypatch,
):

    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )

    settings = Settings.load()

    assert settings.telegram_token is None


def test_worker_queue_settings_are_loaded(monkeypatch):
    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "/data/forex-worker-queue.sqlite3")
    monkeypatch.setenv("WORKER_QUEUE_RECOVERY_GRACE_SECONDS", "45")

    settings = Settings.load()

    assert settings.worker_queue_database_path == "/data/forex-worker-queue.sqlite3"
    assert settings.worker_queue_recovery_grace_seconds == 45


def test_worker_queue_settings_reject_invalid_values(monkeypatch):
    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "   ")
    try:
        Settings.load()
    except ValueError as exc:
        assert "WORKER_QUEUE_DATABASE_PATH" in str(exc)
    else:
        raise AssertionError("Expected empty queue database path to be rejected")

    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "worker_queue.sqlite3")
    monkeypatch.setenv("WORKER_QUEUE_RECOVERY_GRACE_SECONDS", "-1")
    try:
        Settings.load()
    except ValueError as exc:
        assert "WORKER_QUEUE_RECOVERY_GRACE_SECONDS" in str(exc)
    else:
        raise AssertionError("Expected negative recovery grace to be rejected")


def test_pc_worker_transport_settings_are_loaded(monkeypatch):
    monkeypatch.setenv("PC_WORKER_URL", "http://192.168.1.3:8765")
    monkeypatch.setenv("PC_WORKER_TOKEN", "worker-secret")
    monkeypatch.setenv("PC_WORKER_TIMEOUT", "45")
    monkeypatch.setenv("PC_WORKER_HEARTBEAT_MAX_AGE", "90")

    settings = Settings.load()

    assert settings.pc_worker_url == "http://192.168.1.3:8765"
    assert settings.pc_worker_token == "worker-secret"
    assert settings.pc_worker_timeout == 45
    assert settings.pc_worker_heartbeat_max_age == 90


def test_pc_worker_url_requires_token(monkeypatch):
    monkeypatch.setenv("PC_WORKER_URL", "http://worker.example")
    monkeypatch.delenv("PC_WORKER_TOKEN", raising=False)

    try:
        Settings.load()
    except ValueError as exc:
        assert "PC_WORKER_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected configured worker URL without token to be rejected")


def test_pc_worker_timeout_must_be_positive(monkeypatch):
    monkeypatch.setenv("PC_WORKER_TIMEOUT", "0")

    try:
        Settings.load()
    except ValueError as exc:
        assert "PC_WORKER_TIMEOUT" in str(exc)
    else:
        raise AssertionError("Expected non-positive PC worker timeout to be rejected")


def test_pc_worker_heartbeat_max_age_must_be_positive(monkeypatch):
    monkeypatch.setenv("PC_WORKER_HEARTBEAT_MAX_AGE", "0")

    try:
        Settings.load()
    except ValueError as exc:
        assert "PC_WORKER_HEARTBEAT_MAX_AGE" in str(exc)
    else:
        raise AssertionError("Expected non-positive heartbeat max age to be rejected")


def test_account_balance_is_loaded_and_positive(monkeypatch):
    monkeypatch.setenv("ACCOUNT_BALANCE", "25000")

    settings = Settings.load()

    assert settings.account_balance == 25000.0

    monkeypatch.setenv("ACCOUNT_BALANCE", "0")
    with pytest.raises(ValueError, match="ACCOUNT_BALANCE"):
        Settings.load()


def test_settings_reject_non_finite_risk_and_balance(monkeypatch):
    monkeypatch.setenv("ACCOUNT_BALANCE", "nan")
    with pytest.raises(ValueError, match="ACCOUNT_BALANCE"):
        Settings.load()

    monkeypatch.setenv("ACCOUNT_BALANCE", "1000")
    monkeypatch.setenv("RISK_PER_TRADE", str(math.nan))
    with pytest.raises(ValueError, match="RISK_PER_TRADE"):
        Settings.load()

    monkeypatch.setenv("RISK_PER_TRADE", str(math.inf))
    with pytest.raises(ValueError, match="RISK_PER_TRADE"):
        Settings.load()


def test_settings_accept_stablecoin_account_currency(monkeypatch):
    monkeypatch.setenv("ACCOUNT_CURRENCY", "usdt")

    settings = Settings.load()

    assert settings.account_currency == "USDT"


def test_settings_reject_invalid_account_currency(monkeypatch):
    monkeypatch.setenv("ACCOUNT_CURRENCY", "12$")

    with pytest.raises(ValueError, match="ACCOUNT_CURRENCY"):
        Settings.load()
