from types import SimpleNamespace

import pytest

from services.telegram.access import is_authorized


def _update(user_id=None):
    user = None if user_id is None else SimpleNamespace(id=user_id)
    return SimpleNamespace(effective_user=user)


def test_allowlist_allows_only_configured_users(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123,456")
    assert is_authorized(_update(123)) is True
    assert is_authorized(_update(789)) is False


def test_production_without_allowlist_fails_closed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    assert is_authorized(_update(123)) is False


def test_invalid_allowlist_fails_closed(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "123,nope")
    assert is_authorized(_update(123)) is False


def test_development_keeps_existing_open_behavior(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
    assert is_authorized(_update(123)) is True
    assert is_authorized(_update(None)) is False
