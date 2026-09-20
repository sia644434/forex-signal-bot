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
    role_scores: Mapping[str, float] = None
    market_story: tuple[str, ...] = ()

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
    # Each timeframe has a job; they are not six independent votes.
    ROLES = {
        "macro": ("W1", "D1"),
        "context": ("H4", "H1"),
        "setup": ("M15",),
        "execution": ("M5",),
    }
    ROLE_WEIGHTS = {
        "macro": {"W1": 0.60, "D1": 0.40},
        "context": {"H4": 0.60, "H1": 0.40},
    }
    EXECUTABLE = {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}
    BULLISH_THRESHOLD = 55.0
    BEARISH_THRESHOLD = 45.0
    M5_BUY_TRIGGER = 52.0
    M5_SELL_TRIGGER = 48.0

    # A neutral/blocked M15 signal can still define a setup hypothesis from
    # its directional bias. This is only a setup candidate; all higher-
    # timeframe, execution, quality, risk and safety gates remain mandatory.
    SETUP_BIAS_DIRECTIONS = {"bullish": "BUY", "bearish": "SELL"}

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
    def _role_score(cls, reports: Mapping[str, AnalysisReport], role: str) -> float:
        timeframes = cls.ROLES[role]
        weights = cls.ROLE_WEIGHTS.get(role, {})
        if len(timeframes) == 1:
            return round(cls._direction_score(reports[timeframes[0]]), 2)
        total = 0.0
        weight = 0.0
        for timeframe in timeframes:
            report = reports.get(timeframe)
            if report is None:
                continue
            w = float(weights.get(timeframe, 1.0))
            total += cls._direction_score(report) * w
            weight += w
        return round(total / weight, 2) if weight else 50.0

    @classmethod
    def _role_scores(cls, reports: Mapping[str, AnalysisReport]) -> dict[str, float]:
        return {
            role: cls._role_score(reports, role)
            for role in ("macro", "context", "setup", "execution")
        }

    @classmethod
    def _alignment_score(cls, reports: Mapping[str, AnalysisReport]) -> float:
        # Compatibility/telemetry score only. It is deliberately not used as
        # the trade gate because MTF responsibilities are asymmetric.
        roles = cls._role_scores(reports)
        return round(
            roles["macro"] * 0.30
            + roles["context"] * 0.30
            + roles["setup"] * 0.25
            + roles["execution"] * 0.15,
            2,
        )

    @classmethod
    def _higher_context_ok(cls, reports: Mapping[str, AnalysisReport], direction: str) -> bool:
        w1 = cls._direction_score(reports["W1"])
        d1 = cls._direction_score(reports["D1"])
        h4 = cls._direction_score(reports["H4"])
        h1 = cls._direction_score(reports["H1"])

        if direction == "BUY":
            # W1 is the macro anchor. D1 may be a normal correction and need
            # not be bullish, but it must not be decisively bearish. H4/H1
            # define the actionable location/context and both must support the
            # long thesis without requiring identical readings.
            macro_ok = w1 >= cls.BULLISH_THRESHOLD and d1 > 35.0
            context_ok = h4 >= 50.0 and h1 >= cls.BULLISH_THRESHOLD
        else:
            macro_ok = w1 <= cls.BEARISH_THRESHOLD and d1 < 65.0
            context_ok = h4 <= 50.0 and h1 <= cls.BEARISH_THRESHOLD

        return macro_ok and context_ok

    @classmethod
    def _higher_context_diagnostics(
        cls,
        reports: Mapping[str, AnalysisReport],
        direction: str,
    ) -> tuple[bool, tuple[str, ...]]:
        """Return the exact higher-timeframe gate result and failed requirements."""
        scores = {
            timeframe: cls._direction_score(reports[timeframe])
            for timeframe in ("W1", "D1", "H4", "H1")
        }
        if direction == "BUY":
            checks = (
                ("W1", scores["W1"] >= cls.BULLISH_THRESHOLD, f"W1={scores["W1"]:.1f}>=55.0"),
                ("D1", scores["D1"] > 35.0, f"D1={scores["D1"]:.1f}>35.0"),
                ("H4", scores["H4"] >= 50.0, f"H4={scores["H4"]:.1f}>=50.0"),
                ("H1", scores["H1"] >= cls.BULLISH_THRESHOLD, f"H1={scores["H1"]:.1f}>=55.0"),
            )
        else:
            checks = (
                ("W1", scores["W1"] <= cls.BEARISH_THRESHOLD, f"W1={scores["W1"]:.1f}<=45.0"),
                ("D1", scores["D1"] < 65.0, f"D1={scores["D1"]:.1f}<65.0"),
                ("H4", scores["H4"] <= 50.0, f"H4={scores["H4"]:.1f}<=50.0"),
                ("H1", scores["H1"] <= cls.BEARISH_THRESHOLD, f"H1={scores["H1"]:.1f}<=45.0"),
            )
        failed = tuple(f"{name}_failed" for name, ok, _ in checks if not ok)
        detail = tuple(text for _, _, text in checks)
        return not failed, detail + (f"failed={','.join(failed) if failed else 'none'}",)

    @classmethod
    def _role_reasons(cls, reports: Mapping[str, AnalysisReport], direction: str) -> tuple[str, ...]:
        roles = cls._role_scores(reports)
        w1 = cls._direction_score(reports["W1"])
        d1 = cls._direction_score(reports["D1"])
        h4 = cls._direction_score(reports["H4"])
        h1 = cls._direction_score(reports["H1"])
        m15 = roles["setup"]
        m5 = roles["execution"]
        if direction == "BUY":
            macro_text = "W1 bullish with D1 non-bearish correction" if w1 >= cls.BULLISH_THRESHOLD and d1 > 35 else "macro context not bullish"
            context_text = "H4 location supportive and H1 bullish" if h4 >= 50 and h1 >= cls.BULLISH_THRESHOLD else "H4/H1 context not supportive"
        else:
            macro_text = "W1 bearish with D1 non-bullish correction" if w1 <= cls.BEARISH_THRESHOLD and d1 < 65 else "macro context not bearish"
            context_text = "H4 location supportive and H1 bearish" if h4 <= 50 and h1 <= cls.BEARISH_THRESHOLD else "H4/H1 context not supportive"
        return (
            f"Macro regime: {macro_text} (W1={w1:.1f}, D1={d1:.1f}, role={roles['macro']:.1f})",
            f"Setup context: {context_text} (H4={h4:.1f}, H1={h1:.1f}, role={roles['context']:.1f})",
            f"M15 setup score: {m15:.1f}/100",
            f"M5 execution trigger: {m5:.1f}/100",
        )

    @classmethod
    def _setup_direction(cls, report: AnalysisReport) -> tuple[str | None, str]:
        """Resolve an M15 setup hypothesis without forcing a trade signal."""
        signal = str(getattr(report, "signal", "")).upper()
        if signal in cls.EXECUTABLE:
            return ("BUY" if "BUY" in signal else "SELL", "signal")

        bias = str(getattr(report, "decision_bias", "neutral")).lower().strip()
        if bias not in cls.SETUP_BIAS_DIRECTIONS:
            return None, "none"

        decay = str(getattr(report, "signal_decay", "FRESH")).upper()
        crisis = str(getattr(report, "crisis_mode", "NORMAL")).upper()
        macro_risk = str(getattr(report, "macro_risk_level", "NORMAL")).upper()
        if decay in {"STALE", "INVALID"} or crisis in {"CRISIS", "EXTREME"}:
            return None, "blocked_safety_state"
        if bool(getattr(report, "portfolio_risk_blocked", False)):
            return None, "portfolio_risk"
        if macro_risk == "CRISIS":
            return None, "macro_crisis"

        return cls.SETUP_BIAS_DIRECTIONS[bias], "decision_bias"

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
        directional_contributions = getattr(report, "directional_contributions", {}) or {}
        directional_text = ",".join(
            f"{name}={float(value):+.2f}"
            for name, value in directional_contributions.items()
        ) or "none"
        positive_directional = sorted(
            ((name, float(value)) for name, value in directional_contributions.items() if float(value) > 0),
            key=lambda item: (-item[1], item[0]),
        )
        negative_directional = sorted(
            ((name, float(value)) for name, value in directional_contributions.items() if float(value) < 0),
            key=lambda item: (item[1], item[0]),
        )
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

        raw_score_signal = (
            "BUY" if score >= 60.0 else
            "SELL" if score <= 40.0 else
            "NEUTRAL"
        )
        execution_blockers = [
            reason for reason in all_reasons
            if reason.startswith("Execution blocked by")
        ]
        diagnostics = [
            f"m15_signal={signal or 'NONE'}",
            f"m15_raw_score_signal={raw_score_signal}",
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
            f"m15_directional_contributions={directional_text}",
            f"m15_directional_total={sum(float(value) for value in directional_contributions.values()):+.2f}",
            f"m15_directional_positive={','.join(f'{name}:{value:+.2f}' for name, value in positive_directional) or 'none'}",
            f"m15_directional_negative={','.join(f'{name}:{value:+.2f}' for name, value in negative_directional) or 'none'}",
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
        if execution_blockers:
            diagnostics.append("m15_execution_blockers=" + "|".join(execution_blockers))
        if blocking_reasons:
            diagnostics.append("m15_blockers=" + "|".join(blocking_reasons))
        if warnings:
            diagnostics.append("m15_warnings=" + "|".join(warnings))
        if all_reasons:
            diagnostics.append("m15_reasons=" + "|".join(all_reasons))
        return tuple(diagnostics)

    @classmethod
    def _aligned_higher_timeframes(cls, reports: Mapping[str, AnalysisReport], direction: str) -> int:
        # Retained as an observability metric; role gates below are authoritative.
        count = 0
        for timeframe in ("W1", "D1", "H4", "H1"):
            score = cls._direction_score(reports[timeframe])
            if direction == "BUY" and score >= cls.BULLISH_THRESHOLD:
                count += 1
            elif direction == "SELL" and score <= cls.BEARISH_THRESHOLD:
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
        raw_signal = str(setup.signal).upper()
        direction, setup_source = self._setup_direction(setup)
        if direction is None:
            diagnostics = list(self._m15_diagnostics(setup, raw_signal))
            diagnostics.insert(1, "setup_direction=NONE")
            return None, tuple(diagnostics)

        setup_metadata = [
            f"setup_direction={direction}",
            f"setup_direction_source={setup_source}",
            f"m15_raw_signal={raw_signal or 'NONE'}",
        ]

        alignment = self._alignment_score(reports)
        role_scores = self._role_scores(reports)
        aligned_htf = self._aligned_higher_timeframes(reports, direction)
        lower_score = role_scores["execution"]
        setup_quality = float(setup.trade_quality or 0.0)
        confidence = float(setup.confidence or 0.0)
        rr = setup.risk_reward

        role_reasons = self._role_reasons(reports, direction)
        reasons: list[str] = [
            *setup_metadata,
            f"MTF role alignment (telemetry): {alignment:.1f}/100",
            f"Higher-timeframe directional alignment (telemetry): {aligned_htf}/4",
            *role_reasons,
            f"M15 setup quality: {setup_quality:.0f}/100",
        ]
        rejection_codes: list[str] = list(
            self._m15_diagnostics(setup, raw_signal)
        )
        rejection_codes.extend(setup_metadata)

        higher_context_ok, htf_diagnostics = self._higher_context_diagnostics(reports, direction)
        trigger_ok = (
            lower_score >= self.M5_BUY_TRIGGER
            if direction == "BUY"
            else lower_score <= self.M5_SELL_TRIGGER
        )
        aligned = higher_context_ok and trigger_ok
        if not higher_context_ok:
            rejection_codes.append(
                f"role_context=blocked,direction={direction},macro={role_scores['macro']:.1f},context={role_scores['context']:.1f}," + ",".join(htf_diagnostics)
            )
            reasons.append("Macro/context roles do not support the M15 setup.")
        if not trigger_ok:
            rejection_codes.append(
                f"execution_trigger={lower_score:.1f},required={'52.0' if direction == 'BUY' else '48.0'}"
            )
            reasons.append("M5 execution trigger is not confirmed; waiting is required.")
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
            role_scores=role_scores,
            market_story=role_reasons,
        ), ()


__all__ = ["MultiTimeframeAnalysisEngine", "MultiTimeframeDecision"]
