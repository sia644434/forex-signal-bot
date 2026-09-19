from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math

FRESH = "FRESH"
AGING = "AGING"
STALE = "STALE"
INVALID = "INVALID"
NORMAL = "NORMAL"
ELEVATED = "ELEVATED"
CRISIS = "CRISIS"
EXTREME = "EXTREME"


@dataclass(frozen=True, slots=True)
class SignalState:
    decay: str
    crisis_mode: str
    age_seconds: float
    reasons: tuple[str, ...]


def evaluate_signal_state(
    created_at: datetime,
    *,
    now: datetime | None = None,
    max_age_seconds: float = 60.0,
    volatility: float = 0.0,
) -> SignalState:
    if created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    if max_age_seconds <= 0 or not math.isfinite(max_age_seconds):
        raise ValueError("max_age_seconds must be finite and positive")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    age = (current - created_at).total_seconds()
    if age < 0:
        return SignalState(INVALID, EXTREME, age, ("signal timestamp is in the future",))
    if age <= max_age_seconds:
        decay = FRESH
    elif age <= max_age_seconds * 3:
        decay = AGING
    else:
        decay = STALE

    vol = float(volatility)
    if not math.isfinite(vol) or vol < 0:
        raise ValueError("volatility must be finite and non-negative")
    if vol >= 0.10:
        crisis = EXTREME
    elif vol >= 0.06:
        crisis = CRISIS
    elif vol >= 0.03:
        crisis = ELEVATED
    else:
        crisis = NORMAL
    reasons = []
    if decay != FRESH:
        reasons.append(f"signal decay state is {decay}")
    if crisis != NORMAL:
        reasons.append(f"crisis mode is {crisis}")
    return SignalState(decay, crisis, age, tuple(reasons))
