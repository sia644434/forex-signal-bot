from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from analysis.market_aware_engine import MarketAwareAnalysisEngine
from services.market_data.service import MarketDataService


@dataclass
class TrackedSignal:
    user_id: int
    symbol: str
    timeframe: str
    signal: str
    entry: float | None
    stop_loss: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    take_profit_3: float | None
    status: str = "ACTIVE"
    last_signal: str = ""
    last_price: float | None = None
    updated_at: str = ""


def track_report(user_id: int, symbol: str, timeframe: str, report) -> TrackedSignal:
    signal = str(report.signal).upper()
    item = TrackedSignal(
        user_id,
        symbol,
        timeframe,
        signal,
        report.entry_price,
        report.stop_loss,
        report.take_profit_1,
        report.take_profit_2,
        report.take_profit_3,
        last_signal=signal,
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
    ACTIVE_TRACKS[(user_id, symbol, timeframe)] = item
    return item


ACTIVE_TRACKS: dict[tuple[int, str, str], TrackedSignal] = {}


def stop_tracking(user_id: int, symbol: str, timeframe: str) -> bool:
    return ACTIVE_TRACKS.pop((user_id, symbol, timeframe), None) is not None


def list_tracking(user_id: int) -> list[TrackedSignal]:
    return [x for x in ACTIVE_TRACKS.values() if x.user_id == user_id]


def _target_event(item: TrackedSignal, high: float, low: float) -> str | None:
    if item.signal in {"BUY", "STRONG_BUY"}:
        if item.stop_loss is not None and low <= item.stop_loss:
            return "🛑 حد ضرر لمس شد"
        targets = (("TP1", item.take_profit_1), ("TP2", item.take_profit_2), ("TP3", item.take_profit_3))
        for label, target in targets:
            if target is not None and high >= target:
                return f"🎯 {label} لمس شد"
    elif item.signal in {"SELL", "STRONG_SELL"}:
        if item.stop_loss is not None and high >= item.stop_loss:
            return "🛑 حد ضرر لمس شد"
        targets = (("TP1", item.take_profit_1), ("TP2", item.take_profit_2), ("TP3", item.take_profit_3))
        for label, target in targets:
            if target is not None and low <= target:
                return f"🎯 {label} لمس شد"
    return None


def _apply_report(item: TrackedSignal, report) -> tuple[str, str]:
    """Synchronize the tracked risk plan with the newest valid analysis."""
    new_signal = str(report.signal).upper()
    old_signal = item.last_signal
    item.last_signal = new_signal
    item.updated_at = datetime.now(timezone.utc).isoformat()

    if new_signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
        item.signal = new_signal
        item.entry = report.entry_price
        item.stop_loss = report.stop_loss
        item.take_profit_1 = report.take_profit_1
        item.take_profit_2 = report.take_profit_2
        item.take_profit_3 = report.take_profit_3
        item.status = "CHANGED" if new_signal != old_signal else "ACTIVE"
    else:
        item.signal = new_signal
        item.entry = None
        item.stop_loss = None
        item.take_profit_1 = None
        item.take_profit_2 = None
        item.take_profit_3 = None
        item.status = "INVALIDATED"

    return old_signal, new_signal


async def refresh_tracking(
    item: TrackedSignal,
    notify: Callable[[str], Awaitable[None]],
    market_data: MarketDataService,
) -> TrackedSignal:
    candles = await market_data.get_candles_list(item.symbol, item.timeframe, 300)
    if not candles:
        return item

    latest = candles[-1]
    high, low, close = float(latest.high), float(latest.low), float(latest.close)
    item.last_price = close

    # Re-analyze before evaluating TP/SL. Otherwise a direction change in the
    # newest analysis could still be incorrectly closed by the previous plan's
    # levels on the same candle.
    report = await MarketAwareAnalysisEngine(market_data=market_data).analyze(
        candles, symbol=item.symbol, timeframe=item.timeframe
    )
    old_signal, new_signal = _apply_report(item, report)

    if new_signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
        target_event = _target_event(item, high, low)
        if target_event:
            item.status = "TARGET_REACHED" if "TP" in target_event else "STOPPED"
            await notify(
                f"📢 <b>به‌روزرسانی {html.escape(item.symbol, quote=False)}</b>\n\n"
                f"{target_event}\nقیمت فعلی: <b>{close}</b>"
            )
            ACTIVE_TRACKS.pop((item.user_id, item.symbol, item.timeframe), None)
            return item

    if new_signal != old_signal:
        await notify(
            f"📢 <b>به‌روزرسانی {html.escape(item.symbol, quote=False)}</b>\n\n"
            f"سیگنال قبلی: <b>{html.escape(old_signal, quote=False)}</b>\n"
            f"سیگنال فعلی: <b>{html.escape(new_signal, quote=False)}</b>\n"
            f"قیمت: <b>{close}</b>"
        )
    return item


__all__ = ["TrackedSignal", "track_report", "stop_tracking", "list_tracking", "refresh_tracking"]
