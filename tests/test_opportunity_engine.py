from dataclasses import dataclass

from analysis.opportunity_engine import OpportunityEngine


@dataclass
class Result:
    symbol: str
    signal: str
    confidence: float
    trade_quality: float | None
    risk_reward: float | None


def test_opportunity_ranking_is_explainable_and_deterministic():
    results = [
        Result("BTCUSDT", "BUY", 0.8, 85, 2.0),
        Result("EURUSD", "NO_TRADE", 0.9, 90, 3.0),
    ]
    ranked = OpportunityEngine.rank(results)
    assert ranked[0].symbol == "BTCUSDT"
    assert ranked[0].rank == 1
    assert ranked[0].rationale


def test_heatmap_contains_strength_and_score():
    result = OpportunityEngine.heatmap([Result("AAPL", "SELL", 0.9, 90, 3.0)])
    assert result[0]["symbol"] == "AAPL"
    assert result[0]["strength"] in {"HIGH", "MEDIUM", "LOW"}
