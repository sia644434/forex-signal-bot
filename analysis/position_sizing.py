"""Unit-aware position sizing for quote-currency risk.

This module deliberately does not assume an account currency or an FX rate.
A caller must provide an explicit quote-to-account conversion rate whenever
quote currency and account currency differ.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class PositionSizingResult:
    """Position sizing values expressed in explicit monetary units."""

    position_size: float
    lot_size: float
    risk_amount_account: float
    risk_per_unit_account: float


def calculate_position_size(
    *,
    account_balance: float,
    risk_percent: float,
    risk_distance_quote: float,
    contract_size: float,
    account_currency: str,
    quote_currency: str,
    quote_to_account_rate: float | None = None,
) -> PositionSizingResult:
    """Calculate an executable position size with explicit currency units.

    ``risk_distance_quote`` is the price distance denominated in the
    instrument's quote currency per unit of the base asset.

    If quote and account currencies differ, ``quote_to_account_rate`` must
    convert one quote-currency unit into account-currency units. No implicit
    USD assumption or market-rate lookup is performed here.

    The requested monetary risk is treated as a ceiling. Because the broker
    lot precision is 0.001 lots, the executable lot is floored rather than
    rounded upward. ``position_size`` is then derived from that executable
    lot so the two values always describe the same executable quantity.
    """
    if not isinstance(account_currency, str) or not isinstance(quote_currency, str):
        raise TypeError("account_currency and quote_currency must be strings.")

    account_currency = account_currency.strip().upper()
    quote_currency = quote_currency.strip().upper()

    if not account_currency:
        raise ValueError("account_currency must not be empty.")
    if not quote_currency:
        raise ValueError("quote_currency must not be empty.")

    numeric_inputs = {
        "account_balance": account_balance,
        "risk_percent": risk_percent,
        "risk_distance_quote": risk_distance_quote,
        "contract_size": contract_size,
    }
    for name, value in numeric_inputs.items():
        try:
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite.")
        except (TypeError, ValueError) as error:
            if isinstance(error, ValueError) and str(error).endswith("must be finite."):
                raise
            raise ValueError(f"{name} must be a finite number.") from error

    account_balance = float(account_balance)
    risk_percent = float(risk_percent)
    risk_distance_quote = float(risk_distance_quote)
    contract_size = float(contract_size)

    if account_balance <= 0:
        raise ValueError("account_balance must be greater than zero.")
    if risk_percent <= 0:
        raise ValueError("risk_percent must be greater than zero.")
    if risk_distance_quote <= 0:
        raise ValueError("risk_distance_quote must be greater than zero.")
    if contract_size <= 0:
        raise ValueError("contract_size must be greater than zero.")

    if account_currency == quote_currency:
        conversion_rate = 1.0
    else:
        if quote_to_account_rate is None:
            raise ValueError(
                "quote_to_account_rate is required when quote_currency "
                "differs from account_currency."
            )
        try:
            conversion_rate = float(quote_to_account_rate)
        except (TypeError, ValueError) as error:
            raise ValueError("quote_to_account_rate must be a finite number.") from error
        if not math.isfinite(conversion_rate):
            raise ValueError("quote_to_account_rate must be finite.")
        if conversion_rate <= 0:
            raise ValueError("quote_to_account_rate must be greater than zero.")

    risk_amount_account = account_balance * (risk_percent / 100.0)
    risk_per_unit_account = risk_distance_quote * conversion_rate

    if not math.isfinite(risk_amount_account) or not math.isfinite(risk_per_unit_account):
        raise ValueError("calculated risk values must be finite.")
    if risk_per_unit_account <= 0:
        raise ValueError("converted risk per unit must be greater than zero.")

    raw_position_size = risk_amount_account / risk_per_unit_account
    raw_lot_size = raw_position_size / contract_size
    if not math.isfinite(raw_position_size) or not math.isfinite(raw_lot_size):
        raise ValueError("calculated position size must be finite.")

    # Broker lot precision must never round upward: doing so could make the
    # executable lot exceed the requested monetary risk.
    lot_size = math.floor(raw_lot_size * 1000.0) / 1000.0
    if lot_size <= 0:
        raise ValueError("calculated lot size is below the supported precision.")

    # Derive position_size from the executable lot. This prevents the public
    # position_size and lot_size fields from describing different quantities.
    position_size = lot_size * contract_size
    if not math.isfinite(position_size):
        raise ValueError("executable position size must be finite.")

    return PositionSizingResult(
        position_size=round(position_size, 4),
        lot_size=round(lot_size, 3),
        risk_amount_account=round(risk_amount_account, 2),
        risk_per_unit_account=round(risk_per_unit_account, 8),
    )
