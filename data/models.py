
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any


@dataclass(frozen=True, slots=True)
class Candle:
    """
    Standardized market candle.

    This is the canonical market-data model used throughout
    the data, analysis, signal and risk-management layers.

    The public field names are intentionally kept compatible
    with the existing project.
    """

    symbol: str
    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str):
            raise TypeError("symbol must be a string.")

        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty.")

        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime.")

        # A datetime with tzinfo is not necessarily timezone-aware:
        # custom tzinfo implementations may return None from utcoffset().
        # Reject that state at the canonical market-data boundary so
        # timestamp arithmetic cannot fail later in DataQuality/freshness.
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware.")

        numeric_values = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

        for field_name, value in numeric_values.items():
            if isinstance(value, bool):
                raise TypeError(f"{field_name} must be a real number.")

            try:
                numeric_value = float(value)
            except (TypeError, ValueError) as exc:
                raise TypeError(f"{field_name} must be a real number.") from exc

            if not math.isfinite(numeric_value):
                raise ValueError(f"{field_name} must be finite.")

        if self.open <= 0:
            raise ValueError("open must be greater than zero.")
        if self.high <= 0:
            raise ValueError("high must be greater than zero.")
        if self.low <= 0:
            raise ValueError("low must be greater than zero.")
        if self.close <= 0:
            raise ValueError("close must be greater than zero.")
        if self.volume < 0:
            raise ValueError("volume cannot be negative.")

        if self.high < self.low:
            raise ValueError("high cannot be lower than low.")
        if self.high < max(self.open, self.close):
            raise ValueError("high must be >= open and close.")
        if self.low > min(self.open, self.close):
            raise ValueError("low must be <= open and close.")

    @property
    def typical_price(self) -> float:
        return (self.high + self.low + self.close) / 3.0

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2.0

    @property
    def spread(self) -> float:
        return self.high - self.low

    @property
    def range(self) -> float:
        return self.spread

    @property
    def range_percent(self) -> float:
        return (self.spread / self.low) * 100.0

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def body_signed(self) -> float:
        return self.close - self.open

    @property
    def body_percent(self) -> float:
        return (self.body / self.open) * 100.0

    @property
    def body_to_range_ratio(self) -> float:
        if self.spread == 0:
            return 0.0
        return self.body / self.spread

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        return self.close == self.open

    @property
    def direction(self) -> str:
        if self.is_bullish:
            return "bullish"
        if self.is_bearish:
            return "bearish"
        return "neutral"

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def upper_wick_percent(self) -> float:
        if self.spread == 0:
            return 0.0
        return (self.upper_wick / self.spread) * 100.0

    @property
    def lower_wick_percent(self) -> float:
        if self.spread == 0:
            return 0.0
        return (self.lower_wick / self.spread) * 100.0

    @property
    def wick_to_body_ratio(self) -> float:
        if self.body == 0:
            return 0.0
        return (self.upper_wick + self.lower_wick) / self.body

    def change_from_open(self) -> float:
        return self.close - self.open

    def change_percent(self) -> float:
        return ((self.close - self.open) / self.open) * 100.0

    @property
    def close_position(self) -> float:
        if self.spread == 0:
            return 0.5
        return (self.close - self.low) / self.spread

    @property
    def open_position(self) -> float:
        if self.spread == 0:
            return 0.5
        return (self.open - self.low) / self.spread

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }

    def with_symbol(self, symbol: str) -> "Candle":
        return Candle(
            symbol=symbol,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )

    def __repr__(self) -> str:
        return (
            "Candle("
            f"symbol={self.symbol!r}, "
            f"timestamp={self.timestamp.isoformat()!r}, "
            f"open={self.open!r}, "
            f"high={self.high!r}, "
            f"low={self.low!r}, "
            f"close={self.close!r}, "
            f"volume={self.volume!r}"
            ")"
        )


__all__ = ["Candle"]
