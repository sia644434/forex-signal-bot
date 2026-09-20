from analysis.decision_engine import (
    DecisionEngine,
    DecisionResult,
)



class MockAnalysis:
    """
    Fake analysis object
    for testing DecisionEngine.
    """

    smart_money_score = 90

    structure_score = 80

    price_action_score = 70

    trend_score = 60

    momentum_score = 75


    elliott_score = 50

    harmonic_score = 50

    wyckoff_score = 50


    smc_bias = "bullish"



def test_decision_engine_returns_result():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert isinstance(
        result,
        DecisionResult
    )



def test_decision_engine_has_signal():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert result.signal in [

        "STRONG BUY",

        "BUY",

        "NEUTRAL",

        "SELL",

        "STRONG SELL",

    ]



def test_decision_engine_confidence_range():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert 0 <= result.confidence <= 100



def test_bullish_bias():

    engine = DecisionEngine()

    result = engine.decide(
        MockAnalysis()
    )


    assert result.bias == "bullish"


class SupplyDemandAnalysis(MockAnalysis):
    supply_demand_score = -100
    trend_score = 60


class BullishSupplyDemandAnalysis(SupplyDemandAnalysis):
    supply_demand_score = 100


def test_supply_demand_uses_explicit_score_not_trend_score():
    engine = DecisionEngine()

    bearish = engine.decide(SupplyDemandAnalysis())
    bullish = engine.decide(BullishSupplyDemandAnalysis())

    assert bullish.score > bearish.score




def test_decision_component_contributions_reconcile_with_score():
    class Analysis:
        smart_money_score = -35.0
        structure_score = 20.0
        trend_score = -20.0
        price_action_score = 0.0
        supply_demand_score = -20.0
        momentum_score = -10.0
        candlestick_score = 0.0
        elliott_score = 15.0
        harmonic_score = -25.0
        brooks_score = -20.0
        wyckoff_score = -20.0

    result = DecisionEngine().decide(Analysis())
    assert result.component_contributions
    assert round(sum(result.component_contributions.values()), 2) == result.score
    assert result.component_contributions["structure"] == 8.1
    assert result.directional_contributions["structure"] == 0.6
    assert result.directional_contributions["smart_money"] == -3.5
    assert result.directional_contributions["elliott"] == 0.45
    assert abs(sum(result.directional_contributions.values()) - (result.score - 50.0)) <= 0.01
    assert result.score < 50.0


def test_decision_component_contributions_are_directionally_symmetric():
    class Bullish:
        smart_money_score = 35.0
        structure_score = 20.0
        trend_score = 20.0
        price_action_score = 20.0
        supply_demand_score = 20.0
        momentum_score = 10.0
        candlestick_score = 10.0
        elliott_score = 15.0
        harmonic_score = 25.0
        brooks_score = 20.0
        wyckoff_score = 20.0

    class Bearish:
        smart_money_score = -35.0
        structure_score = -20.0
        trend_score = -20.0
        price_action_score = -20.0
        supply_demand_score = -20.0
        momentum_score = -10.0
        candlestick_score = -10.0
        elliott_score = -15.0
        harmonic_score = -25.0
        brooks_score = -20.0
        wyckoff_score = -20.0

    bullish = DecisionEngine().decide(Bullish())
    bearish = DecisionEngine().decide(Bearish())
    assert round(bullish.score + bearish.score, 2) == 100.0
    assert bullish.signal == "BUY"
    assert bearish.signal == "SELL"
    for name in bullish.directional_contributions:
        assert round(bullish.directional_contributions[name] + bearish.directional_contributions[name], 4) == 0.0
