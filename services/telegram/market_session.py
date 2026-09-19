from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from config.symbols import TIMEFRAME_MINUTES, get_market_type, normalize_symbol, normalize_timeframe


@dataclass(frozen=True)
class MarketStatus:
    status: str
    last_candle_time: datetime | None = None


OPEN = "OPEN"
CLOSED = "CLOSED"
STALE = "STALE"
NO_DATA = "NO_DATA"

# Keep status semantics aligned with the canonical MarketDataEngine freshness
# contract: six candle intervals is the default rejection boundary.
DEFAULT_STALE_INTERVALS = 6


def _parse_last_candle_time(candle: object) -> datetime | None:
    last_time = getattr(candle, "time", None) or getattr(candle, "timestamp", None)
    if isinstance(last_time, str):
        try:
            last_time = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(last_time, datetime):
        return None
    if last_time.tzinfo is None or last_time.utcoffset() is None:
        return None
    return last_time.astimezone(timezone.utc)


def _stale_after(timeframe: str) -> timedelta:
    normalized = normalize_timeframe(timeframe)
    minutes = TIMEFRAME_MINUTES[normalized]
    return timedelta(minutes=minutes * DEFAULT_STALE_INTERVALS)


def is_market_weekend_closed(
    *,
    symbol: str | None = None,
    market_type: str | None = None,
    now: datetime | None = None,
) -> bool:
    """Return whether the requested market is in the repository's weekend break."""
    reference = now if now is not None else datetime.now(timezone.utc)
    if (
        not isinstance(reference, datetime)
        or reference.tzinfo is None
        or reference.utcoffset() is None
    ):
        raise ValueError("now must be a timezone-aware datetime.")

    resolved_market_type = market_type.strip().lower() if isinstance(market_type, str) else None
    if resolved_market_type is None and isinstance(symbol, str) and symbol.strip():
        try:
            resolved_market_type = get_market_type(normalize_symbol(symbol))
        except (TypeError, ValueError):
            resolved_market_type = None
    return reference.astimezone(timezone.utc).weekday() >= 5 and resolved_market_type != "crypto"


def evaluate_market_status(
    candles,
    timeframe: str = "M15",
    *,
    symbol: str | None = None,
    market_type: str | None = None,
    now: datetime | None = None,
) -> MarketStatus:
    """Evaluate market availability from validated candle context.

    Status values are intentionally limited to ``OPEN``, ``CLOSED``, ``STALE``,
    and ``NO_DATA``. Weekend closure is applied only to markets that observe a
    weekend session break; 24/7 crypto is not classified as CLOSED merely
    because the calendar day is Saturday or Sunday.
    """
    reference = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(reference, datetime) or reference.tzinfo is None or reference.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime.")
    reference = reference.astimezone(timezone.utc)

    if is_market_weekend_closed(symbol=symbol, market_type=market_type, now=reference):
        last_candle_time = _parse_last_candle_time(candles[-1]) if candles else None
        return MarketStatus(status=CLOSED, last_candle_time=last_candle_time)

    if not candles:
        return MarketStatus(status=NO_DATA)

    try:
        normalized_timeframe = normalize_timeframe(timeframe)
        candle_time = _parse_last_candle_time(candles[-1])
    except (TypeError, ValueError):
        return MarketStatus(status=NO_DATA)

    if candle_time is None:
        return MarketStatus(status=NO_DATA)

    if candle_time > reference:
        return MarketStatus(status=NO_DATA, last_candle_time=candle_time)

    age = reference - candle_time
    if age > _stale_after(normalized_timeframe):
        return MarketStatus(status=STALE, last_candle_time=candle_time)

    return MarketStatus(status=OPEN, last_candle_time=candle_time)


__all__ = [
    "MarketStatus",
    "OPEN",
    "CLOSED",
    "STALE",
    "NO_DATA",
    "is_market_weekend_closed",
    "evaluate_market_status",
]
