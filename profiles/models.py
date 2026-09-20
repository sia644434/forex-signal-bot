from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfileStyle:
    style_id: str
    enabled: bool = True
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"style_id": self.style_id, "enabled": self.enabled, "weight": self.weight}


@dataclass
class AnalysisProfile:
    profile_id: str
    name: str
    styles: list[ProfileStyle] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    timeframes: list[str] = field(default_factory=lambda: ["M15"])
    risk_level: str = "medium"
    schedule_seconds: int = 900
    enabled: bool = True
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id, "name": self.name,
            "styles": [style.to_dict() for style in self.styles],
            "symbols": list(self.symbols), "timeframes": list(self.timeframes),
            "risk_level": self.risk_level, "schedule_seconds": self.schedule_seconds,
            "enabled": self.enabled, "version": self.version,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisProfile":
        return cls(
            profile_id=str(payload["profile_id"]), name=str(payload["name"]),
            styles=[ProfileStyle(str(item["style_id"]), bool(item.get("enabled", True)), float(item.get("weight", 1.0))) for item in payload.get("styles", [])],
            symbols=[str(x) for x in payload.get("symbols", [])],
            timeframes=[str(x) for x in payload.get("timeframes", ["M15"])],
            risk_level=str(payload.get("risk_level", "medium")),
            schedule_seconds=int(payload.get("schedule_seconds", 900)),
            enabled=bool(payload.get("enabled", True)), version=int(payload.get("version", 1)),
        )


PRESET_PROFILES: dict[str, AnalysisProfile] = {
    "preset_scalping": AnalysisProfile("preset_scalping", "اسکلپ", [ProfileStyle("scalping")], timeframes=["M5", "M15"], schedule_seconds=300),
    "preset_swing": AnalysisProfile("preset_swing", "سوئینگ", [ProfileStyle("swing")], timeframes=["H1", "H4", "D1"], schedule_seconds=3600),
    "preset_day_trading": AnalysisProfile("preset_day_trading", "دی‌تریـدینگ", [ProfileStyle("day_trading")], timeframes=["M15", "H1"], schedule_seconds=900),
    "preset_trend": AnalysisProfile("preset_trend", "دنبال‌کننده روند", [ProfileStyle("trend_following")], timeframes=["H1", "H4", "D1"], schedule_seconds=3600),
}


def profile_from_preset(preset_id: str) -> AnalysisProfile:
    try:
        source = PRESET_PROFILES[preset_id]
    except KeyError as exc:
        raise ValueError(f"Unknown profile preset: {preset_id}") from exc
    return AnalysisProfile.from_dict(source.to_dict())
