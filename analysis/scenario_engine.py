from __future__ import annotations

from dataclasses import dataclass
import math

BULLISH = "BULLISH"
BEARISH = "BEARISH"
NEUTRAL = "NEUTRAL"
BREAKOUT = "BREAKOUT"
FALSE_BREAKOUT = "FALSE_BREAKOUT"
REVERSAL = "REVERSAL"
CONTINUATION = "CONTINUATION"
HIGH_VOLATILITY = "HIGH_VOLATILITY"
LIQUIDITY_FAILURE = "LIQUIDITY_FAILURE"
NO_TRADE = "NO_TRADE"


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    primary: str
    alternatives: tuple[str, ...]
    evidence: tuple[str, ...]
    confidence: float

    def summary(self) -> dict[str, object]:
        return {"primary": self.primary, "alternatives": list(self.alternatives), "evidence": list(self.evidence), "confidence": self.confidence}


class ScenarioEngine:
    """Builds explicit, traceable scenarios from observed price behavior."""

    def evaluate(self, prices: list[float], trend: str = "neutral", volatility: float = 0.0) -> ScenarioResult:
        if len(prices) < 5:
            raise ValueError("at least five prices are required")
        values = [float(x) for x in prices]
        if not all(math.isfinite(x) and x > 0 for x in values):
            raise ValueError("prices must be finite and greater than zero")
        vol = float(volatility)
        if not math.isfinite(vol) or vol < 0:
            raise ValueError("volatility must be finite and non-negative")

        change = values[-1] / values[-2] - 1.0
        window_high = max(values[-5:-1])
        window_low = min(values[-5:-1])
        evidence: list[str] = []
        alternatives: list[str] = []
        direction = str(trend).lower()
        if values[-1] > window_high:
            primary = BREAKOUT
            evidence.append("price broke above the recent range")
            alternatives.append(CONTINUATION if direction == "bullish" else FALSE_BREAKOUT)
        elif values[-1] < window_low:
            primary = BREAKOUT
            evidence.append("price broke below the recent range")
            alternatives.append(CONTINUATION if direction == "bearish" else FALSE_BREAKOUT)
        elif direction == "bullish":
            primary = BULLISH
            alternatives.append(CONTINUATION)
        elif direction == "bearish":
            primary = BEARISH
            alternatives.append(CONTINUATION)
        else:
            primary = NEUTRAL
            alternatives.append(REVERSAL)

        if vol > 0.03:
            alternatives.insert(0, HIGH_VOLATILITY)
            evidence.append("observed volatility exceeds the conservative high-volatility threshold")
        if abs(change) > 0.05:
            evidence.append("latest return is unusually large")
        confidence = min(1.0, 0.5 + min(0.4, abs(change) * 5.0) + (0.1 if primary == BREAKOUT else 0.0))
        return ScenarioResult(primary, tuple(dict.fromkeys(alternatives)), tuple(evidence), round(confidence, 3))
