import math

import pytest

from analysis.position_sizing import calculate_position_size


def test_usd_quote_uses_identity_conversion():
    result = calculate_position_size(
        account_balance=1000,
        risk_percent=1,
        risk_distance_quote=0.002,
        contract_size=100000,
        account_currency="USD",
        quote_currency="USD",
    )

    assert result.risk_amount_account == 10.0
    assert result.risk_per_unit_account == 0.002
    assert result.position_size == 5000.0
    assert result.lot_size == 0.05


def test_non_usd_quote_requires_explicit_conversion_rate():
    with pytest.raises(ValueError, match="quote_to_account_rate"):
        calculate_position_size(
            account_balance=1000,
            risk_percent=1,
            risk_distance_quote=0.20,
            contract_size=100000,
            account_currency="USD",
            quote_currency="JPY",
        )


def test_non_usd_quote_applies_explicit_conversion_rate():
    result = calculate_position_size(
        account_balance=1000,
        risk_percent=1,
        risk_distance_quote=0.20,
        contract_size=100000,
        account_currency="USD",
        quote_currency="JPY",
        quote_to_account_rate=0.0065,
    )

    assert result.risk_amount_account == 10.0
    assert result.risk_per_unit_account == 0.0013
    assert result.position_size == pytest.approx(7600.0)
    assert result.lot_size == pytest.approx(0.076)
    assert result.position_size == pytest.approx(result.lot_size * 100000)


def test_lot_precision_floors_instead_of_rounding_up_into_higher_risk():
    result = calculate_position_size(
        account_balance=1000,
        risk_percent=1,
        risk_distance_quote=0.20,
        contract_size=100000,
        account_currency="USD",
        quote_currency="JPY",
        quote_to_account_rate=0.00649,
    )

    raw_position_size = 10.0 / (0.20 * 0.00649)
    raw_lot_size = raw_position_size / 100000
    assert result.lot_size == pytest.approx(0.077)
    assert result.position_size == pytest.approx(7700.0)
    assert result.lot_size <= raw_lot_size
    assert result.position_size == pytest.approx(result.lot_size * 100000)

    executable_risk = result.position_size * 0.20 * 0.00649
    assert executable_risk <= result.risk_amount_account


def test_lot_below_supported_precision_fails_closed():
    with pytest.raises(ValueError, match="below the supported precision"):
        calculate_position_size(
            account_balance=100,
            risk_percent=0.1,
            risk_distance_quote=10,
            contract_size=100000,
            account_currency="USD",
            quote_currency="USD",
        )


def test_conversion_rate_must_be_positive():
    for rate in (0, -1):
        with pytest.raises(ValueError, match="quote_to_account_rate"):
            calculate_position_size(
                account_balance=1000,
                risk_percent=1,
                risk_distance_quote=0.20,
                contract_size=100000,
                account_currency="USD",
                quote_currency="JPY",
                quote_to_account_rate=rate,
            )


def test_position_sizing_rejects_non_finite_numeric_inputs():
    base = {
        "account_balance": 1000,
        "risk_percent": 1,
        "risk_distance_quote": 0.20,
        "contract_size": 100000,
        "account_currency": "USD",
        "quote_currency": "JPY",
        "quote_to_account_rate": 0.0065,
    }
    for field in (
        "account_balance",
        "risk_percent",
        "risk_distance_quote",
        "contract_size",
        "quote_to_account_rate",
    ):
        for value in (math.nan, math.inf, -math.inf):
            kwargs = {**base, field: value}
            with pytest.raises(ValueError, match="finite"):
                calculate_position_size(**kwargs)


def test_position_sizing_rejects_non_string_currency_context():
    with pytest.raises(TypeError, match="must be strings"):
        calculate_position_size(
            account_balance=1000,
            risk_percent=1,
            risk_distance_quote=0.20,
            contract_size=100000,
            account_currency=None,
            quote_currency="USD",
        )
