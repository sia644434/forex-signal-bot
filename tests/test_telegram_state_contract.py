from services.telegram import state as state_module


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
