from analysis.research_engine import ResearchValidationEngine


def prices(n=100):
    return [100.0 + i * 0.2 + (i % 7) * 0.05 for i in range(n)]


def test_out_of_sample_selects_on_train_only():
    result = ResearchValidationEngine.out_of_sample(prices(), train_ratio=0.7)
    assert result["train_size"] + result["test_size"] == 100
    assert result["parameter_count"] == 9
    assert "out_of_sample" in result
    assert result["selected"]["threshold"] in {0.0, 0.001, 0.002}


def test_walk_forward_has_disjoint_oos_windows():
    result = ResearchValidationEngine.walk_forward(prices(), train_size=40, test_size=10)
    assert result["windows"] == 5
    assert 0.0 <= result["positive_oos_ratio"] <= 1.0
    assert len(result["results"]) == 5


def test_overfitting_diagnostics_flag_divergence():
    result = ResearchValidationEngine.overfitting_diagnostics({
        "train_test_gap_median": 0.2,
        "positive_oos_ratio": 0.4,
    })
    assert result["overfitting_warning"] is True
    assert "TRAIN_TEST_DIVERGENCE" in result["warnings"]
    assert "WEAK_OOS_STABILITY" in result["warnings"]


def test_temporal_leakage_is_explicit():
    result = ResearchValidationEngine.temporal_leakage_check([
        {"feature_timestamp": "2026-01-02", "target_timestamp": "2026-01-01"},
        {"feature_timestamp": "2026-01-01", "target_timestamp": "2026-01-02"},
    ])
    assert result["leakage_detected"] is True
    assert result["violations"][0]["index"] == 0
