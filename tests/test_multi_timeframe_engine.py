from __future__ import annotations

from types import SimpleNamespace

from analysis.multi_timeframe_engine import MultiTimeframeAnalysisEngine


def report(score: float, signal: str = "NO_TRADE", *, quality: int = 80, confidence: float = 0.8, rr: float = 2.0):
    return SimpleNamespace(
        score=score,
        signal=signal,
        trade_quality=quality,
        confidence=confidence,
        risk_reward=rr,
        conflict_state="CONSENSUS",
        signal_decay="FRESH",
        portfolio_risk_blocked=False,
        symbol="BTCUSDT",
    )


def candles_by_timeframe():
    return {timeframe: [object()] for timeframe in MultiTimeframeAnalysisEngine.TIMEFRAME_ORDER}


class FakeEngine:
    def __init__(self, reports):
        self.reports = reports

    def analyze(self, candles, *, signal_max_age_seconds):
        timeframe = candles[0]
        return self.reports[timeframe]


def test_multi_timeframe_requires_all_context_layers():
    engine = MultiTimeframeAnalysisEngine(FakeEngine({}))
    candles = candles_by_timeframe()
    candles.pop("W1")
    assert engine.analyze(candles) is None


def test_multi_timeframe_accepts_aligned_m15_setup_and_m5_confirmation():
    reports = {
        "W1": report(68),
        "D1": report(72),
        "H4": report(70),
        "H1": report(67),
        "M15": report(78, "BUY", quality=85, confidence=0.82, rr=2.4),
        "M5": report(66),
    }
    engine = MultiTimeframeAnalysisEngine(FakeEngine(reports))
    candles = {key: [key] for key in reports}
    result = engine.analyze(candles)
    assert result is not None
    assert result.direction == "BUY"
    assert result.alignment_score > 60
    assert result.lower_timeframe_score == 66


def test_multi_timeframe_rejects_higher_timeframe_conflict():
    reports = {
        "W1": report(30),
        "D1": report(35),
        "H4": report(32),
        "H1": report(70),
        "M15": report(78, "BUY", quality=85, confidence=0.82, rr=2.4),
        "M5": report(66),
    }
    engine = MultiTimeframeAnalysisEngine(FakeEngine(reports))
    candles = {key: [key] for key in reports}
    assert engine.analyze(candles) is None


def test_multi_timeframe_rejects_low_risk_reward():
    reports = {
        "W1": report(68),
        "D1": report(72),
        "H4": report(70),
        "H1": report(67),
        "M15": report(78, "BUY", quality=85, confidence=0.82, rr=1.2),
        "M5": report(66),
    }
    engine = MultiTimeframeAnalysisEngine(FakeEngine(reports))
    candles = {key: [key] for key in reports}
    assert engine.analyze(candles) is None
