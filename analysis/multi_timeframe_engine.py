from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from analysis.full_engine import FullAnalysisEngine
from analysis.report import AnalysisReport


@dataclass(frozen=True)
class MultiTimeframeDecision:
    symbol: str
    direction: str
    setup_timeframe: str
    setup_report: AnalysisReport
    timeframe_reports: Mapping[str, AnalysisReport]
    alignment_score: float
    lower_timeframe_score: float
    reasons: tuple[str, ...]

    @property
    def executable(self) -> bool:
        return str(self.direction).upper() in {"BUY", "SELL"}


class MultiTimeframeAnalysisEngine:
    """Evaluate market context from higher timeframes before entry confirmation."""

    TIMEFRAME_ORDER = ("W1", "D1", "H4", "H1", "M15", "M5")
    TIMEFRAME_MINUTES = {
        "W1": 10080,
        "D1": 1440,
        "H4": 240,
        "H1": 60,
        "M15": 15,
        "M5": 5,
    }
    WEIGHTS = {"W1": 5.0, "D1": 15.0, "H4": 25.0, "H1": 20.0, "M15": 25.0, "M5": 10.0}
    EXECUTABLE = {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}

    def __init__(self, analysis_engine: FullAnalysisEngine | None = None) -> None:
        self.analysis_engine = analysis_engine or FullAnalysisEngine()

    @classmethod
    def _signal_age_budget(cls, timeframe: str) -> float:
        minutes = cls.TIMEFRAME_MINUTES[timeframe]
        return float(max(60, minutes * 2 * 60))

    @staticmethod
    def _direction_score(report: AnalysisReport) -> float:
        try:
            score = float(report.score)
        except (TypeError, ValueError):
            return 50.0
        return max(0.0, min(100.0, score))

    @classmethod
    def _alignment_score(cls, reports: Mapping[str, AnalysisReport]) -> float:
        total = 0.0
        weight = 0.0
        for timeframe, report in reports.items():
            w = cls.WEIGHTS.get(timeframe, 0.0)
            if w <= 0:
                continue
            total += cls._direction_score(report) * w
            weight += w
        return round(total / weight, 2) if weight else 50.0

    @staticmethod
    def _m15_diagnostics(report: AnalysisReport, signal: str) -> tuple[str, ...]:
        """Return a precise, stable explanation of why M15 is not executable."""
        score = MultiTimeframeAnalysisEngine._direction_score(report)
        buy_gap = max(0.0, 60.0 - score)
        sell_gap = max(0.0, score - 40.0)
        components = getattr(report, "component_scores", {}) or {}
        contributions = getattr(report, "decision_contributions", {}) or {}
        contribution_text = ",".join(
            f"{name}={float(value):+.2f}"
            for name, value in contributions.items()
        ) or "none"
        component_order = (
            "smart_money_score",
            "structure_score",
            "price_action_score",
            "supply_demand_score",
            "momentum_score",
            "candlestick_score",
            "elliott_score",
            "harmonic_score",
            "brooks_score",
            "wyckoff_score",
        )
        # Keep the diagnostic exhaustive and deterministic so a single Railway
        # cycle explains the M15 decision without requiring another code change.
        # The component map is emitted in a fixed order when known, followed by
        # any newly-added components in sorted order.
        ordered_component_names = list(component_order)
        ordered_component_names.extend(
            sorted(name for name in components if name not in ordered_component_names)
        )
        component_text = ",".join(
            f"{name}={float(components[name]):.1f}"
            for name in ordered_component_names
            if name in components
        )
        all_reasons = [str(reason) for reason in (getattr(report, "reasons", None) or [])]
        blocking_reasons = [
            reason for reason in all_reasons if reason.startswith("Execution blocked by")
        ]
        warnings = [str(item) for item in (getattr(report, "warnings", None) or [])]
        volatility = components.get("volatility_score")
        risk_level = str(getattr(report, "risk_level", "UNKNOWN")).upper()
        market_regime = str(getattr(report, "market_regime", "UNKNOWN")).upper()
        portfolio_blocked = bool(getattr(report, "portfolio_risk_blocked", False))
        portfolio_flags = [
            str(item) for item in (getattr(report, "portfolio_risk_flags", None) or [])
        ]

        diagnostics = [
            f"m15_signal={signal or 'NONE'}",
            f"m15_score={score:.1f}",
            "m15_thresholds=BUY>=60.0,SELL<=40.0",
            f"m15_gap_to_buy={buy_gap:.1f}",
            f"m15_gap_to_sell={sell_gap:.1f}",
            f"m15_trend={str(getattr(report, 'trend', 'unknown')).upper()}",
            f"m15_structure={str(getattr(report, 'structure', 'unknown')).upper()}",
            f"m15_bias={str(getattr(report, 'decision_bias', 'neutral')).upper()}",
            f"m15_confidence={float(getattr(report, 'confidence', 0.0) or 0.0):.2f}",
            f"m15_agreement={float(getattr(report, 'agreement', 0.0) or 0.0):.2f}",
            f"m15_votes=bull:{int(getattr(report, 'bullish_votes', 0) or 0)},bear:{int(getattr(report, 'bearish_votes', 0) or 0)},neutral:{int(getattr(report, 'neutral_votes', 0) or 0)}",
            f"m15_quality={float(getattr(report, 'trade_quality', 0.0) or 0.0):.0f}",
            f"m15_grade={str(getattr(report, 'trade_grade', 'UNKNOWN')).upper()}",
            f"m15_conflict={str(getattr(report, 'conflict_state', 'UNKNOWN')).upper()}",
            f"m15_scenario={str(getattr(report, 'scenario', 'UNKNOWN')).upper()}",
            f"m15_decay={str(getattr(report, 'signal_decay', 'UNKNOWN')).upper()}",
            f"m15_rr={'none' if getattr(report, 'risk_reward', None) is None else format(float(report.risk_reward), '.2f')}",
            f"m15_score_delta={score - 50.0:+.2f}",
            f"m15_score_contributions={contribution_text}",
            f"m15_contribution_total={sum(float(value) for value in contributions.values()):.2f}",
            f"m15_market_regime={market_regime}",
            f"m15_risk_level={risk_level}",
            f"m15_volatility={'none' if volatility is None else format(float(volatility), '.2f')}",
            f"m15_portfolio_risk_blocked={str(portfolio_blocked).lower()}",
        ]
        if portfolio_flags:
            diagnostics.append("m15_portfolio_risk_flags=" + "|".join(portfolio_flags))
        if component_text:
            diagnostics.append(f"m15_components={component_text}")
        if blocking_reasons:
            diagnostics.append("m15_blockers=" + "|".join(blocking_reasons))
        if warnings:
            diagnostics.append("m15_warnings=" + "|".join(warnings))
        if all_reasons:
            diagnostics.append("m15_reasons=" + "|".join(all_reasons))
        return tuple(diagnostics)

    @classmethod
    def _aligned_higher_timeframes(cls, reports: Mapping[str, AnalysisReport], direction: str) -> int:
        count = 0
        for timeframe in ("W1", "D1", "H4", "H1"):
            report = reports.get(timeframe)
            if report is None:
                continue
            score = cls._direction_score(report)
            if direction == "BUY" and score >= 55:
                count += 1
            elif direction == "SELL" and score <= 45:
                count += 1
        return count

    def analyze(
        self,
        candles_by_timeframe: Mapping[str, list],
        symbol: str | None = None,
    ) -> MultiTimeframeDecision | None:
        decision, _ = self.analyze_with_diagnostics(candles_by_timeframe, symbol=symbol)
        return decision

    def analyze_with_diagnostics(
        self,
        candles_by_timeframe: Mapping[str, list],
        symbol: str | None = None,
    ) -> tuple[MultiTimeframeDecision | None, tuple[str, ...]]:
        """Return the decision plus concise rejection diagnostics for observability."""
        missing = [tf for tf in self.TIMEFRAME_ORDER if not candles_by_timeframe.get(tf)]
        if missing:
            return None, (f"missing_timeframes={','.join(missing)}",)

        reports: dict[str, AnalysisReport] = {}
        for timeframe in self.TIMEFRAME_ORDER:
            candles = candles_by_timeframe[timeframe]
            reports[timeframe] = self.analysis_engine.analyze(
                candles,
                signal_max_age_seconds=self._signal_age_budget(timeframe),
            )

        setup = reports["M15"]
        direction = str(setup.signal).upper()
        if direction not in self.EXECUTABLE:
            return None, self._m15_diagnostics(setup, direction)
        direction = "BUY" if "BUY" in direction else "SELL"

        alignment = self._alignment_score(reports)
        aligned_htf = self._aligned_higher_timeframes(reports, direction)
        lower_score = self._direction_score(reports["M5"])
        setup_quality = float(setup.trade_quality or 0.0)
        confidence = float(setup.confidence or 0.0)
        rr = setup.risk_reward

        reasons: list[str] = [
            f"HTF alignment score: {alignment:.1f}/100",
            f"Higher-timeframe directional alignment: {aligned_htf}/4",
            f"M5 confirmation score: {lower_score:.1f}/100",
            f"M15 setup quality: {setup_quality:.0f}/100",
        ]
        rejection_codes: list[str] = []

        if direction == "BUY":
            aligned = alignment >= 60.0 and lower_score >= 52.0
        else:
            aligned = alignment <= 40.0 and lower_score <= 48.0

        directional_alignment_ok = (
            alignment >= 60.0 and lower_score >= 52.0
            if direction == "BUY"
            else alignment <= 40.0 and lower_score <= 48.0
        )
        if not directional_alignment_ok:
            rejection_codes.append(f"directional_alignment={alignment:.1f},m5={lower_score:.1f}")
        if aligned_htf < 3:
            aligned = False
            rejection_codes.append(f"htf_alignment={aligned_htf}/4")
            reasons.append("Higher-timeframe context is not sufficiently aligned.")
        if setup_quality < 70.0:
            aligned = False
            rejection_codes.append(f"setup_quality={setup_quality:.0f}<70")
            reasons.append("Setup quality is below the automatic notification threshold.")
        if confidence < 0.65:
            aligned = False
            rejection_codes.append(f"confidence={confidence:.2f}<0.65")
            reasons.append("Setup confidence is below the automatic notification threshold.")
        if rr is None or float(rr) < 1.5:
            aligned = False
            rejection_codes.append(f"rr={float(rr):.2f}" if rr is not None else "rr=none")
            reasons.append("Risk/reward is below the automatic notification threshold.")
        if str(setup.conflict_state).upper() in {"CONFLICT", "STRONG_CONFLICT"}:
            aligned = False
            rejection_codes.append(f"conflict_state={str(setup.conflict_state).upper()}")
            reasons.append("M15 directional conflict blocks automatic notification.")
        if str(setup.signal_decay).upper() in {"STALE", "INVALID"}:
            aligned = False
            rejection_codes.append(f"signal_decay={str(setup.signal_decay).upper()}")
            reasons.append("M15 signal freshness is no longer valid.")
        if setup.portfolio_risk_blocked:
            aligned = False
            rejection_codes.append("portfolio_risk_blocked=true")
            reasons.append("Portfolio risk guard blocks the setup.")

        if not aligned:
            return None, tuple(rejection_codes or ("validation_failed",))

        return MultiTimeframeDecision(
            symbol=symbol or getattr(setup, "symbol", "UNKNOWN"),
            direction=direction,
            setup_timeframe="M15",
            setup_report=setup,
            timeframe_reports=reports,
            alignment_score=alignment,
            lower_timeframe_score=lower_score,
            reasons=tuple(reasons),
        ), ()


__all__ = ["MultiTimeframeAnalysisEngine", "MultiTimeframeDecision"]
