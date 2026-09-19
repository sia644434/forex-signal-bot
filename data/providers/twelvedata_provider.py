from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from core.errors import ApplicationError
from config.symbols import get_market_type
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.twelvedata import TwelveDataClient


class TwelveDataProvider(MarketDataProvider):
    """Twelve Data OHLC provider for the configured multi-asset universe."""

    name = "twelvedata"
    _INTERVALS: Final[dict[str, str]] = {
        "M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
        "H1": "1h", "H4": "4h", "D1": "1day", "W1": "1week",
    }
    _COMMODITY_SYMBOLS: Final[dict[str, str]] = {
        "XAUUSD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "WTI": "WTI/USD",
        "BRENT": "BRENT/USD",
    }

    def __init__(self, client: TwelveDataClient | None = None) -> None:
        self.client = client if client is not None else TwelveDataClient()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    def supports_symbol(self, symbol: str) -> bool:
        try:
            return get_market_type(symbol) in {"forex", "crypto", "stock", "index", "commodity"}
        except (TypeError, ValueError):
            return False

    @classmethod
    def _interval(cls, timeframe: str) -> str:
        normalized = timeframe.strip().upper().replace(" ", "")
        aliases = {"1M":"M1","5M":"M5","15M":"M15","30M":"M30","1H":"H1","4H":"H4","1D":"D1","D":"D1","1W":"W1","W":"W1"}
        key = aliases.get(normalized, normalized)
        if key not in cls._INTERVALS:
            raise ValueError(f"Unsupported Twelve Data timeframe: {timeframe!r}")
        return cls._INTERVALS[key]

    @classmethod
    def _provider_symbol(cls, symbol: str) -> str:
        canonical = symbol.strip().upper().replace("/", "").replace("_", "").replace("-", "")
        market = get_market_type(canonical)
        if market == "commodity":
            return cls._COMMODITY_SYMBOLS[canonical]
        if market == "forex" and len(canonical) == 6:
            return f"{canonical[:3]}/{canonical[3:]}"
        if market == "crypto":
            if canonical.endswith("USDT"):
                return f"{canonical[:-4]}/USDT"
            if canonical.endswith("USDC"):
                return f"{canonical[:-4]}/USDC"
        return canonical

    @staticmethod
    def _timestamp(value: object) -> datetime:
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)

    @staticmethod
    def _price(value: object) -> float:
        price = float(value)
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        return price

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol, timeframe, limit)
        canonical = self.normalize_symbol(symbol)
        provider_symbol = self._provider_symbol(canonical)
        interval = self._interval(timeframe)
        try:
            crypto_exchange = "Binance" if get_market_type(canonical) == "crypto" else None
            response = await self.client.get_time_series(provider_symbol, interval, limit, exchange=crypto_exchange)
        except Exception as error:
            raise ApplicationError("Failed to fetch Twelve Data candles.", {"provider": self.name, "symbol": canonical, "timeframe": interval}) from error
        values = response.get("values")
        if not isinstance(values, list):
            raise ApplicationError("Twelve Data response has no OHLC values.", {"provider": self.name, "symbol": canonical})
        candles: list[Candle] = []
        for item in reversed(values):
            if not isinstance(item, dict):
                continue
            try:
                candles.append(Candle(
                    symbol=canonical,
                    timestamp=self._timestamp(item["datetime"]),
                    open=self._price(item["open"]),
                    high=self._price(item["high"]),
                    low=self._price(item["low"]),
                    close=self._price(item["close"]),
                    volume=max(0.0, float(item.get("volume", 0) or 0)),
                ))
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
        candles = self.normalize_candles(candles, expected_symbol=canonical, deduplicate=True)
        if not candles:
            raise ApplicationError("Twelve Data returned no usable OHLC candles.", {"provider": self.name, "symbol": canonical})
        return self.apply_limit(candles, limit)
