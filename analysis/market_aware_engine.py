from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
from dataclasses import replace

from analysis.atr_engine import ATREngine
from analysis.currency import get_contract_size, get_quote_currency
from analysis.full_engine import FullAnalysisEngine
from analysis.risk_engine import RiskEngine
from config.settings import Settings
from config.symbols import TIMEFRAME_MINUTES, normalize_symbol, normalize_timeframe
from data.freshness import FreshnessPolicy
from data.models import Candle
from services.market_data.currency_conversion import CurrencyConversionService
from services.market_data.service import MarketDataService


class MarketAwareAnalysisEngine:
    """Bind completed analysis to its real market and currency context."""

    def __init__(self, *, market_data: MarketDataService, settings: Settings | None = None) -> None:
        self.market_data = market_data
        self.settings = settings or Settings.load()
        self.analysis_engine = FullAnalysisEngine()
        self.conversion_service = CurrencyConversionService(market_data)

    @staticmethod
    def _current_price(candles) -> float:
        latest = candles[-1]
        value = latest.close if hasattr(latest, "close") else latest
        try:
            price = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError("latest candle price must be numeric and finite.") from error
        if not math.isfinite(price) or price <= 0:
            raise ValueError("latest candle price must be numeric and finite and greater than zero.")
        return price

    @staticmethod
    def _validate_market_context(candles, normalized_symbol: str) -> None:
        """Reject analysis/risk inputs whose candle identity differs from the requested market."""
        for index, candle in enumerate(candles):
            if not isinstance(candle, Candle):
                # Preserve the existing analysis-engine compatibility contract for
                # legacy candle-like test inputs that do not expose market metadata.
                continue
            try:
                candle_symbol = normalize_symbol(candle.symbol)
            except (TypeError, ValueError) as error:
                raise ValueError(f"Invalid candle symbol at index {index}.") from error
            if candle_symbol != normalized_symbol:
                raise ValueError(
                    f"Candle symbol mismatch at index {index}: "
                    f"expected {normalized_symbol}, got {candle_symbol}."
                )

    @staticmethod
    def _validate_market_freshness(candles, timeframe: str) -> None:
        """Enforce the canonical six-candle freshness boundary at the analysis/risk boundary."""
        try:
            normalized_timeframe = normalize_timeframe(timeframe)
            interval = timedelta(minutes=TIMEFRAME_MINUTES[normalized_timeframe])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Unsupported timeframe for market-aware analysis: {timeframe!r}") from error

        if not all(isinstance(candle, Candle) for candle in candles):
            return

        now = datetime.now(timezone.utc)
        report = FreshnessPolicy.assess(
            candles[-1].timestamp,
            now=now,
            timeframe=interval,
        )
        if not report.is_usable:
            raise ValueError(
                "Market data is not fresh enough for market-aware analysis: "
                f"status={report.status}, age={report.age}, timeframe={normalized_timeframe}"
            )

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

        normalized_symbol = normalize_symbol(symbol)
        normalized_timeframe = normalize_timeframe(timeframe)
        self._validate_market_context(candles, normalized_symbol)
        self._validate_market_freshness(candles, normalized_timeframe)
        quote_currency = get_quote_currency(normalized_symbol)
        contract_size = get_contract_size(normalized_symbol)

        report = self.analysis_engine.analyze(candles)
        report = replace(report, symbol=normalized_symbol, timeframe=normalized_timeframe)

        if not self.settings.account_currency:
            return report

        signal = str(report.signal).upper()
        if signal not in {"BUY", "SELL"}:
            return report

        try:
            conversion = await self.conversion_service.get_conversion(
                source_currency=quote_currency,
                target_currency=self.settings.account_currency,
            )
        except ValueError as error:
            raise ValueError("Unable to resolve fresh currency conversion") from error

        atr_result = ATREngine().calculate(candles)
        if atr_result.atr is None:
            raise ValueError("ATR is required for market-aware risk sizing.")
        atr_value = float(atr_result.atr)
        if not math.isfinite(atr_value) or atr_value <= 0:
            raise ValueError("ATR must be finite and greater than zero for market-aware risk sizing.")
        current_price = self._current_price(candles)

        configured_risk_percent = self.settings.risk_per_trade * 100.0
        # RiskEngine carries per-analysis market/account context. Keep it local
        # instead of mutating the shared FullAnalysisEngine instance; callers may
        # reuse one MarketAwareAnalysisEngine concurrently for different symbols.
        risk_engine = RiskEngine(
            account_balance=self.settings.account_balance,
            account_currency=self.settings.account_currency,
            contract_size=contract_size,
        )
        risk_result = risk_engine.calculate(
            signal=signal,
            current_price=current_price,
            atr=atr_value,
            confidence=report.confidence,
            score=report.score,
            symbol=normalized_symbol,
            quote_to_account_rate=conversion.rate,
            risk_percent=configured_risk_percent,
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
                f"Quote currency: {quote_currency}; conversion {conversion.source_currency}->{conversion.target_currency} "
                f"via {conversion.pair_symbol or 'identity'} at {conversion.rate}; contract size {contract_size}"
            ],
        )


__all__ = ["MarketAwareAnalysisEngine"]
