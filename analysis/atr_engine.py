from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Sequence


@dataclass(frozen=True)
class ATRResult:
    """Professional ATR calculation result."""

    atr: float
    atr_percentage: float
    volatility: str


class ATREngine:
    """
    Professional Average True Range engine.

    Supports close-only price sequences and Candle-like OHLC objects.
    Invalid numeric data is rejected instead of silently removed.
    """

    def __init__(
        self,
        period: int = 14,
        low_volatility_threshold: float = 0.5,
        medium_volatility_threshold: float = 1.5,
        high_volatility_threshold: float = 3.0,
    ) -> None:
        if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
            raise ValueError("ATR period must be a positive integer.")

        thresholds = (
            low_volatility_threshold,
            medium_volatility_threshold,
            high_volatility_threshold,
        )
        if not all(self._is_valid_number(value) for value in thresholds):
            raise ValueError("Volatility thresholds must be finite numbers.")
        if any(float(value) < 0 for value in thresholds):
            raise ValueError("Volatility thresholds cannot be negative.")
        if not (
            low_volatility_threshold
            <= medium_volatility_threshold
            <= high_volatility_threshold
        ):
            raise ValueError(
                "Volatility thresholds must be ordered from low to high."
            )

        self.period = period
        self.low_volatility_threshold = float(low_volatility_threshold)
        self.medium_volatility_threshold = float(medium_volatility_threshold)
        self.high_volatility_threshold = float(high_volatility_threshold)

    @staticmethod
    def _is_valid_number(value: Any) -> bool:
        try:
            return isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            return False

    @classmethod
    def _normalize_prices(cls, prices: Sequence[Any]) -> list[float]:
        """Validate close prices without silently dropping invalid values."""
        if isinstance(prices, (str, bytes)):
            raise TypeError("ATR prices must be a numeric sequence.")

        normalized: list[float] = []
        for value in prices:
            if not cls._is_valid_number(value):
                raise ValueError("ATR prices must contain finite numeric values.")
            price = float(value)
            if price <= 0:
                raise ValueError("ATR prices must be greater than zero.")
            normalized.append(price)
        return normalized

    @classmethod
    def _extract_ohlc(
        cls,
        data: Sequence[Any],
    ) -> tuple[list[float], list[float], list[float]]:
        highs: list[float] = []
        lows: list[float] = []
        closes: list[float] = []

        for item in data:
            high = getattr(item, "high", None)
            low = getattr(item, "low", None)
            close = getattr(item, "close", None)
            if not (
                cls._is_valid_number(high)
                and cls._is_valid_number(low)
                and cls._is_valid_number(close)
            ):
                raise ValueError("Invalid OHLC candle data.")

            high_value = float(high)
            low_value = float(low)
            close_value = float(close)
            if high_value <= 0 or low_value <= 0 or close_value <= 0:
                raise ValueError("OHLC prices must be greater than zero.")
            if high_value < low_value:
                raise ValueError("Candle high cannot be lower than low.")
            if not low_value <= close_value <= high_value:
                raise ValueError("Candle close must be between low and high.")

            highs.append(high_value)
            lows.append(low_value)
            closes.append(close_value)

        return highs, lows, closes

    @staticmethod
    def true_range(prices: list[float]) -> list[float]:
        if len(prices) < 2:
            return []

        ranges: list[float] = []
        for i in range(1, len(prices)):
            current_price = float(prices[i])
            previous_close = float(prices[i - 1])
            tr = abs(current_price - previous_close)
            if not isfinite(tr):
                raise ValueError("ATR true range must be finite.")
            ranges.append(tr)
        return ranges

    @staticmethod
    def ohlc_true_range(
        highs: list[float],
        lows: list[float],
        closes: list[float],
    ) -> list[float]:
        if not (len(highs) == len(lows) == len(closes)):
            raise ValueError("OHLC arrays must have equal length.")
        if len(closes) < 2:
            return []

        ranges: list[float] = []
        for i in range(1, len(closes)):
            high = highs[i]
            low = lows[i]
            previous_close = closes[i - 1]
            current_range = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )
            if not isfinite(current_range):
                raise ValueError("ATR true range must be finite.")
            ranges.append(max(0.0, current_range))
        return ranges

    def _wilder_atr(self, true_ranges: list[float]) -> float:
        if len(true_ranges) < self.period:
            return 0.0
        if not all(isfinite(float(value)) and float(value) >= 0 for value in true_ranges):
            raise ValueError("ATR true ranges must be finite and non-negative.")

        atr = sum(true_ranges[: self.period]) / self.period
        if not isfinite(atr):
            raise ValueError("ATR calculation produced a non-finite value.")

        for current_tr in true_ranges[self.period :]:
            atr = ((atr * (self.period - 1)) + current_tr) / self.period
            if not isfinite(atr):
                raise ValueError("ATR calculation produced a non-finite value.")
        return max(0.0, atr)

    @staticmethod
    def classify_volatility(atr_percentage: float) -> str:
        if not isfinite(float(atr_percentage)):
            raise ValueError("ATR percentage must be finite.")
        if atr_percentage <= 0:
            return "UNKNOWN"
        if atr_percentage < 0.5:
            return "VERY_LOW"
        if atr_percentage < 1.5:
            return "LOW"
        if atr_percentage < 3.0:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def calculate_atr_percentage(atr: float, current_price: float) -> float:
        if not isfinite(float(atr)) or not isfinite(float(current_price)):
            raise ValueError("ATR and current price must be finite.")
        if atr <= 0 or current_price <= 0:
            return 0.0
        result = (atr / current_price) * 100.0
        if not isfinite(result):
            raise ValueError("ATR percentage calculation produced a non-finite value.")
        return result

    @staticmethod
    def _empty_result() -> ATRResult:
        return ATRResult(atr=0.0, atr_percentage=0.0, volatility="UNKNOWN")

    def calculate(self, prices: Sequence[Any]) -> ATRResult:
        if prices is None:
            return self._empty_result()
        if isinstance(prices, (str, bytes)):
            raise TypeError("ATR prices must be a numeric sequence.")
        try:
            if len(prices) == 0:
                return self._empty_result()
            first_item = prices[0]
        except (TypeError, IndexError) as error:
            raise TypeError("ATR prices must be a non-empty sequence.") from error

        has_ohlc = all(
            hasattr(first_item, attribute)
            for attribute in ("high", "low", "close")
        )

        if has_ohlc:
            highs, lows, closes = self._extract_ohlc(prices)
            if len(closes) <= self.period:
                return self._empty_result()
            true_ranges = self.ohlc_true_range(highs, lows, closes)
            atr = self._wilder_atr(true_ranges)
            current_price = closes[-1]
        else:
            normalized = self._normalize_prices(prices)
            if len(normalized) <= self.period:
                return self._empty_result()
            true_ranges = self.true_range(normalized)
            atr = self._wilder_atr(true_ranges)
            current_price = normalized[-1]

        atr_percentage = self.calculate_atr_percentage(atr, current_price)
        volatility = self.classify_volatility(atr_percentage)
        if not isfinite(atr) or not isfinite(atr_percentage):
            raise ValueError("ATR result must be finite.")

        return ATRResult(
            atr=round(atr, 6),
            atr_percentage=round(atr_percentage, 3),
            volatility=volatility,
        )
