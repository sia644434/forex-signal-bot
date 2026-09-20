from services.telegram.state import TelegramUserState
from profiles import create_profile, get_profile, list_profiles, set_active_profile
from analysis.styles import list_analysis_styles


def test_analysis_style_registry_contains_presets_and_custom_styles():
    ids = {style.style_id for style in list_analysis_styles()}
    assert {"scalping", "swing", "day_trading", "trend_following", "price_action", "momentum"}.issubset(ids)


def test_profile_creation_supports_multiple_styles_and_versions():
    state = TelegramUserState(user_id=1001)
    profile = create_profile(state, "Custom", ["price_action", "momentum"])
    assert [item.style_id for item in profile.styles] == ["price_action", "momentum"]
    assert profile.version == 1
    assert get_profile(state, profile.profile_id).profile_id == profile.profile_id


def test_profile_activation_is_persistent_in_user_settings():
    state = TelegramUserState(user_id=1002)
    first = create_profile(state, "One", ["scalping"])
    second = create_profile(state, "Two", ["swing"])
    set_active_profile(state, second.profile_id)
    assert state.settings["active_profile_id"] == second.profile_id
    assert get_profile(state).profile_id == second.profile_id
    assert len(list_profiles(state)) == 2
