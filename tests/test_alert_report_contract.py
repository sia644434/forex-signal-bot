from analysis.report import AnalysisReport


def test_report_alert_context_is_transport_neutral():
    report = AnalysisReport(
        symbol="EURUSD",
        signal="STRONG_BUY",
        confidence=0.90,
        macro_risk_level="NORMAL",
    )
    context = report.alert_context()
    assert context["eligible"] is True
    assert context["severity"] == "HIGH"
    assert context["dedupe_key"] == "EURUSD:STRONG_BUY:HIGH"


def test_report_alert_context_blocks_weak_directional_signal():
    report = AnalysisReport(symbol="BTCUSDT", signal="BUY", confidence=0.4)
    assert report.alert_context()["eligible"] is False
