"""Unit-aware position sizing for quote-currency risk.

This module deliberately does not assume an account currency or an FX rate.
A caller must provide an explicit quote-to-account conversion rate whenever
quote currency and account currency differ.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    """Calculate position size while making currency conversion explicit.

    ``risk_distance_quote`` is the price distance denominated in the
    instrument's quote currency per unit of the base asset.

    If quote and account currencies differ, ``quote_to_account_rate`` must
    convert one quote-currency unit into account-currency units. No implicit
    USD assumption or market-rate lookup is performed here.
    """
    account_currency = account_currency.strip().upper()
    quote_currency = quote_currency.strip().upper()

    if not account_currency:
        raise ValueError("account_currency must not be empty.")
    if not quote_currency:
        raise ValueError("quote_currency must not be empty.")
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
        conversion_rate = float(quote_to_account_rate)
        if conversion_rate <= 0:
            raise ValueError(
                "quote_to_account_rate must be greater than zero."
            )

    risk_amount_account = account_balance * (risk_percent / 100.0)
    risk_per_unit_account = risk_distance_quote * conversion_rate

    if risk_per_unit_account <= 0:
        raise ValueError("converted risk per unit must be greater than zero.")

    position_size = risk_amount_account / risk_per_unit_account
    lot_size = position_size / contract_size

    return PositionSizingResult(
        position_size=round(position_size, 4),
        lot_size=round(lot_size, 3),
        risk_amount_account=round(risk_amount_account, 2),
        risk_per_unit_account=round(risk_per_unit_account, 8),
    )
