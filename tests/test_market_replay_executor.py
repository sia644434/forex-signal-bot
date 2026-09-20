from datetime import datetime, timedelta, timezone

from worker.executors import market_replay


def test_market_replay_produces_trace():
    start = datetime(2026, 9, 19, tzinfo=timezone.utc)
    candles = []
    for i, close in enumerate([100, 101, 100, 102, 103, 104, 103]):
        candles.append({
            "symbol": "EURUSD",
            "timestamp": (start + timedelta(minutes=15 * i)).isoformat(),
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100,
        })
    result = market_replay({"candles": candles})
    assert result["steps"] == 3
    assert all("signal" in item for item in result["trace"])



def test_market_replay_preserves_profile_execution_context():
    from profiles import AnalysisProfile, ProfileStyle, build_execution_context, context_payload
    from worker.executors import market_replay
    from datetime import datetime, timezone, timedelta

    profile = AnalysisProfile("replay-profile", "Replay", [ProfileStyle("momentum")], version=2)
    context = build_execution_context(profile, "REPLAY", user_id="42", experiment_id="exp-replay", requested_capabilities=["profile_analysis", "replay"])
    candles = []
    for i in range(8):
        price = 100 + i
        candles.append({"symbol": "EURUSD", "timestamp": (datetime(2026, 9, 20, tzinfo=timezone.utc) + timedelta(minutes=i)).isoformat(), "open": price, "high": price + 0.5, "low": price - 0.5, "close": price, "volume": 1})
    result = market_replay(context_payload(context, {"candles": candles}))
    assert result["execution_context"]["profile_id"] == "replay-profile"
    assert result["execution_context"]["profile_version"] == 2
    assert result["execution_context"]["user_id"] == "42"
    assert result["execution_context"]["experiment_id"] == "exp-replay"
    assert result["style_ids"] == ["momentum"]
