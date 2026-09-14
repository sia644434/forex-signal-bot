"""Unit-aware position sizing for quote-currency risk.

This module deliberately does not assume an account currency or an FX rate.
A caller must provide an explicit quote-to-account conversion rate whenever
quote currency and account currency differ.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DecimalException, ROUND_FLOOR
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
    """Calculate an executable position size with explicit currency units."""
    if not isinstance(account_currency, str) or not isinstance(quote_currency, str):
        raise TypeError("account_currency and quote_currency must be strings.")

    account_currency = account_currency.strip().upper()
    quote_currency = quote_currency.strip().upper()

    for name, currency in (("account_currency", account_currency), ("quote_currency", quote_currency)):
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError(f"{name} must be a 3-letter currency code.")

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
            raise ValueError("quote_to_account_rate is required when quote_currency differs from account_currency.")
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

    try:
        decimal_risk_amount = Decimal(str(account_balance)) * Decimal(str(risk_percent)) / Decimal("100")
        decimal_risk_per_unit = Decimal(str(risk_distance_quote)) * Decimal(str(conversion_rate))
        decimal_raw_lot = decimal_risk_amount / decimal_risk_per_unit / Decimal(str(contract_size))
        lot_size_decimal = decimal_raw_lot.quantize(Decimal("0.001"), rounding=ROUND_FLOOR)
    except DecimalException as error:
        # A finite float can still exceed Decimal's active precision during
        # quantization. Normalize that numeric-range failure to the public
        # fail-closed ValueError contract instead of leaking Decimal internals.
        raise ValueError("calculated lot size exceeds the supported numeric range.") from error

    lot_size = float(lot_size_decimal)
    if lot_size <= 0:
        raise ValueError("calculated lot size is below the supported precision.")

    position_size = lot_size * contract_size
    if not math.isfinite(position_size):
        raise ValueError("executable position size must be finite.")

    return PositionSizingResult(
        position_size=round(position_size, 4),
        lot_size=round(lot_size, 3),
        risk_amount_account=round(risk_amount_account, 2),
        risk_per_unit_account=round(risk_per_unit_account, 8),
    )
