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
    )
    assert result["allowed"] is True
    assert result["after"].concentration == 0.5
