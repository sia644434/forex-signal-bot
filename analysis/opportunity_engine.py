from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Opportunity:
    symbol: str
    score: float
    rank: int
    rationale: tuple[str, ...]


class OpportunityEngine:
    """Explainable, sample-aware and risk-aware ranking for scanner results."""

    @staticmethod
    def rank(results: Iterable[object]) -> list[Opportunity]:
        candidates = []
        for item in results:
            symbol = str(getattr(item, "symbol", "")).strip()
            signal = str(getattr(item, "signal", "NO_TRADE")).upper()
            confidence = float(getattr(item, "confidence", 0.0))
            quality = getattr(item, "trade_quality", None)
            rr = getattr(item, "risk_reward", None)
            if not symbol or not math.isfinite(confidence):
                continue
            confidence = max(0.0, min(1.0, confidence))
            quality_value = 0.0 if quality is None else max(0.0, min(100.0, float(quality)))
            rr_value = 0.0 if rr is None or not math.isfinite(float(rr)) else max(0.0, min(10.0, float(rr)))
            sample = getattr(item, "sample_size", getattr(item, "sample", None))
            sample_value = 0.0 if sample is None else max(0.0, float(sample))
            risk = str(getattr(item, "risk_level", getattr(item, "macro_risk_level", "NORMAL"))).upper()
            executable = signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}
            score = (confidence * 50.0) + (quality_value * 0.35) + (min(rr_value, 5.0) * 3.0)
            sample_factor = min(1.0, sample_value / 50.0) if sample is not None else 0.75
            risk_factor = 0.35 if risk in {"CRISIS", "EXTREME"} else 0.70 if risk in {"HIGH", "ELEVATED"} else 1.0
            score *= sample_factor * risk_factor
            rationale = []
            if executable:
                rationale.append("executable directional signal")
            else:
                score *= 0.25
                rationale.append("non-executable state")
            if quality is not None:
                rationale.append(f"trade quality={quality_value:.1f}")
            if rr is not None:
                rationale.append(f"risk/reward={rr_value:.2f}")
            if sample is not None:
                rationale.append(f"sample={sample_value:.0f}")
            if risk != "NORMAL":
                rationale.append(f"risk={risk}")
            candidates.append((symbol, score, tuple(rationale)))
        candidates.sort(key=lambda item: (-item[1], item[0]))
        return [Opportunity(symbol, round(score, 2), index + 1, rationale) for index, (symbol, score, rationale) in enumerate(candidates)]

    @staticmethod
    def heatmap(results: Iterable[object]) -> list[dict[str, object]]:
        ranked = OpportunityEngine.rank(results)
        return [
            {
                "symbol": item.symbol,
                "rank": item.rank,
                "opportunity_score": item.score,
                "strength": "HIGH" if item.score >= 70 else "MEDIUM" if item.score >= 40 else "LOW",
                "rationale": list(item.rationale),
            }
            for item in ranked
        ]
