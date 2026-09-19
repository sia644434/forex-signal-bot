from datetime import datetime, timezone, timedelta

import pytest

from config.symbols import CRYPTO_SYMBOLS
from data.models import Candle
from data.providers.binance_provider import BinanceProvider
from data.provider_manager import ProviderManager


BINANCE_TIMEFRAMES = {
    "M1": ("1m", timedelta(minutes=1)),
    "M5": ("5m", timedelta(minutes=5)),
    "M15": ("15m", timedelta(minutes=15)),
    "M30": ("30m", timedelta(minutes=30)),
    "H1": ("1h", timedelta(hours=1)),
    "H4": ("4h", timedelta(hours=4)),
    "D1": ("1d", timedelta(days=1)),
    "W1": ("1w", timedelta(weeks=1)),
}


def _completed_interval_anchor(interval: timedelta) -> datetime:
    now = datetime.now(timezone.utc)
    if interval == timedelta(weeks=1):
        current_week = now - timedelta(days=now.weekday())
        return current_week.replace(hour=0, minute=0, second=0, microsecond=0) - interval
    if interval >= timedelta(days=1):
        current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return current_day - interval
    total_seconds = int(interval.total_seconds())
    epoch_seconds = int(now.timestamp())
    aligned_seconds = epoch_seconds - (epoch_seconds % total_seconds)
    return datetime.fromtimestamp(aligned_seconds, tz=timezone.utc) - interval


def _recent_rows(timeframe="M15", count=2, *, close_last=True):
    _, interval = BINANCE_TIMEFRAMES[timeframe]
    anchor = _completed_interval_anchor(interval)
    rows = []
    for index in range(count):
        opened = anchor - interval * (count - 1 - index)
        close_time = opened + interval - timedelta(milliseconds=1)
        rows.append([
            int(opened.timestamp() * 1000),
            "50000", "50100", "49900", "50050", "12.5",
            int(close_time.timestamp() * 1000), "625625", 100, "6", "300000", "0",
        ])
    if not close_last:
        rows[-1][6] = int((datetime.now(timezone.utc) + timedelta(minutes=1)).timestamp() * 1000)
    return rows


class FakeBinance:
    def __init__(self, rows=None):
        self.calls = []
        self.rows = _recent_rows() if rows is None else rows

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


@pytest.mark.parametrize("symbol", CRYPTO_SYMBOLS)
def test_binance_provider_supports_every_configured_crypto_symbol(symbol):
    assert BinanceProvider(client=FakeBinance()).supports_symbol(symbol) is True


@pytest.mark.parametrize(
    ("timeframe", "expected_interval"),
    [(key, value[0]) for key, value in BINANCE_TIMEFRAMES.items()],
)
@pytest.mark.asyncio
async def test_binance_provider_maps_every_supported_timeframe(timeframe, expected_interval):
    client = FakeBinance(rows=_recent_rows(timeframe))
    result = await BinanceProvider(client=client).get_candles("ETHUSDT", timeframe, 10)

    assert result
    assert client.calls == [("ETHUSDT", expected_interval, 10)]


@pytest.mark.asyncio
async def test_binance_provider_filters_an_open_candle():
    rows = _recent_rows("M15", count=3, close_last=False)
    client = FakeBinance(rows=rows)

    result = await BinanceProvider(client=client).get_candles("BTCUSDT", "M15", 10)

    assert len(result) == 1
    assert result[0].timestamp == datetime.fromtimestamp(rows[0][0] / 1000, tz=timezone.utc)


def test_binance_provider_is_crypto_only():
    provider = BinanceProvider(client=FakeBinance())
    assert provider.supports_symbol("BTCUSDT") is True
    assert provider.supports_symbol("ETHUSDT") is True
    assert provider.supports_symbol("EURUSD") is False
    assert provider.supports_symbol("AAPL") is False


@pytest.mark.asyncio
async def test_binance_provider_rejects_non_contiguous_candles():
    rows = _recent_rows()
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
async def test_provider_manager_fails_over_from_binance_to_next_provider():
    class FailingBinance:
        name = "binance"

        def __init__(self):
            self.calls = 0

        def supports_symbol(self, symbol):
            return True

        async def get_candles(self, symbol, timeframe, limit):
            self.calls += 1
            raise RuntimeError("simulated Binance outage")

    class FallbackProvider:
        name = "twelvedata"

        def __init__(self):
            self.calls = 0

        def supports_symbol(self, symbol):
            return True

        async def get_candles(self, symbol, timeframe, limit):
            self.calls += 1
            return [
                Candle(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    open=2500,
                    high=2510,
                    low=2490,
                    close=2505,
                    volume=10,
                )
            ]

    binance = FailingBinance()
    fallback = FallbackProvider()
    manager = ProviderManager(
        providers=[binance, fallback],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("ETHUSDT", "M15", 10)

    assert result[0].symbol == "ETHUSDT"
    assert binance.calls == 1
    assert fallback.calls == 1
    assert manager.last_failures[0].provider == "binance"
    assert manager.last_failures[0].attempt == 1


@pytest.mark.asyncio
async def test_provider_manager_skips_binance_for_forex_without_network_call():
    class ForexFallback:
        name = "twelvedata"

        async def get_candles(self, symbol, timeframe, limit):
            return [
                Candle(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    open=1.1,
                    high=1.11,
                    low=1.09,
                    close=1.105,
                    volume=10,
                )
            ]

    client = FakeBinance()
    binance = BinanceProvider(client=client)
    manager = ProviderManager(
        providers=[binance, ForexFallback()],
        retries=0,
        cooldown_seconds=0,
    )

    result = await manager.get_candles("EURUSD", "M15", 10)

    assert result[0].symbol == "EURUSD"
    assert client.calls == []
    assert any(
        failure.provider == "binance"
        and failure.error_type == "UnsupportedSymbol"
        and failure.attempt == 0
        for failure in manager.last_failures
    )


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
