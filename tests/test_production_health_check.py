from __future__ import annotations

import json

import pytest

from scripts.production_health_check import HealthCheckError, check_health


class FakeResponse:
    def __init__(self, status: int, payload: object):
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def test_check_health_accepts_successful_json(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        return FakeResponse(200, {"status": "ok"})

    monkeypatch.setattr("scripts.production_health_check.urlopen", fake_urlopen)
    assert check_health("https://example.test/") == {"status": "ok"}
    assert calls[0][0] == "https://example.test/health"


def test_check_health_rejects_non_object_json(monkeypatch):
    monkeypatch.setattr(
        "scripts.production_health_check.urlopen",
        lambda request, timeout: FakeResponse(200, ["ok"]),
    )
    with pytest.raises(HealthCheckError, match="non-object JSON"):
        check_health("https://example.test", attempts=1)


def test_check_health_retries_transient_failure(monkeypatch):
    attempts = 0

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("temporary failure")
        return FakeResponse(200, {"status": "ok"})

    monkeypatch.setattr("scripts.production_health_check.urlopen", fake_urlopen)
    monkeypatch.setattr("scripts.production_health_check.time.sleep", lambda _: None)
    assert check_health("https://example.test", attempts=2) == {"status": "ok"}
    assert attempts == 2
