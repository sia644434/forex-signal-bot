from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from core.health_server import HealthServer


def test_health_server_serves_json_health() -> None:
    server = HealthServer(lambda: {"status": "ok", "service": "test"}, host="127.0.0.1", port=0)
    server.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.port}/health", timeout=2) as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("application/json")
            assert json.loads(response.read()) == {"status": "ok", "service": "test"}
    finally:
        server.stop()


def test_health_server_returns_service_failure_as_503() -> None:
    payload = {
        "application": {"status": "degraded"},
        "services": {
            "telegram": {"status": "stopped", "critical": True},
        },
    }
    server = HealthServer(lambda: payload, host="127.0.0.1", port=0)
    server.start()
    try:
        try:
            urlopen(f"http://127.0.0.1:{server.port}/health", timeout=2)
        except HTTPError as exc:
            assert exc.code == 503
            assert json.loads(exc.read()) == payload
        else:
            raise AssertionError("degraded health unexpectedly returned success")
    finally:
        server.stop()


def test_health_server_returns_not_found_for_unknown_path() -> None:
    server = HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=0)
    server.start()
    try:
        try:
            urlopen(f"http://127.0.0.1:{server.port}/unknown", timeout=2)
        except Exception as exc:
            assert getattr(exc, "code", None) == 404
        else:
            raise AssertionError("unknown health path unexpectedly returned success")
    finally:
        server.stop()


def test_health_server_start_is_idempotent() -> None:
    server = HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=0)
    server.start()
    try:
        first_thread = server._thread
        server.start()
        assert server._thread is first_thread
    finally:
        server.stop()


def test_health_server_stop_is_idempotent() -> None:
    server = HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=0)
    server.start()
    server.stop()
    server.stop()
    assert server._thread is None


def test_health_server_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="health server port"):
        HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=65536)


def test_health_server_returns_503_for_invalid_health_payload() -> None:
    server = HealthServer(lambda: None, host="127.0.0.1", port=0)  # type: ignore[arg-type]
    server.start()
    try:
        try:
            urlopen(f"http://127.0.0.1:{server.port}/health", timeout=2)
        except HTTPError as exc:
            assert exc.code == 503
            assert json.loads(exc.read()) is None
        else:
            raise AssertionError("invalid health payload unexpectedly returned success")
    finally:
        server.stop()


def test_health_server_stop_releases_socket_before_start() -> None:
    server = HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=0)
    bound_port = server.port

    server.stop()

    assert server._thread is None
    assert server._server.fileno() == -1

    replacement = HealthServer(lambda: {"status": "ok"}, host="127.0.0.1", port=bound_port)
    replacement.stop()
