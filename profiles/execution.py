from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .models import AnalysisProfile

ExecutionMode = Literal["LIVE", "BACKTEST", "REPLAY", "RESEARCH"]


@dataclass(frozen=True)
class ProfileExecutionContext:
    """Immutable execution contract shared by live and historical workloads."""

    mode: ExecutionMode
    profile_id: str
    profile_version: int
    style_ids: tuple[str, ...]
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    risk_level: str
    schedule_seconds: int
    config_snapshot: dict[str, Any]
    user_id: str | None = None
    experiment_id: str | None = None
    requested_capabilities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "style_ids": list(self.style_ids),
            "symbols": list(self.symbols),
            "timeframes": list(self.timeframes),
            "risk_level": self.risk_level,
            "schedule_seconds": self.schedule_seconds,
            "config_snapshot": dict(self.config_snapshot),
            "user_id": self.user_id,
            "experiment_id": self.experiment_id,
            "requested_capabilities": list(self.requested_capabilities),
        }


def profile_snapshot(profile: AnalysisProfile) -> dict[str, Any]:
    """Return the exact profile configuration captured for an execution."""

    return profile.to_dict()


def build_execution_context(
    profile: AnalysisProfile,
    mode: ExecutionMode,
    *,
    symbols: list[str] | tuple[str, ...] | None = None,
    timeframes: list[str] | tuple[str, ...] | None = None,
    user_id: str | None = None,
    experiment_id: str | None = None,
    requested_capabilities: list[str] | tuple[str, ...] | None = None,
) -> ProfileExecutionContext:
    if mode not in {"LIVE", "BACKTEST", "REPLAY", "RESEARCH"}:
        raise ValueError(f"Unsupported execution mode: {mode}")

    style_ids = tuple(
        item.style_id for item in profile.styles
        if item.enabled
    )
    if not style_ids:
        raise ValueError("Execution profile must contain at least one enabled style")

    resolved_symbols = tuple(str(item) for item in (symbols if symbols is not None else profile.symbols))
    resolved_timeframes = tuple(
        str(item) for item in (timeframes if timeframes is not None else profile.timeframes)
    )
    snapshot = profile_snapshot(profile)

    return ProfileExecutionContext(
        mode=mode,
        profile_id=profile.profile_id,
        profile_version=profile.version,
        style_ids=style_ids,
        symbols=resolved_symbols,
        timeframes=resolved_timeframes,
        risk_level=profile.risk_level,
        schedule_seconds=profile.schedule_seconds,
        config_snapshot=snapshot,
        user_id=str(user_id) if user_id is not None else None,
        experiment_id=str(experiment_id) if experiment_id is not None else None,
        requested_capabilities=tuple(dict.fromkeys(str(item) for item in (requested_capabilities or ()))),
    )


def context_from_payload(payload: dict[str, Any], mode: ExecutionMode) -> ProfileExecutionContext:
    """Build a validated immutable context from a queued Worker payload."""

    if not isinstance(payload, dict):
        raise TypeError("execution payload must be a dictionary")

    profile_id = str(payload.get("profile_id", "")).strip()
    if not profile_id:
        raise ValueError("profile_id is required for profile execution")

    profile_version = int(payload.get("profile_version", 1))
    if profile_version < 1:
        raise ValueError("profile_version must be positive")

    style_ids = tuple(dict.fromkeys(str(item) for item in payload.get("style_ids", [])))
    if not style_ids:
        raise ValueError("style_ids must contain at least one selected style")

    symbols = tuple(str(item) for item in payload.get("symbols", []))
    timeframes = tuple(str(item) for item in payload.get("timeframes", []))
    risk_level = str(payload.get("risk_level", "medium"))
    schedule_seconds = max(60, int(payload.get("schedule_seconds", 900)))

    snapshot = payload.get("profile_snapshot")
    if snapshot is None:
        snapshot = {
            "profile_id": profile_id,
            "version": profile_version,
            "styles": [{"style_id": item, "enabled": True, "weight": 1.0} for item in style_ids],
            "symbols": list(symbols),
            "timeframes": list(timeframes),
            "risk_level": risk_level,
            "schedule_seconds": schedule_seconds,
        }
    if not isinstance(snapshot, dict):
        raise ValueError("profile_snapshot must be a dictionary")
    if str(snapshot.get("profile_id", profile_id)) != profile_id:
        raise ValueError("profile_snapshot.profile_id does not match profile_id")
    snapshot_version = int(snapshot.get("version", profile_version))
    if snapshot_version != profile_version:
        raise ValueError("profile_snapshot.version does not match profile_version")
    requested_capabilities = tuple(dict.fromkeys(str(item) for item in payload.get("requested_capabilities", [])))

    return ProfileExecutionContext(
        mode=mode,
        profile_id=profile_id,
        profile_version=profile_version,
        style_ids=style_ids,
        symbols=symbols,
        timeframes=timeframes,
        risk_level=risk_level,
        schedule_seconds=schedule_seconds,
        config_snapshot=dict(snapshot),
        user_id=str(payload.get("user_id")) if payload.get("user_id") is not None else None,
        experiment_id=str(payload.get("experiment_id")) if payload.get("experiment_id") is not None else None,
        requested_capabilities=requested_capabilities,
    )
