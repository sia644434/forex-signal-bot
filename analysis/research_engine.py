from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True, slots=True)
class ResearchCase:
    threshold: float
    fee: float
    train_return: float
    test_return: float
    test_drawdown: float
    trades: int


class ResearchValidationEngine:
    """Deterministic out-of-sample, walk-forward and overfitting diagnostics."""

    @staticmethod
    def _prices(prices: Iterable[float]) -> np.ndarray:
        values = np.asarray(list(prices), dtype=float)
        if values.ndim != 1 or len(values) < 12 or not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("at least twelve finite positive prices are required")
        return values

    @staticmethod
    def _validate_params(thresholds: Iterable[float], fees: Iterable[float]) -> tuple[list[float], list[float]]:
        ts, fs = [], []
        for value in thresholds:
            value = float(value)
            if not np.isfinite(value) or value < 0:
                raise ValueError("thresholds must be finite and non-negative")
            ts.append(value)
        for value in fees:
            value = float(value)
            if not np.isfinite(value) or value < 0 or value >= 1:
                raise ValueError("fees must be finite and in [0, 1)")
            fs.append(value)
        if not ts or not fs:
            raise ValueError("thresholds and fees must not be empty")
        return ts, fs

    @staticmethod
    def _evaluate(returns: np.ndarray, threshold: float, fee: float) -> dict[str, float | int]:
        previous = np.concatenate(([0.0], returns[:-1]))
        signal = np.sign(previous)
        signal[np.abs(previous) < threshold] = 0.0
        strategy = signal * returns - fee * np.abs(signal)
        equity = np.cumprod(1.0 + strategy)
        if not np.isfinite(equity).all() or (equity <= 0).any():
            raise ValueError("research case produced invalid equity")
        return {
            "return": float(equity[-1] - 1.0),
            "drawdown": float(np.min(equity / np.maximum.accumulate(equity) - 1.0)),
            "trades": int(np.count_nonzero(signal)),
        }

    @classmethod
    def out_of_sample(
        cls,
        prices: Iterable[float],
        *,
        train_ratio: float = 0.7,
        thresholds: Iterable[float] = (0.0, 0.001, 0.002),
        fees: Iterable[float] = (0.0, 0.0001, 0.0002),
    ) -> dict[str, Any]:
        values = cls._prices(prices)
        if not 0 < float(train_ratio) < 1:
            raise ValueError("train_ratio must be between zero and one")
        ts, fs = cls._validate_params(thresholds, fees)
        split = int(len(values) * float(train_ratio))
        if split < 4 or len(values) - split < 4:
            raise ValueError("train and test partitions are too small")
        train_returns = np.diff(values[: split + 1]) / values[:split]
        test_returns = np.diff(values[split - 1:]) / values[split - 1:-1]
        candidates = []
        for threshold in ts:
            for fee in fs:
                train = cls._evaluate(train_returns, threshold, fee)
                candidates.append((float(train["return"]), threshold, fee, train))
        candidates.sort(key=lambda item: item[0], reverse=True)
        _, threshold, fee, train = candidates[0]
        test = cls._evaluate(test_returns, threshold, fee)
        return {
            "split_index": split,
            "train_size": len(train_returns),
            "test_size": len(test_returns),
            "selected": {"threshold": threshold, "fee": fee},
            "train": train,
            "out_of_sample": test,
            "oos_positive": bool(float(test["return"]) > 0),
            "train_test_gap": float(float(train["return"]) - float(test["return"])),
            "parameter_count": len(candidates),
        }

    @classmethod
    def walk_forward(
        cls,
        prices: Iterable[float],
        *,
        train_size: int = 40,
        test_size: int = 10,
        thresholds: Iterable[float] = (0.0, 0.001, 0.002),
        fees: Iterable[float] = (0.0, 0.0001, 0.0002),
    ) -> dict[str, Any]:
        values = cls._prices(prices)
        if train_size < 4 or test_size < 2:
            raise ValueError("train_size must be >= 4 and test_size >= 2")
        ts, fs = cls._validate_params(thresholds, fees)
        windows = []
        start = 0
        while start + train_size + test_size <= len(values):
            train_values = values[start:start + train_size + 1]
            test_values = values[start + train_size:start + train_size + test_size + 1]
            train_returns = np.diff(train_values) / train_values[:-1]
            test_returns = np.diff(test_values) / test_values[:-1]
            candidates = []
            for threshold in ts:
                for fee in fs:
                    train = cls._evaluate(train_returns, threshold, fee)
                    candidates.append((float(train["return"]), threshold, fee, train))
            candidates.sort(key=lambda item: item[0], reverse=True)
            _, threshold, fee, train = candidates[0]
            test = cls._evaluate(test_returns, threshold, fee)
            windows.append({
                "start": start,
                "selected": {"threshold": threshold, "fee": fee},
                "train": train,
                "out_of_sample": test,
                "train_test_gap": float(train["return"] - test["return"]),
            })
            start += test_size
        if not windows:
            raise ValueError("dataset is too small for one walk-forward window")
        oos = np.asarray([float(w["out_of_sample"]["return"]) for w in windows])
        positive = int(np.count_nonzero(oos > 0))
        gaps = np.asarray([float(w["train_test_gap"]) for w in windows])
        return {
            "windows": len(windows),
            "positive_oos_ratio": float(positive / len(windows)),
            "median_oos_return": float(np.median(oos)),
            "train_test_gap_median": float(np.median(gaps)),
            "results": windows,
        }

    @classmethod
    def overfitting_diagnostics(cls, result: dict[str, Any], *, max_gap: float = 0.10, min_positive_oos_ratio: float = 0.5) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ValueError("result must be a mapping")
        gap = float(result.get("train_test_gap_median", result.get("train_test_gap", 0.0)))
        ratio = float(result.get("positive_oos_ratio", 1.0 if result.get("oos_positive") else 0.0))
        if not np.isfinite(gap) or not np.isfinite(ratio) or max_gap < 0 or not 0 <= min_positive_oos_ratio <= 1:
            raise ValueError("diagnostic thresholds are invalid")
        warnings = []
        if gap > max_gap:
            warnings.append("TRAIN_TEST_DIVERGENCE")
        if ratio < min_positive_oos_ratio:
            warnings.append("WEAK_OOS_STABILITY")
        return {
            "overfitting_warning": bool(warnings),
            "warnings": warnings,
            "train_test_gap": gap,
            "positive_oos_ratio": ratio,
        }

    @staticmethod
    def temporal_leakage_check(rows: list[dict[str, Any]], *, feature_time: str = "feature_timestamp", target_time: str = "target_timestamp") -> dict[str, Any]:
        violations = []
        for index, row in enumerate(rows):
            if feature_time not in row or target_time not in row:
                raise ValueError("each row must contain feature and target timestamps")
            if str(row[feature_time]) > str(row[target_time]):
                violations.append({"index": index, "feature_timestamp": str(row[feature_time]), "target_timestamp": str(row[target_time])})
        return {"checked": len(rows), "violations": violations, "leakage_detected": bool(violations)}


__all__ = ["ResearchCase", "ResearchValidationEngine"]
