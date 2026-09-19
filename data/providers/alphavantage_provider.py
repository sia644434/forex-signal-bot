from __future__ import annotations
from datetime import datetime, timezone
from typing import Final
from core.errors import ApplicationError
from core.logger import setup_logger
from config.symbols import get_market_type
from data.base import MarketDataProvider
from data.models import Candle
from data.providers.clients.alphavantage import AlphaVantageClient

logger = setup_logger()

class AlphaVantageRateLimitError(ApplicationError):
    """Raised when Alpha Vantage rejects a request due to limits."""

class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage multi-asset provider with explicit timeframe capability gates."""
    name = "alphavantage"
    _FX_INTERVALS: Final[dict[str,str]] = {"M1":"1min","M5":"5min","M15":"15min","M30":"30min","H1":"60min"}
    _STOCK_INTERVALS: Final[dict[str,str]] = {"M1":"1min","M5":"5min","M15":"15min","M30":"30min","H1":"60min","D1":"daily","W1":"weekly","M":"monthly"}
    _INDEX_INTERVALS: Final[dict[str,str]] = {"D1":"daily","W1":"weekly","M":"monthly"}
    _COMMODITY_MAP: Final[dict[str,str]] = {"XAGUSD":"SILVER","XAUUSD":"GOLD","WTI":"WTI","BRENT":"BRENT"}
    _COMMODITY_INTERVALS: Final[dict[str,str]] = {"D1":"daily","W1":"weekly","M":"monthly"}

    def __init__(self, client: AlphaVantageClient | None = None) -> None:
        self.client = client if client is not None else AlphaVantageClient()

    def is_configured(self) -> bool:
        return self.client.is_configured()

    def supports_symbol(self, symbol: str) -> bool:
        try:
            return get_market_type(symbol) in {"forex","stock","index","commodity"}
        except (TypeError, ValueError):
            return False

    @classmethod
    def _canonical_timeframe(cls, timeframe: str) -> str:
        normalized = timeframe.strip().upper().replace(" ","")
        aliases={"1MIN":"M1","5MIN":"M5","15MIN":"M15","30MIN":"M30","1HR":"H1","1H":"H1","1DAY":"D1","1D":"D1","1WEEK":"W1","1W":"W1","D":"D1","W":"W1"}
        return aliases.get(normalized, normalized)

    @staticmethod
    def _split_fx(symbol: str) -> tuple[str,str]:
        normalized=symbol.strip().upper().replace("/","").replace("_","")
        if len(normalized)!=6 or not normalized.isalpha():
            raise ValueError(f"Unsupported FX symbol: {symbol!r}")
        return normalized[:3], normalized[3:]

    @staticmethod
    def _parse_ts(value: object) -> datetime:
        text=str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M","%Y-%m-%d"):
            try: return datetime.strptime(text,fmt).replace(tzinfo=timezone.utc)
            except ValueError: continue
        raise ValueError(f"Unsupported Alpha Vantage timestamp: {value!r}")

    @staticmethod
    def _price(value: object) -> float:
        price=float(value)
        if price<=0: raise ValueError("Price must be greater than zero")
        return price

    @classmethod
    def _series(cls, response: dict, marker: str) -> dict:
        for key,value in response.items():
            if isinstance(key,str) and marker.lower() in key.lower() and isinstance(value,dict):
                return value
        data=response.get("data")
        if isinstance(data,list):
            return {str(item.get("date") or item.get("timestamp")): item for item in data if isinstance(item,dict)}
        raise ApplicationError("Alpha Vantage time series was not found.", {"marker":marker})

    @classmethod
    def _candles_from_series(cls, series: dict, symbol: str, limit: int) -> list[Candle]:
        candles=[]
        for timestamp, values in series.items():
            if not isinstance(values,dict): continue
            try:
                candles.append(Candle(symbol=symbol,timestamp=cls._parse_ts(timestamp),open=cls._price(values.get("1. open",values.get("open"))),high=cls._price(values.get("2. high",values.get("high"))),low=cls._price(values.get("3. low",values.get("low"))),close=cls._price(values.get("4. close",values.get("close"))),volume=float(values.get("5. volume",values.get("volume",0)) or 0)))
            except (KeyError,TypeError,ValueError,OverflowError):
                continue
        return cls.normalize_candles(candles, expected_symbol=symbol, deduplicate=True)[-limit:]

    async def get_candles(self, symbol: str, timeframe: str, limit: int = MarketDataProvider.DEFAULT_LIMIT) -> list[Candle]:
        self.validate_request(symbol,timeframe,limit)
        canonical=self.normalize_symbol(symbol)
        market=get_market_type(canonical)
        tf=self._canonical_timeframe(timeframe)
        try:
            if market=="forex":
                interval=self._FX_INTERVALS.get(tf)
                if not interval: raise ValueError(f"Unsupported Alpha Vantage FX timeframe: {timeframe!r}")
                base,quote=self._split_fx(canonical)
                response=await self.client.get_forex_intraday(base,quote,interval)
                series=self._series(response,"time series fx")
            elif market=="stock":
                interval=self._STOCK_INTERVALS.get(tf)
                if not interval: raise ValueError(f"Unsupported Alpha Vantage stock timeframe: {timeframe!r}")
                response=await self.client.get_stock_time_series(canonical,interval)
                series=self._series(response,"time series")
            elif market=="index":
                interval=self._INDEX_INTERVALS.get(tf)
                if not interval: raise ValueError(f"Unsupported Alpha Vantage index timeframe: {timeframe!r}")
                response=await self.client.get_index_time_series(canonical,interval)
                series=self._series(response,"data")
            elif market=="commodity":
                function=self._COMMODITY_MAP.get(canonical)
                if not function or tf not in self._COMMODITY_INTERVALS:
                    raise ValueError(f"Unsupported Alpha Vantage commodity timeframe: {timeframe!r}")
                response=await self.client.get_commodity_time_series(function,self._COMMODITY_INTERVALS[tf])
                series=self._series(response,"data")
            else:
                return []
        except AlphaVantageRateLimitError:
            raise
        except ApplicationError:
            raise
        except Exception as error:
            raise ApplicationError("Failed to fetch Alpha Vantage market candles.",{"provider":self.name,"symbol":canonical,"market":market,"timeframe":tf,"limit":limit}) from error
        candles=self._candles_from_series(series,canonical,limit)
        if not candles:
            raise ApplicationError("Alpha Vantage returned no usable OHLC candles.",{"provider":self.name,"symbol":canonical,"market":market,"timeframe":tf})
        return candles

__all__=["AlphaVantageProvider","AlphaVantageRateLimitError"]
