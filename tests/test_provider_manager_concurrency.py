from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.provider_manager import ProviderManager


class ConcurrentProvider:
    name = "first"

    def __init__(self, gate: asyncio.Event) -> None:
        self.gate = gate
        self.calls: list[str] = []

    async def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        self.calls.append(symbol)
        if symbol == "EURUSD":
            await self.gate.wait()
            raise TimeoutError("EURUSD timeout")
        raise ConnectionError("GBPUSD connection failure")


class FallbackProvider:
    name = "second"

    async def get_candles(
        self,
        *,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[Candle]:
        return [
            Candle(
                symbol=symbol,
                timestamp=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                open=1.1,
                high=1.2,
                low=1.0,
                close=1.15,
                volume=100.0,
            )
        ]


@pytest.mark.asyncio
async def test_concurrent_requests_keep_failure_diagnostics_isolated():
    gate = asyncio.Event()
    first = ConcurrentProvider(gate)
    second = FallbackProvider()
    manager = ProviderManager(
        providers=[first, second],
        retries=0,
        retry_delay=0,
        cooldown_seconds=0,
    )

    async def request(symbol: str):
        result = await manager.get_candles(
            symbol,
            "15m",
            limit=1,
        )
        return result, manager.last_failures

    eurusd_task = asyncio.create_task(request("EURUSD"))
    await asyncio.sleep(0)
    gbpusd_task = asyncio.create_task(request("GBPUSD"))
    await asyncio.sleep(0)

    gate.set()

    eurusd_result, eurusd_failures = await eurusd_task
    gbpusd_result, gbpusd_failures = await gbpusd_task

    assert eurusd_result[0].symbol == "EURUSD"
    assert gbpusd_result[0].symbol == "GBPUSD"
    assert [(failure.provider, failure.error_type) for failure in eurusd_failures] == [
        ("first", "TimeoutError"),
    ]
    assert [(failure.provider, failure.error_type) for failure in gbpusd_failures] == [
        ("first", "ConnectionError"),
    ]
