from __future__ import annotations

from data.market_data import MarketDataEngine
from data.models import Candle
from data.provider_manager import ProviderManager


class MarketDataService:
    """Canonical application-facing market-data service.

    All production callers use the unified MarketDataEngine path. Provider
    routing, normalization, data-quality, and freshness gates remain owned by
    the data layer instead of being duplicated in this service.
    """

    _DEFAULT_LIMIT = 100

    def __init__(
        self,
        *,
        engine: MarketDataEngine | None = None,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        if engine is not None and provider_manager is not None:
            raise ValueError(
                "engine and provider_manager cannot be provided together."
            )

        self.engine = engine or MarketDataEngine(
            provider_manager=provider_manager,
        )

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Return quality- and freshness-gated candles through the canonical path."""
        return await self.engine.get_candles_list(symbol, timeframe, limit)


__all__ = ["MarketDataService"]
