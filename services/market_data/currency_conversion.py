from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from config.symbols import FOREX_SYMBOLS
from data.models import Candle
from services.market_data.service import MarketDataService


@dataclass(frozen=True, slots=True)
class CurrencyConversion:
    """A market-backed or explicitly supported quote-to-account conversion snapshot."""

    source_currency: str
    target_currency: str
    rate: float
    pair_symbol: str
    inverted: bool
    as_of: datetime


class CurrencyConversionService:
    """Resolve quote-to-account conversion through the canonical market-data path.

    Forex currency pairs remain market-backed. USDT/USDC are treated as USD
    equivalents only for the repository's current spot-crypto universe, where
    they are quote currencies; this explicit policy avoids pretending that a
    crypto symbol itself is an FX conversion pair. Other unsupported currency
    conversions fail closed.
    """

    _CONVERSION_TIMEFRAME = "1m"
    _USD_EQUIVALENT_CURRENCIES = frozenset({"USDT", "USDC"})

    def __init__(self, market_data_service: MarketDataService) -> None:
        if not isinstance(market_data_service, MarketDataService):
            raise TypeError("market_data_service must be a MarketDataService.")
        self.market_data_service = market_data_service

    @staticmethod
    def _normalize_currency(currency: str, name: str) -> str:
        if not isinstance(currency, str):
            raise TypeError(f"{name} must be a string.")
        normalized = currency.strip().upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError(f"{name} must be a 3-letter currency code.")
        return normalized

    @staticmethod
    def _pair_candidates(source: str, target: str) -> tuple[tuple[str, bool], ...]:
        direct = f"{source}{target}"
        inverse = f"{target}{source}"
        candidates: list[tuple[str, bool]] = []
        if direct in FOREX_SYMBOLS:
            candidates.append((direct, False))
        if inverse in FOREX_SYMBOLS:
            candidates.append((inverse, True))
        return tuple(candidates)

    async def _direct_market_conversion(self, source: str, target: str) -> CurrencyConversion:
        last_error: Exception | None = None
        for pair_symbol, inverted in self._pair_candidates(source, target):
            try:
                candles = await self.market_data_service.get_candles_list(
                    pair_symbol,
                    self._CONVERSION_TIMEFRAME,
                    1,
                )
                if not candles:
                    raise ValueError(f"No conversion market data for {pair_symbol}.")
                candle: Candle = candles[-1]
                price = float(candle.close)
                if not math.isfinite(price) or price <= 0:
                    raise ValueError(f"Invalid conversion price for {pair_symbol}.")
                rate = 1.0 / price if inverted else price
                if not math.isfinite(rate) or rate <= 0:
                    raise ValueError(f"Invalid conversion rate for {pair_symbol}.")
                return CurrencyConversion(
                    source_currency=source,
                    target_currency=target,
                    rate=rate,
                    pair_symbol=pair_symbol,
                    inverted=inverted,
                    as_of=candle.timestamp,
                )
            except Exception as error:
                last_error = error
        raise ValueError(f"Unable to resolve fresh currency conversion {source}->{target}.") from last_error

    async def get_conversion(
        self,
        *,
        source_currency: str,
        target_currency: str,
    ) -> CurrencyConversion:
        source = self._normalize_currency(source_currency, "source_currency")
        target = self._normalize_currency(target_currency, "target_currency")

        if source == target:
            return CurrencyConversion(source, target, 1.0, "", False, datetime.now().astimezone())

        # The current crypto universe quotes in USDT. Keep this assumption
        # explicit and isolated so it can later be replaced by a live stablecoin
        # market when provider support is available.
        if source in self._USD_EQUIVALENT_CURRENCIES and target == "USD":
            return CurrencyConversion(source, target, 1.0, f"{source}USD", False, datetime.now().astimezone())
        if source == "USD" and target in self._USD_EQUIVALENT_CURRENCIES:
            return CurrencyConversion(source, target, 1.0, f"USD{target}", False, datetime.now().astimezone())

        # Bridge stablecoin-quoted instruments through USD when the account is
        # another supported currency. The FX leg remains market-backed.
        if source in self._USD_EQUIVALENT_CURRENCIES:
            usd_leg = await self.get_conversion(source_currency="USD", target_currency=target)
            return CurrencyConversion(source, target, usd_leg.rate, usd_leg.pair_symbol, usd_leg.inverted, usd_leg.as_of)
        if target in self._USD_EQUIVALENT_CURRENCIES:
            usd_leg = await self.get_conversion(source_currency=source, target_currency="USD")
            return CurrencyConversion(source, target, usd_leg.rate, usd_leg.pair_symbol, usd_leg.inverted, usd_leg.as_of)

        try:
            return await self._direct_market_conversion(source, target)
        except ValueError as error:
            raise ValueError(
                f"No supported market-backed currency conversion for {source}->{target}."
            ) from error


__all__ = ["CurrencyConversion", "CurrencyConversionService"]
