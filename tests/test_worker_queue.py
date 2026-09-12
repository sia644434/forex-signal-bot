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
