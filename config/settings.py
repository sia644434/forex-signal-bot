from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Optional


_SUPPORTED_STABLECOINS = frozenset({"USDT", "USDC"})


def _is_supported_currency_code(currency: str) -> bool:
    return (len(currency) == 3 and currency.isalpha()) or currency in _SUPPORTED_STABLECOINS


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def _get_bool(name: str, default: bool = False) -> bool:
    value = _get_env(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disabled"}:
        return False
    raise ValueError(f"Invalid boolean value for '{name}': {value}")


def _get_int(name: str, default: int) -> int:
    value = _get_env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Invalid integer value for '{name}': {value}") from error


def _get_float(name: str, default: float) -> float:
    value = _get_env(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"Invalid float value for '{name}': {value}") from error


def _get_list(name: str, default: list[str] | None = None, separator: str = ",") -> list[str]:
    if not separator:
        raise ValueError("Environment list separator cannot be empty.")
    value = _get_env(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_env(key: str, default: str | None = None) -> str | None:
    if not isinstance(key, str):
        raise TypeError("Environment key must be a string.")
    key = key.strip()
    if not key:
        raise ValueError("Environment key cannot be empty.")
    return _get_env(key, default)


def get_required_env(key: str) -> str:
    value = get_env(key)
    if value is None:
        raise RuntimeError(f"Required environment variable '{key}' is not configured.")
    return value


def get_bool_env(key: str, default: bool = False) -> bool:
    return _get_bool(key, default)


def get_int_env(key: str, default: int) -> int:
    return _get_int(key, default)


def get_float_env(key: str, default: float) -> float:
    return _get_float(key, default)


def get_list_env(key: str, default: list[str] | None = None, separator: str = ",") -> list[str]:
    return _get_list(key, default, separator)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Professional Trading Bot"
    environment: str = "development"
    debug: bool = False
    telegram_token: Optional[str] = None
    telegram_enabled: bool = False
    OANDA_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    ALPHAVANTAGE_API_KEY: Optional[str] = None
    default_symbol: str = "EURUSD"
    default_timeframe: str = "1h"
    account_currency: Optional[str] = None
    account_balance: float = 1000.0
    risk_per_trade: float = 0.01
    max_open_positions: int = 5
    timezone: str = "UTC"
    log_level: str = "INFO"
    health_host: str = "0.0.0.0"
    health_port: int = 8080
    ai_enabled: bool = False
    ai_api_key: Optional[str] = None
    ai_model: str = "gpt-5.6-luna"
    ai_temperature: float = 0.2
    request_timeout: int = 30
    max_retries: int = 3
    worker_queue_database_path: str = "worker_queue.sqlite3"
    worker_queue_recovery_grace_seconds: int = 30
    pc_worker_url: Optional[str] = None
    pc_worker_token: Optional[str] = None
    pc_worker_timeout: int = 30
    pc_worker_heartbeat_max_age: int = 120

    def __post_init__(self) -> None:
        if not self.app_name.strip():
            raise ValueError("APP_NAME cannot be empty.")
        if self.environment.lower() not in {"development", "testing", "staging", "production"}:
            raise ValueError("ENVIRONMENT must be development, testing, staging, or production.")
        if self.account_currency is not None:
            currency = self.account_currency.strip().upper()
            if not currency:
                raise ValueError("ACCOUNT_CURRENCY cannot be empty when configured.")
            if not _is_supported_currency_code(currency):
                raise ValueError("ACCOUNT_CURRENCY must be a 3-letter ISO currency code or USDT/USDC.")
            object.__setattr__(self, "account_currency", currency)
        if not math.isfinite(self.account_balance) or self.account_balance <= 0:
            raise ValueError("ACCOUNT_BALANCE must be finite and greater than 0.")
        if not math.isfinite(self.risk_per_trade) or not 0 < self.risk_per_trade <= 1:
            raise ValueError("RISK_PER_TRADE must be finite, greater than 0, and at most 1.")
        if self.max_open_positions < 1:
            raise ValueError("MAX_OPEN_POSITIONS must be at least 1.")
        if not self.timezone.strip():
            raise ValueError("TIMEZONE cannot be empty.")
        if self.log_level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("LOG_LEVEL must be DEBUG, INFO, WARNING, ERROR, or CRITICAL.")
        if not self.health_host.strip():
            raise ValueError("HEALTH_HOST cannot be empty.")
        if not 0 <= self.health_port <= 65535:
            raise ValueError("PORT must be between 0 and 65535.")
        if not math.isfinite(self.ai_temperature) or not 0 <= self.ai_temperature <= 2:
            raise ValueError("AI_TEMPERATURE must be between 0 and 2.")
        if self.request_timeout < 1:
            raise ValueError("REQUEST_TIMEOUT must be at least 1 second.")
        if self.max_retries < 0:
            raise ValueError("MAX_RETRIES cannot be negative.")
        if not self.worker_queue_database_path.strip():
            raise ValueError("WORKER_QUEUE_DATABASE_PATH cannot be empty.")
        if self.worker_queue_recovery_grace_seconds < 0:
            raise ValueError("WORKER_QUEUE_RECOVERY_GRACE_SECONDS cannot be negative.")
        if self.pc_worker_url is not None and not self.pc_worker_url.strip():
            raise ValueError("PC_WORKER_URL cannot be empty.")
        if self.pc_worker_url and not self.pc_worker_token:
            raise ValueError("PC_WORKER_URL is configured but PC_WORKER_TOKEN is missing.")
        if self.pc_worker_timeout < 1:
            raise ValueError("PC_WORKER_TIMEOUT must be at least 1 second.")
        if self.pc_worker_heartbeat_max_age < 1:
            raise ValueError("PC_WORKER_HEARTBEAT_MAX_AGE must be at least 1 second.")
        if self.ai_enabled and not self.ai_api_key:
            raise ValueError("AI_ENABLED is true but AI_API_KEY is not configured.")

    @classmethod
    def load(cls) -> "Settings":
        telegram_token = _get_env("TELEGRAM_BOT_TOKEN")
        ai_api_key = _get_env("AI_API_KEY")
        ai_enabled = _get_bool("AI_ENABLED", bool(ai_api_key))
        queue_path_raw = os.getenv("WORKER_QUEUE_DATABASE_PATH")
        queue_path = "worker_queue.sqlite3" if queue_path_raw is None else queue_path_raw.strip()
        return cls(
            app_name=_get_env("APP_NAME", "Professional Trading Bot"),
            environment=_get_env("ENVIRONMENT", "development"),
            debug=_get_bool("DEBUG", False),
            telegram_token=telegram_token,
            telegram_enabled=bool(telegram_token),
            OANDA_API_KEY=_get_env("OANDA_API_KEY"),
            FINNHUB_API_KEY=_get_env("FINNHUB_API_KEY"),
            ALPHAVANTAGE_API_KEY=_get_env("ALPHAVANTAGE_API_KEY"),
            default_symbol=_get_env("DEFAULT_SYMBOL", "EURUSD"),
            default_timeframe=_get_env("DEFAULT_TIMEFRAME", "1h"),
            account_currency=_get_env("ACCOUNT_CURRENCY"),
            account_balance=_get_float("ACCOUNT_BALANCE", 1000.0),
            risk_per_trade=_get_float("RISK_PER_TRADE", 0.01),
            max_open_positions=_get_int("MAX_OPEN_POSITIONS", 5),
            timezone=_get_env("TIMEZONE", "UTC"),
            log_level=_get_env("LOG_LEVEL", "INFO"),
            health_host=_get_env("HEALTH_HOST", "0.0.0.0"),
            health_port=_get_int("PORT", 8080),
            ai_enabled=ai_enabled,
            ai_api_key=ai_api_key,
            ai_model=_get_env("AI_MODEL", "gpt-5.6-luna"),
            ai_temperature=_get_float("AI_TEMPERATURE", 0.2),
            request_timeout=_get_int("REQUEST_TIMEOUT", 30),
            max_retries=_get_int("MAX_RETRIES", 3),
            worker_queue_database_path=queue_path,
            worker_queue_recovery_grace_seconds=_get_int("WORKER_QUEUE_RECOVERY_GRACE_SECONDS", 30),
            pc_worker_url=_get_env("PC_WORKER_URL"),
            pc_worker_token=_get_env("PC_WORKER_TOKEN"),
            pc_worker_timeout=_get_int("PC_WORKER_TIMEOUT", 30),
            pc_worker_heartbeat_max_age=_get_int("PC_WORKER_HEARTBEAT_MAX_AGE", 120),
        )


settings = Settings.load()

__all__ = [
    "Settings", "settings", "get_env", "get_required_env",
    "get_bool_env", "get_int_env", "get_float_env", "get_list_env",
]
