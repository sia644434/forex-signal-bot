import pytest

from analysis.portfolio_engine import PortfolioEngine


def test_portfolio_snapshot_is_multi_asset_and_explainable():
    engine = PortfolioEngine()
    snapshot = engine.snapshot([
        {"symbol": "EURUSD", "market": "forex", "quantity": 1, "price": 100, "risk_amount": 2},
        {"symbol": "BTCUSD", "market": "crypto", "quantity": 2, "price": 50, "risk_amount": 3},
    ], equity_curve=[100, 98, 101])
    assert snapshot.total_exposure == 200
    assert snapshot.market_exposure["crypto"] == 100
    assert snapshot.total_risk == 5
    assert snapshot.drawdown < 0


def test_portfolio_correlation_matrix():
    matrix = PortfolioEngine.correlation_matrix({
        "A": [0.01, 0.02, -0.01],
        "B": [0.02, 0.04, -0.02],
    })
    assert matrix["A"]["A"] == 1
    assert matrix["A"]["B"] == pytest.approx(1)


def test_portfolio_rejects_mismatched_correlation_lengths():
    with pytest.raises(ValueError):
        PortfolioEngine.correlation_matrix({"A": [1, 2], "B": [1]})


def test_portfolio_stress_is_traceable():
    engine = PortfolioEngine()
    snapshot = engine.snapshot([{"symbol": "BTCUSD", "market": "crypto", "quantity": 1, "price": 100}])
    result = engine.stress(snapshot, {"BTCUSD": -0.2})
    assert result["estimated_loss"] == pytest.approx(20)
