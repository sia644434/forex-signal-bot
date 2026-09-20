from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
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
from core.logger import setup_logger

logger = setup_logger()

AUTO_SCANNER_JOB_NAME = "telegram-auto-multi-timeframe-scanner"
DEFAULT_INTERVAL_SECONDS = 60
DEFAULT_CANDLE_LIMIT = 300
TRIGGER_MINUTE_MODULUS = 15
TRIGGER_MINUTE_OFFSETS = frozenset({0, 1})


class ScanOutcome:
    """Stable outcome codes used for per-cycle observability."""

    DATA_FAILED = "data_failed"
    ALREADY_PROCESSED = "already_processed"
    M15_NO_TRADE = "m15_no_trade"
    M15_NEUTRAL = "m15_neutral"
    M15_DIRECTIONAL = "m15_directional"
    DIRECTIONAL_ALIGNMENT_REJECTED = "directional_alignment_rejected"
    HTF_ALIGNMENT_REJECTED = "htf_alignment_rejected"
    SETUP_QUALITY_REJECTED = "setup_quality_rejected"
    CONFIDENCE_REJECTED = "confidence_rejected"
    RR_REJECTED = "rr_rejected"
    CONFLICT_REJECTED = "conflict_rejected"
    FRESHNESS_REJECTED = "freshness_rejected"
    PORTFOLIO_RISK_REJECTED = "portfolio_risk_rejected"
    VALIDATED_SENT = "validated_sent"
    VALIDATED_NO_RECIPIENT = "validated_no_recipient"
    VALIDATED_DELIVERY_PENDING = "validated_delivery_pending"
    VALIDATION_FAILED = "validation_failed"


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
    def _cycle_bucket(now: datetime) -> str:
        """Return the canonical M15 bucket used to de-duplicate full cycles."""
        reference = now.astimezone(timezone.utc).replace(second=0, microsecond=0)
        bucket_minute = (reference.minute // TRIGGER_MINUTE_MODULUS) * TRIGGER_MINUTE_MODULUS
        return reference.replace(minute=bucket_minute).isoformat()

    @staticmethod
    def _eligible_symbols_for_session(symbols: tuple[str, ...], now: datetime) -> tuple[str, ...]:
        if now.weekday() < 5:
            return symbols
        if now.weekday() == 5:
            return tuple(symbol for symbol in symbols if get_market_type(symbol) == "crypto")
        # Sunday: crypto is open continuously; FX and commodities generally
        # reopen around 21:00 UTC. Stocks and indices remain closed.
        if now.hour < 21:
            return tuple(symbol for symbol in symbols if get_market_type(symbol) == "crypto")
        return tuple(
            symbol
            for symbol in symbols
            if get_market_type(symbol) in {"crypto", "forex", "commodity"}
        )

    @staticmethod
    def _closed_candles(candles: list[Any], timeframe: str, now: datetime | None = None) -> list[Any]:
        """Return only fully closed candles; never analyze a forming bar."""
        if not candles:
            return []
        durations = {
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(days=7),
        }
        duration = durations[normalize_timeframe(timeframe)]
        reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        closed = []
        for candle in candles:
            timestamp = getattr(candle, "timestamp", None)
            if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
                continue
            if timestamp.astimezone(timezone.utc) + duration <= reference:
                closed.append(candle)
        return closed

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
        candles = self._closed_candles(candles, normalized)
        if not candles:
            raise RuntimeError(f"No closed candles returned for {symbol}/{normalized}.")
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

    @staticmethod
    def _classify_diagnostics(diagnostics: tuple[str, ...]) -> str:
        """Map rejection diagnostics to stable cycle counters."""
        if not diagnostics:
            return ScanOutcome.VALIDATION_FAILED
        joined = "|".join(diagnostics)
        if any(item.startswith("directional_alignment=") for item in diagnostics):
            return ScanOutcome.DIRECTIONAL_ALIGNMENT_REJECTED
        if any(item.startswith("htf_alignment=") for item in diagnostics):
            return ScanOutcome.HTF_ALIGNMENT_REJECTED
        if any(item.startswith("setup_quality=") for item in diagnostics):
            return ScanOutcome.SETUP_QUALITY_REJECTED
        if any(item.startswith("confidence=") for item in diagnostics):
            return ScanOutcome.CONFIDENCE_REJECTED
        if any(item.startswith("rr=") for item in diagnostics):
            return ScanOutcome.RR_REJECTED
        if any(item.startswith("conflict_state=") for item in diagnostics):
            return ScanOutcome.CONFLICT_REJECTED
        if any(item.startswith("signal_decay=") for item in diagnostics):
            return ScanOutcome.FRESHNESS_REJECTED
        if "portfolio_risk_blocked=true" in joined:
            return ScanOutcome.PORTFOLIO_RISK_REJECTED
        return ScanOutcome.VALIDATION_FAILED

    async def _scan_symbol(self, bot, market_data, symbol: str) -> str:
        try:
            m15 = await self._fetch_timeframe(market_data, symbol, "M15", force=True)
            latest = m15[-1].timestamp
            if not isinstance(latest, datetime):
                raise RuntimeError(f"Invalid M15 timestamp for {symbol}.")
            key = f"processed:{symbol}:M15"
            latest_key = latest.astimezone(timezone.utc).isoformat()
            if self._state.get(key) == latest_key:
                return ScanOutcome.ALREADY_PROCESSED

            context = await self._context_for_symbol(market_data, symbol, m15)
            decision, diagnostics = self._engine.analyze_with_diagnostics(context, symbol=symbol)
            if decision is None:
                logger.info(
                    "Automatic scanner rejected %s/M15: %s",
                    symbol,
                    "; ".join(diagnostics) if diagnostics else "unknown_reason",
                )
                if diagnostics and diagnostics[0].startswith("m15_signal="):
                    signal = diagnostics[0].split("=", 1)[1].upper()
                    outcome = (
                        ScanOutcome.M15_NO_TRADE
                        if signal in {"NO_TRADE", "NONE", ""}
                        else ScanOutcome.M15_NEUTRAL
                        if signal == "NEUTRAL"
                        else ScanOutcome.M15_DIRECTIONAL
                    )
                else:
                    outcome = self._classify_diagnostics(diagnostics)
                self._state.put(key, latest_key)
                return outcome

            sent, eligible = await self._notify(bot, decision, latest_key)
            if eligible == 0:
                self._state.put(key, latest_key)
                return ScanOutcome.VALIDATED_NO_RECIPIENT
            if sent == eligible:
                self._state.put(key, latest_key)
            if sent:
                logger.info(
                    "Automatic validated setup sent for %s/M15 (%s recipients).",
                    symbol,
                    sent,
                )
                return ScanOutcome.VALIDATED_SENT
            return ScanOutcome.VALIDATED_DELIVERY_PENDING
        except Exception:
            logger.exception("Continuous market scan failed for %s.", symbol)
            return ScanOutcome.DATA_FAILED

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
            cycle_bucket = self._cycle_bucket(now)
            cycle_state_key = "cycle:last_m15"
            if self._state.get(cycle_state_key) == cycle_bucket:
                logger.info(
                    "Automatic scanner cycle skipped: M15 bucket already processed: bucket=%s",
                    cycle_bucket,
                )
                return 0

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

            async def guarded(symbol: str) -> str:
                async with semaphore:
                    return await self._scan_symbol(bot, market_data, symbol)

            results = await asyncio.gather(*(guarded(symbol) for symbol in symbols))
            summary = {outcome: results.count(outcome) for outcome in set(results)}
            sent_count = summary.get(ScanOutcome.VALIDATED_SENT, 0)

            # Persist the completed M15 cycle only when at least one symbol
            # produced a non-data-failure outcome. This keeps a transient
            # provider outage retryable while preventing duplicate full fetches
            # during the same 15-minute candle window.
            data_failed = summary.get(ScanOutcome.DATA_FAILED, 0)
            if data_failed < len(symbols):
                self._state.put(cycle_state_key, cycle_bucket)
            logger.info(
                "Automatic scanner cycle summary: symbols=%d data_failed=%d already_processed=%d "
                "m15_no_trade=%d m15_neutral=%d m15_directional=%d "
                "directional_alignment_rejected=%d htf_alignment_rejected=%d "
                "setup_quality_rejected=%d confidence_rejected=%d rr_rejected=%d "
                "conflict_rejected=%d freshness_rejected=%d portfolio_risk_rejected=%d "
                "validated_sent=%d validated_no_recipient=%d validated_delivery_pending=%d validation_failed=%d",
                len(symbols),
                summary.get(ScanOutcome.DATA_FAILED, 0),
                summary.get(ScanOutcome.ALREADY_PROCESSED, 0),
                summary.get(ScanOutcome.M15_NO_TRADE, 0),
                summary.get(ScanOutcome.M15_NEUTRAL, 0),
                summary.get(ScanOutcome.M15_DIRECTIONAL, 0),
                summary.get(ScanOutcome.DIRECTIONAL_ALIGNMENT_REJECTED, 0),
                summary.get(ScanOutcome.HTF_ALIGNMENT_REJECTED, 0),
                summary.get(ScanOutcome.SETUP_QUALITY_REJECTED, 0),
                summary.get(ScanOutcome.CONFIDENCE_REJECTED, 0),
                summary.get(ScanOutcome.RR_REJECTED, 0),
                summary.get(ScanOutcome.CONFLICT_REJECTED, 0),
                summary.get(ScanOutcome.FRESHNESS_REJECTED, 0),
                summary.get(ScanOutcome.PORTFOLIO_RISK_REJECTED, 0),
                sent_count,
                summary.get(ScanOutcome.VALIDATED_NO_RECIPIENT, 0),
                summary.get(ScanOutcome.VALIDATED_DELIVERY_PENDING, 0),
                summary.get(ScanOutcome.VALIDATION_FAILED, 0),
            )
            logger.info(
                "Automatic scanner cycle finished: symbols=%d, validated_setups_sent=%d",
                len(symbols),
                sent_count,
            )
            return sent_count


_SCANNER: ContinuousMarketScanner | None = None


async def run_continuous_market_scan(context) -> None:
    """Scheduler entry point with explicit lifecycle diagnostics.

    Keep this wrapper observable so a scheduler failure, missed execution, or
    callback crash cannot silently look like a healthy continuous scanner.
    """
    global _SCANNER
    started_at = datetime.now(timezone.utc)
    logger.info(
        "Automatic scanner job invoked: job=%s, utc=%s",
        AUTO_SCANNER_JOB_NAME,
        started_at.isoformat(),
    )
    try:
        if _SCANNER is None:
            _SCANNER = ContinuousMarketScanner()
        sent = await _SCANNER.run_once(context.bot, context.application)
        logger.info(
            "Automatic scanner job completed: job=%s, sent=%s, duration_seconds=%.3f",
            AUTO_SCANNER_JOB_NAME,
            sent,
            (datetime.now(timezone.utc) - started_at).total_seconds(),
        )
    except Exception:
        logger.exception(
            "Automatic scanner job crashed: job=%s, duration_seconds=%.3f",
            AUTO_SCANNER_JOB_NAME,
            (datetime.now(timezone.utc) - started_at).total_seconds(),
        )
        raise



__all__ = [
    "ContinuousMarketScanner",
    "run_continuous_market_scan",
    "auto_scanner_enabled",
    "auto_scanner_interval_seconds",
    "AUTO_SCANNER_JOB_NAME",
]
