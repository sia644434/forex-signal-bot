import pytest

from services.telegram import tracker_job


class _FakeBot:
    def __init__(self):
        self.sent = []

    async def send_message(self, **kwargs):
        self.sent.append(kwargs)


class _FakeApplication:
    def __init__(self):
        self.bot = _FakeBot()


class _FakeContext:
    def __init__(self):
        self.bot = _FakeBot()
        self.application = _FakeApplication()


def test_notifications_disabled_suppresses_tracker_notification(monkeypatch):
    item = type("Item", (), {"user_id": 1001, "symbol": "EURUSD", "timeframe": "M15"})()
    monkeypatch.setattr(tracker_job, "_all_tracked", lambda: [item])
    monkeypatch.setattr(tracker_job, "list_tracking", lambda user_id: [item])
    monkeypatch.setattr(tracker_job, "get_user_state", lambda user_id: type("State", (), {"settings": {"notifications_enabled": False}})())

    called = False

    async def fake_refresh(item, notify, market_data):
        nonlocal called
        called = True
        await notify("should not be delivered")

    monkeypatch.setattr(tracker_job, "refresh_tracking", fake_refresh)
    monkeypatch.setattr(tracker_job, "get_market_data_service", lambda application: object())

    context = _FakeContext()
    import asyncio
    asyncio.run(tracker_job.refresh_all_tracked_signals(context))

    assert called
    assert context.bot.sent == []


def test_notifications_enabled_delivers_tracker_notification(monkeypatch):
    item = type("Item", (), {"user_id": 1002, "symbol": "EURUSD", "timeframe": "M15"})()
    monkeypatch.setattr(tracker_job, "_all_tracked", lambda: [item])
    monkeypatch.setattr(tracker_job, "list_tracking", lambda user_id: [item])
    monkeypatch.setattr(tracker_job, "get_user_state", lambda user_id: type("State", (), {"settings": {"notifications_enabled": True}})())

    async def fake_refresh(item, notify, market_data):
        await notify("delivered")

    monkeypatch.setattr(tracker_job, "refresh_tracking", fake_refresh)
    monkeypatch.setattr(tracker_job, "get_market_data_service", lambda application: object())

    context = _FakeContext()
    import asyncio
    asyncio.run(tracker_job.refresh_all_tracked_signals(context))

    assert context.bot.sent == [{"chat_id": 1002, "text": "delivered", "parse_mode": "HTML"}]
