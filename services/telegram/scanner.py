from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime
import html
import logging
import os
from typing import Any

from analysis.full_engine import FullAnalysisEngine
from config.symbols import get_market_type
from core.errors import ApplicationError
from data.factory import ProviderFactory
from data.provider_manager import ProviderManager
from services.market_data.service import MarketDataService
from .market_session import evaluate_market_status
from .i18n import t

logger = logging.getLogger(__name__)
DEFAULT_SCAN_SYMBOLS = (
    "EURUSD", "GBPUSD", "USDJPY",
    "BTCUSDT", "ETHUSDT",
    "AAPL", "NVDA",
    "SPX", "NDX",
    "XAUUSD", "XAGUSD", "WTI",
)
DEFAULT_TIMEFRAME = "M15"
DEFAULT_LIMIT = 300
SCANNER_PROVIDER_MANAGER_KEY = "scanner_provider_manager"


@dataclass(frozen=True)
class ScanResult:
    symbol: str
    signal: str
    confidence: float
    score: float
    trade_quality: float | None
    trade_grade: str
    trend: str
    risk_reward: float | None
    error: str | None = None
    market_status: str = "OPEN"
    last_candle_time: datetime | str | None = None


@dataclass(frozen=True)
class ScanReadiness:
    configured_providers: tuple[str, ...]
    unavailable_providers: tuple[str, ...]


def _configured_scan_symbols() -> tuple[str, ...]:
    """Return a bounded, normalized scanner universe with an explicit env override."""
    raw = os.getenv("TELEGRAM_SCANNER_SYMBOLS", "").strip()
    if not raw:
        return DEFAULT_SCAN_SYMBOLS
    symbols = tuple(dict.fromkeys(item.strip().upper().replace("/", "") for item in raw.split(",") if item.strip()))
    if not symbols:
        raise ValueError("TELEGRAM_SCANNER_SYMBOLS must contain at least one symbol")
    if len(symbols) > 20:
        raise ValueError("TELEGRAM_SCANNER_SYMBOLS must contain at most 20 symbols")
    return symbols


def _provider_readiness() -> ScanReadiness:
    configured = []
    unavailable = []
    for provider_name in ProviderFactory.available():
        try:
            (configured if ProviderFactory.configured(provider_name) else unavailable).append(provider_name)
        except Exception:
            unavailable.append(provider_name)
    return ScanReadiness(tuple(configured), tuple(unavailable))


def _build_provider_manager() -> ProviderManager:
    readiness = _provider_readiness()
    if not readiness.configured_providers:
        raise ApplicationError("No market-data provider is configured.", {})
    return ProviderManager(providers=readiness.configured_providers)


def get_scanner_provider_manager(application: Any) -> ProviderManager:
    """Return the application-scoped scanner ProviderManager."""
    bot_data = getattr(application, "bot_data", None)
    if not isinstance(bot_data, dict):
        raise TypeError("application must expose a mutable bot_data dictionary.")

    readiness = _provider_readiness()
    if not readiness.configured_providers:
        raise ApplicationError("No market-data provider is configured.", {})

    manager = bot_data.get(SCANNER_PROVIDER_MANAGER_KEY)
    if manager is None:
        manager = ProviderManager(providers=readiness.configured_providers)
        bot_data[SCANNER_PROVIDER_MANAGER_KEY] = manager
        return manager

    if not isinstance(manager, ProviderManager):
        raise TypeError("application scanner provider manager has an invalid type.")

    manager.set_providers(readiness.configured_providers)
    return manager


async def scan_market(
    symbols=None,
    timeframe=DEFAULT_TIMEFRAME,
    limit=DEFAULT_LIMIT,
    provider_manager: ProviderManager | None = None,
):
    provider_manager = provider_manager or _build_provider_manager()
    scan_symbols = _configured_scan_symbols() if symbols is None else tuple(symbols)
    if not scan_symbols:
        raise ValueError("Scanner symbol universe cannot be empty")
    if len(scan_symbols) > 20:
        raise ValueError("Scanner symbol universe cannot exceed 20 symbols")
    market_data = MarketDataService(provider_manager=provider_manager)
    analyzer = FullAnalysisEngine()

    async def scan_one(symbol):
        try:
            candles = await market_data.get_candles_list(symbol, timeframe, limit)
            if not candles:
                raise RuntimeError("empty market data")

            status = evaluate_market_status(candles, timeframe, symbol=symbol)
            if status.status != "OPEN":
                return ScanResult(
                    symbol, "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None,
                    market_status=status.status,
                    last_candle_time=getattr(status, "last_candle_time", None),
                )

            report = await asyncio.to_thread(analyzer.analyze, candles)
            report = replace(report, symbol=symbol, timeframe=timeframe)
            return ScanResult(
                symbol,
                str(report.signal).upper(),
                float(report.confidence),
                float(report.score),
                report.trade_quality,
                report.trade_grade,
                report.trend,
                report.risk_reward,
                market_status=status.status,
                last_candle_time=getattr(status, "last_candle_time", None),
            )
        except Exception:
            logger.exception("Market scan failed for %s/%s", symbol, timeframe)
            return ScanResult(symbol, "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None, error="scan_failed")

    return sorted(await asyncio.gather(*(scan_one(s) for s in scan_symbols)), key=lambda x: (x.error is None, x.confidence, x.score), reverse=True)


def _status_text(status: str, language: str = "fa") -> str:
    key = {
        "CLOSED": "scan_status_closed",
        "STALE": "scan_status_stale",
        "NO_DATA": "scan_status_no_data",
        "HOLIDAY": "scan_status_holiday",
        "UNKNOWN": "scan_status_unknown",
    }.get(status)
    return t(language, key) if key else t(language, "scan_status_unknown")


def format_scan(results, timeframe, language="fa"):
    lines = [t(language, "scan_title", timeframe=html.escape(str(timeframe), quote=False)), ""]

    for item in results:
        symbol = html.escape(str(item.symbol), quote=False)
        if item.error:
            lines.append(f"• <b>{symbol}</b> → {t(language, 'scan_unavailable')}")
            continue

        if item.market_status != "OPEN":
            extra = f" | {t(language, 'scan_last_candle')}: {html.escape(str(item.last_candle_time), quote=False)}" if item.last_candle_time else ""
            lines.append(f"• <b>{symbol}</b> → ⚠️ {t(language, 'scan_market')} {_status_text(item.market_status, language)}{extra}")
            continue

        signal = html.escape(str(item.signal), quote=False)
        trade_grade = html.escape(str(item.trade_grade), quote=False)
        trend = html.escape(str(item.trend), quote=False)
        confidence = max(0, min(1, item.confidence)) * 100
        quality = "—" if item.trade_quality is None else f"{item.trade_quality:.0f}"
        rr = "—" if item.risk_reward is None else f"{item.risk_reward:.2f}"
        lines.append(
            f"• <b>{symbol}</b> → {signal} | {t(language, 'scan_confidence')} {confidence:.0f}% | "
            f"{t(language, 'scan_quality')} {quality} | RR {rr} | {t(language, 'scan_trend')} {trend} | {trade_grade}"
        )

    lines.extend(["", t(language, "scan_note")])
    return "\n".join(lines)


__all__ = [
    "ScanResult", "ScanReadiness", "scan_market",
    "format_scan", "get_scanner_provider_manager", "DEFAULT_SCAN_SYMBOLS",
]
