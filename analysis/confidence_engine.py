from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from analysis.directional_contract import classify_direction, combined_structure_score, normalize_signed_score


@dataclass(frozen=True)
class ConfidenceResult:
    """Professional confidence evaluation result."""

    confidence: float
    agreement: float
    bullish_votes: int
    bearish_votes: int
    neutral_votes: int
    weighted_bullish: float = 0.0
    weighted_bearish: float = 0.0
    weighted_neutral: float = 0.0
    data_quality: float = 1.0
    market_uncertainty: float = 0.0
    conflict_score: float = 0.0
    warnings: list[str] = field(default_factory=list)


class ConfidenceEngine:
    """Evaluate reliability of multi-engine market analysis."""

    WEIGHTS = {
        "smart_money": 2.00,
        "structure": 1.80,
        "price_action": 1.50,
        "momentum": 1.30,
        "supply_demand": 1.30,
        "candlestick": 1.10,
        "elliott": 1.00,
        "harmonic": 1.00,
        "brooks": 0.90,
        "wyckoff": 1.10,
    }

    BULLISH_THRESHOLD = 55.0
    BEARISH_THRESHOLD = 45.0
    HIGH_AGREEMENT = 0.80
    MEDIUM_AGREEMENT = 0.60
    LOW_AGREEMENT = 0.50

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        candidate = weights.copy() if weights is not None else self.WEIGHTS.copy()
        self.weights: dict[str, float] = {}
        for name, weight in candidate.items():
            try:
                value = float(weight)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"weight for {name!r} must be finite") from exc
            if not isfinite(value):
                raise ValueError(f"weight for {name!r} must be finite")
            if value < 0.0:
                raise ValueError(f"weight for {name!r} must be non-negative")
            self.weights[name] = value

    @staticmethod
    def _finite(value: Any, *, field_name: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric and finite") from exc
        if not isfinite(numeric):
            raise ValueError(f"{field_name} must be numeric and finite")
        return numeric

    @classmethod
    def normalize(cls, score: float | None) -> float:
        if score is None:
            return 50.0
        value = cls._finite(score, field_name="score")
        return max(0.0, min(100.0, value))

    @classmethod
    def normalize_signed_score(cls, score: float | None) -> float:
        if score is None:
            return 50.0
        return normalize_signed_score(score)

    @classmethod
    def normalize_confidence(cls, value: float | None) -> float:
        if value is None:
            return 0.0
        numeric = cls._finite(value, field_name="confidence")
        if numeric > 1.0:
            numeric /= 100.0
        return max(0.0, min(1.0, numeric))

    @classmethod
    def direction(cls, score: float | None) -> str:
        return classify_direction(cls.normalize(score))

    @classmethod
    def direction_strength(cls, score: float | None) -> float:
        score = cls.normalize(score)
        return max(0.0, min(1.0, abs(score - 50.0) / 50.0))

    @staticmethod
    def _get(analysis: Any, name: str, default: Any = None) -> Any:
        return getattr(analysis, name, default)

    def _read_score(self, analysis: Any, name: str, default: float = 0.0) -> float:
        value = self._get(analysis, name, default)
        if value is None:
            return self.normalize_signed_score(default)
        return self.normalize_signed_score(value)

    def _collect_engines(self, analysis: Any) -> dict[str, float]:
        return {
            "smart_money": self._read_score(analysis, "smart_money_score"),
            "structure": (
                self.normalize_signed_score(
                    combined_structure_score(
                        self._get(analysis, "structure_score", 0.0),
                        self._get(analysis, "trend_score", 0.0),
                    )
                )
                if hasattr(analysis, "trend_score")
                else self._read_score(analysis, "structure_score")
            ),
            "price_action": self._read_score(analysis, "price_action_score"),
            "momentum": self._read_score(analysis, "momentum_score"),
            "supply_demand": self._read_score(analysis, "supply_demand_score"),
            "candlestick": self._read_score(analysis, "candlestick_score"),
            "elliott": self._read_score(analysis, "elliott_score"),
            "harmonic": self._read_score(analysis, "harmonic_score"),
            "brooks": self._read_score(analysis, "brooks_score"),
            "wyckoff": self._read_score(analysis, "wyckoff_score"),
        }

    def _calculate_votes(self, engines: dict[str, float]) -> tuple[int, int, int, float, float, float]:
        bullish_votes = bearish_votes = neutral_votes = 0
        weighted_bullish = weighted_bearish = weighted_neutral = 0.0
        for name, score in engines.items():
            direction = self.direction(score)
            weight = self.weights.get(name, 1.0)
            if weight <= 0.0:
                continue
            if direction == "bullish":
                bullish_votes += 1
                weighted_bullish += weight
            elif direction == "bearish":
                bearish_votes += 1
                weighted_bearish += weight
            else:
                neutral_votes += 1
                weighted_neutral += weight
        return bullish_votes, bearish_votes, neutral_votes, weighted_bullish, weighted_bearish, weighted_neutral

    @staticmethod
    def _calculate_agreement(weighted_bullish: float, weighted_bearish: float, weighted_neutral: float) -> float:
        values = (weighted_bullish, weighted_bearish, weighted_neutral)
        if not all(isfinite(value) for value in values):
            raise ValueError("agreement weights must be finite")
        total_weight = sum(values)
        if total_weight <= 0.0:
            return 0.0
        return max(0.0, min(1.0, max(values) / total_weight))

    @staticmethod
    def _calculate_conflict(weighted_bullish: float, weighted_bearish: float, total_weight: float) -> float:
        values = (weighted_bullish, weighted_bearish, total_weight)
        if not all(isfinite(value) for value in values):
            raise ValueError("conflict weights must be finite")
        if total_weight <= 0.0:
            return 1.0
        directional_weight = weighted_bullish + weighted_bearish
        if directional_weight <= 0.0:
            return 0.0
        return max(0.0, min(1.0, min(weighted_bullish, weighted_bearish) / directional_weight))

    def _calculate_data_quality(self, analysis: Any) -> float:
        required_fields = (
            "smart_money_score", "structure_score", "price_action_score",
            "momentum_score", "elliott_score", "harmonic_score", "wyckoff_score",
        )
        available = 0
        for field_name in required_fields:
            value = self._get(analysis, field_name, None)
            if value is None:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if isfinite(numeric):
                available += 1
        return available / len(required_fields)

    def _calculate_market_uncertainty(self, analysis: Any) -> float:
        uncertainty = 0.0
        volatility_score = self._get(analysis, "volatility_score", 0.0)
        if volatility_score is None:
            volatility_score = 0.0
        volatility_score = self._finite(volatility_score, field_name="volatility_score")
        volatility_score = max(0.0, volatility_score)
        if volatility_score >= 2.0:
            uncertainty += 0.15
        elif volatility_score >= 1.0:
            uncertainty += 0.05
        structure_score = self.normalize_signed_score(self._get(analysis, "structure_score", 0.0))
        if 45.0 < structure_score < 55.0:
            uncertainty += 0.15
        momentum_score = self.normalize_signed_score(self._get(analysis, "momentum_score", 0.0))
        if 45.0 < momentum_score < 55.0:
            uncertainty += 0.10
        return max(0.0, min(1.0, uncertainty))

    def _build_warnings(self, bullish_votes: int, bearish_votes: int, neutral_votes: int, agreement: float, conflict_score: float, data_quality: float, market_uncertainty: float) -> list[str]:
        warnings: list[str] = []
        total_votes = bullish_votes + bearish_votes + neutral_votes
        if bullish_votes > 0 and bearish_votes > 0:
            warnings.append("Analysis engines are directionally conflicting.")
        if neutral_votes >= 4:
            warnings.append("Several analysis engines remain neutral.")
        if agreement < self.LOW_AGREEMENT:
            warnings.append("Model agreement is low.")
        elif agreement < self.MEDIUM_AGREEMENT:
            warnings.append("Model agreement is moderate.")
        if conflict_score >= 0.35:
            warnings.append("Bullish and bearish evidence are significantly balanced.")
        if data_quality < 0.70:
            warnings.append("Some analysis components contain insufficient data.")
        if market_uncertainty >= 0.25:
            warnings.append("Current market conditions contain elevated uncertainty.")
        if total_votes == 0:
            warnings.append("No valid analysis engine votes were available.")
        return warnings

    def evaluate(self, analysis: Any) -> ConfidenceResult:
        engines = self._collect_engines(analysis)
        bullish_votes, bearish_votes, neutral_votes, weighted_bullish, weighted_bearish, weighted_neutral = self._calculate_votes(engines)
        agreement = self._calculate_agreement(weighted_bullish, weighted_bearish, weighted_neutral)
        total_weight = weighted_bullish + weighted_bearish + weighted_neutral
        conflict_score = self._calculate_conflict(weighted_bullish, weighted_bearish, total_weight)
        data_quality = self._calculate_data_quality(analysis)
        market_uncertainty = self._calculate_market_uncertainty(analysis)
        confidence = agreement
        if conflict_score > 0.0:
            confidence *= 1.0 - (conflict_score * 0.35)
        confidence *= 0.70 + (data_quality * 0.30)
        confidence *= 1.0 - (market_uncertainty * 0.25)
        decision_value = self._get(analysis, "decision_score", self._get(analysis, "total_score", 50.0))
        if decision_value is not None:
            decision_score = self.normalize(decision_value)
            if decision_score != 50.0:
                decision_direction = self.direction(decision_score)
                directional_weights = {"bullish": weighted_bullish, "bearish": weighted_bearish, "neutral": weighted_neutral}
                dominant_direction = max(directional_weights, key=directional_weights.get)
                if decision_direction != "neutral" and dominant_direction != "neutral" and decision_direction != dominant_direction:
                    confidence *= 0.85
        confidence = max(0.0, min(1.0, confidence))
        if not isfinite(confidence):
            raise ValueError("final confidence must be finite")
        warnings = self._build_warnings(bullish_votes, bearish_votes, neutral_votes, agreement, conflict_score, data_quality, market_uncertainty)
        if bullish_votes >= 3 and bearish_votes >= 3:
            warnings.append("Strong bullish and bearish disagreement detected.")
        if confidence < 0.40:
            warnings.append("Overall confidence is too low for a high-conviction setup.")
        if confidence >= 0.80 and agreement >= 0.80 and conflict_score < 0.20:
            warnings.append("High multi-engine agreement detected.")
        return ConfidenceResult(
            confidence=round(confidence, 3),
            agreement=round(agreement, 3),
            bullish_votes=bullish_votes,
            bearish_votes=bearish_votes,
            neutral_votes=neutral_votes,
            weighted_bullish=round(weighted_bullish, 3),
            weighted_bearish=round(weighted_bearish, 3),
            weighted_neutral=round(weighted_neutral, 3),
            data_quality=round(data_quality, 3),
            market_uncertainty=round(market_uncertainty, 3),
            conflict_score=round(conflict_score, 3),
            warnings=warnings,
        )
