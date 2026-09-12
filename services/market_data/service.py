from __future__ import annotations

from data.market_data import MarketDataEngine
from data.models import Candle
from data.provider_manager import ProviderManager


MARKET_DATA_SERVICE_KEY = "market_data_service"


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


def install_market_data_service(application: object) -> MarketDataService:
    """Create and register one market-data service for an application lifetime.

    The service owns a ProviderManager through MarketDataEngine, so keeping the
    service application-scoped preserves provider instance caches and cooldown
    state across independent Telegram requests without introducing a process-
    global singleton.
    """
    bot_data = getattr(application, "bot_data", None)
    if not isinstance(bot_data, dict):
        raise TypeError("application must expose a mutable bot_data dictionary.")

    service = MarketDataService()
    bot_data[MARKET_DATA_SERVICE_KEY] = service
    return service


def get_market_data_service(application: object) -> MarketDataService:
    """Return the application-scoped market-data service."""
    bot_data = getattr(application, "bot_data", None)
    if not isinstance(bot_data, dict):
        raise TypeError("application must expose a mutable bot_data dictionary.")

    service = bot_data.get(MARKET_DATA_SERVICE_KEY)
    if not isinstance(service, MarketDataService):
        raise RuntimeError("Application market-data service is not configured.")
    return service


__all__ = [
    "MARKET_DATA_SERVICE_KEY",
    "MarketDataService",
    "get_market_data_service",
    "install_market_data_service",
]
