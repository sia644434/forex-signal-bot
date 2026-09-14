from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from config.symbols import FOREX_SYMBOLS
from data.models import Candle
from services.market_data.service import MarketDataService


@dataclass(frozen=True, slots=True)
class CurrencyConversion:
    """A market-backed quote-to-account currency conversion snapshot."""

    source_currency: str
    target_currency: str
    rate: float
    pair_symbol: str
    inverted: bool
    as_of: datetime


class CurrencyConversionService:
    """Resolve explicit FX conversion rates through the canonical market-data path.

    No account-currency assumption is made. When the requested conversion is not
    directly quoted, an explicitly supported inverse Forex pair may be used.
    Missing, invalid, or stale market data propagates as an error so callers can
    fail closed instead of producing an unsafe position size.
    """

    _CONVERSION_TIMEFRAME = "1m"

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
        if not candidates:
            raise ValueError(
                f"No supported Forex conversion pair exists for {source}->{target}."
            )
        return tuple(candidates)

    async def get_conversion(
        self,
        *,
        source_currency: str,
        target_currency: str,
    ) -> CurrencyConversion:
        source = self._normalize_currency(source_currency, "source_currency")
        target = self._normalize_currency(target_currency, "target_currency")

        if source == target:
            # Identity conversion has no market dependency and therefore no pair
            # or market timestamp. An empty pair avoids inventing symbols such as
            # USDUSD, which are not valid Forex instruments.
            return CurrencyConversion(
                source_currency=source,
                target_currency=target,
                rate=1.0,
                pair_symbol="",
                inverted=False,
                as_of=datetime.now().astimezone(),
            )

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

        raise ValueError(
            f"Unable to resolve fresh currency conversion {source}->{target}."
        ) from last_error


__all__ = ["CurrencyConversion", "CurrencyConversionService"]
