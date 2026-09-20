from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping


BULLISH_THRESHOLD = 55.0
BEARISH_THRESHOLD = 45.0


@dataclass(frozen=True)
class DirectionalEvidence:
    """Canonical directional interpretation shared by scoring and confidence."""

    raw_score: float
    normalized_score: float
    direction: str
    strength: float


def normalize_signed_score(score: float) -> float:
    value = float(score)
    if not isfinite(value):
        raise ValueError("directional score must be numeric and finite")
    value = max(-100.0, min(100.0, value))
    return ((value + 100.0) / 200.0) * 100.0


def classify_direction(normalized_score: float) -> str:
    value = float(normalized_score)
    if not isfinite(value):
        raise ValueError("normalized directional score must be numeric and finite")
    if value >= BULLISH_THRESHOLD:
        return "bullish"
    if value <= BEARISH_THRESHOLD:
        return "bearish"
    return "neutral"


def evidence(score: float) -> DirectionalEvidence:
    normalized = normalize_signed_score(score)
    return DirectionalEvidence(
        raw_score=float(score),
        normalized_score=normalized,
        direction=classify_direction(normalized),
        strength=abs(normalized - 50.0) / 50.0,
    )


def combined_structure_score(structure_score: float, trend_score: float) -> float:
    """Blend local structure with trend context without treating trend as a second vote.

    BOS/structure is the local structural event; trend is contextual state. A
    70/30 blend prevents an opposing trend from mechanically cancelling a fresh
    structural break while still making the conflict visible in the score.
    """

    structure = float(structure_score)
    trend = float(trend_score)
    if not isfinite(structure) or not isfinite(trend):
        raise ValueError("Market Structure score became non-finite")
    if abs(structure) > 100.0 or abs(trend) > 100.0:
        raise ValueError("Market Structure score became non-finite")
    combined = (structure * 0.70) + (trend * 0.30)
    if not isfinite(combined):
        raise ValueError("Market Structure score became non-finite")
    return combined


def component_directions(components: Mapping[str, float]) -> dict[str, DirectionalEvidence]:
    return {name: evidence(score) for name, score in components.items()}


def vote_counts(components: Mapping[str, float]) -> tuple[int, int, int]:
    readings = component_directions(components).values()
    bullish = sum(item.direction == "bullish" for item in readings)
    bearish = sum(item.direction == "bearish" for item in readings)
    neutral = sum(item.direction == "neutral" for item in readings)
    return bullish, bearish, neutral


def conflict_state(components: Mapping[str, float]) -> str:
    bullish, bearish, _ = vote_counts(components)
    if bullish and bearish:
        return "STRONG_CONFLICT" if min(bullish, bearish) >= 3 else "CONFLICT"
    if max(bullish, bearish) >= 3:
        return "CONSENSUS"
    if bullish or bearish:
        return "WEAK_CONSENSUS"
    return "INSUFFICIENT_EVIDENCE"
