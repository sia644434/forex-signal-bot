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


def test_strategy_weakness_detection_adaptation_and_rollback():
    engine = StrategyIntelligenceEngine()
    engine.register("s", "Adaptive", dna={"threshold": 1})
    engine.observe("s", StrategyObservation("Forex", "EURUSD", "1h", "RANGING", 30, .45, -.02, -.12, .9))
    weaknesses = engine.weaknesses("s")
    assert weaknesses and "negative_expectancy" in weaknesses[0]["reasons"]
    adapted = engine.adapt("s", {"threshold": 2}, reason="reduce weak regime exposure")
    assert adapted["version"] == 2
    assert adapted["dna"]["threshold"] == 2
    rolled = engine.rollback("s", reason="adaptation regressed validation")
    assert rolled["version"] == 3
    assert rolled["dna"]["threshold"] == 1
    assert [e["action"] for e in engine.snapshot()[0]["audit_log"][-2:]] == ["ADAPT", "ROLLBACK"]


def test_strategy_continuous_evaluation_and_promotion_audit():
    engine = StrategyIntelligenceEngine()
    engine.register("champ", "Champion")
    engine.register("chall", "Challenger", parent_id="champ")
    engine.observe("champ", StrategyObservation("Forex", "EURUSD", "1h", "TRENDING", 50, .55, .01, -.10))
    engine.observe("chall", StrategyObservation("Forex", "EURUSD", "1h", "TRENDING", 50, .60, .03, -.05))
    evaluated = engine.continuous_evaluate()
    assert len(evaluated) == 2
    engine.promote("champ", "chall")
    assert engine.snapshot()[1]["audit_log"][-1]["action"] == "PROMOTE"
