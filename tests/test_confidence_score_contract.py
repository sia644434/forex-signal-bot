from analysis.confidence_engine import ConfidenceEngine


class SignedAnalysis:
    smart_money_score = 20
    structure_score = -20
    price_action_score = 0
    momentum_score = 20
    trend_score = -20
    candlestick_score = 0
    elliott_score = 20
    harmonic_score = -20
    brooks_score = 0
    wyckoff_score = 20
    volatility_score = 2.5


def test_signed_score_normalization_matches_decision_contract():
    engine = ConfidenceEngine()
    assert engine.normalize_signed_score(-20) == 40.0
    assert engine.normalize_signed_score(0) == 50.0
    assert engine.normalize_signed_score(20) == 60.0


def test_signed_component_votes_preserve_direction():
    engine = ConfidenceEngine()
    assert engine.direction(engine.normalize_signed_score(-20)) == "bearish"
    assert engine.direction(engine.normalize_signed_score(0)) == "neutral"
    assert engine.direction(engine.normalize_signed_score(20)) == "bullish"


def test_collect_engines_uses_signed_component_contract():
    engine = ConfidenceEngine()
    scores = engine._collect_engines(SignedAnalysis())
    assert scores["smart_money"] == 60.0
    assert scores["structure"] == 40.0
    assert scores["price_action"] == 50.0
    assert scores["supply_demand"] == 40.0


def test_volatility_remains_ratio_contract():
    engine = ConfidenceEngine()
    assert engine._calculate_market_uncertainty(SignedAnalysis()) >= 0.15
