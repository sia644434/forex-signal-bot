from __future__ import annotations

import math


def validate_series(
    values: list[float],
) -> None:
    """
    Validate indicator input series.
    """

    if not isinstance(
        values,
        list,
    ):
        raise TypeError(
            "values must be a list."
        )

    if len(values) == 0:
        raise ValueError(
            "values cannot be empty."
        )

    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"series value at index {index} must be numeric and finite."
            )
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(
                f"series value at index {index} must be numeric and finite."
            )


def validate_period(
    period: int,
) -> None:
    """
    Validate indicator period.
    """

    if not isinstance(
        period,
        int,
    ):
        raise TypeError(
            "period must be an integer."
        )

    if period < 1:
        raise ValueError(
            "period must be greater than zero."
        )
