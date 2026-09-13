"""Currency metadata helpers for forex risk calculations.

This module intentionally provides only instrument-level currency metadata.
It does not assume an account currency and does not perform FX conversion.
Those concerns belong to the account/risk configuration layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.symbols import FOREX_SYMBOLS, normalize_symbol


@dataclass(frozen=True, slots=True)
class ForexCurrencyPair:
    """Base and quote currencies for a supported forex instrument."""

    symbol: str
    base_currency: str
    quote_currency: str


def get_forex_currency_pair(symbol: str) -> ForexCurrencyPair:
    """Return explicit base/quote currency metadata for a forex symbol.

    The symbol must be one of the repository's supported forex instruments.
    No account-currency or conversion-rate assumption is made here.
    """
    normalized = normalize_symbol(symbol)

    if normalized not in FOREX_SYMBOLS or len(normalized) != 6:
        raise ValueError(
            f"Unsupported forex symbol for currency metadata: {symbol}"
        )

    return ForexCurrencyPair(
        symbol=normalized,
        base_currency=normalized[:3],
        quote_currency=normalized[3:],
    )
