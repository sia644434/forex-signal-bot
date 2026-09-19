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



def test_multi_timeframe_m15_diagnostics_expose_precise_rejection_details():
    base = report(47, "NO_TRADE", quality=23, confidence=0.41)
    m15 = SimpleNamespace(
        **base.__dict__,
        trend="bearish",
        structure="NORMAL",
        decision_bias="bearish",
        agreement=0.54,
        bullish_votes=3,
        bearish_votes=4,
        neutral_votes=3,
        trade_grade="D",
        conflict_state="CONFLICT",
        scenario="NO_TRADE",
        signal_decay="FRESH",
        component_scores={
            "smart_money_score": 30.0,
            "structure_score": 20.0,
            "price_action_score": -10.0,
        },
        reasons=["Execution blocked by insufficient directional agreement"],
    )
    reports = {
        "W1": report(68),
        "D1": report(72),
        "H4": report(70),
        "H1": report(67),
        "M15": m15,
        "M5": report(66),
    }
    engine = MultiTimeframeAnalysisEngine(FakeEngine(reports))
    candles = {key: [key] for key in reports}
    decision, diagnostics = engine.analyze_with_diagnostics(candles)
    assert decision is None
    assert "m15_signal=NO_TRADE" in diagnostics
    assert "m15_score=47.0" in diagnostics
    assert "m15_thresholds=BUY>=60.0,SELL<=40.0" in diagnostics
    assert "m15_gap_to_buy=13.0" in diagnostics
    assert "m15_gap_to_sell=7.0" in diagnostics
    assert "m15_votes=bull:3,bear:4,neutral:3" in diagnostics
    assert "m15_components=smart_money_score=30.0,structure_score=20.0,price_action_score=-10.0" in diagnostics
    assert "m15_blockers=Execution blocked by insufficient directional agreement" in diagnostics


def test_multi_timeframe_diagnostics_explain_missing_context():
    engine = MultiTimeframeAnalysisEngine(FakeEngine({}))
    candles = candles_by_timeframe()
    candles.pop("M5")
    decision, diagnostics = engine.analyze_with_diagnostics(candles)
    assert decision is None
    assert diagnostics == ("missing_timeframes=M5",)


def test_multi_timeframe_diagnostics_explain_non_executable_m15():
    reports = {
        "W1": report(68),
        "D1": report(72),
        "H4": report(70),
        "H1": report(67),
        "M15": report(50, "NO_TRADE", quality=85, confidence=0.82, rr=2.4),
        "M5": report(66),
    }
    engine = MultiTimeframeAnalysisEngine(FakeEngine(reports))
    candles = {key: [key] for key in reports}
    decision, diagnostics = engine.analyze_with_diagnostics(candles)
    assert decision is None
    assert diagnostics[0] == "m15_signal=NO_TRADE"
