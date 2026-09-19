from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean, pstdev


@dataclass(frozen=True, slots=True)
class StatisticalSnapshot:
    samples: int
    return_mean: float
    return_volatility: float
    positive_probability: float
    negative_probability: float
    expectancy: float
    max_drawdown: float
    correlation: float | None = None

    def summary(self) -> dict[str, float | int | None]:
        return {
            "samples": self.samples,
            "return_mean": self.return_mean,
            "return_volatility": self.return_volatility,
            "positive_probability": self.positive_probability,
            "negative_probability": self.negative_probability,
            "expectancy": self.expectancy,
            "max_drawdown": self.max_drawdown,
            "correlation": self.correlation,
        }


class StatisticalEngine:
    """Deterministic, dependency-light statistics for real historical price data."""

    @staticmethod
    def _finite_prices(prices: list[float]) -> list[float]:
        if len(prices) < 3:
            raise ValueError("at least three prices are required")
        values = [float(value) for value in prices]
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise ValueError("prices must be finite and greater than zero")
        return values

    def evaluate(self, prices: list[float]) -> StatisticalSnapshot:
        values = self._finite_prices(prices)
        returns = [(b / a) - 1.0 for a, b in zip(values, values[1:])]
        if not all(math.isfinite(value) for value in returns):
            raise ValueError("returns must be finite")
        equity = 1.0
        peak = 1.0
        max_drawdown = 0.0
        for change in returns:
            equity *= 1.0 + change
            peak = max(peak, equity)
            max_drawdown = min(max_drawdown, equity / peak - 1.0)
        positive = [value for value in returns if value > 0]
        negative = [value for value in returns if value < 0]
        return StatisticalSnapshot(
            samples=len(returns),
            return_mean=mean(returns),
            return_volatility=pstdev(returns) if len(returns) > 1 else 0.0,
            positive_probability=len(positive) / len(returns),
            negative_probability=len(negative) / len(returns),
            expectancy=mean(returns),
            max_drawdown=max_drawdown,
        )
