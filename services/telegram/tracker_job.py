from __future__ import annotations

import logging
import os

from telegram.ext import ContextTypes

from services.market_data.service import get_market_data_service
from .state import get_user_state
from .tracker import list_tracking, refresh_tracking

logger = logging.getLogger(__name__)
DEFAULT_TRACKER_INTERVAL_SECONDS = 60


def _notifications_enabled(user_id: int) -> bool:
    """Read the persisted per-user notification preference; default to enabled."""
    state = get_user_state(user_id)
    value = state.settings.get("notifications_enabled", True)
    return value is not False


def tracker_refresh_interval_seconds() -> int:
    raw = os.getenv("TELEGRAM_TRACKER_INTERVAL_SECONDS", str(DEFAULT_TRACKER_INTERVAL_SECONDS)).strip()
    try:
        interval = int(raw)
    except ValueError as error:
        raise RuntimeError("TELEGRAM_TRACKER_INTERVAL_SECONDS must be an integer") from error
    if interval < 5:
        raise RuntimeError("TELEGRAM_TRACKER_INTERVAL_SECONDS must be at least 5 seconds")
    return interval


async def refresh_all_tracked_signals(context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    market_data = get_market_data_service(context.application)
    for user_id in {item.user_id for item in list(_all_tracked())}:
        notifications_enabled = _notifications_enabled(user_id)
        for item in list_tracking(user_id):
            async def notify(text: str, uid: int = user_id) -> None:
                if not notifications_enabled:
                    return
                await bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            try:
                await refresh_tracking(item, notify, market_data)
            except Exception:
                logger.exception("Signal tracking refresh failed for user=%s symbol=%s", user_id, item.symbol)


def _all_tracked():
    # Kept local to avoid exposing mutable tracker internals outside this service.
    from .tracker import ACTIVE_TRACKS
    return list(ACTIVE_TRACKS.values())


__all__ = ["refresh_all_tracked_signals", "tracker_refresh_interval_seconds"]
