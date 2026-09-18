from __future__ import annotations

import asyncio
import datetime as dt
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .contracts import JobRequest
from .runtime import WorkerRuntime


MAX_JOB_BODY_BYTES = 5_000_000
MAX_JOB_TIMEOUT_SECONDS = 86_400
MAX_JOB_ID_LENGTH = 256
MAX_JOB_TYPE_LENGTH = 128


class WorkerHTTPServer:
    """Threaded HTTP boundary backed by one persistent asyncio runtime loop."""

    def __init__(self, runtime: WorkerRuntime, host: str | None = None, port: int | None = None, token: str | None = None):
        self.runtime = runtime
        self.host = host or os.getenv("PC_WORKER_HOST", "127.0.0.1")
        self.port = port or int(os.getenv("PC_WORKER_PORT", "8765"))
        self.token = token or os.getenv("PC_WORKER_TOKEN", "")
        if not self.token:
            raise ValueError("PC_WORKER_TOKEN must be configured")

        runtime_ref = runtime
        token_ref = self.token
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._run_loop,
            name="pc-worker-runtime-loop",
            daemon=True,
        )
        self._started = threading.Event()
        self._stopped = threading.Event()

        class Handler(BaseHTTPRequestHandler):
            def _authorized(self) -> bool:
                supplied = self.headers.get("Authorization", "")
                expected = f"Bearer {token_ref}"
                return hmac.compare_digest(supplied, expected)

            def _json(self, status: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path != "/health":
                    self._json(404, {"error": "not_found"})
                    return
                self._json(200, {"status": "READY"})

            def do_POST(self) -> None:  # noqa: N802
                if self.path not in {"/jobs", "/heartbeat"}:
                    self._json(404, {"error": "not_found"})
                    return
                if not self._authorized():
                    self._json(401, {"error": "unauthorized"})
                    return
                if self.path == "/heartbeat":
                    self._json(200, {
                        "status": "READY",
                        "worker_id": runtime_ref.worker_id,
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    })
                    return
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    self._json(415, {"error": "unsupported_media_type"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0:
                        self._json(400, {"error": "invalid_request"})
                        return
                    if length > MAX_JOB_BODY_BYTES:
                        self._json(413, {"error": "payload_too_large"})
                        return
                    payload = json.loads(self.rfile.read(length))
                    if not isinstance(payload, dict):
                        raise ValueError("request body must be a JSON object")
                    job_id = payload["job_id"]
                    job_type = payload["job_type"]
                    timeout_seconds = payload.get("timeout_seconds", 3600)
                    priority = payload.get("priority", 50)
                    job_payload = payload.get("payload", {})
                    if not isinstance(job_id, str) or not job_id.strip() or len(job_id) > MAX_JOB_ID_LENGTH:
                        raise ValueError("invalid job_id")
                    if not isinstance(job_type, str) or not job_type.strip() or len(job_type) > MAX_JOB_TYPE_LENGTH:
                        raise ValueError("invalid job_type")
                    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_JOB_TIMEOUT_SECONDS:
                        raise ValueError("invalid timeout_seconds")
                    if isinstance(priority, bool) or not isinstance(priority, int) or not 0 <= priority <= 100:
                        raise ValueError("invalid priority")
                    if not isinstance(job_payload, dict):
                        raise ValueError("payload must be a JSON object")
                    request = JobRequest(
                        job_id=job_id.strip(),
                        job_type=job_type.strip(),
                        payload=job_payload,
                        priority=priority,
                        timeout_seconds=timeout_seconds,
                        allow_cpu_fallback=bool(payload.get("allow_cpu_fallback", True)),
                    )
                    future = asyncio.run_coroutine_threadsafe(runtime_ref.execute(request), self.server.runtime_loop)
                    result = future.result(timeout=request.timeout_seconds + 5)
                    self._json(200, {
                        "job_id": result.job_id,
                        "status": result.status,
                        "job_type": result.job_type,
                        "output": result.output,
                        "error": result.error,
                        "worker_id": result.worker_id,
                    })
                except TimeoutError:
                    self._json(504, {"error": "worker_timeout"})
                except (KeyError, ValueError, TypeError, json.JSONDecodeError):
                    self._json(400, {"error": "invalid_request"})
                except Exception:
                    self._json(500, {"error": "internal_error"})

            def log_message(self, format: str, *args: Any) -> None:
                return

        class RuntimeHTTPServer(ThreadingHTTPServer):
            allow_reuse_address = True

            def __init__(self, address, request_handler):
                super().__init__(address, request_handler)
                self.runtime_loop = self_loop

        self_loop = self._loop
        self._server = RuntimeHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="pc-worker-http", daemon=True)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._started.set()
        try:
            self._loop.run_forever()
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()
            self._stopped.set()

    def start(self) -> None:
        if self._thread.is_alive():
            return
        self._loop_thread.start()
        if not self._started.wait(timeout=5):
            raise RuntimeError("Worker runtime event loop failed to start")
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        self._loop_thread.join(timeout=10)
        self._thread.join(timeout=10)


__all__ = ["WorkerHTTPServer"]
