from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PortfolioExposure:
    symbol: str
    market: str
    side: str
    notional: float
    weight: float


@dataclass(frozen=True, slots=True)
class PortfolioRiskSnapshot:
    total_notional: float
    gross_long: float
    gross_short: float
    net_exposure: float
    concentration: float
    risk_flags: tuple[str, ...] = field(default_factory=tuple)


class PortfolioRiskGuard:
    """Asset-class-neutral pre-trade portfolio concentration guard."""

    def assess(
        self,
        exposures: list[PortfolioExposure],
        *,
        max_symbol_weight: float = 0.35,
        max_gross_exposure: float = 1.0,
        equity: float | None = None,
    ) -> PortfolioRiskSnapshot:
        if not 0 < max_symbol_weight <= 1:
            raise ValueError("max_symbol_weight must be in (0, 1]")
        if max_gross_exposure <= 0:
            raise ValueError("max_gross_exposure must be positive")
        if equity is not None and float(equity) <= 0:
            raise ValueError("equity must be positive when provided")
        total = sum(max(0.0, float(item.notional)) for item in exposures)
        if total <= 0:
            return PortfolioRiskSnapshot(0.0, 0.0, 0.0, 0.0, 0.0, ())
        long = sum(max(0.0, float(item.notional)) for item in exposures if item.side.upper() == "BUY")
        short = sum(max(0.0, float(item.notional)) for item in exposures if item.side.upper() == "SELL")
        by_symbol: dict[str, float] = {}
        for item in exposures:
            by_symbol[item.symbol] = by_symbol.get(item.symbol, 0.0) + max(0.0, float(item.notional))
        concentration = max(by_symbol.values(), default=0.0) / total
        gross_base = float(equity) if equity is not None else total
        gross = (long + short) / gross_base
        flags: list[str] = []
        if concentration > max_symbol_weight:
            flags.append("SYMBOL_CONCENTRATION")
        if gross > max_gross_exposure:
            flags.append("GROSS_EXPOSURE")
        return PortfolioRiskSnapshot(
            total_notional=total,
            gross_long=long,
            gross_short=short,
            net_exposure=long - short,
            concentration=concentration,
            risk_flags=tuple(flags),
        )

    def can_add(
        self,
        exposures: list[PortfolioExposure],
        candidate: PortfolioExposure,
        *,
        max_symbol_weight: float = 0.35,
        max_gross_exposure: float = 1.0,
        equity: float | None = None,
    ) -> dict[str, Any]:
        before = self.assess(exposures, max_symbol_weight=max_symbol_weight, max_gross_exposure=max_gross_exposure, equity=equity)
        after = self.assess(exposures + [candidate], max_symbol_weight=max_symbol_weight, max_gross_exposure=max_gross_exposure, equity=equity)
        blocked = bool(after.risk_flags)
        return {
            "allowed": not blocked,
            "blocked": blocked,
            "before": before,
            "after": after,
            "reason": "portfolio risk limits exceeded" if blocked else "within configured portfolio risk limits",
        }


__all__ = ["PortfolioExposure", "PortfolioRiskSnapshot", "PortfolioRiskGuard"]
