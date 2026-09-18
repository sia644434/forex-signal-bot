from __future__ import annotations

import pytest

from config.settings import (
    Settings,
    get_bool_env,
    get_env,
    get_float_env,
    get_int_env,
    get_list_env,
    get_required_env,
)


def test_environment_helpers_normalize_and_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_TEXT", "  value  ")
    monkeypatch.setenv("TEST_BOOL", "YeS")
    monkeypatch.setenv("TEST_INT", "42")
    monkeypatch.setenv("TEST_FLOAT", "1.25")
    monkeypatch.setenv("TEST_LIST", " EURUSD, GBPUSD, , USDJPY ")

    assert get_env("TEST_TEXT") == "value"
    assert get_bool_env("TEST_BOOL") is True
    assert get_int_env("TEST_INT", 0) == 42
    assert get_float_env("TEST_FLOAT", 0.0) == 1.25
    assert get_list_env("TEST_LIST") == ["EURUSD", "GBPUSD", "USDJPY"]


def test_environment_helpers_apply_defaults_and_required_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_ENV", raising=False)

    assert get_env("MISSING_ENV", "fallback") == "fallback"
    assert get_bool_env("MISSING_ENV", True) is True
    assert get_int_env("MISSING_ENV", 7) == 7
    assert get_float_env("MISSING_ENV", 2.5) == 2.5
    assert get_list_env("MISSING_ENV", ["EURUSD"]) == ["EURUSD"]

    with pytest.raises(RuntimeError, match="MISSING_ENV"):
        get_required_env("MISSING_ENV")


def test_environment_helpers_reject_invalid_values() -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setenv("BAD_BOOL", "maybe")
        monkeypatch.setenv("BAD_INT", "1.2")
        monkeypatch.setenv("BAD_FLOAT", "not-a-number")

        with pytest.raises(ValueError, match="BAD_BOOL"):
            get_bool_env("BAD_BOOL")
        with pytest.raises(ValueError, match="BAD_INT"):
            get_int_env("BAD_INT", 0)
        with pytest.raises(ValueError, match="BAD_FLOAT"):
            get_float_env("BAD_FLOAT", 0.0)


def test_environment_key_and_separator_contracts() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        get_env(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cannot be empty"):
        get_env("   ")
    with pytest.raises(ValueError, match="separator cannot be empty"):
        get_list_env("TEST_LIST", separator="")


def test_settings_loads_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "  Test Bot  ")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("RISK_PER_TRADE", "0.05")
    monkeypatch.setenv("MAX_OPEN_POSITIONS", "3")
    monkeypatch.setenv("AI_ENABLED", "true")
    monkeypatch.setenv("AI_API_KEY", "ai-key")
    monkeypatch.setenv("AI_TEMPERATURE", "0.7")
    monkeypatch.setenv("REQUEST_TIMEOUT", "15")
    monkeypatch.setenv("MAX_RETRIES", "4")
    monkeypatch.setenv("HEALTH_HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9090")

    settings = Settings.load()

    assert settings.app_name == "Test Bot"
    assert settings.environment == "testing"
    assert settings.debug is True
    assert settings.telegram_enabled is True
    assert settings.risk_per_trade == 0.05
    assert settings.max_open_positions == 3
    assert settings.ai_enabled is True
    assert settings.ai_api_key == "ai-key"
    assert settings.ai_temperature == 0.7
    assert settings.request_timeout == 15
    assert settings.max_retries == 4
    assert settings.health_host == "127.0.0.1"
    assert settings.health_port == 9090


def test_settings_validation_rejects_invalid_runtime_configuration() -> None:
    invalid_values = [
        {"environment": "invalid"},
        {"risk_per_trade": 0},
        {"risk_per_trade": 1.1},
        {"max_open_positions": 0},
        {"timezone": "   "},
        {"log_level": "TRACE"},
        {"health_host": "   "},
        {"health_port": -1},
        {"health_port": 65536},
        {"ai_temperature": 2.1},
        {"request_timeout": 0},
        {"max_retries": -1},
        {"ai_enabled": True, "ai_api_key": None},
    ]

    for values in invalid_values:
        with pytest.raises(ValueError):
            Settings(**values)


def test_settings_is_immutable() -> None:
    settings = Settings()

    with pytest.raises((AttributeError, TypeError)):
        settings.environment = "production"  # type: ignore[misc]


def test_production_rejects_debug_and_invalid_worker_urls() -> None:
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(environment="production", debug=True)

    invalid_urls = [
        "ftp://worker.example",
        "worker.example:8765",
        "http://user:pass@worker.example",
        "http://worker.example/#fragment",
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError):
            Settings(pc_worker_url=url, pc_worker_token="secret")


def test_worker_token_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="PC_WORKER_TOKEN"):
        Settings(pc_worker_token="   ")
