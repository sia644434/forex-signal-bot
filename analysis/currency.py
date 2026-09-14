"""Instrument currency metadata helpers for multi-asset risk calculations.

These helpers identify an instrument's quote currency without performing
account-currency conversion. Conversion remains the responsibility of the
market-data conversion service.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.symbols import (
    COMMODITY_SYMBOLS,
    CRYPTO_SYMBOLS,
    FOREX_SYMBOLS,
    INDEX_SYMBOLS,
    STOCK_SYMBOLS,
    normalize_symbol,
)


@dataclass(frozen=True, slots=True)
class ForexCurrencyPair:
    """Base and quote currencies for a supported forex instrument."""

    symbol: str
    base_currency: str
    quote_currency: str


def get_forex_currency_pair(symbol: str) -> ForexCurrencyPair:
    """Return explicit base/quote currency metadata for a forex symbol."""
    normalized = normalize_symbol(symbol)
    if normalized not in FOREX_SYMBOLS or len(normalized) != 6:
        raise ValueError(f"Unsupported forex symbol for currency metadata: {symbol}")
    return ForexCurrencyPair(
        symbol=normalized,
        base_currency=normalized[:3],
        quote_currency=normalized[3:],
    )


def get_quote_currency(symbol: str) -> str:
    """Return the quote currency for every currently supported asset class.

    Forex pairs derive the quote from the six-character pair. Supported crypto
    instruments currently quote in USDT. The repository's stock, index, and
    commodity universe is USD-denominated. Unknown symbols fail closed rather
    than guessing from arbitrary symbol length.
    """
    normalized = normalize_symbol(symbol)

    if normalized in FOREX_SYMBOLS and len(normalized) == 6:
        return normalized[3:]

    if normalized in CRYPTO_SYMBOLS and normalized.endswith("USDT"):
        return "USDT"

    if normalized in STOCK_SYMBOLS or normalized in INDEX_SYMBOLS or normalized in COMMODITY_SYMBOLS:
        return "USD"

    raise ValueError(f"Unsupported symbol for quote-currency metadata: {symbol}")


def get_contract_size(symbol: str) -> float:
    """Return the default unit/contract size for the supported asset class.

    Forex keeps the existing 100,000 base-unit convention. Spot-like crypto,
    stocks, indices, and commodities use one underlying unit by default. A
    broker/provider-specific contract specification can override this later;
    this helper only prevents the Forex default from leaking into other assets.
    """
    normalized = normalize_symbol(symbol)
    if normalized in FOREX_SYMBOLS:
        return 100000.0
    if normalized in CRYPTO_SYMBOLS or normalized in STOCK_SYMBOLS or normalized in INDEX_SYMBOLS or normalized in COMMODITY_SYMBOLS:
        return 1.0
    raise ValueError(f"Unsupported symbol for contract-size metadata: {symbol}")


__all__ = ["ForexCurrencyPair", "get_forex_currency_pair", "get_quote_currency", "get_contract_size"]
