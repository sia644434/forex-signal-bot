from __future__ import annotations

import asyncio
import math
import time
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterable

from core.errors import ApplicationError
from core.logger import setup_logger
from data.base import MarketDataProvider
from data.factory import ProviderFactory
from data.models import Candle

logger = setup_logger()


@dataclass(frozen=True, slots=True)
class ProviderFailure:
    provider: str
    attempt: int
    error_type: str
    message: str


ProviderReference = str | MarketDataProvider


class ProviderManager:
    DEFAULT_PROVIDERS: tuple[str, ...] = ("oanda", "finnhub", "alphavantage")
    DEFAULT_RETRIES = 2

    def __init__(self, providers: Iterable[ProviderReference] | None = None, *, retries: int = DEFAULT_RETRIES, retry_delay: float = 0.5, cooldown_seconds: float = 30.0) -> None:
        raw_providers = list(self.DEFAULT_PROVIDERS if providers is None else providers)
        if not raw_providers:
            raise ValueError("At least one provider must be configured.")
        self.retries = self._validate_non_negative_int(retries, "retries")
        self.retry_delay = self._validate_non_negative_number(retry_delay, "retry_delay")
        self.cooldown_seconds = self._validate_non_negative_number(cooldown_seconds, "cooldown_seconds")
        self._providers: tuple[str, ...]
        self._provider_instances: dict[str, MarketDataProvider] = {}
        self._provider_objects: dict[str, MarketDataProvider] = {}
        names: list[str] = []
        for index, reference in enumerate(raw_providers):
            if isinstance(reference, str):
                name = ProviderFactory.normalize_name(reference)
                if not ProviderFactory.is_supported(name):
                    raise ApplicationError("Unknown market data provider.", {"provider": name, "available": ProviderFactory.available()})
                instance = None
            else:
                instance = reference
                if not self._is_provider_instance(instance):
                    raise TypeError("Each provider must be either a provider name string or an object implementing get_candles().")
                name = self._provider_instance_name(instance, index)
            if name in names:
                raise ValueError(f"Duplicate provider identity: {name}")
            names.append(name)
            if instance is not None:
                self._provider_objects[name] = instance
        self._providers = tuple(names)
        if not self._providers:
            raise ValueError("At least one provider must be configured.")
        self._cooldowns: dict[str, float] = {}
        self._last_failures: ContextVar[tuple[ProviderFailure, ...]] = ContextVar("provider_manager_last_failures", default=())

    @staticmethod
    def _validate_non_negative_int(value: int, name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
        return value

    @staticmethod
    def _validate_non_negative_number(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number.")
        value = float(value)
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")
        return value

    @staticmethod
    def _is_provider_instance(provider: object) -> bool:
        return callable(getattr(provider, "get_candles", None))

    @staticmethod
    def _provider_instance_name(provider: MarketDataProvider, index: int) -> str:
        for attribute in ("name", "provider_name"):
            value = getattr(provider, attribute, None)
            if isinstance(value, str) and value.strip():
                try:
                    return ProviderFactory.normalize_name(value)
                except (TypeError, ValueError):
                    pass
        name = provider.__class__.__name__.strip().lower()
        if name.endswith("provider"):
            name = name[:-8]
        return f"{name or 'provider'}_{index}"

    @property
    def providers(self) -> tuple[str, ...]:
        return self._providers

    def set_providers(self, providers: Iterable[ProviderReference]) -> None:
        raw = list(providers)
        if not raw:
            raise ValueError("At least one provider must be configured.")
        names: list[str] = []
        objects: dict[str, MarketDataProvider] = {}
        for index, reference in enumerate(raw):
            if isinstance(reference, str):
                name = ProviderFactory.normalize_name(reference)
                if not ProviderFactory.is_supported(name):
                    raise ApplicationError("Unknown market data provider.", {"provider": name, "available": ProviderFactory.available()})
            else:
                if not self._is_provider_instance(reference):
                    raise TypeError("Each provider must be either a provider name string or an object implementing get_candles().")
                name = self._provider_instance_name(reference, index)
                objects[name] = reference
            if name in names:
                raise ValueError(f"Duplicate provider identity: {name}")
            names.append(name)
        active = set(names)
        self._providers = tuple(names)
        self._provider_objects = objects
        self._provider_instances = {name: instance for name, instance in self._provider_instances.items() if name in active}
        self._cooldowns = {name: expiry for name, expiry in self._cooldowns.items() if name in active}

    def _get_provider(self, provider_name: str) -> MarketDataProvider:
        if provider_name in self._provider_objects:
            return self._provider_objects[provider_name]
        provider = self._provider_instances.get(provider_name)
        if provider is None:
            provider = ProviderFactory.create(provider_name)
            self._provider_instances[provider_name] = provider
        return provider

    def clear_instances(self) -> None:
        self._provider_instances.clear()

    def _is_in_cooldown(self, provider_name: str) -> bool:
        expiry = self._cooldowns.get(provider_name)
        if expiry is None:
            return False
        if time.monotonic() >= expiry:
            self._cooldowns.pop(provider_name, None)
            return False
        return True

    def _put_in_cooldown(self, provider_name: str) -> None:
        if self.cooldown_seconds > 0:
            self._cooldowns[provider_name] = time.monotonic() + self.cooldown_seconds

    def clear_cooldown(self, provider_name: str) -> None:
        self._cooldowns.pop(provider_name, None)
        try:
            self._cooldowns.pop(ProviderFactory.normalize_name(provider_name), None)
        except (TypeError, ValueError):
            pass

    def clear_all_cooldowns(self) -> None:
        self._cooldowns.clear()

    @property
    def last_failures(self) -> tuple[ProviderFailure, ...]:
        return self._last_failures.get()

    async def _request_with_retry(self, provider_name: str, provider: MarketDataProvider, *, symbol: str, timeframe: str, limit: int, failures: list[ProviderFailure]) -> list[Candle]:
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 2):
            try:
                candles = await provider.get_candles(symbol=symbol, timeframe=timeframe, limit=limit)
                validated = self._validate_result(provider_name, candles, symbol)
                if not validated:
                    raise ApplicationError("Provider returned no candles.", {"provider": provider_name, "symbol": symbol, "timeframe": timeframe})
                return validated
            except Exception as error:
                last_error = error
                failures.append(ProviderFailure(provider_name, attempt, type(error).__name__, str(error)))
                logger.warning("Provider %s failed (attempt %d/%d): %s", provider_name, attempt, self.retries + 1, error)
                if attempt < self.retries + 1 and self.retry_delay > 0:
                    await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))
        assert last_error is not None
        raise last_error

    @staticmethod
    def _canonical_symbol_for_validation(symbol: str) -> str:
        return "".join(character for character in symbol.strip().upper() if character not in "_/ -")

    @staticmethod
    def _validate_result(provider_name: str, candles: object, symbol: str) -> list[Candle]:
        if not isinstance(candles, (list, tuple)):
            raise ApplicationError("Provider returned an invalid candle collection.", {"provider": provider_name, "symbol": symbol, "expected": "list[Candle]", "actual": type(candles).__name__})
        expected = ProviderManager._canonical_symbol_for_validation(symbol)
        previous_timestamp = None
        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                raise ApplicationError("Provider returned invalid candle data.", {"provider": provider_name, "symbol": symbol, "index": index, "expected": "Candle", "actual": type(candle).__name__})
            actual = ProviderManager._canonical_symbol_for_validation(candle.symbol)
            if actual != expected:
                raise ApplicationError("Provider returned candles for an unexpected symbol.", {"provider": provider_name, "symbol": symbol, "index": index, "actual_symbol": candle.symbol})
            if previous_timestamp is not None and candle.timestamp <= previous_timestamp:
                raise ApplicationError("Provider returned non-chronological or duplicate candles.", {"provider": provider_name, "symbol": symbol, "index": index})
            previous_timestamp = candle.timestamp
        return list(candles)

    @staticmethod
    def _normalize_candles(candles: list[Candle], *, limit: int) -> list[Candle]:
        return candles[-limit:] if len(candles) > limit else candles

    async def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        if not symbol.strip():
            raise ValueError("symbol cannot be empty.")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        if not timeframe.strip():
            raise ValueError("timeframe cannot be empty.")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")

        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip().upper()
        failures: list[ProviderFailure] = []
        self._last_failures.set(())
        attempted = skipped = 0

        for provider_name in self._providers:
            if self._is_in_cooldown(provider_name):
                skipped += 1
                continue
            try:
                provider = self._get_provider(provider_name)
                supports_symbol = getattr(provider, "supports_symbol", None)
                if callable(supports_symbol) and not supports_symbol(normalized_symbol):
                    skipped += 1
                    failures.append(ProviderFailure(provider_name, 0, "UnsupportedSymbol", f"Provider {provider_name} does not support symbol {normalized_symbol}"))
                    logger.info("Skipping provider %s: symbol %s is outside its declared capability.", provider_name, normalized_symbol)
                    continue
                attempted += 1
                candles = await self._request_with_retry(provider_name, provider, symbol=normalized_symbol, timeframe=normalized_timeframe, limit=limit, failures=failures)
                candles = self._normalize_candles(candles, limit=limit)
                if not candles:
                    raise ApplicationError("Provider returned no usable candles.", {"provider": provider_name, "symbol": normalized_symbol, "timeframe": normalized_timeframe})
                self._cooldowns.pop(provider_name, None)
                self._last_failures.set(tuple(failures))
                return candles
            except Exception as error:
                self._put_in_cooldown(provider_name)
                logger.warning("Provider %s exhausted. Trying next provider: %s", provider_name, error)

        self._last_failures.set(tuple(failures))
        raise ApplicationError("All market data providers failed.", {"symbol": normalized_symbol, "timeframe": normalized_timeframe, "limit": limit, "providers": list(self._providers), "attempted_providers": attempted, "skipped_providers": skipped, "failures": [{"provider": f.provider, "attempt": f.attempt, "error_type": f.error_type, "message": f.message} for f in failures]})

    def status(self) -> dict[str, object]:
        now = time.monotonic()
        return {"providers": list(self._providers), "cached_instances": list(self._provider_instances.keys()), "injected_instances": list(self._provider_objects.keys()), "cooldowns": {name: max(0.0, expiry - now) for name, expiry in self._cooldowns.items()}, "retries": self.retries, "retry_delay": self.retry_delay, "cooldown_seconds": self.cooldown_seconds}


__all__ = ["ProviderFailure", "ProviderManager"]
