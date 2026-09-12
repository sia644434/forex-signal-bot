from __future__ import annotations

import json
import socket
import urllib.request

from worker.runtime import WorkerRuntime
from worker.server import WorkerHTTPServer


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_worker_health_exposes_only_minimal_liveness_contract():
    runtime = WorkerRuntime.create()
    server = WorkerHTTPServer(runtime, host="127.0.0.1", port=_free_port(), token="secret")
    server.start()
    try:
        request = urllib.request.Request(f"http://{server.host}:{server.port}/health", method="GET")
        with urllib.request.urlopen(request, timeout=2) as response:
            assert response.status == 200
            assert json.loads(response.read().decode("utf-8")) == {"status": "READY"}
    finally:
        server.stop()
