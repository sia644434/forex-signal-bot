from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any

from .contracts import JobRequest


QUEUE_STATES = frozenset({"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"})


@dataclass(frozen=True)
class QueueRecord:
    job_id: str
    job_type: str
    payload: dict[str, Any]
    priority: int
    timeout_seconds: int
    allow_cpu_fallback: bool
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


class WorkerQueue:
    """Small durable SQLite queue for heavy Forex worker jobs.

    The queue owns job persistence and state transitions; transport and execution
    remain outside this module. A unique job_id makes enqueue idempotent.
    """

    def __init__(self, database_path: str = ":memory:") -> None:
        self._connection = sqlite3.connect(database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS worker_jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                priority INTEGER NOT NULL,
                timeout_seconds INTEGER NOT NULL,
                allow_cpu_fallback INTEGER NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                error TEXT
            )
            """
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def enqueue(self, request: JobRequest) -> QueueRecord:
        if not request.job_id.strip():
            raise ValueError("Job ID must not be empty")
        if request.timeout_seconds <= 0:
            raise ValueError("Job timeout must be greater than zero")
        self._connection.execute(
            """
            INSERT OR IGNORE INTO worker_jobs
            (job_id, job_type, payload, priority, timeout_seconds, allow_cpu_fallback, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
            """,
            (
                request.job_id,
                request.job_type,
                json.dumps(request.payload, sort_keys=True),
                request.priority,
                request.timeout_seconds,
                int(request.allow_cpu_fallback),
            ),
        )
        self._connection.commit()
        record = self.get(request.job_id)
        if record is None:
            raise RuntimeError(f"Queue record was not created: {request.job_id}")
        return record

    def claim_next(self) -> QueueRecord | None:
        row = self._connection.execute(
            "SELECT job_id FROM worker_jobs WHERE status = 'PENDING' ORDER BY priority DESC, rowid ASC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        cursor = self._connection.execute(
            "UPDATE worker_jobs SET status = 'RUNNING' WHERE job_id = ? AND status = 'PENDING'",
            (row["job_id"],),
        )
        self._connection.commit()
        if cursor.rowcount != 1:
            return None
        return self.get(row["job_id"])

    def finish(self, job_id: str, *, result: dict[str, Any] | None = None) -> QueueRecord:
        return self._transition(job_id, "COMPLETED", result=result, error=None)

    def fail(self, job_id: str, error: str) -> QueueRecord:
        return self._transition(job_id, "FAILED", result=None, error=error)

    def timeout(self, job_id: str, error: str = "Worker job timeout") -> QueueRecord:
        return self._transition(job_id, "TIMEOUT", result=None, error=error)

    def cancel(self, job_id: str) -> QueueRecord:
        return self._transition(job_id, "CANCELLED", result=None, error=None)

    def get(self, job_id: str) -> QueueRecord | None:
        row = self._connection.execute("SELECT * FROM worker_jobs WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return QueueRecord(
            job_id=row["job_id"],
            job_type=row["job_type"],
            payload=json.loads(row["payload"]),
            priority=row["priority"],
            timeout_seconds=row["timeout_seconds"],
            allow_cpu_fallback=bool(row["allow_cpu_fallback"]),
            status=row["status"],
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
        )

    def _transition(
        self,
        job_id: str,
        status: str,
        *,
        result: dict[str, Any] | None,
        error: str | None,
    ) -> QueueRecord:
        if status not in QUEUE_STATES - {"PENDING", "RUNNING"}:
            raise ValueError(f"Invalid terminal queue state: {status}")
        cursor = self._connection.execute(
            """
            UPDATE worker_jobs
            SET status = ?, result = ?, error = ?
            WHERE job_id = ? AND status = 'RUNNING'
            """,
            (status, json.dumps(result, sort_keys=True) if result is not None else None, error, job_id),
        )
        self._connection.commit()
        if cursor.rowcount != 1:
            record = self.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return record
        record = self.get(job_id)
        if record is None:
            raise RuntimeError(f"Queue record disappeared: {job_id}")
        return record


__all__ = ["QUEUE_STATES", "QueueRecord", "WorkerQueue"]
