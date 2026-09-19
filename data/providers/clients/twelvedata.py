from __future__ import annotations

from typing import Any
import httpx
from config.settings import settings


class TwelveDataClient:
    """Async Twelve Data client for OHLC time-series market data."""

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self) -> None:
        self.api_key = settings.TWELVEDATA_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and str(self.api_key).strip())

    async def get_time_series(self, symbol: str, interval: str, outputsize: int, *, exchange: str | None = None) -> dict[str, Any]:
        if not self.is_configured():
            raise RuntimeError("TWELVEDATA_API_KEY is not configured.")
        async with httpx.AsyncClient(timeout=30.0) as http:
            response = await http.get(
                self.BASE_URL,
                params={"symbol": symbol, "interval": interval, "outputsize": outputsize, "apikey": self.api_key, "timezone": "UTC", **({"exchange": exchange} if exchange else {})},
            )
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Invalid Twelve Data response.")
        if data.get("status") == "error":
            message = str(data.get("message") or "unknown API error").strip()
            code = data.get("code")
            suffix = f" (code={code})" if code is not None else ""
            raise RuntimeError(f"Twelve Data API error for {symbol}: {message}{suffix}")
        return data
