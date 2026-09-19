from worker.executors import strategy_evaluation


def test_strategy_evaluation_worker_returns_comparison():
    result = strategy_evaluation({
        "strategies": [
            {"strategy_id": "champ", "name": "Champion", "validation": {"oos_positive": True, "positive_oos_ratio": .8, "robust": True}, "observations": [
                {"market": "Forex", "symbol": "EURUSD", "timeframe": "1h", "regime": "TRENDING",
                 "trades": 50, "win_rate": .55, "expectancy": .01, "max_drawdown": -.10}
            ]},
            {"strategy_id": "chall", "name": "Challenger", "validation": {"oos_positive": True, "positive_oos_ratio": .8, "robust": True}, "observations": [
                {"market": "Forex", "symbol": "EURUSD", "timeframe": "1h", "regime": "TRENDING",
                 "trades": 50, "win_rate": .60, "expectancy": .03, "max_drawdown": -.05}
            ]},
        ],
        "champion_id": "champ",
        "challenger_id": "chall",
    })
    assert result["comparison"]["comparable"] is True
    assert result["comparison"]["challenger_eligible"] is True
    assert len(result["strategies"]) == 2


def test_strategy_evaluation_can_build_validation_from_research_data():
    prices = [100.0 * (1.001 ** i) for i in range(61)]
    result = strategy_evaluation({
        "strategies": [
            {
                "strategy_id": "research",
                "name": "Research Candidate",
                "dna": {"threshold": 0.001},
                "research_validation": {
                    "prices": prices,
                    "mode": "walk_forward",
                    "train_size": 40,
                    "test_size": 10,
                    "robust": True,
                },
                "observations": [
                    {"market": "Forex", "symbol": "EURUSD", "timeframe": "1h", "regime": "TRENDING",
                     "trades": 50, "win_rate": .60, "expectancy": .02, "max_drawdown": -.05}
                ],
            }
        ]
    })
    evidence = result["strategies"][0]["validation_evidence"]
    assert evidence["oos_positive"] is True
    assert evidence["robust"] is True
    assert evidence["validated_version"] == 1
    assert evidence["dna_fingerprint"]
    assert evidence["diagnostics"]["robustness"]["case_count"] == 9
    assert evidence["diagnostics"]["overfitting"]["overfitting_warning"] is False


def test_strategy_evaluation_rejects_stale_validation_identity():
    from analysis.strategy_intelligence import StrategyIntelligenceEngine
    engine = StrategyIntelligenceEngine()
    fingerprint = engine.dna_fingerprint({"threshold": 1})
    with __import__("pytest").raises(ValueError, match="current strategy version"):
        strategy_evaluation({
            "strategies": [{
                "strategy_id": "stale",
                "dna": {"threshold": 1},
                "validation": {
                    "oos_positive": True,
                    "positive_oos_ratio": .8,
                    "robust": True,
                    "validated_version": 2,
                    "dna_fingerprint": fingerprint,
                },
                "observations": [],
            }]
        })


def test_strategy_research_validation_uses_robustness_engine_result():
    prices = [100.0 + i for i in range(61)]
    result = strategy_evaluation({
        "strategies": [{
            "strategy_id": "robust-auto",
            "dna": {"threshold": 0.001},
            "research_validation": {
                "prices": prices,
                "mode": "oos",
                "train_ratio": .7,
                "robustness_thresholds": (0.0, 0.001),
                "robustness_fees": (0.0, 0.0001),
            },
        }]
    })
    evidence = result["strategies"][0]["validation_evidence"]
    assert evidence["robust"] is True
