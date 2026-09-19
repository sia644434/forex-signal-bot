from datetime import datetime, timedelta, timezone

from analysis.macro_risk import FREDProvider, MacroEvent, MacroRiskEngine, NewsAPIProvider


def test_news_and_fred_providers_report_configuration_dependency():
    assert NewsAPIProvider(api_key="").available() is False
    assert FREDProvider(api_key="").available() is False


def test_macro_risk_assessment_is_explicit_and_deterministic():
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    events = [
        MacroEvent("newsapi", "1", "rate decision", now + timedelta(minutes=30), "HIGH", "NEWS"),
        MacroEvent("fred", "2", "CPI", now + timedelta(minutes=45), "HIGH", "MACRO_SERIES"),
        MacroEvent("newsapi", "3", "old item", now - timedelta(hours=5), "HIGH", "NEWS"),
    ]
    result = MacroRiskEngine.assess(events, now=now, proximity_minutes=120)
    assert result["status"] == "OK"
    assert result["risk_level"] == "CRISIS"
    assert result["high_impact_count"] == 2
    assert len(result["events"]) == 2


def test_macro_risk_without_nearby_events_is_normal_no_data():
    now = datetime(2026, 9, 19, 10, 0, tzinfo=timezone.utc)
    result = MacroRiskEngine.assess(
        [MacroEvent("newsapi", "1", "old", now - timedelta(hours=5), "HIGH", "NEWS")],
        now=now,
        proximity_minutes=60,
    )
    assert result["status"] == "NO_DATA"
    assert result["risk_level"] == "NORMAL"


def test_macro_collection_is_cached_and_exposes_cache_status():
    provider = NewsAPIProvider(api_key="test")
    provider.fetch = lambda **kwargs: []
    engine = MacroRiskEngine([provider], cache_ttl_seconds=300)
    now = datetime.fromisoformat("2026-09-19T10:00:00+00:00")
    first = engine.collect(now=now)
    second = engine.collect(now=now.replace(minute=1))
    assert first["status"] == "NO_DATA"
    assert second["status"] == "CACHED"
    assert second["cache_age_seconds"] == 60.0


def test_collect_and_assess_returns_provider_diagnostics():
    class BrokenProvider:
        name = "broken"
        def fetch(self, **kwargs):
            raise MacroProviderError("offline")

    result = MacroRiskEngine([BrokenProvider()]).collect_and_assess(
        now=datetime.fromisoformat("2026-09-19T10:00:00+00:00")
    )
    assert result["provider_status"] == "EXTERNAL_DEPENDENCY"
    assert result["provider_diagnostics"][0]["provider"] == "broken"
