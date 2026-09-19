from types import SimpleNamespace

from services.alert_engine import AlertEngine, serialize_alert


def test_alert_engine_emits_high_signal_once():
    report = SimpleNamespace(symbol="EURUSD", signal="STRONG_BUY", confidence=0.9, macro_risk_level="NORMAL")
    engine = AlertEngine()
    first = engine.evaluate(report)
    second = engine.evaluate(report)
    assert first is not None
    assert first.severity == "HIGH"
    assert second is None
    assert serialize_alert(first)["symbol"] == "EURUSD"


def test_alert_engine_emits_critical_macro_alert():
    report = SimpleNamespace(symbol="XAUUSD", signal="BUY", confidence=0.4, macro_risk_level="CRISIS")
    alert = AlertEngine().evaluate(report)
    assert alert is not None
    assert alert.severity == "CRITICAL"


def test_alert_engine_ignores_weak_neutral_state():
    report = SimpleNamespace(symbol="BTCUSDT", signal="WAIT", confidence=0.95, macro_risk_level="NORMAL")
    assert AlertEngine().evaluate(report) is None
