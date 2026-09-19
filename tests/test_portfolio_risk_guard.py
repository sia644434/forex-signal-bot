from analysis.portfolio_risk_guard import PortfolioExposure, PortfolioRiskGuard


def test_portfolio_guard_blocks_concentration():
    guard = PortfolioRiskGuard()
    exposures = [PortfolioExposure("EURUSD", "FOREX", "BUY", 70, 0.7)]
    candidate = PortfolioExposure("EURUSD", "FOREX", "BUY", 40, 0.4)
    result = guard.can_add(exposures, candidate)
    assert result["blocked"] is True
    assert "SYMBOL_CONCENTRATION" in result["after"].risk_flags


def test_portfolio_guard_allows_diversified_exposure():
    guard = PortfolioRiskGuard()
    result = guard.can_add(
        [PortfolioExposure("EURUSD", "FOREX", "BUY", 20, 0.2)],
        PortfolioExposure("XAUUSD", "COMMODITY", "SELL", 20, 0.2),
        max_symbol_weight=0.60,
    )
    assert result["allowed"] is True
    assert result["after"].concentration == 0.5


def test_portfolio_guard_uses_equity_for_gross_exposure():
    guard = PortfolioRiskGuard()
    snapshot = guard.assess(
        [PortfolioExposure("EURUSD", "FOREX", "BUY", 80, 0.8)],
        equity=100,
        max_gross_exposure=0.75,
    )
    assert "GROSS_EXPOSURE" in snapshot.risk_flags
    assert snapshot.net_exposure == 80
