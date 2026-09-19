from datetime import datetime, timedelta, timezone

from analysis.time_machine import TimeMachineEngine


def _candles():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    values = [100, 101, 100, 102, 103, 104, 103]
    return [
        {
            "symbol": "EURUSD",
            "timestamp": (start + timedelta(minutes=15 * i)).isoformat(),
            "open": value,
            "high": value + 1,
            "low": value - 1,
            "close": value,
            "volume": 100,
        }
        for i, value in enumerate(values)
    ]


def test_time_machine_is_deterministic_and_prefix_only():
    engine = TimeMachineEngine()
    first = engine.run(_candles(), start_index=5)
    second = engine.run(_candles(), start_index=5)
    assert first == second
    assert first["steps"] == 3
    assert [item["index"] for item in first["trace"]] == [4, 5, 6]
    assert all("counterfactual" in item for item in first["trace"])


def test_time_machine_counterfactual_is_traceable():
    result = TimeMachineEngine().run(
        _candles(),
        start_index=5,
        counterfactual={"risk_valid": False},
    )
    for item in result["trace"]:
        assert item["counterfactual"]["changed_decision"] == "NO_TRADE"
        assert "risk_valid=false" in item["counterfactual"]["changed_conditions"]
