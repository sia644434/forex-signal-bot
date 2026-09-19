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
