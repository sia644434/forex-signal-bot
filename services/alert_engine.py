from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class Alert:
    alert_id: str
    symbol: str
    signal: str
    severity: str
    reason: str
    created_at: str
    dedupe_key: str


class AlertEngine:
    """Deterministic alert policy with deduplication and explicit severity."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    @staticmethod
    def _severity(signal: str, confidence: float, risk_level: str) -> str:
        if str(risk_level).upper() in {"CRISIS", "EXTREME"}:
            return "CRITICAL"
        if str(signal).upper() in {"STRONG_BUY", "STRONG_SELL"} and confidence >= 0.75:
            return "HIGH"
        if str(signal).upper() in {"BUY", "SELL"} and confidence >= 0.60:
            return "MEDIUM"
        return "INFO"

    def evaluate(self, report: Any, *, created_at: datetime | None = None) -> Alert | None:
        signal = str(getattr(report, "signal", "NO_TRADE")).upper()
        symbol = str(getattr(report, "symbol", "UNKNOWN")).strip().upper()
        confidence = float(getattr(report, "confidence", 0.0) or 0.0)
        risk_level = str(getattr(report, "macro_risk_level", "NORMAL")).upper()
        portfolio_blocked = bool(getattr(report, "portfolio_risk_blocked", False))
        if not symbol or signal in {"NEUTRAL", "WAIT", "NO_TRADE"} or portfolio_blocked:
            return None
        if confidence < 0.60 and risk_level not in {"CRISIS", "EXTREME"}:
            return None
        severity = self._severity(signal, confidence, risk_level)
        reason = f"{signal} confidence={max(0.0, min(1.0, confidence)):.2f}"
        dedupe_key = f"{symbol}:{signal}:{severity}"
        if dedupe_key in self._seen:
            return None
        self._seen.add(dedupe_key)
        stamp = created_at or datetime.now(timezone.utc)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return Alert(
            alert_id=f"{dedupe_key}:{stamp.isoformat()}",
            symbol=symbol,
            signal=signal,
            severity=severity,
            reason=reason,
            created_at=stamp.isoformat(),
            dedupe_key=dedupe_key,
        )

    def reset(self) -> None:
        self._seen.clear()


def serialize_alert(alert: Alert) -> dict[str, Any]:
    return {
        "alert_id": alert.alert_id,
        "symbol": alert.symbol,
        "signal": alert.signal,
        "severity": alert.severity,
        "reason": alert.reason,
        "created_at": alert.created_at,
        "dedupe_key": alert.dedupe_key,
    }


__all__ = ["Alert", "AlertEngine", "serialize_alert"]
