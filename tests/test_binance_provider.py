from datetime import datetime, timezone, timedelta

import pytest

from data.models import Candle
from data.providers.binance_provider import BinanceProvider
from data.provider_manager import ProviderManager


def _recent_m15_rows(count=2):
    now = datetime.now(timezone.utc)
    anchor = now.replace(second=0, microsecond=0) - timedelta(minutes=15)
    anchor = anchor.replace(minute=(anchor.minute // 15) * 15)
    rows = []
    for index in range(count):
        opened = anchor - timedelta(minutes=15 * (count - 1 - index))
        close_time = opened + timedelta(minutes=14, seconds=59, milliseconds=999)
        rows.append([
            int(opened.timestamp() * 1000), "50000", "50100", "49900", "50050", "12.5",
            int(close_time.timestamp() * 1000), "625625", 100, "6", "300000", "0",
        ])
    return rows


class FakeBinance:
    def __init__(self, rows=None):
        self.calls = []
        self.rows = _recent_m15_rows() if rows is None else rows

    async def get_klines(self, symbol, interval, limit):
        self.calls.append((symbol, interval, limit))
        return self.rows


@pytest.mark.asyncio
async def test_binance_provider_fetches_completed_btcusdt_m15_candles():
    client = FakeBinance()
    result = await BinanceProvider(client=client).get_candles("BTCUSDT", "M15", 10)

    assert len(result) == 2
    assert all(isinstance(candle, Candle) for candle in result)
    assert result[0].symbol == "BTCUSDT"
    assert result[0].close == 50050
    assert client.calls == [("BTCUSDT", "15m", 10)]


def test_binance_provider_is_crypto_only():
    provider = BinanceProvider(client=FakeBinance())
    assert provider.supports_symbol("BTCUSDT") is True
    assert provider.supports_symbol("ETHUSDT") is True
    assert provider.supports_symbol("EURUSD") is False
    assert provider.supports_symbol("AAPL") is False


@pytest.mark.asyncio
async def test_binance_provider_rejects_non_contiguous_candles():
    rows = _recent_m15_rows()
    rows[1][0] += 60_000
    rows[1][6] += 60_000
    with pytest.raises(Exception, match="invalid or stale candle sequence"):
        await BinanceProvider(client=FakeBinance(rows)).get_candles("BTCUSDT", "M15", 10)


@pytest.mark.asyncio
async def test_binance_provider_rejects_stale_candles():
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    rows = [[
        int(old.timestamp() * 1000), "50000", "50100", "49900", "50050", "12.5",
        int((old + timedelta(minutes=14, seconds=59)).timestamp() * 1000), "625625", 100, "6", "300000", "0",
    ]]
    with pytest.raises(Exception, match="invalid or stale candle sequence"):
        await BinanceProvider(client=FakeBinance(rows)).get_candles("BTCUSDT", "M15", 10)


@pytest.mark.asyncio
async def test_provider_manager_default_order_puts_binance_before_twelvedata_for_crypto():
    manager = ProviderManager()
    assert manager.providers.index("binance") < manager.providers.index("twelvedata")


@pytest.mark.asyncio
async def test_provider_manager_skips_unsupported_provider_without_network_call():
    class UnsupportedProvider:
        name = "fx_only"

        def __init__(self):
            self.calls = 0

        def supports_symbol(self, symbol):
            return False

        async def get_candles(self, symbol, timeframe, limit):
            self.calls += 1
            raise AssertionError("unsupported provider must be skipped")

    class CryptoProvider:
        name = "crypto"

        def supports_symbol(self, symbol):
            return True

        async def get_candles(self, symbol, timeframe, limit):
            return [
                Candle(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    open=50000,
                    high=50100,
                    low=49900,
                    close=50050,
                    volume=1,
                )
            ]

    unsupported = UnsupportedProvider()
    manager = ProviderManager(
        providers=[unsupported, CryptoProvider()],
        retries=0,
        cooldown_seconds=0,
    )
    result = await manager.get_candles("BTCUSDT", "M15", 10)

    assert len(result) == 1
    assert unsupported.calls == 0
    assert any(
        failure.provider == "fx_only"
        and failure.error_type == "UnsupportedSymbol"
        and failure.attempt == 0
        for failure in manager.last_failures
    )
