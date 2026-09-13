from analysis.risk_engine import RiskEngine


def test_risk_engine_uses_explicit_currency_context_for_eurusd() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")

    result = engine.calculate(
        signal="BUY",
        current_price=1.1000,
        atr=0.0100,
        confidence=0.90,
        score=90,
        symbol="EURUSD",
    )

    assert result.position_size == 1333.3333
    assert result.lot_size == 0.0133333
    assert result.risk_amount == 20.0
    assert "Position sizing unavailable" not in result.reason


def test_risk_engine_never_falls_back_to_unitless_sizing() -> None:
    engine = RiskEngine(account_balance=1000, account_currency=None)

    result = engine.calculate(
        signal="BUY",
        current_price=1.1000,
        atr=0.0100,
        confidence=0.90,
        score=90,
        symbol="EURUSD",
    )

    assert result.position_size is None
    assert result.lot_size is None
    assert result.risk_amount is None
    assert "account currency is not configured" in result.reason


def test_risk_engine_requires_conversion_for_non_matching_quote_currency() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")

    result = engine.calculate(
        signal="SELL",
        current_price=150.0,
        atr=1.0,
        confidence=0.90,
        score=10,
        symbol="USDJPY",
    )

    assert result.position_size is None
    assert result.lot_size is None
    assert result.risk_amount is None
    assert "quote_to_account_rate is required" in result.reason


def test_risk_engine_applies_explicit_jpy_to_usd_conversion() -> None:
    engine = RiskEngine(account_balance=1000, account_currency="USD")

    result = engine.calculate(
        signal="SELL",
        current_price=150.0,
        atr=1.0,
        confidence=0.90,
        score=10,
        symbol="USDJPY",
        quote_to_account_rate=0.0066666667,
    )

    assert result.position_size == 1333.3333
    assert result.lot_size == 0.0133333
    assert result.risk_amount == 20.0
    assert "Position sizing unavailable" not in result.reason
