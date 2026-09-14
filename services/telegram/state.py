from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict

from .state_store import TelegramStateStore, TelegramStateStoreError


@dataclass
class TelegramUserState:
    user_id: int
    current_menu: str = "home"
    language: str = "fa"
    settings: Dict[str, Any] = field(default_factory=dict)


USER_STATES: Dict[int, TelegramUserState] = {}
_STORE = TelegramStateStore(os.getenv("TELEGRAM_STATE_FILE", "data/telegram_state.json"))


def _deserialize(user_id: int, payload: dict | None) -> TelegramUserState:
    if payload is None:
        return TelegramUserState(user_id=user_id)
    if not isinstance(payload, dict):
        raise TelegramStateStoreError("invalid Telegram user state")
    language = payload.get("language", "fa")
    current_menu = payload.get("current_menu", "home")
    settings = payload.get("settings", {})
    if language not in {"fa", "en"} or not isinstance(current_menu, str) or not isinstance(settings, dict):
        raise TelegramStateStoreError("invalid Telegram user state")
    return TelegramUserState(user_id=user_id, current_menu=current_menu, language=language, settings=dict(settings))


def _serialize(state: TelegramUserState) -> dict:
    return {
        "current_menu": state.current_menu,
        "language": state.language,
        "settings": dict(state.settings),
    }


def get_user_state(user_id: int) -> TelegramUserState:
    if user_id not in USER_STATES:
        USER_STATES[user_id] = _deserialize(user_id, _STORE.load(user_id))
    return USER_STATES[user_id]


def persist_user_state(state: TelegramUserState) -> TelegramUserState:
    _STORE.save(state.user_id, _serialize(state))
    return state


def update_menu(user_id: int, menu: str) -> TelegramUserState:
    state = get_user_state(user_id)
    state.current_menu = menu
    persist_user_state(state)
    return state


__all__ = ["TelegramUserState", "USER_STATES", "get_user_state", "persist_user_state", "update_menu"]
