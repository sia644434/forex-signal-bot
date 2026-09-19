from worker.executors import strategy_evaluation


def test_strategy_evaluation_worker_returns_comparison():
    result = strategy_evaluation({
        "strategies": [
            {"strategy_id": "champ", "name": "Champion", "observations": [
                {"market": "Forex", "symbol": "EURUSD", "timeframe": "1h", "regime": "TRENDING",
                 "trades": 50, "win_rate": .55, "expectancy": .01, "max_drawdown": -.10}
            ]},
            {"strategy_id": "chall", "name": "Challenger", "observations": [
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
