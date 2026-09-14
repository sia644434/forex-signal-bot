from __future__ import annotations

from dataclasses import dataclass
import math

from analysis.currency import get_forex_currency_pair
from analysis.position_sizing import calculate_position_size


@dataclass(frozen=True)
class RiskResult:
    """Professional trade risk output."""

    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    take_profit_1: float | None
    take_profit_2: float | None
    take_profit_3: float | None
    risk_reward: float | None
    position_size: float | None
    lot_size: float | None
    risk_amount: float | None
    risk_percent: float | None
    trailing_stop: float | None
    trade_quality: float | None
    trade_grade: str
    risk_level: str
    market_condition: str
    reason: str


class RiskEngine:
    """Advanced professional risk management engine."""

    def __init__(self, risk_reward_target: float = 2.0, atr_multiplier: float = 1.5, account_balance: float = 1000.0, risk_percent: float = 1.0, contract_size: float = 100000, account_currency: str | None = None) -> None:
        self.risk_reward_target = self._coerce_finite(risk_reward_target, "risk_reward_target")
        self.atr_multiplier = self._coerce_finite(atr_multiplier, "atr_multiplier")
        self.account_balance = self._coerce_finite(account_balance, "account_balance")
        self.risk_percent = self._coerce_finite(risk_percent, "risk_percent")
        self.contract_size = self._coerce_finite(contract_size, "contract_size")
        if account_currency is not None and not isinstance(account_currency, str):
            raise TypeError("account_currency must be a string or None.")
        self.account_currency = account_currency.strip().upper() if account_currency is not None and account_currency.strip() else None
        if self.risk_reward_target <= 0:
            raise ValueError("risk_reward_target must be greater than zero.")
        if self.atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be greater than zero.")
        if self.account_balance <= 0:
            raise ValueError("account_balance must be greater than zero.")
        if self.risk_percent <= 0:
            raise ValueError("risk_percent must be greater than zero.")
        if self.contract_size <= 0:
            raise ValueError("contract_size must be greater than zero.")

    @staticmethod
    def _coerce_finite(value: float, name: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a finite number.") from error
        if not math.isfinite(numeric):
            raise ValueError(f"{name} must be finite.")
        return numeric

    @staticmethod
    def _directional_strength(score: float) -> float:
        numeric = RiskEngine._coerce_finite(score, "score")
        return abs((numeric - 50.0) * 2.0)

    def _dynamic_risk_percent(self, confidence: float, score: float) -> float:
        if confidence >= 0.85 and self._directional_strength(score) >= 80:
            return 2.0
        if confidence >= 0.70 and self._directional_strength(score) >= 60:
            return 1.5
        if confidence >= 0.50:
            return 1.0
        return 0.5

    @staticmethod
    def _calculate_risk_level(confidence: float, score: float) -> str:
        if confidence >= 0.80 and RiskEngine._directional_strength(score) >= 60:
            return "LOW"
        if confidence >= 0.50:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _market_condition(atr: float | None, price: float) -> str:
        if atr is None or price <= 0:
            return "UNKNOWN"
        atr_percent = (atr / price) * 100
        if atr_percent < 0.2:
            return "LOW_VOLATILITY"
        if atr_percent > 3:
            return "EXTREME_VOLATILITY"
        if atr_percent > 2:
            return "HIGH_VOLATILITY"
        return "NORMAL"

    def _calculate_risk_distance(self, price: float, atr: float | None = None, risk_distance: float | None = None) -> float:
        if risk_distance is not None:
            return risk_distance
        if atr is not None and atr > 0:
            return atr * self.atr_multiplier
        return price * 0.01

    def _calculate_position_size(self, risk_distance: float, dynamic_risk_percent: float, *, symbol: str | None, quote_to_account_rate: float | None) -> tuple[float | None, float | None, float | None, str | None]:
        if not self.account_currency:
            return None, None, None, "account currency is not configured"
        if not symbol:
            return None, None, None, "market symbol is required for position sizing"
        try:
            pair = get_forex_currency_pair(symbol)
            result = calculate_position_size(account_balance=self.account_balance, risk_percent=dynamic_risk_percent, risk_distance_quote=risk_distance, contract_size=self.contract_size, account_currency=self.account_currency, quote_currency=pair.quote_currency, quote_to_account_rate=quote_to_account_rate)
        except ValueError as error:
            return None, None, None, str(error)
        return result.position_size, result.lot_size, result.risk_amount_account, None

    @staticmethod
    def _trade_quality(confidence: float, score: float, market_condition: str) -> tuple[float, str]:
        quality = confidence * 50
        quality += min(RiskEngine._directional_strength(score), 50)
        if market_condition == "NORMAL":
            quality += 10
        elif market_condition == "HIGH_VOLATILITY":
            quality -= 10
        elif market_condition == "EXTREME_VOLATILITY":
            quality -= 20
        quality = max(0, min(quality, 100))
        if quality >= 90:
            grade = "A+"
        elif quality >= 75:
            grade = "A"
        elif quality >= 60:
            grade = "B"
        else:
            grade = "NO_TRADE"
        return round(quality, 2), grade

    def _build_sizing(self, risk_distance: float, risk_percent: float, *, symbol: str | None, quote_to_account_rate: float | None) -> tuple[float | None, float | None, float | None, str]:
        position_size, lot_size, risk_amount, sizing_error = self._calculate_position_size(risk_distance, risk_percent, symbol=symbol, quote_to_account_rate=quote_to_account_rate)
        if sizing_error:
            return position_size, lot_size, risk_amount, f"Position sizing unavailable: {sizing_error}"
        return position_size, lot_size, risk_amount, ""

    @staticmethod
    def _validate_setup_levels(entry_price: float, stop_loss: float, tp1: float, tp2: float, tp3: float, risk_reward: float, *, signal: str) -> None:
        levels = (entry_price, stop_loss, tp1, tp2, tp3, risk_reward)
        if any(not math.isfinite(value) for value in levels):
            raise ValueError("risk plan output must be finite")
        if any(value <= 0 for value in levels):
            raise ValueError("risk plan levels must be greater than zero")
        if signal == "BUY":
            valid_order = stop_loss < entry_price < tp1 < tp2 < tp3
        else:
            valid_order = tp3 < tp2 < tp1 < entry_price < stop_loss
        if not valid_order:
            raise ValueError("risk plan levels have invalid directional ordering")

    def _buy_setup(self, price: float, risk_distance: float, risk_level: str, market_condition: str, confidence: float, score: float, risk_percent: float, *, symbol: str | None, quote_to_account_rate: float | None) -> RiskResult:
        stop_loss = price - risk_distance
        tp1 = price + risk_distance
        tp2 = price + risk_distance * self.risk_reward_target
        tp3 = price + risk_distance * 3
        self._validate_setup_levels(price, stop_loss, tp1, tp2, tp3, self.risk_reward_target, signal="BUY")
        position_size, lot_size, risk_amount, sizing_reason = self._build_sizing(risk_distance, risk_percent, symbol=symbol, quote_to_account_rate=quote_to_account_rate)
        trade_quality, trade_grade = self._trade_quality(confidence, score, market_condition)
        reason = "Professional bullish risk plan generated"
        if sizing_reason:
            reason += f"; {sizing_reason}"
        return RiskResult(entry_price=round(price, 5), stop_loss=round(stop_loss, 5), take_profit=round(tp2, 5), take_profit_1=round(tp1, 5), take_profit_2=round(tp2, 5), take_profit_3=round(tp3, 5), risk_reward=self.risk_reward_target, position_size=position_size, lot_size=lot_size, risk_amount=risk_amount, risk_percent=risk_percent, trailing_stop=round(tp1, 5), trade_quality=trade_quality, trade_grade=trade_grade, risk_level=risk_level, market_condition=market_condition, reason=reason)

    def _sell_setup(self, price: float, risk_distance: float, risk_level: str, market_condition: str, confidence: float, score: float, risk_percent: float, *, symbol: str | None, quote_to_account_rate: float | None) -> RiskResult:
        stop_loss = price + risk_distance
        tp1 = price - risk_distance
        tp2 = price - risk_distance * self.risk_reward_target
        tp3 = price - risk_distance * 3
        self._validate_setup_levels(price, stop_loss, tp1, tp2, tp3, self.risk_reward_target, signal="SELL")
        position_size, lot_size, risk_amount, sizing_reason = self._build_sizing(risk_distance, risk_percent, symbol=symbol, quote_to_account_rate=quote_to_account_rate)
        trade_quality, trade_grade = self._trade_quality(confidence, score, market_condition)
        reason = "Professional bearish risk plan generated"
        if sizing_reason:
            reason += f"; {sizing_reason}"
        return RiskResult(entry_price=round(price, 5), stop_loss=round(stop_loss, 5), take_profit=round(tp2, 5), take_profit_1=round(tp1, 5), take_profit_2=round(tp2, 5), take_profit_3=round(tp3, 5), risk_reward=self.risk_reward_target, position_size=position_size, lot_size=lot_size, risk_amount=risk_amount, risk_percent=risk_percent, trailing_stop=round(tp1, 5), trade_quality=trade_quality, trade_grade=trade_grade, risk_level=risk_level, market_condition=market_condition, reason=reason)

    def calculate(self, signal: str, current_price: float, atr: float | None = None, confidence: float = 0.0, score: float = 0.0, risk_distance: float | None = None, *, symbol: str | None = None, quote_to_account_rate: float | None = None, risk_percent: float | None = None) -> RiskResult:
        """Calculate a risk plan with unit-aware position sizing."""
        if not isinstance(signal, str):
            raise ValueError("signal must be a string.")
        current_price = self._coerce_finite(current_price, "current_price")
        confidence = self._coerce_finite(confidence, "confidence")
        score = self._coerce_finite(score, "score")
        if atr is not None:
            atr = self._coerce_finite(atr, "atr")
            if atr < 0:
                raise ValueError("atr must be greater than or equal to zero.")
        if risk_distance is not None:
            risk_distance = self._coerce_finite(risk_distance, "risk distance")
        if risk_percent is not None:
            risk_percent = self._coerce_finite(risk_percent, "risk_percent")
            if risk_percent <= 0:
                raise ValueError("risk_percent must be greater than zero.")
        if current_price <= 0:
            raise ValueError("current_price must be greater than zero.")
        if risk_distance is not None and risk_distance <= 0:
            raise ValueError("risk distance must be greater than zero.")
        distance = self._coerce_finite(self._calculate_risk_distance(price=current_price, atr=atr, risk_distance=risk_distance), "risk distance")
        if distance <= 0:
            raise ValueError("risk distance must be greater than zero.")
        signal = signal.upper()
        risk_level = self._calculate_risk_level(confidence, score)
        market_condition = self._market_condition(atr, current_price)
        effective_risk_percent = risk_percent if risk_percent is not None else self._dynamic_risk_percent(confidence, score)
        if signal == "BUY":
            return self._buy_setup(price=current_price, risk_distance=distance, risk_level=risk_level, market_condition=market_condition, confidence=confidence, score=score, risk_percent=effective_risk_percent, symbol=symbol, quote_to_account_rate=quote_to_account_rate)
        if signal == "SELL":
            return self._sell_setup(price=current_price, risk_distance=distance, risk_level=risk_level, market_condition=market_condition, confidence=confidence, score=score, risk_percent=effective_risk_percent, symbol=symbol, quote_to_account_rate=quote_to_account_rate)
        trade_quality, trade_grade = self._trade_quality(confidence, score, market_condition)
        return RiskResult(entry_price=None, stop_loss=None, take_profit=None, take_profit_1=None, take_profit_2=None, take_profit_3=None, risk_reward=None, position_size=None, lot_size=None, risk_amount=None, risk_percent=effective_risk_percent, trailing_stop=None, trade_quality=trade_quality, trade_grade=trade_grade, risk_level="NONE", market_condition=market_condition, reason="No valid trade setup available")
