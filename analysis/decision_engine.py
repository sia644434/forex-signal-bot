from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class DecisionResult:
    """Final trading decision result."""
    signal: str
    strength: str
    score: float
    confidence: float
    bias: str
    reasons: list[str]
    # Exact weighted contribution of each decision component. The values sum to score.
    component_contributions: dict[str, float] = field(default_factory=dict)


class DecisionEngine:
    """Professional multi-engine directional decision engine."""

    DEFAULT_WEIGHTS: dict[str, float] = {
        "smart_money": 0.20, "structure": 0.15, "price_action": 0.15,
        "supply_demand": 0.10, "indicators": 0.10, "candlestick": 0.08,
        "elliott": 0.06, "harmonic": 0.05, "brooks": 0.05, "wyckoff": 0.06,
    }

    STRONG_BUY_THRESHOLD = 80.0
    BUY_THRESHOLD = 60.0
    SELL_THRESHOLD = 40.0
    STRONG_SELL_THRESHOLD = 20.0

    def __init__(self, weights: dict[str, float] | None = None, buy_threshold: float = BUY_THRESHOLD, sell_threshold: float = SELL_THRESHOLD, strong_buy_threshold: float = STRONG_BUY_THRESHOLD, strong_sell_threshold: float = STRONG_SELL_THRESHOLD) -> None:
        self.weights = self._prepare_weights(weights)
        self.buy_threshold = self._require_finite(buy_threshold, "buy_threshold")
        self.sell_threshold = self._require_finite(sell_threshold, "sell_threshold")
        self.strong_buy_threshold = self._require_finite(strong_buy_threshold, "strong_buy_threshold")
        self.strong_sell_threshold = self._require_finite(strong_sell_threshold, "strong_sell_threshold")
        self._validate_thresholds()

    @staticmethod
    def _require_finite(value: Any, name: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be finite.") from error
        if not isfinite(numeric):
            raise ValueError(f"{name} must be finite.")
        return numeric

    def _prepare_weights(self, weights: dict[str, float] | None) -> dict[str, float]:
        result = self.DEFAULT_WEIGHTS.copy()
        if weights is None:
            return result
        if not isinstance(weights, dict):
            raise TypeError("weights must be a dictionary.")
        for key, value in weights.items():
            if key not in result:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"weight '{key}' must be finite and non-negative.") from error
            if not isfinite(numeric_value) or numeric_value < 0:
                raise ValueError(f"weight '{key}' must be finite and non-negative.")
            result[key] = numeric_value
        total = sum(result.values())
        if not isfinite(total) or total <= 0:
            raise ValueError("Decision weights must have a finite positive total.")
        normalized = {key: value / total for key, value in result.items()}
        if not all(isfinite(value) for value in normalized.values()):
            raise ValueError("Decision weights must normalize to finite values.")
        return normalized

    def _validate_thresholds(self) -> None:
        if not (0.0 <= self.strong_sell_threshold < self.sell_threshold < self.buy_threshold < self.strong_buy_threshold <= 100.0):
            raise ValueError("Invalid decision thresholds.")

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        if value is None:
            return default
        try:
            result = float(value)
        except (TypeError, ValueError):
            return default
        return result if isfinite(result) else default

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        if not isfinite(value):
            raise ValueError("Decision value must be finite.")
        return max(minimum, min(maximum, value))

    @classmethod
    def normalize_signed_component(cls, value: float | None) -> float:
        numeric_value = cls._safe_float(value)
        numeric_value = cls._clamp(numeric_value, -100.0, 100.0)
        return (numeric_value + 100.0) / 2.0

    @classmethod
    def normalize_component(cls, value: float | None) -> float:
        numeric_value = cls._safe_float(value)
        return cls._clamp(numeric_value, 0.0, 100.0)

    @classmethod
    def _read_component(cls, analysis: Any, attribute: str, default: float = 0.0) -> float:
        try:
            value = getattr(analysis, attribute)
        except AttributeError:
            return default
        try:
            numeric = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{attribute} must be numeric and finite.") from error
        if not isfinite(numeric):
            raise ValueError(f"{attribute} must be numeric and finite.")
        return numeric

    @staticmethod
    def _direction_from_score(score: float) -> str:
        if score > 55.0:
            return "bullish"
        if score < 45.0:
            return "bearish"
        return "neutral"

    def _apply_component(self, total: float, analysis_score: float, weight: float, reasons: list[str], name: str, bullish_reason: str, bearish_reason: str, neutral_reason: str | None = None) -> float:
        component_score = self.normalize_signed_component(analysis_score)
        contribution = component_score * weight
        if not isfinite(contribution):
            raise ValueError(f"{name} produced a non-finite decision contribution.")
        total += contribution
        if not isfinite(total):
            raise ValueError("Decision score became non-finite.")
        direction = self._direction_from_score(component_score)
        if direction == "bullish": reasons.append(bullish_reason)
        elif direction == "bearish": reasons.append(bearish_reason)
        elif neutral_reason: reasons.append(neutral_reason)
        return total

    def _apply_smart_money(self, total: float, analysis: Any, reasons: list[str]) -> float:
        total = self._apply_component(total, self._read_component(analysis, "smart_money_score"), self.weights["smart_money"], reasons, "Smart Money", "Smart Money Concepts support a bullish scenario", "Smart Money Concepts support a bearish scenario", "Smart Money Concepts are currently neutral")
        smc_bias = getattr(analysis, "smc_bias", "neutral")
        if isinstance(smc_bias, str):
            smc_bias = smc_bias.lower().strip()
            if smc_bias == "bullish": reasons.append("SMC bias is bullish")
            elif smc_bias == "bearish": reasons.append("SMC bias is bearish")
        return total

    def _apply_structure(self, total: float, analysis: Any, reasons: list[str]) -> float:
        structure_score = self._read_component(analysis, "structure_score")
        trend_score = self._read_component(analysis, "trend_score")
        combined_score = structure_score + trend_score
        if not isfinite(combined_score): raise ValueError("Market Structure score became non-finite.")
        combined_score /= 2.0
        return self._apply_component(total, combined_score, self.weights["structure"], reasons, "Market Structure", "Market structure favors buyers", "Market structure favors sellers", "Market structure is balanced")

    def _apply_price_action(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "price_action_score"), self.weights["price_action"], reasons, "Price Action", "Price action confirms bullish pressure", "Price action confirms bearish pressure", "Price action does not provide a strong directional edge")
    def _apply_supply_demand(self, total: float, analysis: Any, reasons: list[str]) -> float:
        total = self._apply_component(total, self._read_component(analysis, "supply_demand_score"), self.weights["supply_demand"], reasons, "Supply Demand", "Supply/Demand conditions favor demand", "Supply/Demand conditions favor supply", "Supply/Demand conditions are neutral")
        supply_demand = getattr(analysis, "supply_demand", None)
        if supply_demand: reasons.append(f"Supply/Demand zone: {supply_demand}")
        return total
    def _apply_indicators(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "momentum_score"), self.weights["indicators"], reasons, "Indicators", "Momentum and indicators support buyers", "Momentum and indicators support sellers", "Momentum is not strongly directional")
    def _apply_candlestick(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "candlestick_score"), self.weights["candlestick"], reasons, "Candlestick", "Candlestick structure supports bullish continuation/reversal", "Candlestick structure supports bearish continuation/reversal", "Candlestick signals are inconclusive")
    def _apply_elliott(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "elliott_score"), self.weights["elliott"], reasons, "Elliott", "Elliott analysis favors bullish structure", "Elliott analysis favors bearish structure", "Elliott wave structure is inconclusive")
    def _apply_harmonic(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "harmonic_score"), self.weights["harmonic"], reasons, "Harmonic", "Harmonic analysis supports bullish conditions", "Harmonic analysis supports bearish conditions", "No strong harmonic directional confirmation")
    def _apply_brooks(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "brooks_score"), self.weights["brooks"], reasons, "Brooks", "Brooks price-action analysis favors bulls", "Brooks price-action analysis favors bears", "Brooks analysis is currently balanced")
    def _apply_wyckoff(self, total: float, analysis: Any, reasons: list[str]) -> float:
        return self._apply_component(total, self._read_component(analysis, "wyckoff_score"), self.weights["wyckoff"], reasons, "Wyckoff", "Wyckoff structure favors accumulation/markup", "Wyckoff structure favors distribution/markdown", "Wyckoff structure is inconclusive")

    def _calculate_final_score(self, analysis: Any, reasons: list[str]) -> float:
        score = 0.0
        for method in (self._apply_smart_money, self._apply_structure, self._apply_price_action, self._apply_supply_demand, self._apply_indicators, self._apply_candlestick, self._apply_elliott, self._apply_harmonic, self._apply_brooks, self._apply_wyckoff):
            score = method(score, analysis, reasons)
        return round(self._clamp(score, 0.0, 100.0), 2)

    def _calculate_component_contributions(self, analysis: Any) -> dict[str, float]:
        """Return the exact weighted contributions used by the final score."""
        structure_score = self._read_component(analysis, "structure_score")
        trend_score = self._read_component(analysis, "trend_score")
        raw_components = {
            "smart_money": self._read_component(analysis, "smart_money_score"),
            "structure": (structure_score + trend_score) / 2.0,
            "price_action": self._read_component(analysis, "price_action_score"),
            "supply_demand": self._read_component(analysis, "supply_demand_score"),
            "indicators": self._read_component(analysis, "momentum_score"),
            "candlestick": self._read_component(analysis, "candlestick_score"),
            "elliott": self._read_component(analysis, "elliott_score"),
            "harmonic": self._read_component(analysis, "harmonic_score"),
            "brooks": self._read_component(analysis, "brooks_score"),
            "wyckoff": self._read_component(analysis, "wyckoff_score"),
        }
        contributions: dict[str, float] = {}
        for name, raw_value in raw_components.items():
            normalized = self.normalize_signed_component(raw_value)
            contributions[name] = round(normalized * self.weights[name], 4)
        return contributions

    def _calculate_signal(self, score: float) -> str:
        if score >= self.buy_threshold: return "BUY"
        if score <= self.sell_threshold: return "SELL"
        return "NEUTRAL"
    def _calculate_strength(self, score: float) -> str:
        if score >= self.strong_buy_threshold or score <= self.strong_sell_threshold: return "STRONG"
        if score >= self.buy_threshold or score <= self.sell_threshold: return "MODERATE"
        return "WEAK"
    @staticmethod
    def _calculate_bias(score: float) -> str:
        if score > 50.0: return "bullish"
        if score < 50.0: return "bearish"
        return "neutral"
    @classmethod
    def _calculate_confidence(cls, score: float) -> float:
        distance = abs(score - 50.0)
        return round(cls._clamp(distance / 50.0, 0.0, 1.0), 3)
    @classmethod
    def _adjust_confidence_for_neutrality(cls, confidence: float, score: float) -> float:
        if 45.0 <= score <= 55.0: confidence *= 0.50
        return round(cls._clamp(confidence, 0.0, 1.0), 3)
    @staticmethod
    def _build_final_reasons(reasons: list[str], score: float, confidence: float, signal: str, strength: str, bias: str) -> list[str]:
        final_reasons = list(reasons)
        final_reasons.append(f"Final decision score: {score:.2f}/100")
        final_reasons.append(f"Decision signal: {signal}")
        final_reasons.append(f"Signal strength: {strength}")
        final_reasons.append(f"Directional bias: {bias}")
        final_reasons.append(f"Decision confidence: {confidence:.3f}")
        return final_reasons

    def decide(self, analysis: Any) -> DecisionResult:
        reasons: list[str] = []
        score = self._calculate_final_score(analysis, reasons)
        component_contributions = self._calculate_component_contributions(analysis)
        contribution_total = round(sum(component_contributions.values()), 2)
        if abs(contribution_total - score) > 0.02:
            raise ValueError("Decision contribution breakdown does not reconcile with final score.")
        signal = self._calculate_signal(score)
        strength = self._calculate_strength(score)
        bias = self._calculate_bias(score)
        confidence = self._adjust_confidence_for_neutrality(self._calculate_confidence(score), score)

        decay = str(getattr(analysis, "signal_decay", "FRESH")).upper()
        conflict = str(getattr(analysis, "conflict_state", "")).upper()
        crisis = str(getattr(analysis, "crisis_mode", "NORMAL")).upper()
        scenario = str(getattr(analysis, "scenario", "")).upper()

        if decay in {"STALE", "INVALID"}:
            signal = "NO_TRADE"
            strength = "BLOCKED"
            reasons.append(f"Execution blocked by signal decay state: {decay}")
        elif crisis in {"CRISIS", "EXTREME"}:
            signal = "NO_TRADE"
            strength = "BLOCKED"
            reasons.append(f"Execution blocked by crisis mode: {crisis}")
        elif conflict == "STRONG_CONFLICT" or scenario == "NO_TRADE":
            signal = "NO_TRADE"
            strength = "BLOCKED"
            reasons.append("Execution blocked by insufficient directional agreement")
        elif bool(getattr(analysis, "portfolio_risk_blocked", False)):
            signal = "NO_TRADE"
            strength = "BLOCKED"
            flags = getattr(analysis, "portfolio_risk_flags", [])
            flag_text = ", ".join(map(str, flags)) if flags else "RISK_LIMIT"
            reasons.append(f"Execution blocked by portfolio risk limits: {flag_text}")
        elif str(getattr(analysis, "macro_risk_level", "NORMAL")).upper() == "CRISIS":
            signal = "NO_TRADE"
            strength = "BLOCKED"
            reasons.append("Execution blocked by high-impact macro event risk")
        elif str(getattr(analysis, "macro_risk_level", "NORMAL")).upper() == "ELEVATED" and signal in {"BUY", "SELL"}:
            signal = "WAIT"
            strength = "WEAK"
            reasons.append("Elevated macro event risk downgraded the executable signal to WAIT")
        elif conflict == "CONFLICT" and signal in {"BUY", "SELL"}:
            signal = "WAIT"
            strength = "WEAK"
            reasons.append("Directional conflict downgraded the executable signal to WAIT")

        reasons = self._build_final_reasons(reasons, score, confidence, signal, strength, bias)
        return DecisionResult(signal=signal, strength=strength, score=score, confidence=confidence, bias=bias, reasons=reasons, component_contributions=component_contributions)
