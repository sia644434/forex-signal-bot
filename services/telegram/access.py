from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def _allowed_user_ids() -> tuple[int, ...]:
    raw = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").strip()
    if not raw:
        return ()
    try:
        values = tuple(int(item.strip()) for item in raw.split(",") if item.strip())
    except ValueError:
        logger.error("Invalid TELEGRAM_ALLOWED_USER_IDS configuration; denying access.")
        return ()
    if any(value <= 0 for value in values):
        logger.error("Invalid TELEGRAM_ALLOWED_USER_IDS configuration; denying access.")
        return ()
    return tuple(dict.fromkeys(values))


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    if user is None:
        return False

    allowed = _allowed_user_ids()
    if allowed:
        return user.id in allowed

    # A production bot must never become an unrestricted public endpoint by
    # omission. Development/testing retain the existing open behavior so the
    # bot remains usable without IDs in local tests.
    if os.getenv("ENVIRONMENT", "development").strip().lower() == "production":
        return False
    return True


def authorized(handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]):
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if is_authorized(update):
            return await handler(update, context)

        query = update.callback_query
        if query is not None:
            await query.answer("دسترسی مجاز نیست.", show_alert=True)
            return None

        message = update.effective_message
        if message is not None:
            await message.reply_text("⛔ دسترسی به این ربات برای حساب شما مجاز نیست.")
        return None

    return wrapper


__all__ = ["authorized", "is_authorized"]
