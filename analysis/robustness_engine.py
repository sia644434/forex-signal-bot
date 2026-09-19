from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True, slots=True)
class RobustnessCase:
    threshold: float
    fee: float
    return_value: float
    max_drawdown: float
    trades: int


class RobustnessEngine:
    """Deterministic, model-free robustness and temporal leakage checks."""

    @staticmethod
    def _validate_prices(prices: Iterable[float]) -> np.ndarray:
        values = np.asarray(list(prices), dtype=float)
        if values.ndim != 1 or len(values) < 4 or not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("at least four finite positive prices are required")
        return values

    @classmethod
    def evaluate(
        cls,
        prices: Iterable[float],
        *,
        thresholds: Iterable[float] = (0.0, 0.001, 0.002),
        fees: Iterable[float] = (0.0, 0.0001, 0.0002),
    ) -> dict[str, Any]:
        values = cls._validate_prices(prices)
        cases: list[RobustnessCase] = []
        for raw_threshold in thresholds:
            threshold = float(raw_threshold)
            if not np.isfinite(threshold) or threshold < 0:
                raise ValueError("thresholds must be finite and non-negative")
            returns = np.diff(values) / values[:-1]
            previous = np.concatenate(([0.0], returns[:-1]))
            signal = np.sign(previous)
            signal[np.abs(previous) < threshold] = 0.0
            for raw_fee in fees:
                fee = float(raw_fee)
                if not np.isfinite(fee) or fee < 0 or fee >= 1:
                    raise ValueError("fees must be finite and in [0, 1)")
                strategy = signal * returns - fee * np.abs(signal)
                equity = np.cumprod(1.0 + strategy)
                if not np.isfinite(equity).all() or (equity <= 0).any():
                    raise ValueError("robustness case produced invalid equity")
                drawdown = float(np.min(equity / np.maximum.accumulate(equity) - 1.0))
                cases.append(RobustnessCase(
                    threshold=threshold,
                    fee=fee,
                    return_value=float(equity[-1] - 1.0),
                    max_drawdown=drawdown,
                    trades=int(np.count_nonzero(signal)),
                ))
        returns = np.asarray([case.return_value for case in cases], dtype=float)
        drawdowns = np.asarray([case.max_drawdown for case in cases], dtype=float)
        positive = int(np.count_nonzero(returns > 0))
        return {
            "cases": [case.__dict__ if hasattr(case, "__dict__") else {
                "threshold": case.threshold, "fee": case.fee,
                "return": case.return_value, "max_drawdown": case.max_drawdown,
                "trades": case.trades,
            } for case in cases],
            "case_count": len(cases),
            "positive_case_ratio": float(positive / len(cases)),
            "return_range": float(np.max(returns) - np.min(returns)),
            "drawdown_range": float(np.max(drawdowns) - np.min(drawdowns)),
            "robust": bool(positive > 0 and np.median(returns) > 0),
        }

    @staticmethod
    def temporal_leakage_check(rows: list[dict[str, Any]], *, feature_time: str = "feature_timestamp", target_time: str = "target_timestamp") -> dict[str, Any]:
        violations = []
        for index, row in enumerate(rows):
            if feature_time not in row or target_time not in row:
                raise ValueError("each row must contain feature and target timestamps")
            feature = str(row[feature_time])
            target = str(row[target_time])
            if feature > target:
                violations.append({"index": index, "feature_timestamp": feature, "target_timestamp": target})
        return {"checked": len(rows), "violations": violations, "leakage_detected": bool(violations)}


__all__ = ["RobustnessCase", "RobustnessEngine"]
