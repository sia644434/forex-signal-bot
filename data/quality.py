from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math
from collections.abc import Sequence

from config.symbols import normalize_symbol
from data.models import Candle


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    valid: bool
    candle_count: int
    duplicate_timestamps: int
    out_of_order: int
    gaps: int
    suspicious_gaps: int
    issues: tuple[str, ...]


class DataQuality:
    """Validate normalized market candles while allowing normal market closures."""

    _WEEKEND_CLOSURE_MARKETS = frozenset({"forex", "stock", "index", "commodity"})

    @staticmethod
    def _validate_interval(interval: timedelta) -> None:
        if not isinstance(interval, timedelta):
            raise TypeError("interval must be a timedelta")
        if interval <= timedelta(0):
            raise ValueError("interval must be greater than zero.")

    @staticmethod
    def _validate_gap_tolerance(gap_tolerance) -> None:
        if isinstance(gap_tolerance, bool) or not isinstance(gap_tolerance, int):
            raise TypeError("gap_tolerance must be an integer")
        if gap_tolerance <= 0:
            raise ValueError("gap_tolerance must be greater than zero")

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return normalize_symbol(symbol)

    @classmethod
    def _is_expected_market_closure_gap(
        cls,
        previous,
        current,
        expected_interval: timedelta,
        market_type: str = "forex",
    ) -> bool:
        delta = current.timestamp - previous.timestamp
        if delta <= expected_interval:
            return False

        if market_type not in cls._WEEKEND_CLOSURE_MARKETS:
            return False

        previous_day = previous.timestamp.weekday()
        current_day = current.timestamp.weekday()

        # Only a genuine Friday -> Monday transition is treated as the normal
        # weekend closure. Crypto is explicitly 24/7, so its Friday->Monday
        # gap must remain visible as a data-quality failure.
        if previous_day == 4 and current_day == 0 and current.timestamp.date() > previous.timestamp.date():
            return delta <= timedelta(days=3, hours=6)

        return False

    @classmethod
    def inspect(
        cls,
        candles: Sequence[Candle],
        *,
        expected_symbol=None,
        expected_interval=None,
        gap_tolerance=1,
        market_type: str = "forex",
    ):
        if candles is None:
            raise TypeError("candles cannot be None")
        if not isinstance(candles, Sequence):
            raise TypeError("candles must be a sequence")

        if not isinstance(market_type, str):
            raise TypeError("market_type must be a string")
        normalized_market_type = market_type.strip().lower()
        if not normalized_market_type:
            raise ValueError("market_type cannot be empty")

        cls._validate_gap_tolerance(gap_tolerance)
        if expected_interval is not None:
            cls._validate_interval(expected_interval)

        issues = []
        duplicate_timestamps = 0
        out_of_order = 0
        gaps = 0
        suspicious_gaps = 0
        seen = set()
        previous = None
        symbol_check = cls._normalize_symbol(expected_symbol) if expected_symbol else None

        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                issues.append(f"item {index} is not a Candle")
                continue

            symbol = cls._normalize_symbol(candle.symbol)
            if symbol_check and symbol != symbol_check:
                issues.append(f"item {index} has unexpected symbol {candle.symbol!r}")

            values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
            if not all(math.isfinite(float(v)) for v in values):
                issues.append(f"item {index} contains non-finite numeric data")

            key = (symbol, candle.timestamp)
            if key in seen:
                duplicate_timestamps += 1
                issues.append(f"duplicate timestamp at item {index}")
            seen.add(key)

            if previous is not None:
                delta = candle.timestamp - previous.timestamp
                if delta <= timedelta(0):
                    out_of_order += 1
                    issues.append(f"timestamp order violation at item {index}")
                elif expected_interval and delta > expected_interval * gap_tolerance:
                    if not cls._is_expected_market_closure_gap(
                        previous,
                        candle,
                        expected_interval,
                        normalized_market_type,
                    ):
                        gaps += 1
                        suspicious_gaps += 1
                        issues.append(f"gap detected before item {index}: {delta}")

            previous = candle

        return DataQualityReport(not issues, len(candles), duplicate_timestamps, out_of_order, gaps, suspicious_gaps, tuple(issues))

    @classmethod
    def validate(cls, candles: Sequence[Candle], **kwargs):
        report = cls.inspect(candles, **kwargs)
        if not report.valid:
            raise ValueError("Invalid market data: " + "; ".join(report.issues))
        return list(candles)


__all__ = ["DataQuality", "DataQualityReport"]
