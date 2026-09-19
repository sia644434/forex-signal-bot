from datetime import datetime, timedelta, timezone

import pytest

from analysis.counterfactual_engine import CounterfactualEngine
from analysis.scenario_engine import BREAKOUT, ScenarioEngine
from analysis.signal_state import CRISIS, EXTREME, FRESH, INVALID, STALE, evaluate_signal_state
from analysis.statistical_engine import StatisticalEngine


def test_statistical_engine_returns_traceable_metrics():
    result = StatisticalEngine().evaluate([100, 101, 100, 102, 104])
    assert result.samples == 4
    assert 0 <= result.positive_probability <= 1
    assert result.max_drawdown < 0


def test_statistical_engine_rejects_invalid_prices():
    with pytest.raises(ValueError):
        StatisticalEngine().evaluate([100, float("nan"), 101])


def test_scenario_engine_detects_breakout():
    result = ScenarioEngine().evaluate([100, 101, 100, 101, 103], trend="bullish")
    assert result.primary == BREAKOUT
    assert result.evidence


def test_counterfactual_engine_is_traceable():
    result = CounterfactualEngine().evaluate("BUY", confidence=0.2)
    assert result.changed_decision == "WAIT"
    assert result.changed_conditions


def test_signal_state_classifies_decay_and_crisis():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    fresh = evaluate_signal_state(now - timedelta(seconds=10), now=now, volatility=0.01)
    stale = evaluate_signal_state(now - timedelta(seconds=200), now=now, volatility=0.11)
    assert fresh.decay == FRESH
    assert stale.decay == STALE
    assert stale.crisis_mode == EXTREME


def test_future_signal_fails_closed():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = evaluate_signal_state(now + timedelta(seconds=1), now=now)
    assert result.decay == INVALID
    assert result.crisis_mode == EXTREME


def test_crisis_threshold_is_explicit():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = evaluate_signal_state(now, now=now, volatility=0.06)
    assert result.crisis_mode == CRISIS
