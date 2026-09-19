from __future__ import annotations

import html
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from analysis.market_aware_engine import MarketAwareAnalysisEngine
from services.market_data.service import MarketDataService
from .tracker_store import TrackerStore, TrackerStoreError


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
    events: list[dict[str, str]] | None = None


_STORE = TrackerStore()


def _key(user_id: int, symbol: str, timeframe: str) -> str:
    return f"{user_id}:{symbol}:{timeframe}"


def _serialize(item: TrackedSignal) -> dict:
    return asdict(item)


def _deserialize(data: dict) -> TrackedSignal:
    return TrackedSignal(
        user_id=int(data["user_id"]),
        symbol=str(data["symbol"]),
        timeframe=str(data["timeframe"]),
        signal=str(data["signal"]),
        entry=data.get("entry"),
        stop_loss=data.get("stop_loss"),
        take_profit_1=data.get("take_profit_1"),
        take_profit_2=data.get("take_profit_2"),
        take_profit_3=data.get("take_profit_3"),
        status=str(data.get("status", "ACTIVE")),
        last_signal=str(data.get("last_signal", "")),
        last_price=data.get("last_price"),
        updated_at=str(data.get("updated_at", "")),
        events=list(data.get("events") or []),
    )


def _load_tracks() -> dict[tuple[int, str, str], TrackedSignal]:
    raw = _STORE.load_all()
    tracks: dict[tuple[int, str, str], TrackedSignal] = {}
    for key, data in raw.items():
        try:
            item = _deserialize(data)
            expected_key = _key(item.user_id, item.symbol, item.timeframe)
            if key != expected_key:
                raise ValueError("tracker key does not match stored signal identity")
            tracks[(item.user_id, item.symbol, item.timeframe)] = item
        except (KeyError, TypeError, ValueError) as error:
            raise TrackerStoreError(f"invalid tracked signal record: {key}") from error
    return tracks


ACTIVE_TRACKS: dict[tuple[int, str, str], TrackedSignal] = _load_tracks()


def _persist_tracks() -> None:
    _STORE.save_all({_key(*key): _serialize(item) for key, item in ACTIVE_TRACKS.items()})


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
        events=[{"type": "CREATED", "signal": signal, "timestamp": datetime.now(timezone.utc).isoformat()}],
    )
    ACTIVE_TRACKS[(user_id, symbol, timeframe)] = item
    _persist_tracks()
    return item


def stop_tracking(user_id: int, symbol: str, timeframe: str) -> bool:
    removed = ACTIVE_TRACKS.pop((user_id, symbol, timeframe), None) is not None
    if removed:
        _persist_tracks()
    return removed


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
    if item.events is None:
        item.events = []
    item.updated_at = datetime.now(timezone.utc).isoformat()

    if new_signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}:
        item.signal = new_signal
        item.entry = report.entry_price
        item.stop_loss = report.stop_loss
        item.take_profit_1 = report.take_profit_1
        item.take_profit_2 = report.take_profit_2
        item.take_profit_3 = report.take_profit_3
        item.status = "CHANGED" if new_signal != old_signal else "ACTIVE"
        if new_signal != old_signal:
            item.events.append({"type": "SIGNAL_CHANGED", "from": old_signal, "to": new_signal, "timestamp": item.updated_at})
    else:
        item.signal = new_signal
        item.entry = None
        item.stop_loss = None
        item.take_profit_1 = None
        item.take_profit_2 = None
        item.take_profit_3 = None
        item.status = "INVALIDATED"
        item.events.append({"type": "INVALIDATED", "from": old_signal, "to": new_signal, "timestamp": item.updated_at})

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

    if new_signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"} and new_signal == old_signal:
        target_event = _target_event(item, high, low)
        if target_event:
            item.status = "TARGET_REACHED" if "TP" in target_event else "STOPPED"
            if item.events is None:
                item.events = []
            item.events.append({"type": item.status, "detail": target_event, "timestamp": item.updated_at})
            await notify(
                f"📢 <b>به‌روزرسانی {html.escape(item.symbol, quote=False)}</b>\n\n"
                f"{target_event}\nقیمت فعلی: <b>{close}</b>"
            )
            ACTIVE_TRACKS.pop((item.user_id, item.symbol, item.timeframe), None)
            _persist_tracks()
            return item

    if new_signal != old_signal:
        await notify(
            f"📢 <b>به‌روزرسانی {html.escape(item.symbol, quote=False)}</b>\n\n"
            f"سیگنال قبلی: <b>{html.escape(old_signal, quote=False)}</b>\n"
            f"سیگنال فعلی: <b>{html.escape(new_signal, quote=False)}</b>\n"
            f"قیمت: <b>{close}</b>"
        )
    _persist_tracks()
    return item


__all__ = ["TrackedSignal", "track_report", "stop_tracking", "list_tracking", "refresh_tracking"]
