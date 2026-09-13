from analysis.risk_engine import RiskEngine


def test_directional_strength_is_symmetric_for_decision_scores():
    assert RiskEngine._directional_strength(0) == 100
    assert RiskEngine._directional_strength(100) == 100
    assert RiskEngine._directional_strength(25) == 50
    assert RiskEngine._directional_strength(75) == 50
    assert RiskEngine._directional_strength(50) == 0


def test_dynamic_risk_percent_is_symmetric_for_extreme_scores():
    engine = RiskEngine()
    assert engine._dynamic_risk_percent(0.90, 100) == 2.0
    assert engine._dynamic_risk_percent(0.90, 0) == 2.0
    assert engine._dynamic_risk_percent(0.75, 75) == 1.5
    assert engine._dynamic_risk_percent(0.75, 25) == 1.5


def test_risk_level_is_symmetric_for_bullish_and_bearish_scores():
    assert RiskEngine._calculate_risk_level(0.85, 100) == "LOW"
    assert RiskEngine._calculate_risk_level(0.85, 0) == "LOW"


def test_trade_quality_is_symmetric_for_bullish_and_bearish_scores():
    bullish = RiskEngine._trade_quality(0.90, 100, "NORMAL")
    bearish = RiskEngine._trade_quality(0.90, 0, "NORMAL")
    assert bullish == bearish
