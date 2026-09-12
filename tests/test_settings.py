from config.settings import Settings


def test_settings_without_token(
    monkeypatch,
):

    monkeypatch.delenv(
        "TELEGRAM_BOT_TOKEN",
        raising=False,
    )

    settings = Settings.load()

    assert settings.telegram_token is None


def test_worker_queue_settings_are_loaded(monkeypatch):
    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "/data/forex-worker-queue.sqlite3")
    monkeypatch.setenv("WORKER_QUEUE_RECOVERY_GRACE_SECONDS", "45")

    settings = Settings.load()

    assert settings.worker_queue_database_path == "/data/forex-worker-queue.sqlite3"
    assert settings.worker_queue_recovery_grace_seconds == 45


def test_worker_queue_settings_reject_invalid_values(monkeypatch):
    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "   ")
    try:
        Settings.load()
    except ValueError as exc:
        assert "WORKER_QUEUE_DATABASE_PATH" in str(exc)
    else:
        raise AssertionError("Expected empty queue database path to be rejected")

    monkeypatch.setenv("WORKER_QUEUE_DATABASE_PATH", "worker_queue.sqlite3")
    monkeypatch.setenv("WORKER_QUEUE_RECOVERY_GRACE_SECONDS", "-1")
    try:
        Settings.load()
    except ValueError as exc:
        assert "WORKER_QUEUE_RECOVERY_GRACE_SECONDS" in str(exc)
    else:
        raise AssertionError("Expected negative recovery grace to be rejected")
