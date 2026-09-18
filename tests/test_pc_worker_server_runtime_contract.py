from __future__ import annotations

import json
import socket
import threading
import time
import urllib.error
import urllib.request

from worker.runtime import WorkerRuntime
from worker.server import WorkerHTTPServer


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _request(server: WorkerHTTPServer, payload: bytes, content_type: str = "application/json") -> tuple[int, dict]:
    request = urllib.request.Request(
        f"http://{server.host}:{server.port}/jobs",
        data=payload,
        method="POST",
        headers={"Authorization": "Bearer secret", "Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


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


def test_worker_jobs_reject_non_json_requests():
    runtime = WorkerRuntime.create()
    server = WorkerHTTPServer(runtime, host="127.0.0.1", port=_free_port(), token="secret")
    server.start()
    try:
        status, body = _request(server, b"{}", content_type="text/plain")
        assert status == 415
        assert body == {"error": "unsupported_media_type"}
    finally:
        server.stop()


def test_worker_jobs_do_not_expose_internal_exception_details():
    runtime = WorkerRuntime.create()

    async def fail(_request):
        raise RuntimeError("secret internal detail")

    runtime.execute = fail  # type: ignore[method-assign]
    server = WorkerHTTPServer(runtime, host="127.0.0.1", port=_free_port(), token="secret")
    server.start()
    try:
        status, body = _request(server, b'{"job_id":"job-1","job_type":"backtest"}')
        assert status == 500
        assert body == {"error": "internal_error"}
        assert "secret internal detail" not in json.dumps(body)
    finally:
        server.stop()


def test_worker_http_uses_persistent_runtime_loop_for_timeout_fencing():
    runtime = WorkerRuntime.create()
    started = threading.Event()
    release = threading.Event()

    def handler(_payload):
        started.set()
        release.wait(timeout=5)
        return {"ok": True}

    runtime.register("backtest", handler)
    server = WorkerHTTPServer(runtime, host="127.0.0.1", port=_free_port(), token="secret")
    server.start()
    try:
        status, body = _request(
            server,
            b'{"job_id":"slow-1","job_type":"backtest","timeout_seconds":1}',
        )
        assert status == 200
        assert body["status"] == "TIMEOUT"
        assert started.wait(timeout=1)

        status2, body2 = _request(
            server,
            b'{"job_id":"slow-1","job_type":"backtest","timeout_seconds":1}',
        )
        assert status2 == 200
        assert body2["status"] == "RUNNING"

        release.set()
        deadline = time.time() + 3
        while time.time() < deadline:
            status3, body3 = _request(
                server,
                b'{"job_id":"slow-1","job_type":"backtest","timeout_seconds":1}',
            )
            if body3["status"] == "COMPLETED":
                break
            time.sleep(0.05)
        else:
            raise AssertionError("timed-out synchronous job did not complete on persistent runtime loop")
    finally:
        release.set()
        server.stop()
