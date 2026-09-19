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
            return None, (
                f"m15_signal={direction or 'NONE'}",
                f"m15_score={self._direction_score(setup):.1f}",
                f"m15_quality={float(setup.trade_quality or 0.0):.0f}",
                f"m15_confidence={float(setup.confidence or 0.0):.2f}",
            )
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
