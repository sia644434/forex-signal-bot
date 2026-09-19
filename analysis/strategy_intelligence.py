from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


STATUSES = {"CANDIDATE", "CHAMPION", "CHALLENGER", "RETIRED", "PAUSED"}


@dataclass(frozen=True, slots=True)
class StrategyObservation:
    market: str
    symbol: str
    timeframe: str
    regime: str
    trades: int
    win_rate: float
    expectancy: float
    max_drawdown: float
    sample_quality: float = 1.0

    def __post_init__(self) -> None:
        if self.trades < 0:
            raise ValueError("trades must be non-negative")
        for name, value in {
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "max_drawdown": self.max_drawdown,
            "sample_quality": self.sample_quality,
        }.items():
            if not isinstance(value, (int, float)) or not (-1e9 < float(value) < 1e9):
                raise ValueError(f"{name} must be finite")
        if not 0 <= self.win_rate <= 1:
            raise ValueError("win_rate must be between 0 and 1")
        if not 0 <= self.sample_quality <= 1:
            raise ValueError("sample_quality must be between 0 and 1")


@dataclass
class StrategyRecord:
    strategy_id: str
    name: str
    status: str = "CANDIDATE"
    dna: dict[str, Any] = field(default_factory=dict)
    observations: list[StrategyObservation] = field(default_factory=list)
    parent_id: str | None = None
    version: int = 1
    retirement_reason: str | None = None

    def add_observation(self, observation: StrategyObservation) -> None:
        self.observations.append(observation)

    def performance(self) -> dict[str, float]:
        if not self.observations:
            return {"score": 0.0, "sample": 0.0, "drawdown": 0.0, "expectancy": 0.0}
        total = sum(max(o.trades, 1) for o in self.observations)
        weight = sum(max(o.trades, 1) * o.sample_quality for o in self.observations)
        expectancy = sum(o.expectancy * max(o.trades, 1) for o in self.observations) / total
        drawdown = sum(o.max_drawdown * max(o.trades, 1) for o in self.observations) / total
        score = (expectancy * 0.6 + sum(o.win_rate * max(o.trades, 1) for o in self.observations) / total * 0.4)
        return {"score": score * max(min(weight / total, 1.0), 0.0), "sample": float(sum(o.trades for o in self.observations)), "drawdown": drawdown, "expectancy": expectancy}


class StrategyIntelligenceEngine:
    """Auditable strategy lifecycle and champion/challenger registry."""

    def __init__(self) -> None:
        self._records: dict[str, StrategyRecord] = {}

    def register(self, strategy_id: str, name: str, dna: dict[str, Any] | None = None, *, parent_id: str | None = None) -> StrategyRecord:
        if not strategy_id.strip() or strategy_id in self._records:
            raise ValueError("strategy_id must be unique and non-empty")
        record = StrategyRecord(strategy_id=strategy_id, name=name, dna=dna or {}, parent_id=parent_id)
        self._records[strategy_id] = record
        return record

    def observe(self, strategy_id: str, observation: StrategyObservation) -> dict[str, Any]:
        record = self._records[strategy_id]
        record.add_observation(observation)
        return self.evaluate(strategy_id)

    def evaluate(self, strategy_id: str) -> dict[str, Any]:
        record = self._records[strategy_id]
        perf = record.performance()
        if record.status == "RETIRED":
            return {"strategy_id": strategy_id, "status": record.status, "performance": perf}
        if perf["sample"] >= 20 and perf["expectancy"] < 0:
            record.status = "PAUSED"
        elif perf["sample"] >= 50 and perf["expectancy"] > 0:
            record.status = "CHALLENGER"
        return {"strategy_id": strategy_id, "status": record.status, "performance": perf}

    def compare(self, champion_id: str, challenger_id: str) -> dict[str, Any]:
        champion = self._records[champion_id]
        challenger = self._records[challenger_id]
        cp, xp = champion.performance(), challenger.performance()
        comparable = min(cp["sample"], xp["sample"]) >= 20
        challenger_wins = comparable and xp["score"] > cp["score"] and abs(xp["drawdown"]) <= abs(cp["drawdown"])
        return {
            "champion": champion_id,
            "challenger": challenger_id,
            "comparable": comparable,
            "challenger_eligible": challenger_wins,
            "champion_performance": cp,
            "challenger_performance": xp,
            "reason": "sample_and_risk_adjusted_metrics_support challenger review" if challenger_wins else "insufficient or non-superior evidence",
        }

    def promote(self, champion_id: str, challenger_id: str) -> dict[str, Any]:
        result = self.compare(champion_id, challenger_id)
        if not result["challenger_eligible"]:
            raise ValueError("challenger is not eligible for promotion")
        self._records[champion_id].status = "RETIRED"
        self._records[challenger_id].status = "CHAMPION"
        self._records[challenger_id].version += 1
        return result

    def retire(self, strategy_id: str, reason: str) -> None:
        if not reason.strip():
            raise ValueError("retirement reason is required")
        record = self._records[strategy_id]
        record.status = "RETIRED"
        record.retirement_reason = reason

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(record) for record in self._records.values()]


__all__ = ["StrategyObservation", "StrategyRecord", "StrategyIntelligenceEngine"]
