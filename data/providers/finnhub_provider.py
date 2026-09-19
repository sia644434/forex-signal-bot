from __future__ import annotations
from datetime import datetime, timezone
from typing import Final
from core.errors import ApplicationError
from core.logger import setup_logger
from config.symbols import get_market_type
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.finnhub import FinnhubClient

logger = setup_logger()

class FinnhubProvider(MarketDataProvider):
    """Finnhub implementation for supported real-time candle asset classes."""
    name = "finnhub"
    _TIMEFRAME_ALIASES: Final[dict[str, str]] = {"M1":"1","M5":"5","M15":"15","M30":"30","H1":"60","D1":"D","W1":"W","D":"D","W":"W","M":"M","1M":"1","5M":"5","15M":"15","30M":"30","1H":"60","1D":"D","1W":"W"}
    _TIMEFRAME_MINUTES: Final[dict[str, int]] = {"1":1,"5":5,"15":15,"30":30,"60":60,"D":1440,"W":10080,"M":43200}
    _MARKET_ENDPOINTS: Final[dict[str, str]] = {"forex":"forex","stock":"stock","crypto":"crypto","index":"index"}

    def __init__(self, client: FinnhubClient | None = None) -> None:
        self.client = client if client is not None else FinnhubClient()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    def supports_symbol(self, symbol: str) -> bool:
        try:
            return get_market_type(symbol) in self._MARKET_ENDPOINTS
        except (TypeError, ValueError):
            return False

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise ValueError("timeframe cannot be empty")
        normalized = timeframe.strip().upper().replace(" ", "")
        aliases = {"1MIN":"1","5MIN":"5","15MIN":"15","30MIN":"30","1HR":"60","1DAY":"D","1WEEK":"W","1MONTH":"M"}
        resolution = aliases.get(normalized, cls._TIMEFRAME_ALIASES.get(normalized, normalized))
        if resolution not in cls._TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported Finnhub timeframe: {timeframe!r}")
        return resolution

    @classmethod
    def _calculate_time_range(cls, timeframe: str, limit: int) -> tuple[int, int]:
        resolution = cls._normalize_timeframe(timeframe)
        end = int(datetime.now(timezone.utc).timestamp())
        return end - cls._TIMEFRAME_MINUTES[resolution] * 60 * limit, end

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        timestamp = int(value)
        if timestamp <= 0:
            raise ValueError("Finnhub timestamp must be positive")
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    @staticmethod
    def _parse_price(value: object) -> float:
        price = float(value)
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        return price

    @staticmethod
    def _parse_volume(value: object) -> float:
        volume = 0.0 if value is None else float(value)
        if volume < 0:
            raise ValueError("Volume cannot be negative")
        return volume

    @staticmethod
    def _extract_arrays(response: dict, *, symbol: str, timeframe: str, limit: int) -> tuple[list, list, list, list, list, list]:
        arrays = tuple(response.get(key, []) for key in ("t","o","h","l","c","v"))
        if not all(isinstance(value, list) for value in arrays) or len({len(value) for value in arrays}) != 1:
            raise ApplicationError("Invalid Finnhub candle payload.", {"provider":"finnhub","symbol":symbol,"timeframe":timeframe,"limit":limit})
        return arrays

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol, timeframe, limit)
        canonical_symbol = self.normalize_symbol(symbol)
        market = get_market_type(canonical_symbol)
        resolution = self._normalize_timeframe(timeframe)
        start, end = self._calculate_time_range(resolution, limit)
        endpoint = self._MARKET_ENDPOINTS.get(market)
        if endpoint is None:
            raise ApplicationError("Finnhub does not support this market.", {"provider":self.name,"symbol":canonical_symbol,"market":market})
        try:
            method_name = f"get_{endpoint}_candles"
            # Preserve explicit instance-level test/mocking overrides while using
            # market-specific methods on the real FinnhubClient implementation.
            instance_get_candles = getattr(self.client, "__dict__", {}).get("get_candles")
            if instance_get_candles is not None:
                method = instance_get_candles
            else:
                method = getattr(self.client, method_name, None) if method_name in getattr(type(self.client), "__dict__", {}) else None
                if method is None:
                    method = getattr(self.client, "get_candles")
            response = await method(canonical_symbol, resolution, start, end)
        except Exception as error:
            raise ApplicationError("Failed to fetch Finnhub candles.", {"provider":self.name,"symbol":canonical_symbol,"market":market,"timeframe":resolution,"limit":limit}) from error
        if not isinstance(response, dict):
            raise ApplicationError("Invalid Finnhub response.", {"provider":self.name,"symbol":canonical_symbol,"timeframe":resolution,"limit":limit})
        if response.get("s") != "ok":
            return []
        timestamps, opens, highs, lows, closes, volumes = self._extract_arrays(response, symbol=canonical_symbol, timeframe=resolution, limit=limit)
        candles: list[Candle] = []
        for values in zip(timestamps, opens, highs, lows, closes, volumes):
            try:
                candles.append(Candle(symbol=canonical_symbol, timestamp=self._parse_timestamp(values[0]), open=self._parse_price(values[1]), high=self._parse_price(values[2]), low=self._parse_price(values[3]), close=self._parse_price(values[4]), volume=self._parse_volume(values[5])))
            except (TypeError, ValueError, OverflowError):
                continue
        candles = self.normalize_candles(candles, expected_symbol=canonical_symbol, deduplicate=True)
        return self.apply_limit(candles, limit)

__all__ = ["FinnhubProvider"]
