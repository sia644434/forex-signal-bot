from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from worker.client import PCWorkerClient
from worker.runtime import WorkerRuntime
from worker.server import WorkerHTTPServer


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_worker_heartbeat_requires_authentication_and_returns_identity():
    runtime = WorkerRuntime.create()
    server = WorkerHTTPServer(runtime, host="127.0.0.1", port=_free_port(), token="secret")
    server.start()
    try:
        client = PCWorkerClient(f"http://{server.host}:{server.port}", "secret")
        heartbeat = client.heartbeat()
        assert heartbeat["status"] == "READY"
        assert heartbeat["worker_id"] == runtime.worker_id
        assert heartbeat["timestamp"].endswith("+00:00")

        unauthorized = urllib.request.Request(
            f"http://{server.host}:{server.port}/heartbeat",
            data=b"{}",
            method="POST",
            headers={"Authorization": "Bearer wrong", "Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(unauthorized, timeout=2)
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
            assert json.loads(exc.read().decode("utf-8")) == {"error": "unauthorized"}
        else:
            raise AssertionError("heartbeat must reject an invalid token")
    finally:
        server.stop()
