from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

from analysis.models import AnalysisResult
from analysis.report import AnalysisReport
from analysis.candle import Candle
from analysis.market_structure import MarketStructureDetector
from analysis.decision_engine import DecisionEngine
from analysis.confidence_engine import ConfidenceEngine
from analysis.risk_engine import RiskEngine
from analysis.atr_engine import ATREngine
from analysis.indicator_engine import IndicatorEngine
from analysis.momentum_engine import MomentumEngine
from analysis.price_action_engine import PriceActionEngine
from analysis.supply_demand_engine import SupplyDemandEngine
from analysis.candlestick_engine import CandlestickEngine
from analysis.elliott_engine import ElliottEngine
from analysis.harmonic_engine import HarmonicEngine
from analysis.brooks_engine import BrooksEngine
from analysis.wyckoff_engine import WyckoffEngine
from analysis.smc_engine import SMCEngine
from analysis.statistical_engine import StatisticalEngine
from analysis.scenario_engine import ScenarioEngine
from analysis.signal_state import evaluate_signal_state
from analysis.portfolio_risk_guard import PortfolioExposure, PortfolioRiskGuard


class FullAnalysisEngine:
    """Complete professional Forex analysis pipeline."""

    def __init__(self) -> None:
        self.structure_detector = MarketStructureDetector()
        self.indicator_engine = IndicatorEngine()
        self.momentum_engine = MomentumEngine()
        self.price_action_engine = PriceActionEngine()
        self.supply_demand_engine = SupplyDemandEngine()
        self.candlestick_engine = CandlestickEngine()
        self.elliott_engine = ElliottEngine()
        self.harmonic_engine = HarmonicEngine()
        self.brooks_engine = BrooksEngine()
        self.wyckoff_engine = WyckoffEngine()
        self.smc_engine = SMCEngine()
        self.decision_engine = DecisionEngine()
        self.confidence_engine = ConfidenceEngine()
        self.risk_engine = RiskEngine()
        self.atr_engine = ATREngine()
        self.statistical_engine = StatisticalEngine()
        self.scenario_engine = ScenarioEngine()
        self.portfolio_risk_guard = PortfolioRiskGuard()

    @staticmethod
    def _require_finite(value: object, name: str) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric and finite.") from exc
        if not math.isfinite(numeric_value):
            raise ValueError(f"{name} must be numeric and finite.")
        return numeric_value

    @staticmethod
    def _directional_strength(score: float) -> float:
        """Convert a finite 0..100 decision score to symmetric strength."""
        numeric_score = FullAnalysisEngine._require_finite(score, "decision score")
        return abs((numeric_score - 50.0) * 2.0)

    @staticmethod
    def _normalize_candles(candles: list[Candle] | list[float]) -> tuple[list[Candle], list[float]]:
        if candles is None:
            raise ValueError("Input candles cannot be None.")
        try:
            candle_count = len(candles)
        except TypeError as exc:
            raise TypeError("Input candles must be a sized collection.") from exc
        if candle_count == 0:
            raise ValueError("Input candles cannot be empty.")

        first = candles[0]
        if isinstance(first, Candle):
            if not all(isinstance(candle, Candle) for candle in candles):
                raise TypeError("Input candle collection must contain only Candle objects.")
            closes: list[float] = []
            for index, candle in enumerate(candles):
                closes.append(FullAnalysisEngine._require_finite(candle.close, f"Candle close at index {index}"))
                if closes[-1] <= 0:
                    raise ValueError(f"Candle close at index {index} must be greater than zero.")
            return list(candles), closes

        closes: list[float] = []
        for index, price in enumerate(candles):
            if isinstance(price, bool):
                raise TypeError(f"Input price at index {index} must be a real number.")
            try:
                numeric_price = float(price)
            except (TypeError, ValueError) as exc:
                raise TypeError(f"Input price at index {index} must be a real number.") from exc
            if not math.isfinite(numeric_price) or numeric_price <= 0:
                raise ValueError(f"Input price at index {index} must be finite and greater than zero.")
            closes.append(numeric_price)

        start = datetime(1970, 1, 1, tzinfo=timezone.utc)
        candle_data = [
            Candle(symbol="UNKNOWN", timestamp=start + timedelta(minutes=index), open=price, high=price, low=price, close=price, volume=0.0)
            for index, price in enumerate(closes)
        ]
        return candle_data, closes

    def analyze(
        self,
        candles: list[Candle] | list[float],
        *,
        macro_risk: dict[str, object] | None = None,
        portfolio_exposures: list[PortfolioExposure] | None = None,
        portfolio_candidate: PortfolioExposure | None = None,
        portfolio_equity: float | None = None,
        portfolio_max_symbol_weight: float = 0.35,
        portfolio_max_gross_exposure: float = 1.0,
        signal_max_age_seconds: float = 60.0,
    ) -> AnalysisReport:
        if signal_max_age_seconds <= 0 or not math.isfinite(float(signal_max_age_seconds)):
            raise ValueError("signal_max_age_seconds must be finite and positive.")

        candle_data, closes = self._normalize_candles(candles)
        atr_result = self.atr_engine.calculate(closes)
        atr_value = self._require_finite(atr_result.atr if atr_result.atr is not None else 0.0, "ATR")
        atr_percentage = self._require_finite(atr_result.atr_percentage if atr_result.atr_percentage is not None else 0.0, "ATR percentage")
        if atr_value < 0 or atr_percentage < 0:
            raise ValueError("ATR metrics must be non-negative.")

        structure = self.structure_detector.analyze(closes)
        statistics = self.statistical_engine.evaluate(closes)
        scenario = self.scenario_engine.evaluate(closes, trend=structure.trend, volatility=atr_percentage / 100.0)
        indicator_snapshot = self.indicator_engine.calculate(closes)
        momentum_result = self.momentum_engine.analyze(indicator_snapshot.values)
        price_action_result = self.price_action_engine.analyze(closes)
        supply_demand_result = self.supply_demand_engine.analyze(closes)
        candlestick_result = self.candlestick_engine.analyze(candle_data)
        elliott_result = self.elliott_engine.analyze(closes)
        harmonic_result = self.harmonic_engine.analyze(closes)
        brooks_result = self.brooks_engine.analyze(closes)
        wyckoff_result = self.wyckoff_engine.analyze(closes)
        smc_result = self.smc_engine.analyze(closes)

        component_scores = {
            "trend_score": 20 if structure.trend == "bullish" else -20 if structure.trend == "bearish" else 0,
            "momentum_score": momentum_result.score,
            "structure_score": 20 if structure.bos else 0,
            "volatility_score": atr_percentage,
            "price_action_score": price_action_result.score,
            "supply_demand_score": supply_demand_result.score,
            "candlestick_score": candlestick_result.score,
            "elliott_score": elliott_result.score,
            "harmonic_score": harmonic_result.score,
            "brooks_score": brooks_result.score,
            "wyckoff_score": wyckoff_result.score,
            "smart_money_score": smc_result.score,
        }
        for name, value in component_scores.items():
            self._require_finite(value, name)

        directional_scores = [float(value) for key, value in component_scores.items() if key != "volatility_score"]
        positive_votes = sum(value > 0 for value in directional_scores)
        negative_votes = sum(value < 0 for value in directional_scores)
        if positive_votes and negative_votes:
            conflict_state = "STRONG_CONFLICT" if min(positive_votes, negative_votes) >= 3 else "CONFLICT"
        elif max(positive_votes, negative_votes) >= 3:
            conflict_state = "CONSENSUS"
        elif positive_votes or negative_votes:
            conflict_state = "WEAK_CONSENSUS"
        else:
            conflict_state = "INSUFFICIENT_EVIDENCE"

        if structure.trend in {"bullish", "bearish"} and atr_percentage >= 3.0:
            market_regime = "HIGH_VOLATILITY"
        elif structure.trend in {"bullish", "bearish"}:
            market_regime = "TRENDING"
        elif atr_percentage >= 3.0:
            market_regime = "HIGH_VOLATILITY"
        else:
            market_regime = "RANGING"

        latest = candle_data[-1].timestamp
        has_real_timestamps = isinstance(candles[0], Candle)
        signal_state = evaluate_signal_state(latest, max_age_seconds=float(signal_max_age_seconds), volatility=atr_percentage / 100.0) if has_real_timestamps and latest.tzinfo is not None else None

        macro_context = macro_risk or {}
        macro_level = str(macro_context.get("risk_level", "NORMAL")).upper()
        if macro_level not in {"NORMAL", "ELEVATED", "CRISIS"}:
            raise ValueError("macro_risk.risk_level must be NORMAL, ELEVATED, or CRISIS")
        macro_events = macro_context.get("events", [])
        if not isinstance(macro_events, list):
            raise ValueError("macro_risk.events must be a list")

        portfolio_blocked = False
        portfolio_flags: list[str] = []
        if portfolio_candidate is not None:
            portfolio_result = self.portfolio_risk_guard.can_add(
                list(portfolio_exposures or []),
                portfolio_candidate,
                max_symbol_weight=portfolio_max_symbol_weight,
                max_gross_exposure=portfolio_max_gross_exposure,
                equity=portfolio_equity,
            )
            portfolio_blocked = bool(portfolio_result["blocked"])
            portfolio_flags = list(portfolio_result["after"].risk_flags)

        analysis_result = AnalysisResult(
            trend=structure.trend, momentum=momentum_result.state, indicators=indicator_snapshot.values, candles=candle_data,
            supply_demand=supply_demand_result.zone, trend_score=component_scores["trend_score"], momentum_score=component_scores["momentum_score"],
            structure_score=component_scores["structure_score"], volatility_score=component_scores["volatility_score"], price_action_score=component_scores["price_action_score"],
            supply_demand_score=component_scores["supply_demand_score"], candlestick_score=component_scores["candlestick_score"], elliott_score=component_scores["elliott_score"],
            harmonic_score=component_scores["harmonic_score"], brooks_score=component_scores["brooks_score"], wyckoff_score=component_scores["wyckoff_score"],
            smart_money_score=component_scores["smart_money_score"], smc_bias=smc_result.bias, smc_structure=smc_result.structure, order_block=smc_result.order_block,
            liquidity=smc_result.liquidity, fair_value_gap=smc_result.fair_value_gap, premium_discount=smc_result.premium_discount,
            reasons=momentum_result.reasons + price_action_result.reasons + [supply_demand_result.reason, candlestick_result.reason, elliott_result.reason, harmonic_result.reason, brooks_result.reason, wyckoff_result.reason, smc_result.reason],
            market_regime=market_regime,
            scenario=scenario.primary,
            statistical_context=statistics.summary(),
            conflict_state=conflict_state,
            signal_decay=signal_state.decay if signal_state else "INVALID",
            macro_risk_level=macro_level,
            macro_events=macro_events,
            crisis_mode=signal_state.crisis_mode if signal_state else "NORMAL",
            portfolio_risk_blocked=portfolio_blocked,
            portfolio_risk_flags=portfolio_flags,
        )

        decision = self.decision_engine.decide(analysis_result)
        confidence_result = self.confidence_engine.evaluate(analysis_result)
        risk_result = self.risk_engine.calculate(signal=decision.signal, current_price=closes[-1], atr=atr_value, confidence=confidence_result.confidence, score=decision.score)

        confidence_value = self._require_finite(confidence_result.confidence, "confidence")
        decision_score = self._require_finite(decision.score, "decision score")
        # RiskResult intentionally uses None for a NO-TRADE plan. Validate every
        # populated numeric field without converting the legitimate None contract
        # into a failure.
        risk_values = {
            "entry_price": risk_result.entry_price,
            "stop_loss": risk_result.stop_loss,
            "take_profit": risk_result.take_profit,
            "risk_reward": risk_result.risk_reward,
            "position_size": risk_result.position_size,
            "risk_amount": risk_result.risk_amount,
        }
        for name, value in risk_values.items():
            if value is not None:
                self._require_finite(value, name)

        if confidence_value >= 0.85:
            confidence_grade = "VERY_HIGH"
        elif confidence_value >= 0.70:
            confidence_grade = "HIGH"
        elif confidence_value >= 0.50:
            confidence_grade = "MEDIUM"
        elif confidence_value >= 0.30:
            confidence_grade = "LOW"
        else:
            confidence_grade = "VERY_LOW"

        structure_name = "BOS" if structure.bos else "NORMAL"
        trade_quality = min(100, max(0, int((confidence_value * 50) + (self._directional_strength(decision_score) * 0.5))))
        if trade_quality >= 90:
            trade_grade = "A+"
        elif trade_quality >= 80:
            trade_grade = "A"
        elif trade_quality >= 70:
            trade_grade = "B"
        elif trade_quality >= 50:
            trade_grade = "C"
        else:
            trade_grade = "D"

        return AnalysisReport(
            trend=structure.trend, structure=structure_name, score=decision_score, signal=decision.signal, confidence=confidence_value,
            agreement=confidence_result.agreement, bullish_votes=confidence_result.bullish_votes, bearish_votes=confidence_result.bearish_votes, neutral_votes=confidence_result.neutral_votes,
            warnings=confidence_result.warnings, confidence_grade=confidence_grade, decision_bias=decision.bias, risk_level=risk_result.risk_level,
            entry_price=risk_result.entry_price, stop_loss=risk_result.stop_loss, take_profit=risk_result.take_profit, take_profit_1=risk_result.take_profit_1,
            take_profit_2=risk_result.take_profit_2, take_profit_3=risk_result.take_profit_3, risk_reward=risk_result.risk_reward, position_size=risk_result.position_size,
            risk_amount=risk_result.risk_amount, trailing_stop=risk_result.trailing_stop, market_condition=risk_result.market_condition, trade_quality=trade_quality,
            trade_grade=trade_grade, smc_bias=smc_result.bias, smc_structure=smc_result.structure, order_block=smc_result.order_block, liquidity=smc_result.liquidity,
            fair_value_gap=smc_result.fair_value_gap, premium_discount=smc_result.premium_discount,
            reasons=analysis_result.reasons + decision.reasons + confidence_result.warnings + [risk_result.reason, f"ATR: {atr_value}", f"ATR Percentage: {atr_percentage}", f"Market Condition: {risk_result.market_condition}", f"Trade Grade: {trade_grade}"],
            indicators=indicator_snapshot.values,
            component_scores={name: float(value) for name, value in component_scores.items()},
            decision_contributions={name: float(value) for name, value in decision.component_contributions.items()},
            directional_contributions={name: float(value) for name, value in decision.directional_contributions.items()},
            market_regime=analysis_result.market_regime,
            scenario=analysis_result.scenario,
            statistical_context=analysis_result.statistical_context,
            conflict_state=analysis_result.conflict_state,
            macro_risk_level=analysis_result.macro_risk_level,
            macro_events=analysis_result.macro_events,
            signal_decay=analysis_result.signal_decay,
            crisis_mode=analysis_result.crisis_mode,
            portfolio_risk_blocked=analysis_result.portfolio_risk_blocked,
            portfolio_risk_flags=analysis_result.portfolio_risk_flags,
        )
