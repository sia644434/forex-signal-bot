from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from data.provider_manager import ProviderManager
from services.market_data.service import (
    MarketDataService,
    get_market_data_service,
    install_market_data_service,
)


@pytest.mark.asyncio
async def test_service_delegates_to_canonical_engine() -> None:
    engine = AsyncMock()
    engine.get_candles_list.return_value = ["candle"]
    service = MarketDataService(engine=engine)

    result = await service.get_candles_list("EUR_USD", "M15", 10)

    assert result == ["candle"]
    engine.get_candles_list.assert_awaited_once_with("EUR_USD", "M15", 10)


@pytest.mark.asyncio
async def test_service_propagates_engine_failure() -> None:
    engine = AsyncMock()
    engine.get_candles_list.side_effect = RuntimeError("engine failure")
    service = MarketDataService(engine=engine)

    with pytest.raises(RuntimeError, match="engine failure"):
        await service.get_candles_list("EUR_USD", "M15", 10)


def test_service_builds_engine_from_provider_manager() -> None:
    provider_manager = ProviderManager(providers=["oanda"])

    service = MarketDataService(provider_manager=provider_manager)

    assert service.engine.provider_manager is provider_manager


def test_service_rejects_engine_and_provider_manager_together() -> None:
    engine = AsyncMock()
    provider_manager = ProviderManager(providers=["oanda"])

    with pytest.raises(ValueError, match="cannot be provided together"):
        MarketDataService(
            engine=engine,
            provider_manager=provider_manager,
        )


def test_install_market_data_service_registers_one_application_scoped_instance() -> None:
    class Application:
        def __init__(self) -> None:
            self.bot_data = {}

    application = Application()

    service = install_market_data_service(application)

    assert application.bot_data["market_data_service"] is service
    assert get_market_data_service(application) is service
    assert service.engine.provider_manager is not None


def test_get_market_data_service_rejects_unconfigured_application() -> None:
    class Application:
        def __init__(self) -> None:
            self.bot_data = {}

    with pytest.raises(RuntimeError, match="not configured"):
        get_market_data_service(Application())
