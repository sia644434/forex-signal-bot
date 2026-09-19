import logging
from typing import Any, Optional
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

class FinnhubClient:
    """Async client for Finnhub forex, stocks, crypto and index market data."""
    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self) -> None:
        self.api_key = settings.FINNHUB_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("FINNHUB_API_KEY is not configured.")

    def is_configured(self) -> bool:
        return bool(self.api_key and str(self.api_key).strip())

    @staticmethod
    def _forex_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper().replace("/", "_").replace("-", "_")
        if normalized.startswith("OANDA:"):
            return normalized
        if len(normalized) == 6 and normalized.isalpha():
            normalized = f"{normalized[:3]}_{normalized[3:]}"
        return f"OANDA:{normalized}"

    @staticmethod
    def _crypto_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper().replace("/", "")
        if normalized.startswith("BINANCE:"):
            return normalized
        return f"BINANCE:{normalized}"

    @staticmethod
    def _stock_symbol(symbol: str) -> str:
        return symbol.strip().upper()

    @staticmethod
    def _index_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        aliases = {"SPX": "^SPX", "NDX": "^NDX", "DJI": "^DJI", "RUT": "^RUT"}
        return aliases.get(normalized, normalized)

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        self._check_api_key()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.BASE_URL}/quote", params={"symbol": symbol, "token": self.api_key})
            response.raise_for_status()
            return response.json()

    async def _get_candles(self, endpoint: str, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> dict[str, Any]:
        self._check_api_key()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{self.BASE_URL}/{endpoint}", params={"symbol": symbol, "resolution": resolution, "from": from_timestamp, "to": to_timestamp, "token": self.api_key})
            response.raise_for_status()
            data = response.json()
        if data.get("s") != "ok":
            logger.warning("Finnhub returned non-ok %s status for %s: %s", endpoint, symbol, data.get("s"))
        return data

    async def get_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> Optional[dict[str, Any]]:
        """Backward-compatible forex candle endpoint."""
        return await self.get_forex_candles(symbol, resolution, from_timestamp, to_timestamp)

    async def get_forex_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> dict[str, Any]:
        return await self._get_candles("forex/candle", self._forex_symbol(symbol), resolution, from_timestamp, to_timestamp)

    async def get_stock_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> dict[str, Any]:
        return await self._get_candles("stock/candle", self._stock_symbol(symbol), resolution, from_timestamp, to_timestamp)

    async def get_crypto_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> dict[str, Any]:
        return await self._get_candles("crypto/candle", self._crypto_symbol(symbol), resolution, from_timestamp, to_timestamp)

    async def get_index_candles(self, symbol: str, resolution: str, from_timestamp: int, to_timestamp: int) -> dict[str, Any]:
        return await self._get_candles("index/candle", self._index_symbol(symbol), resolution, from_timestamp, to_timestamp)
