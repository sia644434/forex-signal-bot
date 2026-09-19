from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    symbol: str
    market: str
    quantity: float
    price: float
    risk_amount: float = 0.0

    @property
    def notional(self) -> float:
        return self.quantity * self.price


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    total_exposure: float
    market_exposure: dict[str, float]
    symbol_exposure: dict[str, float]
    concentration: float
    total_risk: float
    drawdown: float
    correlation: dict[str, dict[str, float]]

    def summary(self) -> dict[str, object]:
        return {
            "total_exposure": self.total_exposure,
            "market_exposure": self.market_exposure,
            "symbol_exposure": self.symbol_exposure,
            "concentration": self.concentration,
            "total_risk": self.total_risk,
            "drawdown": self.drawdown,
            "correlation": self.correlation,
        }


class PortfolioEngine:
    """Multi-asset portfolio exposure, concentration, correlation and stress calculations."""

    @staticmethod
    def _finite(value: object, name: str, *, minimum: float | None = None) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric and finite") from exc
        if not math.isfinite(result) or (minimum is not None and result < minimum):
            raise ValueError(f"{name} must be finite and at least {minimum}" if minimum is not None else f"{name} must be numeric and finite")
        return result

    @classmethod
    def normalize_positions(cls, positions: list[PortfolioPosition | dict[str, object]]) -> list[PortfolioPosition]:
        result: list[PortfolioPosition] = []
        for item in positions:
            if isinstance(item, PortfolioPosition):
                position = item
            elif isinstance(item, dict):
                position = PortfolioPosition(
                    symbol=str(item.get("symbol", "")).strip().upper(),
                    market=str(item.get("market", "")).strip().lower(),
                    quantity=cls._finite(item.get("quantity"), "quantity"),
                    price=cls._finite(item.get("price"), "price", minimum=0.0),
                    risk_amount=cls._finite(item.get("risk_amount", 0.0), "risk_amount", minimum=0.0),
                )
            else:
                raise TypeError("positions must contain PortfolioPosition or mapping values")
            if not position.symbol or not position.market:
                raise ValueError("position symbol and market are required")
            cls._finite(position.quantity, "quantity")
            cls._finite(position.price, "price", minimum=0.0)
            cls._finite(position.risk_amount, "risk_amount", minimum=0.0)
            result.append(position)
        return result

    @staticmethod
    def correlation_matrix(returns: dict[str, list[float]]) -> dict[str, dict[str, float]]:
        names = sorted(returns)
        if not names:
            return {}
        normalized: dict[str, list[float]] = {}
        for name in names:
            values = [float(v) for v in returns[name]]
            if len(values) < 2 or not all(math.isfinite(v) for v in values):
                raise ValueError("each return series must contain at least two finite values")
            normalized[name] = values
        matrix: dict[str, dict[str, float]] = {name: {} for name in names}
        for left in names:
            for right in names:
                a, b = normalized[left], normalized[right]
                if len(a) != len(b):
                    raise ValueError("return series must have equal lengths")
                ma, mb = mean(a), mean(b)
                da = math.sqrt(sum((x - ma) ** 2 for x in a))
                db = math.sqrt(sum((x - mb) ** 2 for x in b))
                value = 1.0 if left == right and da > 0 else 0.0 if da == 0 or db == 0 else sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (da * db)
                matrix[left][right] = round(max(-1.0, min(1.0, value)), 6)
        return matrix

    def snapshot(
        self,
        positions: list[PortfolioPosition | dict[str, object]],
        *,
        equity_curve: list[float] | None = None,
        returns: dict[str, list[float]] | None = None,
    ) -> PortfolioSnapshot:
        normalized = self.normalize_positions(positions)
        symbol_exposure: dict[str, float] = {}
        market_exposure: dict[str, float] = {}
        total_risk = 0.0
        for position in normalized:
            notional = self._finite(position.notional, f"{position.symbol} notional")
            if notional < 0:
                raise ValueError("position notional cannot be negative")
            symbol_exposure[position.symbol] = symbol_exposure.get(position.symbol, 0.0) + notional
            market_exposure[position.market] = market_exposure.get(position.market, 0.0) + notional
            total_risk += position.risk_amount
        total_exposure = sum(symbol_exposure.values())
        concentration = max(symbol_exposure.values(), default=0.0) / total_exposure if total_exposure else 0.0

        drawdown = 0.0
        if equity_curve is not None:
            values = [self._finite(v, "equity") for v in equity_curve]
            if not values or any(v <= 0 for v in values):
                raise ValueError("equity curve must contain positive finite values")
            peak = values[0]
            drawdown = min((value / (peak := max(peak, value)) - 1.0) for value in values)
        return PortfolioSnapshot(
            total_exposure=total_exposure,
            market_exposure=market_exposure,
            symbol_exposure=symbol_exposure,
            concentration=concentration,
            total_risk=total_risk,
            drawdown=drawdown,
            correlation=self.correlation_matrix(returns or {}),
        )

    def stress(self, snapshot: PortfolioSnapshot, shocks: dict[str, float]) -> dict[str, object]:
        stressed: dict[str, float] = {}
        for symbol, shock in shocks.items():
            numeric = self._finite(shock, f"shock for {symbol}")
            stressed[symbol] = snapshot.symbol_exposure.get(symbol, 0.0) * (1.0 + numeric)
        loss = sum(
            snapshot.symbol_exposure.get(symbol, 0.0) - value
            for symbol, value in stressed.items()
        )
        return {"stressed_exposure": stressed, "estimated_loss": loss}
