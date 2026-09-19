import logging
from typing import Any
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Async client for Alpha Vantage multi-asset market data."""
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self) -> None:
        self.api_key = settings.ALPHAVANTAGE_API_KEY

    def _check_api_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is not configured.")

    def is_configured(self) -> bool:
        return bool(self.api_key and str(self.api_key).strip())

    async def _get(self, params: dict[str, str]) -> dict[str, Any]:
        self._check_api_key()
        params = {**params, "apikey": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        if "Error Message" in data:
            raise RuntimeError(str(data["Error Message"]))
        if "Note" in data or "Information" in data:
            logger.warning("Alpha Vantage availability message: %s", data.get("Note") or data.get("Information"))
        return data

    async def get_forex_quote(self, from_currency: str, to_currency: str) -> dict[str, Any]:
        return await self._get({"function":"CURRENCY_EXCHANGE_RATE","from_currency":from_currency,"to_currency":to_currency})

    async def get_forex_intraday(self, from_currency: str, to_currency: str, interval: str = "15min") -> dict[str, Any]:
        return await self._get({"function":"FX_INTRADAY","from_symbol":from_currency,"to_symbol":to_currency,"interval":interval,"outputsize":"full"})

    async def get_intraday(self, symbol: str, interval: str = "15min") -> dict[str, Any]:
        return await self._get({"function":"TIME_SERIES_INTRADAY","symbol":symbol,"interval":interval})

    async def get_stock_time_series(self, symbol: str, interval: str) -> dict[str, Any]:
        if interval == "daily":
            return await self._get({"function":"TIME_SERIES_DAILY","symbol":symbol,"outputsize":"full"})
        if interval == "weekly":
            return await self._get({"function":"TIME_SERIES_WEEKLY","symbol":symbol})
        if interval == "monthly":
            return await self._get({"function":"TIME_SERIES_MONTHLY","symbol":symbol})
        return await self._get({"function":"TIME_SERIES_INTRADAY","symbol":symbol,"interval":interval,"outputsize":"full"})

    async def get_index_time_series(self, symbol: str, interval: str) -> dict[str, Any]:
        return await self._get({"function":"INDEX_DATA","symbol":symbol,"interval":interval})

    async def get_commodity_time_series(self, function: str, interval: str) -> dict[str, Any]:
        params={"function":function}
        if interval:
            params["interval"]=interval
        return await self._get(params)
