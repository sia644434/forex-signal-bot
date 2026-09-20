from __future__ import annotations

import re
from typing import Any

from analysis.styles import get_analysis_style
from .models import AnalysisProfile, ProfileStyle

_PROFILE_KEY = "analysis_profiles"
_ACTIVE_PROFILE_KEY = "active_profile_id"


def _profiles(state) -> dict[str, AnalysisProfile]:
    raw = state.settings.get(_PROFILE_KEY, {})
    if not isinstance(raw, dict):
        return {}
    return {key: AnalysisProfile.from_dict(value) for key, value in raw.items() if isinstance(value, dict)}


def _save(state, profiles: dict[str, AnalysisProfile]) -> None:
    state.settings[_PROFILE_KEY] = {key: value.to_dict() for key, value in profiles.items()}


def list_profiles(state) -> list[AnalysisProfile]:
    return list(_profiles(state).values())


def get_profile(state, profile_id: str | None = None) -> AnalysisProfile | None:
    profiles = _profiles(state)
    selected = profile_id or state.settings.get(_ACTIVE_PROFILE_KEY)
    return profiles.get(selected) if selected else None


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return value or "profile"


def create_profile(state, name: str, style_ids: list[str], *, symbols=None, timeframes=None, risk_level="medium", schedule_seconds=900) -> AnalysisProfile:
    if not style_ids:
        raise ValueError("A profile must contain at least one analysis style")
    for style_id in style_ids:
        get_analysis_style(style_id)
    profiles = _profiles(state)
    base = _slug(name)
    profile_id = base
    index = 2
    while profile_id in profiles:
        profile_id = f"{base}-{index}"
        index += 1
    profile = AnalysisProfile(profile_id, name, [ProfileStyle(style_id) for style_id in dict.fromkeys(style_ids)], list(symbols or []), list(timeframes or ["M15"]), risk_level, int(schedule_seconds))
    profiles[profile_id] = profile
    _save(state, profiles)
    if not state.settings.get(_ACTIVE_PROFILE_KEY):
        state.settings[_ACTIVE_PROFILE_KEY] = profile_id
    return profile


def create_profile_from_profile(state, profile: AnalysisProfile, name: str | None = None) -> AnalysisProfile:
    return create_profile(state, name or profile.name, [item.style_id for item in profile.styles], symbols=profile.symbols, timeframes=profile.timeframes, risk_level=profile.risk_level, schedule_seconds=profile.schedule_seconds)


def update_profile(state, profile_id: str, **changes: Any) -> AnalysisProfile:
    profiles = _profiles(state)
    if profile_id not in profiles:
        raise KeyError(profile_id)
    profile = profiles[profile_id]
    for key, value in changes.items():
        if key == "styles":
            value = [ProfileStyle(str(item)) if isinstance(item, str) else item for item in value]
            for item in value:
                get_analysis_style(item.style_id)
        if hasattr(profile, key):
            setattr(profile, key, value)
    profile.version += 1
    _save(state, profiles)
    return profile


def set_active_profile(state, profile_id: str) -> AnalysisProfile:
    profile = get_profile(state, profile_id)
    if profile is None:
        raise KeyError(profile_id)
    state.settings[_ACTIVE_PROFILE_KEY] = profile_id
    return profile
