import sqlite3
import time

from worker.contracts import JobRequest
from worker.queue import WorkerQueue


def test_enqueue_is_idempotent_for_duplicate_job_id():
    queue = WorkerQueue()
    request = JobRequest("job-1", "backtest", payload={"symbol": "EURUSD"}, priority=80)
    first = queue.enqueue(request)
    second = queue.enqueue(request)
    assert first == second
    assert first.status == "PENDING"
    queue.close()


def test_claims_highest_priority_pending_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("low", "backtest", priority=10))
    queue.enqueue(JobRequest("high", "backtest", priority=90))
    claimed = queue.claim_next()
    assert claimed is not None
    assert claimed.job_id == "high"
    assert claimed.status == "RUNNING"
    assert claimed.claim_token
    queue.close()


def test_targeted_claim_does_not_steal_another_pending_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("low", "backtest", priority=10))
    queue.enqueue(JobRequest("high", "backtest", priority=90))
    claimed = queue.claim("low")
    assert claimed is not None
    assert claimed.job_id == "low"
    assert claimed.status == "RUNNING"
    assert queue.get("high").status == "PENDING"
    queue.close()


def test_targeted_claim_is_idempotent_for_non_pending_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("job", "backtest"))
    first = queue.claim("job")
    second = queue.claim("job")
    assert first is not None
    assert second is None
    queue.close()


def test_queue_metrics_report_state_counts_without_payloads():
    queue = WorkerQueue()
    assert queue.metrics() == {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0, "timeout": 0, "total": 0}
    queue.enqueue(JobRequest("pending", "backtest", priority=10))
    queue.enqueue(JobRequest("running", "backtest", priority=20))
    claimed = queue.claim_next()
    assert claimed is not None and claimed.job_id == "running"
    queue.enqueue(JobRequest("completed", "backtest", priority=90))
    claimed = queue.claim_next()
    assert claimed is not None and claimed.job_id == "completed"
    queue.finish("completed", result={"secret": "must not be exposed by metrics"})
    queue.enqueue(JobRequest("failed", "backtest", priority=80))
    claimed = queue.claim_next()
    assert claimed is not None and claimed.job_id == "failed"
    queue.fail("failed", "provider unavailable")
    queue.enqueue(JobRequest("cancelled", "backtest", priority=70))
    claimed = queue.claim_next()
    assert claimed is not None and claimed.job_id == "cancelled"
    queue.cancel("cancelled")
    queue.enqueue(JobRequest("timeout", "backtest", priority=60))
    claimed = queue.claim_next()
    assert claimed is not None and claimed.job_id == "timeout"
    queue.timeout("timeout")
    assert queue.metrics() == {"pending": 1, "running": 1, "completed": 1, "failed": 1, "cancelled": 1, "timeout": 1, "total": 6}
    queue.close()


def test_terminal_states_persist_result_and_error():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("done", "backtest"))
    queue.claim_next()
    queue.finish("done", result={"profit_factor": 1.4})
    completed = queue.get("done")
    assert completed is not None
    assert completed.status == "COMPLETED"
    assert completed.result == {"profit_factor": 1.4}
    assert completed.claimed_at is None
    queue.enqueue(JobRequest("failed", "backtest"))
    queue.claim_next()
    queue.fail("failed", "provider unavailable")
    failed = queue.get("failed")
    assert failed is not None
    assert failed.status == "FAILED"
    assert failed.error == "provider unavailable"
    queue.close()


def test_terminal_transition_is_idempotent_after_completion():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("done", "backtest"))
    queue.claim_next()
    first = queue.finish("done", result={"ok": True})
    second = queue.finish("done", result={"ok": False})
    assert second == first
    queue.close()


def test_cancel_and_timeout_are_explicit_terminal_states():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("cancel", "backtest"))
    queue.claim_next()
    assert queue.cancel("cancel").status == "CANCELLED"
    queue.enqueue(JobRequest("timeout", "backtest"))
    queue.claim_next()
    timed_out = queue.timeout("timeout")
    assert timed_out.status == "TIMEOUT"
    assert timed_out.error == "Worker job timeout"
    queue.close()


def test_stale_running_job_is_recovered_to_pending(tmp_path):
    database = tmp_path / "worker_queue.sqlite3"
    queue = WorkerQueue(str(database))
    queue.enqueue(JobRequest("stale", "backtest"))
    claimed = queue.claim_next()
    assert claimed is not None
    connection = sqlite3.connect(database)
    connection.execute("UPDATE worker_jobs SET claimed_at = ? WHERE job_id = ?", (time.time() - 10, "stale"))
    connection.commit()
    connection.close()
    recovered = queue.recover_stale_running(1)
    assert [record.job_id for record in recovered] == ["stale"]
    record = queue.get("stale")
    assert record is not None
    assert record.status == "PENDING"
    assert record.claimed_at is None
    assert record.claim_token is None
    assert record.error == "Recovered stale running job"
    queue.close()


def test_non_stale_running_job_is_not_recovered():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("active", "backtest"))
    queue.claim_next()
    recovered = queue.recover_stale_running(3600)
    assert recovered == []
    record = queue.get("active")
    assert record is not None
    assert record.status == "RUNNING"
    queue.close()


def test_recovery_age_must_be_positive():
    queue = WorkerQueue()
    try:
        queue.recover_stale_running(0)
    except ValueError as exc:
        assert str(exc) == "Recovery age must be greater than zero"
    else:
        raise AssertionError("non-positive recovery age must be rejected")
    queue.close()


def test_expired_running_job_uses_its_own_timeout(tmp_path):
    database = tmp_path / "worker_queue.sqlite3"
    queue = WorkerQueue(str(database))
    queue.enqueue(JobRequest("expired", "backtest", timeout_seconds=1))
    claimed = queue.claim_next()
    assert claimed is not None
    connection = sqlite3.connect(database)
    connection.execute("UPDATE worker_jobs SET claimed_at = ? WHERE job_id = ?", (time.time() - 10, "expired"))
    connection.commit()
    connection.close()
    recovered = queue.recover_expired_running(grace_seconds=0)
    assert [record.job_id for record in recovered] == ["expired"]
    record = queue.get("expired")
    assert record is not None
    assert record.status == "PENDING"
    queue.close()


def test_expired_recovery_does_not_recover_long_running_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("active", "backtest", timeout_seconds=3600))
    queue.claim_next()
    recovered = queue.recover_expired_running(grace_seconds=0)
    assert recovered == []
    record = queue.get("active")
    assert record is not None
    assert record.status == "RUNNING"
    queue.close()


def test_recovery_grace_must_not_be_negative():
    queue = WorkerQueue()
    try:
        queue.recover_expired_running(-1)
    except ValueError as exc:
        assert str(exc) == "Recovery grace must not be negative"
    else:
        raise AssertionError("negative recovery grace must be rejected")
    queue.close()


def test_queue_persists_across_connections(tmp_path):
    database = tmp_path / "worker_queue.sqlite3"
    request = JobRequest("persisted", "backtest", payload={"bars": 500})
    first = WorkerQueue(str(database))
    first.enqueue(request)
    first.close()
    second = WorkerQueue(str(database))
    record = second.get("persisted")
    assert record is not None
    assert record.payload == {"bars": 500}
    assert record.status == "PENDING"
    second.close()


def test_stale_worker_cannot_complete_recovered_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("leased", "backtest", timeout_seconds=1))
    first = queue.claim("leased")
    assert first is not None and first.claim_token
    connection = queue._connection
    connection.execute("UPDATE worker_jobs SET claimed_at = ? WHERE job_id = ?", (time.time() - 10, "leased"))
    connection.commit()
    recovered = queue.recover_expired_running(grace_seconds=0)
    assert [item.job_id for item in recovered] == ["leased"]
    second = queue.claim("leased")
    assert second is not None and second.claim_token and second.claim_token != first.claim_token
    stale_result = queue.finish("leased", result={"stale": True}, claim_token=first.claim_token)
    assert stale_result.status == "RUNNING"
    assert queue.get("leased").claim_token == second.claim_token
    fresh_result = queue.finish("leased", result={"fresh": True}, claim_token=second.claim_token)
    assert fresh_result.status == "COMPLETED"
    assert fresh_result.result == {"fresh": True}
    queue.close()


def test_active_claim_can_be_renewed_without_changing_lease_identity():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("renew", "backtest", timeout_seconds=10))
    claimed = queue.claim("renew")
    assert claimed is not None and claimed.claim_token
    before = claimed.claimed_at
    renewed = queue.renew_lease("renew", claimed.claim_token)
    assert renewed.status == "RUNNING"
    assert renewed.claim_token == claimed.claim_token
    assert renewed.claimed_at is not None
    assert before is not None
    assert renewed.claimed_at >= before
    queue.close()


def test_stale_claim_cannot_renew_recovered_job():
    queue = WorkerQueue()
    queue.enqueue(JobRequest("renew-stale", "backtest", timeout_seconds=1))
    first = queue.claim("renew-stale")
    assert first is not None and first.claim_token
    queue._connection.execute("UPDATE worker_jobs SET claimed_at = ? WHERE job_id = ?", (time.time() - 10, "renew-stale"))
    queue._connection.commit()
    queue.recover_expired_running(grace_seconds=0)
    second = queue.claim("renew-stale")
    assert second is not None and second.claim_token != first.claim_token
    unchanged = queue.renew_lease("renew-stale", first.claim_token)
    assert unchanged.claim_token == second.claim_token
    queue.close()
