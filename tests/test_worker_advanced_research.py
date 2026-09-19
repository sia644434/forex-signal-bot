from worker.executors import correlation_matrix, counterfactual_batch, portfolio_stress, stress_sensitivity


def test_worker_portfolio_stress_executor():
    result = portfolio_stress({
        "positions": [{"symbol": "BTCUSD", "market": "crypto", "quantity": 1, "price": 100}],
        "shocks": {"BTCUSD": -0.25},
    })
    assert result["estimated_loss"] == 25


def test_worker_correlation_executor():
    result = correlation_matrix({"returns": {"A": [1, 2, 3], "B": [2, 4, 6]}})
    assert result["correlation"]["A"]["B"] == 1


def test_worker_sensitivity_executor():
    result = stress_sensitivity({
        "positions": [{"symbol": "EURUSD", "market": "forex", "quantity": 1, "price": 100}],
        "shocks": {"EURUSD": -0.1},
        "scenarios": [-0.1, 0.1],
    })
    assert len(result["scenarios"]) == 2


def test_worker_counterfactual_batch_executor():
    result = counterfactual_batch({
        "cases": [{"baseline_decision": "BUY", "confidence": 0.2}],
    })
    assert result["results"][0]["changed_decision"] == "WAIT"
