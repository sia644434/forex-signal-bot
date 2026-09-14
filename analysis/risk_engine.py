from __future__ import annotations

from dataclasses import dataclass
import math

from analysis.currency import get_contract_size, get_quote_currency
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
    def __init__(self, risk_reward_target: float = 2.0, atr_multiplier: float = 1.5, account_balance: float = 1000.0, risk_percent: float = 1.0, contract_size: float | None = None, account_currency: str | None = None) -> None:
        self.risk_reward_target = self._coerce_finite(risk_reward_target, "risk_reward_target")
        self.atr_multiplier = self._coerce_finite(atr_multiplier, "atr_multiplier")
        self.account_balance = self._coerce_finite(account_balance, "account_balance")
        self.risk_percent = self._coerce_finite(risk_percent, "risk_percent")
        if contract_size is not None:
            contract_size = self._coerce_finite(contract_size, "contract_size")
        self.contract_size = contract_size
        if account_currency is not None and not isinstance(account_currency, str):
            raise TypeError("account_currency must be a string or None.")
        self.account_currency = account_currency.strip().upper() if account_currency is not None and account_currency.strip() else None
        if self.account_currency is not None and not ((len(self.account_currency) == 3 and self.account_currency.isalpha()) or self.account_currency in {"USDT", "USDC"}):
            raise ValueError("account_currency must be a supported 3-letter ISO currency code (or USDT/USDC).")
        if self.risk_reward_target <= 0:
            raise ValueError("risk_reward_target must be greater than zero.")
        if self.atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be greater than zero.")
        if self.account_balance <= 0:
            raise ValueError("account_balance must be greater than zero.")
        if self.risk_percent <= 0 or self.risk_percent > 100:
            raise ValueError("risk_percent must be greater than zero and at most 100.")
        if self.contract_size is not None and self.contract_size <= 0:
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
        return abs((RiskEngine._coerce_finite(score, "score") - 50.0) * 2.0)

    def _dynamic_risk_percent(self, confidence: float, score: float) -> float:
        strength = self._directional_strength(score)
        if confidence >= 0.85 and strength >= 80:
            return 2.0
        if confidence >= 0.70 and strength >= 60:
            return 1.5
        if confidence >= 0.50:
            return 1.0
        return 0.5
