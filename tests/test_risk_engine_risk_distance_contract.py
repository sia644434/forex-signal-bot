import pytest

from analysis.risk_engine import RiskEngine


@pytest.mark.parametrize(
    ("signal", "price", "expected_stop", "expected_tp1", "expected_tp2"),
    [
        ("BUY", 1.1000, 1.0850, 1.1150, 1.1300),
        ("SELL", 1.1000, 1.1150, 1.0850, 1.0700),
    ],
)
def test_risk_distance_is_the_single_source_for_sl_tp_and_sizing(
    signal: str,
    price: float,
    expected_stop: float,
    expected_tp1: float,
    expected_tp2: float,
) -> None:
    engine = RiskEngine(
        account_balance=1000,
        account_currency="USD",
        risk_reward_target=2.0,
    )

    result = engine.calculate(
        signal=signal,
        current_price=price,
        risk_distance=0.015,
        confidence=0.90,
        score=100.0 if signal == "BUY" else 0.0,
        symbol="EURUSD",
    )

    assert result.entry_price == pytest.approx(price)
    assert result.stop_loss == pytest.approx(expected_stop)
    assert result.take_profit_1 == pytest.approx(expected_tp1)
    assert result.take_profit_2 == pytest.approx(expected_tp2)
    assert result.take_profit == pytest.approx(expected_tp2)
    assert result.risk_reward == 2.0

    assert result.position_size == pytest.approx(1300.0)
    assert result.lot_size == pytest.approx(0.013)
    assert result.position_size == pytest.approx(result.lot_size * 100000)
    assert result.risk_amount == pytest.approx(20.0)

    executable_risk = result.position_size * abs(result.entry_price - result.stop_loss)
    assert executable_risk <= result.risk_amount + 1e-9


def test_risk_reward_report_matches_actual_tp2_to_stop_distance() -> None:
    engine = RiskEngine(
        account_balance=1000,
        account_currency="USD",
        risk_reward_target=2.5,
    )

    result = engine.calculate(
        signal="BUY",
        current_price=1.1000,
        risk_distance=0.012,
        confidence=0.90,
        score=100.0,
        symbol="EURUSD",
    )

    stop_distance = abs(result.entry_price - result.stop_loss)
    reward_distance = abs(result.take_profit_2 - result.entry_price)

    assert stop_distance == pytest.approx(0.012, abs=1e-9)
    assert reward_distance == pytest.approx(stop_distance * result.risk_reward, abs=1e-9)


def test_atr_derived_risk_distance_is_used_consistently() -> None:
    engine = RiskEngine(
        account_balance=1000,
        account_currency="USD",
        atr_multiplier=1.5,
        risk_reward_target=2.0,
    )

    result = engine.calculate(
        signal="SELL",
        current_price=1.1000,
        atr=0.010,
        confidence=0.90,
        score=0.0,
        symbol="EURUSD",
    )

    expected_distance = 0.015
    assert abs(result.entry_price - result.stop_loss) == pytest.approx(expected_distance, abs=1e-9)
    assert abs(result.take_profit_2 - result.entry_price) == pytest.approx(
        expected_distance * 2.0,
        abs=1e-9,
    )
    assert result.position_size == pytest.approx(1300.0)
    assert result.risk_amount == pytest.approx(20.0)


@pytest.mark.parametrize("signal", ["BUY", "SELL"])
@pytest.mark.parametrize("symbol", ["USDJPY", "EURJPY"])
def test_jpy_quote_conversion_never_exceeds_account_risk(
    signal: str,
    symbol: str,
) -> None:
    engine = RiskEngine(
        account_balance=1000,
        account_currency="USD",
        risk_reward_target=2.0,
    )

    result = engine.calculate(
        signal=signal,
        current_price=150.0 if symbol == "USDJPY" else 160.0,
        risk_distance=1.5,
        confidence=0.90,
        score=100.0 if signal == "BUY" else 0.0,
        symbol=symbol,
        quote_to_account_rate=0.0065,
    )

    assert result.position_size is not None
    assert result.lot_size is not None
    assert result.risk_amount == pytest.approx(20.0)
    assert result.position_size == pytest.approx(result.lot_size * 100000)

    # risk_distance is denominated in JPY for these pairs, so convert the
    # executable quote-currency loss back into the USD account currency.
    executable_risk_usd = (
        result.position_size
        * abs(result.entry_price - result.stop_loss)
        * 0.0065
    )
    assert executable_risk_usd <= result.risk_amount + 1e-9
