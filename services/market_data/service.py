from __future__ import annotations

from data.market_data import MarketDataEngine
from data.models import Candle


class MarketDataService:
    """Canonical application-facing market-data service.

    All production callers use the unified MarketDataEngine path. Provider
    routing, normalization, data-quality, and freshness gates remain owned by
    the data layer instead of being duplicated in this service.
    """

    _DEFAULT_LIMIT = 100

    def __init__(self, *, engine: MarketDataEngine | None = None) -> None:
        self.engine = engine or MarketDataEngine()

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Return quality- and freshness-gated candles through the canonical path."""
        return await self.engine.get_candles_list(symbol, timeframe, limit)


__all__ = ["MarketDataService"]
