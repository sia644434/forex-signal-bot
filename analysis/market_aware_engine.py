from __future__ import annotations

from dataclasses import replace

from analysis.atr_engine import ATREngine
from analysis.currency import get_forex_currency_pair
from analysis.full_engine import FullAnalysisEngine
from analysis.risk_engine import RiskEngine
from config.settings import Settings
from services.market_data.currency_conversion import CurrencyConversionService
from services.market_data.service import MarketDataService


class MarketAwareAnalysisEngine:
    """Bind completed analysis to its real market and currency context."""

    def __init__(self, *, market_data: MarketDataService, settings: Settings | None = None) -> None:
        self.market_data = market_data
        self.settings = settings or Settings.load()
        self.analysis_engine = FullAnalysisEngine()
        self.conversion_service = CurrencyConversionService(market_data)

    async def analyze(self, candles, *, symbol: str, timeframe: str):
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string.")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string.")
        if not symbol.strip():
            raise ValueError("symbol is required for market-aware analysis")
        if not timeframe.strip():
            raise ValueError("timeframe is required for market-aware analysis")
        if candles is None:
            raise ValueError("candles are required for market-aware analysis")
        try:
            candle_count = len(candles)
        except TypeError as error:
            raise TypeError("candles must be a sized candle collection.") from error
        if candle_count == 0:
            raise ValueError("candles are required for market-aware analysis")

        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()
        pair = get_forex_currency_pair(normalized_symbol)

        report = self.analysis_engine.analyze(candles)
        report = replace(report, symbol=normalized_symbol, timeframe=normalized_timeframe)

        if not self.settings.account_currency:
            return report

        signal = str(report.signal).upper()
        if signal not in {"BUY", "SELL"}:
            return report

        conversion = await self.conversion_service.get_conversion(
            source_currency=pair.quote_currency,
            target_currency=self.settings.account_currency,
        )

        atr_result = ATREngine().calculate(candles)
        atr_value = atr_result.atr if atr_result.atr is not None else 0.0

        self.analysis_engine.risk_engine = RiskEngine(account_currency=self.settings.account_currency)
        risk_result = self.analysis_engine.risk_engine.calculate(
            signal=signal,
            current_price=float(candles[-1].close),
            atr=atr_value,
            confidence=report.confidence,
            score=report.score,
            symbol=normalized_symbol,
            quote_to_account_rate=conversion.rate,
        )

        return replace(
            report,
            risk_level=risk_result.risk_level,
            entry_price=risk_result.entry_price,
            stop_loss=risk_result.stop_loss,
            take_profit=risk_result.take_profit,
            take_profit_1=risk_result.take_profit_1,
            take_profit_2=risk_result.take_profit_2,
            take_profit_3=risk_result.take_profit_3,
            risk_reward=risk_result.risk_reward,
            position_size=risk_result.position_size,
            lot_size=risk_result.lot_size,
            risk_amount=risk_result.risk_amount,
            risk_percent=risk_result.risk_percent,
            trailing_stop=risk_result.trailing_stop,
            market_condition=risk_result.market_condition,
            trade_grade=risk_result.trade_grade,
            reasons=report.reasons + [
                f"Currency conversion: {conversion.source_currency}->{conversion.target_currency} "
                f"via {conversion.pair_symbol} at {conversion.rate}"
            ],
        )


__all__ = ["MarketAwareAnalysisEngine"]
