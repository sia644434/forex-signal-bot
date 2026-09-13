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
    assert engine._dynamic_risk_percent(0.75, 90) == 1.5
    assert engine._dynamic_risk_percent(0.75, 10) == 1.5


def test_risk_level_is_symmetric_for_bullish_and_bearish_scores():
    assert RiskEngine._calculate_risk_level(0.85, 100) == "LOW"
    assert RiskEngine._calculate_risk_level(0.85, 0) == "LOW"


def test_trade_quality_is_symmetric_for_bullish_and_bearish_scores():
    bullish = RiskEngine._trade_quality(0.90, 100, "NORMAL")
    bearish = RiskEngine._trade_quality(0.90, 0, "NORMAL")
    assert bullish == bearish


def test_custom_risk_reward_target_controls_take_profit_and_reported_ratio():
    engine = RiskEngine(risk_reward_target=3.0)

    result = engine.calculate(
        signal="BUY",
        current_price=100.0,
        risk_distance=2.0,
        confidence=0.90,
        score=100.0,
    )

    assert result.stop_loss == 98.0
    assert result.take_profit_1 == 102.0
    assert result.take_profit_2 == 106.0
    assert result.take_profit == 106.0
    assert result.take_profit_3 == 106.0
    assert result.risk_reward == 3.0


def test_custom_risk_reward_target_is_applied_to_sell_setups():
    engine = RiskEngine(risk_reward_target=2.5)

    result = engine.calculate(
        signal="SELL",
        current_price=100.0,
        risk_distance=2.0,
        confidence=0.90,
        score=0.0,
    )

    assert result.stop_loss == 102.0
    assert result.take_profit_1 == 98.0
    assert result.take_profit_2 == 95.0
    assert result.take_profit == 95.0
    assert result.risk_reward == 2.5


def test_risk_reward_target_must_be_positive():
    try:
        RiskEngine(risk_reward_target=0)
    except ValueError as exc:
        assert "risk_reward_target" in str(exc)
    else:
        raise AssertionError("RiskEngine must reject a non-positive risk-reward target")


def test_current_price_must_be_positive():
    engine = RiskEngine()

    for price in (0.0, -1.0):
        try:
            engine.calculate(
                signal="BUY",
                current_price=price,
                risk_distance=1.0,
                confidence=0.90,
                score=100.0,
            )
        except ValueError as exc:
            assert "current_price" in str(exc)
        else:
            raise AssertionError("RiskEngine must reject non-positive current prices")


def test_risk_distance_must_be_positive_when_explicitly_overridden():
    engine = RiskEngine()

    for distance in (0.0, -2.0):
        try:
            engine.calculate(
                signal="BUY",
                current_price=100.0,
                risk_distance=distance,
                confidence=0.90,
                score=100.0,
            )
        except ValueError as exc:
            assert "risk distance" in str(exc)
        else:
            raise AssertionError("RiskEngine must reject non-positive risk distances")
