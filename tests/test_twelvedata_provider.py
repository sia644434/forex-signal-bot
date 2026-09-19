import pytest

from data.models import Candle
from data.providers.twelvedata_provider import TwelveDataProvider


class FakeTwelve:
    def is_configured(self):
        return True

    async def get_time_series(self, symbol, interval, outputsize):
        assert symbol == "XAU/USD"
        assert interval == "1day"
        return {
            "status": "ok",
            "values": [
                {"datetime": "2026-09-18", "open": "3650", "high": "3680", "low": "3630", "close": "3670", "volume": "0"},
                {"datetime": "2026-09-19", "open": "3670", "high": "3690", "low": "3660", "close": "3685", "volume": "0"},
            ],
        }


@pytest.mark.asyncio
async def test_twelvedata_provides_real_ohlc_contract_for_commodities():
    result = await TwelveDataProvider(client=FakeTwelve()).get_candles("XAUUSD", "1d", 10)
    assert len(result) == 2
    assert all(isinstance(item, Candle) for item in result)
    assert result[-1].close == 3685


def test_twelvedata_maps_configured_commodity_symbols():
    provider = TwelveDataProvider(client=FakeTwelve())
    assert provider._provider_symbol("XAGUSD") == "XAG/USD"
    assert provider._provider_symbol("WTI") == "WTI/USD"
    assert provider._provider_symbol("BRENT") == "BRENT/USD"
