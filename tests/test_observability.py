from observability.redaction import redact_value
from observability.report import build_summary,parse_json_lines
def test_redaction_removes_secret_values():
    data=redact_value({"api_key":"secret","nested":{"token":"abc","ok":"yes"}})
    assert data["api_key"]=="[REDACTED]"; assert data["nested"]["token"]=="[REDACTED]"; assert data["nested"]["ok"]=="yes"
def test_parse_structured_railway_logs_and_build_summary():
    events=parse_json_lines('{"timestamp":"2026-09-20T08:00:00Z","level":"error","message":"boom","event":"scanner_failure"}',"railway","forex-signal-bot")
    summary=build_summary(events,commit_sha="abc")
    assert summary["event_count"]==1; assert summary["levels"]=={"ERROR":1}; assert summary["errors"][0]["event"]=="scanner_failure"
