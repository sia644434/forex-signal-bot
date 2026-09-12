from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from collections.abc import Callable


class _HealthHandler(BaseHTTPRequestHandler):
    server_version = "ForexSignalHealth/1.0"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_error(404)
            return

        payload = self.server.health_provider()  # type: ignore[attr-defined]
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        status = _http_status_for_health(payload)

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def _http_status_for_health(payload: object) -> int:
    """Map the health contract to an orchestration-friendly HTTP status."""
    if not isinstance(payload, dict):
        return 503

    application = payload.get("application")
    if isinstance(application, dict):
        status = application.get("status")
        if status in {"degraded", "error", "unhealthy"}:
            return 503

    top_level_status = payload.get("status")
    if top_level_status in {"degraded", "error", "unhealthy"}:
        return 503

    return 200


class HealthServer:
    """Small dependency-free HTTP health endpoint for container orchestration."""

    def __init__(
        self,
        health_provider: Callable[[], dict],
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        if not 0 <= port <= 65535:
            raise ValueError("health server port must be between 0 and 65535")

        self._server = ThreadingHTTPServer((host, port), _HealthHandler)
        self._server.health_provider = health_provider  # type: ignore[attr-defined]
        self._thread: threading.Thread | None = None

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="health-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)
        self._thread = None
