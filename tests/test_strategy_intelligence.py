from analysis.strategy_intelligence import StrategyIntelligenceEngine, StrategyObservation


def obs(expectancy, trades=25, drawdown=-0.05):
    return StrategyObservation("Forex", "EURUSD", "1h", "TRENDING", trades, .6, expectancy, drawdown, .9)


def test_strategy_lifecycle_and_challenger_promotion():
    engine = StrategyIntelligenceEngine()
    engine.register("s1", "Base")
    engine.register("s2", "Variant", parent_id="s1")
    engine.observe("s1", obs(.01, 50, -.10))
    engine.observe("s2", obs(.03, 50, -.05))
    comparison = engine.compare("s1", "s2")
    assert comparison["challenger_eligible"] is True
    engine.promote("s1", "s2")
    assert engine.snapshot()[0]["status"] == "RETIRED"
    assert engine.snapshot()[1]["status"] == "CHAMPION"


def test_negative_expectancy_pauses_strategy():
    engine = StrategyIntelligenceEngine()
    engine.register("bad", "Bad")
    result = engine.observe("bad", obs(-.02, 25))
    assert result["status"] == "PAUSED"
