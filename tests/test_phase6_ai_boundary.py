from __future__ import annotations

from analysis import AnalysisResult, AnalysisScorer
from core.production_readiness import ProductionReadiness


def test_ai_is_not_a_production_scoring_component() -> None:
    result = AnalysisResult(
        trend="sideways",
        momentum="neutral",
        indicators={},
    )
    score = AnalysisScorer().score(result)
    assert all(component.name != "ai" for component in score.components)
    assert score.score == 0.0


def test_production_readiness_does_not_assume_ai_enabled() -> None:
    result = ProductionReadiness(
        {"OANDA_API_KEY": "configured", "AI_ENABLED": "false"}
    ).evaluate()
    assert not any("AI is enabled" in warning for warning in result.warnings)


def test_explicit_ai_enable_without_key_is_visible() -> None:
    result = ProductionReadiness(
        {"OANDA_API_KEY": "configured", "AI_ENABLED": "true"}
    ).evaluate()
    assert any("AI is explicitly enabled" in warning for warning in result.warnings)
