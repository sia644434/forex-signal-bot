from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    baseline_decision: str
    changed_decision: str
    changed_conditions: tuple[str, ...]
    explanation: str

    def summary(self) -> dict[str, object]:
        return {
            "baseline_decision": self.baseline_decision,
            "changed_decision": self.changed_decision,
            "changed_conditions": list(self.changed_conditions),
            "explanation": self.explanation,
        }


class CounterfactualEngine:
    """Traceable what-if analysis; it never invents market data."""

    def evaluate(
        self,
        baseline_decision: str,
        *,
        confidence: float,
        conflict: bool = False,
        risk_valid: bool = True,
    ) -> CounterfactualResult:
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        conditions: list[str] = []
        changed = str(baseline_decision)
        if not risk_valid:
            changed = "NO_TRADE"
            conditions.append("risk_valid=false")
        elif conflict or confidence < 0.30:
            changed = "WAIT"
            conditions.append("evidence became insufficient or conflicting")
        explanation = "Decision is unchanged under the supplied counterfactual conditions."
        if conditions:
            explanation = "The decision changes because " + "; ".join(conditions) + "."
        return CounterfactualResult(str(baseline_decision), changed, tuple(conditions), explanation)
