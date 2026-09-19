from analysis.strategy_intelligence import StrategyIntelligenceEngine, StrategyObservation, StrategyValidationEvidence


def obs(expectancy, trades=25, drawdown=-0.05):
    return StrategyObservation("Forex", "EURUSD", "1h", "TRENDING", trades, .6, expectancy, drawdown, .9)


def test_strategy_lifecycle_and_challenger_promotion():
    engine = StrategyIntelligenceEngine()
    engine.register("s1", "Base")
    engine.register("s2", "Variant", parent_id="s1")
    engine.observe("s1", obs(.01, 50, -.10))
    engine.observe("s2", obs(.03, 50, -.05))
    evidence_s1 = StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["s1"].dna))
    evidence_s2 = StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["s2"].dna))
    engine.attach_validation("s1", evidence_s1)
    engine.attach_validation("s2", evidence_s2)
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


def test_persistent_negative_strategy_is_retired_automatically():
    engine = StrategyIntelligenceEngine()
    engine.register("bad-long", "Persistently Bad")
    result = engine.observe("bad-long", obs(-.03, 120, -.25))
    assert result["status"] == "RETIRED"
    assert "negative expectancy" in result["status"] or engine.snapshot()[0]["retirement_reason"]


def test_strategy_weakness_detection_adaptation_and_rollback():
    engine = StrategyIntelligenceEngine()
    engine.register("s", "Adaptive", dna={"threshold": 1})
    engine.observe("s", StrategyObservation("Forex", "EURUSD", "1h", "RANGING", 30, .45, -.02, -.12, .9))
    weaknesses = engine.weaknesses("s")
    assert weaknesses and "negative_expectancy" in weaknesses[0]["reasons"]
    proposal = engine.adapt("s", {"threshold": 2}, reason="reduce weak regime exposure")
    assert proposal["status"] == "PROPOSED"
    assert engine.snapshot()[0]["dna"]["threshold"] == 1
    with __import__("pytest").raises(ValueError):
        engine.apply_adaptation("s", StrategyValidationEvidence(True, 0.8, robust=False))
    adapted = engine.apply_adaptation("s", StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["s"].dna)))
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
    evidence_champ = StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["champ"].dna))
    evidence_chall = StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["chall"].dna))
    engine.attach_validation("champ", evidence_champ)
    engine.attach_validation("chall", evidence_chall)
    engine.promote("champ", "chall")
    assert engine.snapshot()[1]["audit_log"][-1]["action"] == "PROMOTE"


def test_positive_strategy_requires_current_validation_for_challenger_status():
    engine = StrategyIntelligenceEngine()
    engine.register("s", "Candidate")
    result = engine.observe("s", obs(.02, 50))
    assert result["status"] == "CANDIDATE"
    evidence = StrategyValidationEvidence(
        True, .8, robust=True, validated_version=1,
        dna_fingerprint=engine.dna_fingerprint(engine._records["s"].dna),
    )
    engine.attach_validation("s", evidence)
    result = engine.evaluate("s")
    assert result["status"] == "CHALLENGER"
    assert result["validation_ready"] is True


def test_validation_blocks_unverified_challenger():
    engine = StrategyIntelligenceEngine()
    engine.register("champ", "Champion")
    engine.register("chall", "Challenger")
    engine.observe("champ", obs(.01, 50))
    engine.observe("chall", obs(.03, 50))
    result = engine.compare("champ", "chall")
    assert result["validation_ready"] is False
    assert result["challenger_eligible"] is False


def test_validation_is_invalidated_by_version_and_dna_change():
    engine = StrategyIntelligenceEngine()
    engine.register("s", "Versioned", dna={"threshold": 1})
    evidence = StrategyValidationEvidence(True, 0.8, robust=True, validated_version=1, dna_fingerprint=engine.dna_fingerprint(engine._records["s"].dna))
    engine.attach_validation("s", evidence)
    engine.propose_adaptation("s", {"threshold": 2}, reason="validated change")
    applied = engine.apply_adaptation("s", evidence)
    assert applied["version"] == 2
    assert engine.snapshot()[0]["validation_evidence"] is None
    with __import__("pytest").raises(ValueError):
        engine.attach_validation("s", evidence)


def test_continuous_evaluation_records_validation_aware_history():
    engine = StrategyIntelligenceEngine()
    engine.register("s", "Tracked", dna={"threshold": 1})
    evidence = StrategyValidationEvidence(
        True, .8, robust=True, validated_version=1,
        dna_fingerprint=engine.dna_fingerprint(engine._records["s"].dna),
    )
    result = engine.continuous_evaluate({"s": evidence})
    assert result[0]["validation_ready"] is True
    snapshot = engine.snapshot()[0]
    assert len(snapshot["evaluation_history"]) == 1
    assert snapshot["evaluation_history"][0]["version"] == 1
    assert snapshot["evaluation_history"][0]["validation_ready"] is True
