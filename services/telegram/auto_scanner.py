from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import os
from typing import Any

from config.symbols import get_market_type, normalize_timeframe
from services.market_data.service import MarketDataService
from services.telegram.scanner import _configured_scan_symbols, get_scanner_provider_manager
from services.telegram.state import get_user_state
from services.telegram.access import _allowed_user_ids
from services.telegram.handlers.signal import _format_signal
from services.telegram.auto_scan_state import AutoScannerStateStore
from analysis.multi_timeframe_engine import MultiTimeframeAnalysisEngine

logger = logging.getLogger(__name__)

AUTO_SCANNER_JOB_NAME = "telegram-auto-multi-timeframe-scanner"
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_CANDLE_LIMIT = 300
TRIGGER_MINUTE_MODULUS = 15
TRIGGER_MINUTE_OFFSETS = frozenset({0, 1})
TIMEFRAMES = ("W1", "D1", "H4", "H1", "M15", "M5")


def auto_scanner_interval_seconds() -> int:
    raw = os.getenv("TELEGRAM_AUTO_SCAN_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError("TELEGRAM_AUTO_SCAN_INTERVAL_SECONDS must be an integer.") from error
    if not 30 <= value <= 300:
        raise ValueError("TELEGRAM_AUTO_SCAN_INTERVAL_SECONDS must be between 30 and 300 seconds.")
    return value


def auto_scanner_enabled() -> bool:
    raw = os.getenv("TELEGRAM_AUTO_SCANNER_ENABLED", "true").strip().lower()
    return raw in {"1", "true", "yes", "on", "enabled"}


def _chat_ids() -> tuple[int, ...]:
    raw = os.getenv("TELEGRAM_AUTO_SCAN_CHAT_IDS", "").strip()
    if raw:
        try:
            values = tuple(int(item.strip()) for item in raw.split(",") if item.strip())
        except ValueError as error:
            raise ValueError("TELEGRAM_AUTO_SCAN_CHAT_IDS contains an invalid chat id.") from error
    else:
        values = _allowed_user_ids()
    if any(value <= 0 for value in values):
        raise ValueError("Automatic scanner chat ids must be positive.")
    return tuple(dict.fromkeys(values))


class ContinuousMarketScanner:
    """Continuously monitor closed M15 setups and notify only validated opportunities."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._state = AutoScannerStateStore()
        self._engine = MultiTimeframeAnalysisEngine()
        self._cache: dict[tuple[str, str], tuple[datetime, list[Any]]] = {}

    @staticmethod
    def _should_scan_now(now: datetime | None = None) -> bool:
        reference = now or datetime.now(timezone.utc)
        return reference.minute % TRIGGER_MINUTE_MODULUS in TRIGGER_MINUTE_OFFSETS

    @staticmethod
    def _eligible_symbols_for_session(symbols: tuple[str, ...], now: datetime) -> tuple[str, ...]:
        if now.weekday() < 5:
            return symbols
        return tuple(symbol for symbol in symbols if get_market_type(symbol) == "crypto")

    async def _fetch_timeframe(
        self,
        market_data,
        symbol: str,
        timeframe: str,
        *,
        force: bool = False,
    ) -> list[Any]:
        normalized = normalize_timeframe(timeframe)
        key = (symbol, normalized)
        cached = self._cache.get(key)
        if cached and not force:
            fetched_at = cached[0]
            interval_seconds = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}[normalized]
            age = (datetime.now(timezone.utc) - fetched_at.astimezone(timezone.utc)).total_seconds()
            if age < interval_seconds:
                return cached[1]

        candles = await market_data.get_candles_list(symbol=symbol, timeframe=normalized, limit=DEFAULT_CANDLE_LIMIT)
        if not candles:
            raise RuntimeError(f"No candles returned for {symbol}/{normalized}.")
        latest = getattr(candles[-1], "timestamp", None)
        if not isinstance(latest, datetime) or latest.tzinfo is None:
            raise RuntimeError(f"Invalid latest candle timestamp for {symbol}/{normalized}.")
        self._cache[key] = (datetime.now(timezone.utc), candles)
        return candles

    async def _context_for_symbol(self, market_data, symbol: str, m15_candles: list[Any]) -> dict[str, list[Any]]:
        context = {"M15": m15_candles}
        for timeframe in ("W1", "D1", "H4", "H1"):
            context[timeframe] = await self._fetch_timeframe(market_data, symbol, timeframe, force=False)
        # M5 is only requested after higher-timeframe context exists; it is the
        # lower-timeframe entry confirmation rather than the primary trigger.
        context["M5"] = await self._fetch_timeframe(market_data, symbol, "M5", force=False)
        return context

    @staticmethod
    def _notification_key(
        symbol: str,
        timeframe: str,
        candle_key: str,
        direction: str,
        chat_id: int,
    ) -> str:
        return (
            f"sent:{symbol}:{timeframe}:{candle_key}:{direction}:"
            f"{chat_id}"
        )

    async def _notify(self, bot, decision, candle_key: str) -> tuple[int, int]:
        sent = 0
        eligible = 0
        for chat_id in _chat_ids():
            try:
                state = get_user_state(chat_id)
                if not bool(state.settings.get("notifications_enabled", True)):
                    continue

                eligible += 1
                notification_key = self._notification_key(
                    decision.symbol,
                    decision.setup_timeframe,
                    candle_key,
                    decision.direction,
                    chat_id,
                )
                if self._state.get(notification_key) == "sent":
                    sent += 1
                    continue

                language = state.language if state.language in {"fa", "en"} else "fa"
                message = _format_signal(
                    decision.setup_report,
                    decision.symbol,
                    decision.setup_timeframe,
                )
                message += (
                    "\n\n🧭 <b>تحلیل چندتایم‌فریمی</b>"
                    f"\n• هم‌جهتی تایم‌فریم‌های بالاتر: <b>{decision.alignment_score:.1f}/100</b>"
                    f"\n• تأیید M5: <b>{decision.lower_timeframe_score:.1f}/100</b>"
                    "\n• W1 → D1 → H4 → H1 → M15 → M5"
                )
                if decision.reasons:
                    message += "\n" + "\n".join(f"• {reason}" for reason in decision.reasons[:4])
                if language == "en":
                    message = message.replace("تحلیل چندتایم‌فریمی", "Multi-timeframe analysis")
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
                self._state.put(notification_key, "sent")
                sent += 1
            except Exception:
                logger.exception("Automatic signal notification failed for chat %s.", chat_id)
        return sent, eligible

    async def _scan_symbol(self, bot, market_data, symbol: str) -> bool:
        try:
            m15 = await self._fetch_timeframe(market_data, symbol, "M15", force=True)
            latest = m15[-1].timestamp
            if not isinstance(latest, datetime):
                raise RuntimeError(f"Invalid M15 timestamp for {symbol}.")
            key = f"processed:{symbol}:M15"
            latest_key = latest.astimezone(timezone.utc).isoformat()
            if self._state.get(key) == latest_key:
                return False

            context = await self._context_for_symbol(market_data, symbol, m15)
            decision = self._engine.analyze(context, symbol=symbol)

            # A no-signal result is deterministic for this closed M15 candle.
            # For a signal, keep the candle unprocessed until every eligible
            # recipient has either already received it or receives it now.
            # This makes Telegram delivery retryable after transient failures.
            if decision is None:
                self._state.put(key, latest_key)
                return False

            sent, eligible = await self._notify(bot, decision, latest_key)
            if eligible == 0 or sent == eligible:
                self._state.put(key, latest_key)

            if sent:
                logger.info(
                    "Automatic validated setup sent for %s/M15 (%s recipients).",
                    symbol,
                    sent,
                )
                return True
            return False
        except Exception:
            logger.exception("Continuous market scan failed for %s.", symbol)
            return False

    async def run_once(self, bot, application: Any) -> int:
        if not auto_scanner_enabled():
            return 0
        now = datetime.now(timezone.utc)
        if not self._should_scan_now(now):
            return 0
        async with self._lock:
            # Non-crypto markets are closed over the weekend. Do not manufacture
            # failures from intentionally stale Friday candles; crypto remains
            # continuously monitored because it trades 24/7.
            configured_symbols = _configured_scan_symbols()
            symbols = self._eligible_symbols_for_session(configured_symbols, now)
            if not symbols:
                logger.info(
                    "Automatic scanner skipped: all configured non-crypto markets are closed (UTC weekend)."
                )
                return 0

            # Refresh provider configuration before each automatic cycle so
            # newly available configured providers are picked up without restart.
            provider_manager = get_scanner_provider_manager(application)
            market_data = MarketDataService(provider_manager=provider_manager)
            semaphore = asyncio.Semaphore(4)
            logger.info(
                "Automatic scanner cycle started: symbols=%d/%d, timeframes=%s, utc=%s",
                len(symbols),
                len(configured_symbols),
                ",".join(TIMEFRAMES),
                now.isoformat(),
            )

            async def guarded(symbol: str) -> bool:
                async with semaphore:
                    return await self._scan_symbol(bot, market_data, symbol)

            results = await asyncio.gather(*(guarded(symbol) for symbol in symbols))
            sent_count = sum(bool(result) for result in results)
            logger.info(
                "Automatic scanner cycle finished: symbols=%d, validated_setups_sent=%d",
                len(symbols),
                sent_count,
            )
            return sent_count


_SCANNER: ContinuousMarketScanner | None = None


async def run_continuous_market_scan(context) -> None:
    global _SCANNER
    if _SCANNER is None:
        _SCANNER = ContinuousMarketScanner()
    sent = await _SCANNER.run_once(context.bot, context.application)
    if sent:
        logger.info("Continuous scanner cycle delivered %s validated setup(s).", sent)


__all__ = [
    "ContinuousMarketScanner",
    "run_continuous_market_scan",
    "auto_scanner_enabled",
    "auto_scanner_interval_seconds",
    "AUTO_SCANNER_JOB_NAME",
]
