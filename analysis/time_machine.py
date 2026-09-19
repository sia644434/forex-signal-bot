from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from analysis.counterfactual_engine import CounterfactualEngine
from analysis.full_engine import FullAnalysisEngine
from analysis.candle import Candle


@dataclass(frozen=True, slots=True)
class TimeMachineStep:
    index: int
    timestamp: str
    signal: str
    score: float
    confidence: float
    counterfactual: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "signal": self.signal,
            "score": self.score,
            "confidence": self.confidence,
            "counterfactual": self.counterfactual,
        }


class TimeMachineEngine:
    """Deterministic historical replay + what-if orchestration.

    The engine never uses future candles for a historical step. Each step is
    evaluated only from the prefix ending at that timestamp.
    """

    def __init__(self) -> None:
        self.analysis = FullAnalysisEngine()
        self.counterfactual = CounterfactualEngine()

    @staticmethod
    def _candle(item: dict[str, Any]) -> Candle:
        timestamp = item.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise ValueError("time-machine timestamps must be timezone-aware")
        return Candle(
            symbol=str(item.get("symbol", "UNKNOWN")),
            timestamp=timestamp,
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume", 0.0)),
        )

    def run(
        self,
        candles: list[dict[str, Any]],
        *,
        start_index: int = 5,
        step: int = 1,
        counterfactual: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(candles, list) or len(candles) < 5:
            raise ValueError("at least five candles are required")
        if start_index < 5 or start_index > len(candles):
            raise ValueError("start_index is outside the valid replay range")
        if step < 1:
            raise ValueError("step must be greater than zero")

        parsed = [self._candle(item) for item in candles]
        what_if = counterfactual or {}
        steps: list[dict[str, Any]] = []

        for end in range(start_index, len(parsed) + 1, step):
            report = self.analysis.analyze(parsed[:end])
            result = self.counterfactual.evaluate(
                report.signal,
                confidence=report.confidence,
                conflict=bool(what_if.get("conflict", False)),
                risk_valid=bool(what_if.get("risk_valid", True)),
            )
            steps.append(
                TimeMachineStep(
                    index=end - 1,
                    timestamp=parsed[end - 1].timestamp.isoformat(),
                    signal=report.signal,
                    score=float(report.score),
                    confidence=float(report.confidence),
                    counterfactual=result.summary(),
                ).summary()
            )

        return {
            "candles": len(parsed),
            "start_index": start_index,
            "step": step,
            "steps": len(steps),
            "trace": steps,
        }


__all__ = ["TimeMachineEngine", "TimeMachineStep"]
