from analysis.robustness_engine import RobustnessEngine
from worker.executors import robustness_analysis


def test_robustness_matrix_is_deterministic_and_reports_fragility_metrics():
    prices = [100, 101, 100.5, 102, 101.5, 103, 102.5]
    first = RobustnessEngine.evaluate(prices)
    second = RobustnessEngine.evaluate(prices)
    assert first == second
    assert first["case_count"] == 9
    assert 0 <= first["positive_case_ratio"] <= 1
    assert "return_range" in first and "drawdown_range" in first


def test_temporal_leakage_check_rejects_future_feature_timestamp():
    result = RobustnessEngine.temporal_leakage_check([
        {"feature_timestamp": "2026-01-01T10:00:00Z", "target_timestamp": "2026-01-01T11:00:00Z"},
        {"feature_timestamp": "2026-01-01T12:00:00Z", "target_timestamp": "2026-01-01T11:00:00Z"},
    ])
    assert result["leakage_detected"] is True
    assert result["violations"][0]["index"] == 1


def test_worker_robustness_executor_includes_leakage_report():
    result = robustness_analysis({
        "prices": [100, 101, 100.5, 102, 101.5, 103, 102.5],
        "thresholds": [0.0, 0.001],
        "fees": [0.0, 0.0001],
        "temporal_rows": [
            {"feature_timestamp": "2026-01-01T10:00:00Z", "target_timestamp": "2026-01-01T11:00:00Z"},
        ],
    })
    assert result["case_count"] == 4
    assert result["leakage"]["leakage_detected"] is False
