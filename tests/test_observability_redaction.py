from __future__ import annotations

from observability.redaction import redact_value


def test_redacts_telegram_bot_url_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    raw = "https://api.telegram.org/bot123456789:ABCdef_Example/getMe"
    redacted = redact_value(raw)
    assert "123456789:ABCdef_Example" not in redacted
    assert "api.telegram.org/bot[REDACTED]/getMe" in redacted


def test_redacts_secret_key_value():
    raw = "Authorization: Bearer secret-value"
    redacted = redact_value(raw)
    assert "secret-value" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_raw_telegram_bot_token():
    raw = "123456789:ABCdefghijklmnopqrstuvwxyz_12345"
    redacted = redact_value(raw)
    assert raw not in redacted
    assert redacted == "[REDACTED]"
