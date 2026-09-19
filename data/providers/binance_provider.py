from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from config.symbols import get_market_type
from core.errors import ApplicationError
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.binance import BinanceClient


class BinanceProvider(MarketDataProvider):
    """Binance Spot OHLCV provider for the configured crypto universe."""

    name = "binance"

    _INTERVALS: Final[dict[str, str]] = {
        "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
        "H1": "1h", "H4": "4h", "D1": "1d", "W1": "1w",
    }

    def __init__(self, client: BinanceClient | None = None) -> None:
        self.client = client if client is not None else BinanceClient()

    def is_configured(self) -> bool:
        return True

    def supports_symbol(self, symbol: str) -> bool:
        try:
            return get_market_type(symbol) == "crypto"
        except (TypeError, ValueError):
            return False

    @classmethod
    def _interval(cls, timeframe: str) -> str:
        normalized = timeframe.strip().upper().replace(" ", "")
        aliases = {
            "1MIN": "M1", "5MIN": "M5", "15MIN": "M15", "30MIN": "M30",
            "1HR": "H1", "4HR": "H4", "1DAY": "D1", "D": "D1",
            "1WEEK": "W1", "W": "W1",
        }
        key = aliases.get(normalized, normalized)
        interval = cls._INTERVALS.get(key)
        if interval is None:
            raise ValueError(f"Unsupported Binance timeframe: {timeframe!r}")
        return interval

    @staticmethod
    def _timestamp(value: object) -> datetime:
        timestamp = int(value)
        if timestamp <= 0:
            raise ValueError("Binance timestamp must be positive.")
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)

    @staticmethod
    def _price(value: object) -> float:
        price = float(value)
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        return price

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol, timeframe, limit)
        canonical = self.normalize_symbol(symbol)
        if not self.supports_symbol(canonical):
            raise ValueError(f"Unsupported Binance symbol: {symbol!r}")

        interval = self._interval(timeframe)
        try:
            rows = await self.client.get_klines(canonical, interval, min(limit, 1000))
        except Exception as error:
            raise ApplicationError(
                "Failed to fetch Binance Spot candles.",
                {"provider": self.name, "symbol": canonical, "timeframe": interval, "limit": limit},
            ) from error

        now = datetime.now(timezone.utc)
        candles: list[Candle] = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                continue
            try:
                timestamp = self._timestamp(row[0])
                close_time = self._timestamp(row[6])
                if close_time > now:
                    continue
                candles.append(
                    Candle(
                        symbol=canonical,
                        timestamp=timestamp,
                        open=self._price(row[1]),
                        high=self._price(row[2]),
                        low=self._price(row[3]),
                        close=self._price(row[4]),
                        volume=max(0.0, float(row[5])),
                    )
                )
            except (TypeError, ValueError, OverflowError):
                continue

        candles = self.normalize_candles(candles, expected_symbol=canonical, deduplicate=True)
        candles = self.apply_limit(candles, limit)
        if not candles:
            raise ApplicationError(
                "Binance returned no usable completed OHLC candles.",
                {"provider": self.name, "symbol": canonical, "timeframe": interval},
            )
        candles = self.validate_candles(candles, expected_symbol=canonical, require_sorted=True, reject_duplicates=True)
        try:
            self._validate_market_sequence(candles, timeframe, now)
        except ValueError as error:
            raise ApplicationError(
                "Binance returned invalid or stale candle sequence.",
                {"provider": self.name, "symbol": canonical, "timeframe": interval, "reason": str(error)},
            ) from error
        return candles


__all__ = ["BinanceProvider"]
