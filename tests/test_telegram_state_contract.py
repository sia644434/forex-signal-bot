from services.telegram import state as state_module
from services.telegram.state_store import TelegramStateStore


def setup_function() -> None:
    state_module.USER_STATES.clear()


def test_get_user_state_creates_and_reuses_per_user_state() -> None:
    first = state_module.get_user_state(1001)
    first.settings["market_symbol"] = "GBPUSD"

    second = state_module.get_user_state(1001)
    other = state_module.get_user_state(1002)

    assert second is first
    assert second.user_id == 1001
    assert second.settings["market_symbol"] == "GBPUSD"
    assert other is not first
    assert other.user_id == 1002
    assert other.language == "fa"
    assert other.current_menu == "home"


def test_update_menu_mutates_existing_user_state() -> None:
    original = state_module.get_user_state(2001)

    updated = state_module.update_menu(2001, "settings")

    assert updated is original
    assert updated.current_menu == "settings"
    assert state_module.get_user_state(2001).current_menu == "settings"


def test_user_settings_are_isolated_between_users() -> None:
    first = state_module.get_user_state(3001)
    second = state_module.get_user_state(3002)

    first.settings["timeframe"] = "H1"
    second.settings["timeframe"] = "M15"

    assert first.settings == {"timeframe": "H1"}
    assert second.settings == {"timeframe": "M15"}


def test_user_state_persists_language_menu_and_settings(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(state_module, "_STORE", TelegramStateStore(str(tmp_path / "telegram_state.json")))
    state_module.USER_STATES.clear()

    state = state_module.get_user_state(4001)
    state.language = "en"
    state.current_menu = "settings"
    state.settings["market_symbol"] = "GBPUSD"
    state.settings["timeframe"] = "H1"

    state_module.USER_STATES.clear()
    restored = state_module.get_user_state(4001)

    assert restored.language == "en"
    assert restored.current_menu == "settings"
    assert restored.settings == {"market_symbol": "GBPUSD", "timeframe": "H1"}


def test_corrupted_user_state_fails_closed(tmp_path, monkeypatch) -> None:
    path = tmp_path / "telegram_state.json"
    path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(state_module, "_STORE", TelegramStateStore(str(path)))
    state_module.USER_STATES.clear()

    try:
        state_module.get_user_state(5001)
    except state_module.TelegramStateStoreError:
        pass
    else:
        raise AssertionError("corrupted Telegram state must not be treated as empty state")
