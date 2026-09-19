from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


STATUSES = {"CANDIDATE", "CHAMPION", "CHALLENGER", "RETIRED", "PAUSED"}


@dataclass(frozen=True, slots=True)
class StrategyValidationEvidence:
    oos_positive: bool
    positive_oos_ratio: float
    overfitting_warning: bool = False
    leakage_detected: bool = False
    robust: bool = False
    source: str = "research_validation"

    def __post_init__(self) -> None:
        if not 0 <= float(self.positive_oos_ratio) <= 1:
            raise ValueError("positive_oos_ratio must be between 0 and 1")
        if not self.source.strip():
            raise ValueError("validation source is required")
        if self.leakage_detected:
            raise ValueError("validation evidence with temporal leakage cannot be accepted")


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
@dataclass(frozen=True, slots=True)
class StrategyAuditEvent:
    action: str
    strategy_id: str
    reason: str
    from_version: int
    to_version: int
    metadata: dict[str, Any] = field(default_factory=dict)


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
    dna_history: list[dict[str, Any]] = field(default_factory=list)
    audit_log: list[StrategyAuditEvent] = field(default_factory=list)
    validation_evidence: StrategyValidationEvidence | None = None

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
        self._audit: list[StrategyAuditEvent] = []

    def register(self, strategy_id: str, name: str, dna: dict[str, Any] | None = None, *, parent_id: str | None = None) -> StrategyRecord:
        if not strategy_id.strip() or strategy_id in self._records:
            raise ValueError("strategy_id must be unique and non-empty")
        initial_dna = dict(dna or {})
        record = StrategyRecord(
            strategy_id=strategy_id,
            name=name,
            dna=initial_dna,
            parent_id=parent_id,
            dna_history=[dict(initial_dna)],
        )
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

    def attach_validation(self, strategy_id: str, evidence: StrategyValidationEvidence) -> dict[str, Any]:
        record = self._records[strategy_id]
        if evidence.overfitting_warning or evidence.leakage_detected:
            raise ValueError("strategy validation evidence is not admissible")
        record.validation_evidence = evidence
        return {"strategy_id": strategy_id, "oos_positive": evidence.oos_positive, "positive_oos_ratio": evidence.positive_oos_ratio, "robust": evidence.robust, "source": evidence.source}

    def compare(self, champion_id: str, challenger_id: str) -> dict[str, Any]:
        champion = self._records[champion_id]
        challenger = self._records[challenger_id]
        cp, xp = champion.performance(), challenger.performance()
        comparable = min(cp["sample"], xp["sample"]) >= 20
        champion_validation = champion.validation_evidence
        challenger_validation = challenger.validation_evidence
        validation_ready = (
            champion_validation is not None
            and challenger_validation is not None
            and champion_validation.oos_positive
            and challenger_validation.oos_positive
            and champion_validation.positive_oos_ratio >= 0.5
            and challenger_validation.positive_oos_ratio >= 0.5
            and champion_validation.robust
            and challenger_validation.robust
        )
        challenger_wins = (
            comparable
            and validation_ready
            and xp["score"] > cp["score"]
            and abs(xp["drawdown"]) <= abs(cp["drawdown"])
        )
        return {
            "champion": champion_id,
            "challenger": challenger_id,
            "comparable": comparable,
            "validation_ready": validation_ready,
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
        before = self._records[challenger_id].version
        self._records[challenger_id].version += 1
        event = StrategyAuditEvent(
            "PROMOTE",
            challenger_id,
            "eligible challenger promoted",
            before,
            self._records[challenger_id].version,
            {"previous_champion": champion_id},
        )
        self._records[challenger_id].audit_log.append(event)
        self._audit.append(event)
        return result


    def weaknesses(self, strategy_id: str, *, min_sample: int = 20) -> list[dict[str, Any]]:
        if min_sample < 1:
            raise ValueError("min_sample must be positive")
        record = self._records[strategy_id]
        groups: dict[tuple[str, str, str, str], list[StrategyObservation]] = {}
        for observation in record.observations:
            key = (observation.market, observation.symbol, observation.timeframe, observation.regime)
            groups.setdefault(key, []).append(observation)
        result: list[dict[str, Any]] = []
        for key, observations in groups.items():
            sample = sum(o.trades for o in observations)
            if sample < min_sample:
                continue
            weight = sum(max(o.trades, 1) for o in observations)
            expectancy = sum(o.expectancy * max(o.trades, 1) for o in observations) / weight
            drawdown = sum(o.max_drawdown * max(o.trades, 1) for o in observations) / weight
            reasons = []
            if expectancy < 0:
                reasons.append("negative_expectancy")
            if abs(drawdown) >= 0.10:
                reasons.append("elevated_drawdown")
            if reasons:
                result.append({
                    "market": key[0], "symbol": key[1], "timeframe": key[2], "regime": key[3],
                    "sample": sample, "expectancy": expectancy, "drawdown": drawdown,
                    "reasons": reasons,
                })
        return sorted(result, key=lambda item: (item["expectancy"], item["drawdown"]))

    def adapt(self, strategy_id: str, dna_changes: dict[str, Any], *, reason: str) -> dict[str, Any]:
        if not isinstance(dna_changes, dict) or not dna_changes:
            raise ValueError("dna_changes must be a non-empty mapping")
        if not reason.strip():
            raise ValueError("adaptation reason is required")
        record = self._records[strategy_id]
        before = record.version
        record.dna_history.append(dict(record.dna))
        record.dna.update(dna_changes)
        record.version += 1
        event = StrategyAuditEvent("ADAPT", strategy_id, reason, before, record.version, {"changes": dict(dna_changes)})
        record.audit_log.append(event)
        self._audit.append(event)
        return {"strategy_id": strategy_id, "version": record.version, "dna": dict(record.dna), "reason": reason}

    def continuous_evaluate(self) -> list[dict[str, Any]]:
        return [self.evaluate(strategy_id) for strategy_id in self._records]

    def rollback(self, strategy_id: str, *, reason: str) -> dict[str, Any]:
        if not reason.strip():
            raise ValueError("rollback reason is required")
        record = self._records[strategy_id]
        if not record.dna_history:
            raise ValueError("no prior DNA version is available")
        previous = dict(record.dna_history.pop())
        before = record.version
        record.dna = previous
        record.version += 1
        event = StrategyAuditEvent("ROLLBACK", strategy_id, reason, before, record.version, {"restored_version": before - 1})
        record.audit_log.append(event)
        self._audit.append(event)
        return {"strategy_id": strategy_id, "version": record.version, "dna": dict(record.dna), "reason": reason}

    def retire(self, strategy_id: str, reason: str) -> None:
        if not reason.strip():
            raise ValueError("retirement reason is required")
        record = self._records[strategy_id]
        before = record.version
        record.status = "RETIRED"
        record.retirement_reason = reason
        event = StrategyAuditEvent("RETIRE", strategy_id, reason, before, record.version)
        record.audit_log.append(event)
        self._audit.append(event)

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(record) for record in self._records.values()]


__all__ = ["StrategyObservation", "StrategyValidationEvidence", "StrategyRecord", "StrategyAuditEvent", "StrategyIntelligenceEngine"]
