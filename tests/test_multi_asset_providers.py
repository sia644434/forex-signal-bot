from datetime import datetime, timezone

import pytest

from data.models import Candle
from data.providers.finnhub_provider import FinnhubProvider
from data.providers.alphavantage_provider import AlphaVantageProvider


def fin_response():
    return {"s":"ok","t":[1700000000],"o":[100.0],"h":[102.0],"l":[99.0],"c":[101.0],"v":[1000.0]}


class FinnhubFake:
    def __init__(self):
        self.calls=[]
    def is_configured(self): return True
    async def get_forex_candles(self,*args): self.calls.append(("forex",args)); return fin_response()
    async def get_stock_candles(self,*args): self.calls.append(("stock",args)); return fin_response()
    async def get_crypto_candles(self,*args): self.calls.append(("crypto",args)); return fin_response()
    async def get_index_candles(self,*args): self.calls.append(("index",args)); return fin_response()


@pytest.mark.asyncio
@pytest.mark.parametrize(("symbol","market"), [("AAPL","stock"),("BTCUSDT","crypto"),("SPX","index"),("EURUSD","forex")])
async def test_finnhub_routes_supported_asset_classes(symbol, market):
    client=FinnhubFake()
    result=await FinnhubProvider(client=client).get_candles(symbol,"M15",10)
    assert len(result)==1
    assert isinstance(result[0], Candle)
    assert client.calls[0][0]==market


@pytest.mark.asyncio
async def test_finnhub_rejects_commodity_capability_without_candle_endpoint():
    client=FinnhubFake()
    provider=FinnhubProvider(client=client)
    assert provider.supports_symbol("XAUUSD") is False


class AlphaFake:
    def is_configured(self): return True
    async def get_forex_intraday(self,*args): return {"Time Series FX (15min)": {"2026-01-01 00:00:00":{"1. open":"10","2. high":"11","3. low":"9","4. close":"10.5"}}}
    async def get_stock_time_series(self,*args): return {"Time Series (Daily)": {"2026-01-01":{"1. open":"10","2. high":"11","3. low":"9","4. close":"10.5","5. volume":"100"}}}
    async def get_index_time_series(self,*args): return {"data":[{"date":"2026-01-01","open":"10","high":"11","low":"9","close":"10.5"}]}
    async def get_commodity_time_series(self,*args): return {"data":[{"date":"2026-01-01","value":"10.5"}]}


@pytest.mark.asyncio
async def test_alphavantage_stock_daily_is_supported():
    result=await AlphaVantageProvider(client=AlphaFake()).get_candles("AAPL","1d",10)
    assert len(result)==1
    assert result[0].close==10.5


@pytest.mark.asyncio
async def test_alphavantage_index_daily_is_supported():
    result=await AlphaVantageProvider(client=AlphaFake()).get_candles("SPX","1d",10)
    assert len(result)==1
    assert result[0].high==11


@pytest.mark.asyncio
async def test_alphavantage_commodity_close_only_data_is_not_promoted_to_fake_ohlc():
    with pytest.raises(Exception, match="no usable OHLC"):
        await AlphaVantageProvider(client=AlphaFake()).get_candles("WTI","1d",10)


def test_finnhub_normalizes_spx_to_supported_index_symbol():
    from data.providers.clients.finnhub import FinnhubClient
    assert FinnhubClient._index_symbol("SPX") == "^GSPC"
