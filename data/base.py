
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Final

from data.models import Candle


class MarketDataProvider(ABC):
    """Common contract for all market-data providers."""

    name: str
    DEFAULT_LIMIT: Final[int] = 100
    MAX_LIMIT: Final[int] = 5000

    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, limit: int = DEFAULT_LIMIT) -> list[Candle]:
        """Fetch standardized market candles."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        """Return whether local credentials/configuration are available."""
        return True

    def supports_symbol(self, symbol: str) -> bool:
        """Return whether this provider explicitly supports the requested symbol.

        The default is permissive for custom providers; concrete providers with
        narrower market coverage must override this method so ProviderManager
        can avoid futile requests and report capability gaps explicitly.
        """
        if not isinstance(symbol, str) or not symbol.strip():
            return False
        return True

    @classmethod
    def validate_request(cls, symbol: str, timeframe: str, limit: int = DEFAULT_LIMIT) -> None:
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
        if limit > cls.MAX_LIMIT:
            raise ValueError(f"limit cannot exceed {cls.MAX_LIMIT}.")

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol cannot be empty.")
        return normalized

    @classmethod
    def validate_candles(cls, candles: Iterable[Candle], *, expected_symbol: str | None = None, require_sorted: bool = True, reject_duplicates: bool = True) -> list[Candle]:
        if candles is None:
            raise ValueError("candles cannot be None.")
        result = list(candles)
        if not result:
            return []
        for index, candle in enumerate(result):
            if not isinstance(candle, Candle):
                raise TypeError(f"All candle values must be Candle instances. Invalid item at index {index}.")
            if candle.timestamp.tzinfo is None:
                raise ValueError("Candle timestamp must be timezone-aware.")
            if not candle.symbol.strip():
                raise ValueError("Candle symbol cannot be empty.")
        if expected_symbol is not None:
            normalized_symbol = cls.normalize_symbol(expected_symbol)
            for candle in result:
                if cls.normalize_symbol(candle.symbol) != normalized_symbol:
                    raise ValueError(f"Candle symbol does not match requested symbol {expected_symbol!r}.")
        if reject_duplicates:
            seen: set[tuple[str, datetime]] = set()
            for candle in result:
                key = (cls.normalize_symbol(candle.symbol), candle.timestamp)
                if key in seen:
                    raise ValueError(f"Duplicate candle detected for {candle.symbol} at {candle.timestamp.isoformat()}.")
                seen.add(key)
        if require_sorted:
            for previous, current in zip(result, result[1:]):
                if current.timestamp <= previous.timestamp:
                    raise ValueError("Candles must be strictly ordered chronologically.")
        return result

    @classmethod
    def normalize_candles(cls, candles: Iterable[Candle], *, expected_symbol: str | None = None, deduplicate: bool = True) -> list[Candle]:
        if candles is None:
            raise ValueError("candles cannot be None.")
        items = list(candles)
        for index, candle in enumerate(items):
            if not isinstance(candle, Candle):
                raise TypeError(f"All candle values must be Candle instances. Invalid item at index {index}.")
        if expected_symbol is not None:
            normalized_symbol = cls.normalize_symbol(expected_symbol)
            for candle in items:
                if cls.normalize_symbol(candle.symbol) != normalized_symbol:
                    raise ValueError(f"Candle symbol does not match requested symbol {expected_symbol!r}.")
        if not deduplicate:
            return sorted(items, key=lambda candle: candle.timestamp)
        unique: dict[tuple[str, datetime], Candle] = {}
        for candle in items:
            unique[(cls.normalize_symbol(candle.symbol), candle.timestamp)] = candle
        return sorted(unique.values(), key=lambda candle: candle.timestamp)

    @classmethod
    def apply_limit(cls, candles: Iterable[Candle], limit: int) -> list[Candle]:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        if limit > cls.MAX_LIMIT:
            raise ValueError(f"limit cannot exceed {cls.MAX_LIMIT}.")
        items = list(candles)
        return items if len(items) <= limit else items[-limit:]

    @staticmethod
    def normalize_timeframe(timeframe: str) -> str:
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        normalized = timeframe.strip().upper()
        if not normalized:
            raise ValueError("timeframe cannot be empty.")
        aliases = {"1M":"M1", "5M":"M5", "15M":"M15", "30M":"M30", "60M":"H1", "1H":"H1", "1HR":"H1", "1D":"D1", "1DAY":"D1", "1W":"W1", "1WEEK":"W1"}
        return aliases.get(normalized, normalized)

    def __repr__(self) -> str:
        provider_name = getattr(self, "name", self.__class__.__name__)
        return f"{self.__class__.__name__}(name={provider_name!r})"


__all__ = ["MarketDataProvider"]
