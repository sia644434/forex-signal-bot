from __future__ import annotations

from data.manager import DataManager
from data.models import Candle
from data.market_data import MarketDataEngine

from core.errors import ApplicationError
from core.logger import setup_logger


logger = setup_logger()


class MarketDataService:
    """Canonical application-facing market-data service.

    Production callers use ``MarketDataEngine`` through this boundary so the
    provider, normalization, data-quality, and freshness gates remain in one
    canonical path. The DataManager-backed methods remain available for the
    lower-level service contract tests and explicit provider operations.
    """

    _DEFAULT_LIMIT = 100
    _MAX_LIMIT = 5000

    def __init__(
        self,
        data_manager: DataManager | None = None,
        *,
        engine: MarketDataEngine | None = None,
    ) -> None:
        if data_manager is not None and engine is not None:
            raise TypeError("provide either data_manager or engine, not both")
        self.data_manager = data_manager
        self.engine = engine or (MarketDataEngine() if data_manager is None else None)

    async def get_candles_list(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
    ) -> list[Candle]:
        """Return quality- and freshness-gated candles through the canonical path."""
        if self.engine is not None:
            return await self.engine.get_candles_list(symbol, timeframe, limit)
        return await self.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
        provider_name: str | None = None,
    ) -> list[Candle]:
        """Retrieve normalized candles from the lower-level data contract."""
        if self.data_manager is None:
            if provider_name is not None:
                raise ApplicationError(
                    "Explicit provider selection is unavailable on the canonical engine path."
                )
            return await self.get_candles_list(symbol, timeframe, limit)

        normalized_symbol, normalized_timeframe = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            provider_name=provider_name,
        )

        try:
            candles = await self.data_manager.get_candles(
                provider_name=provider_name,
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                limit=limit,
            )
        except ApplicationError:
            raise
        except Exception as error:
            logger.exception(
                "MarketDataService failed. symbol=%s timeframe=%s provider=%s limit=%s",
                normalized_symbol,
                normalized_timeframe,
                provider_name,
                limit,
            )
            raise ApplicationError(
                "Market data service failed.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                    "provider": provider_name,
                },
            ) from error

        if candles is None:
            return []
        if not isinstance(candles, list):
            raise ApplicationError("Market data manager returned invalid candle data.")
        return candles

    async def get_candles_with_fallback(
        self,
        symbol: str,
        timeframe: str,
        limit: int = _DEFAULT_LIMIT,
        providers: list[str] | tuple[str, ...] | None = None,
    ) -> list[Candle]:
        """Retrieve candles using DataManager's provider fallback mechanism."""
        if self.data_manager is None:
            return await self.get_candles_list(symbol, timeframe, limit)

        normalized_symbol, normalized_timeframe = self._validate_request(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )

        if not hasattr(self.data_manager, "get_candles_with_fallback"):
            raise ApplicationError("Data manager does not support provider fallback.")

        try:
            candles = await self.data_manager.get_candles_with_fallback(
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                limit=limit,
                providers=providers,
            )
        except ApplicationError:
            raise
        except Exception as error:
            logger.exception(
                "MarketDataService fallback request failed. symbol=%s timeframe=%s",
                normalized_symbol,
                normalized_timeframe,
            )
            raise ApplicationError(
                "Market data fallback service failed.",
                {
                    "symbol": normalized_symbol,
                    "timeframe": normalized_timeframe,
                    "limit": limit,
                    "providers": providers,
                },
            ) from error

        if not isinstance(candles, list):
            raise ApplicationError("Market data fallback returned invalid candle data.")
        return candles

    @staticmethod
    def _validate_request(
        symbol: str,
        timeframe: str,
        limit: int,
        provider_name: str | None = None,
    ) -> tuple[str, str]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol cannot be empty.")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        normalized_timeframe = timeframe.strip().upper()
        if not normalized_timeframe:
            raise ValueError("timeframe cannot be empty.")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer.")
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        if limit > MarketDataService._MAX_LIMIT:
            raise ValueError(f"limit cannot be greater than {MarketDataService._MAX_LIMIT}.")
        if provider_name is not None:
            if not isinstance(provider_name, str):
                raise TypeError("provider_name must be a string or None.")
            if not provider_name.strip():
                raise ValueError("provider_name cannot be empty.")
        return normalized_symbol, normalized_timeframe


__all__ = ["MarketDataService"]
