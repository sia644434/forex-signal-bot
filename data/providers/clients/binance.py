from __future__ import annotations

from typing import Any

import httpx


class BinanceClient:
    """Async public Binance Spot market-data client."""

    BASE_URL = "https://data-api.binance.vision/api/v3/klines"

    async def get_klines(self, symbol: str, interval: str, limit: int) -> list[list[Any]]:
        if not symbol or not symbol.strip():
            raise ValueError("Binance symbol cannot be empty.")
        if limit < 1 or limit > 1000:
            raise ValueError("Binance Spot kline limit must be between 1 and 1000.")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                self.BASE_URL,
                params={"symbol": symbol.strip().upper(), "interval": interval, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            raise RuntimeError("Invalid Binance kline response.")
        return data
