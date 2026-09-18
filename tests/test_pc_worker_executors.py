import numpy as np

from worker.executors import (
    backtest, candle_batch_analysis, deep_learning_training, ensemble_training,
    feature_engineering, gru_training, lstm_training, monte_carlo,
    multitimeframe_analysis, random_forest_training, timeseries_training,
    transformer_training, walk_forward,
)


def candles(n=120):
    close = 100 + np.cumsum(np.sin(np.arange(n) / 7) * .3 + .05)
    return [{"close": float(v)} for v in close]


def xy():
    x = np.arange(1200, dtype=float).reshape(120, 10)
    y = x.sum(axis=1) + np.sin(np.arange(120))
    return x.tolist(), y.tolist()


def test_core_executors():
    data = candles()
    assert backtest({"data": data})["trades"] >= 0
    assert walk_forward({"data": data, "train_size": 50, "test_size": 20})["windows"] >= 1
    mc = monte_carlo({"data": data, "simulations": 100, "horizon": 20, "seed": 1})
    assert mc["p05"] <= mc["median"] <= mc["p95"]
    assert feature_engineering({"data": data})["rows"] > 0
    assert candle_batch_analysis({"data": data})["rows"] == 120


def test_timeframe_and_ensemble():
    data = candles()
    assert multitimeframe_analysis({"timeframes": {"M5": data, "H1": data}})["timeframes"]
    x, y = xy()
    assert ensemble_training({"X": x, "y": y, "test_size": 20})["members"] == 3
    assert timeseries_training({"X": x, "y": y, "test_size": 20})["model"] == "time_series_gradient_boost"


def test_bounded_limited_models():
    x, y = xy()
    for fn, name in [(deep_learning_training, "deep_learning_bounded"), (transformer_training, "small_transformer_bounded"), (lstm_training, "lstm_bounded"), (gru_training, "gru_bounded")]:
        result = fn({"X": x, "y": y, "test_size": 20, "max_iter": 20, "hidden_layers": [16, 8]})
        assert result["model"] == name
        assert result["execution"] == "bounded_cpu_fallback"


def test_random_forest():
    x, y = xy()
    result = random_forest_training({"X": x, "y": y, "n_estimators": 20})
    assert result["model"] == "random_forest"
    assert result["rmse"] >= 0


def test_backtest_rejects_invalid_market_data_and_parameters():
    import pytest

    with pytest.raises(ValueError):
        backtest({"data": [{"close": 100}, {"close": float("nan")}]})
    with pytest.raises(ValueError):
        backtest({"data": [{"close": 100}, {"close": 101}], "fee": -0.01})
    with pytest.raises(ValueError):
        monte_carlo({"data": candles(), "simulations": 0})


def test_walk_forward_uses_training_history_without_scoring_it():
    data = candles(80)
    result = walk_forward({"data": data, "train_size": 40, "test_size": 20})
    assert result["windows"] == 2
    assert all(window["train_size"] == 40 and window["test_size"] == 20 for window in result["results"])
    assert all(window["final_equity"] > 0 for window in result["results"])


def test_monte_carlo_is_deterministic_with_seed():
    payload = {"data": candles(), "simulations": 100, "horizon": 20, "seed": 123}
    assert monte_carlo(payload) == monte_carlo(payload)
