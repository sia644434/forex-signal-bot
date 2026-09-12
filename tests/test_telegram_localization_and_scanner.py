from services.telegram.i18n import t
from services.telegram.scanner import ScanReadiness, ScanResult, format_scan, get_scanner_provider_manager


def test_language_translation_changes_main_text():
    assert "Settings" in t("en", "settings")
    assert "تنظیمات" in t("fa", "settings")


def test_scanner_hides_internal_exception_name():
    result = ScanResult("EURUSD", "NO_TRADE", 0.0, 0.0, None, "UNKNOWN", "unknown", None, "ValueError")
    text = format_scan([result], "M15", "en")
    assert "ValueError" not in text
    assert "Valid data or analysis is unavailable" in text


def test_scanner_localizes_success_output():
    result = ScanResult("EURUSD", "BUY", .82, 1.2, 80, "A", "bullish", 2.1)
    fa = format_scan([result], "M15", "fa")
    en = format_scan([result], "M15", "en")
    assert "اطمینان" in fa and "confidence" in en


def test_scanner_provider_manager_is_application_scoped(monkeypatch):
    class Application:
        def __init__(self):
            self.bot_data = {}

    application = Application()
    readiness = iter([
        ScanReadiness(("oanda",), ("finnhub",)),
        ScanReadiness(("finnhub",), ("oanda",)),
    ])
    monkeypatch.setattr(
        "services.telegram.scanner._provider_readiness",
        lambda: next(readiness),
    )

    first = get_scanner_provider_manager(application)
    second = get_scanner_provider_manager(application)

    assert first is second
    assert first.providers == ("finnhub",)
    assert application.bot_data["scanner_provider_manager"] is first
