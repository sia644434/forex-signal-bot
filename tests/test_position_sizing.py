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
    assert result.position_size == pytest.approx(7692.3077)
    assert result.lot_size == pytest.approx(0.077)


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
