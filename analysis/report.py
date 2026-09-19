from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any



# ==================================================
# Analysis Report
# ==================================================

@dataclass(
    frozen=True
)
class AnalysisReport:
    """
    Final user-facing analysis report.

    Complete output model for:

    - Trading Bot
    - Telegram API
    - Web Dashboard
    - AI Explanation Layer
    """



    # ==================================================
    # Market Context
    # ==================================================

    symbol: str = "UNKNOWN"


    timeframe: str = "UNKNOWN"



    # ==================================================
    # Core Result
    # ==================================================

    trend: str = "neutral"


    structure: str = "unknown"


    score: float = 0.0


    signal: str = "NEUTRAL"


    confidence: float = 0.0



    # ==================================================
    # Confidence Layer
    # ==================================================

    agreement: float = 0.0


    bullish_votes: int = 0


    bearish_votes: int = 0


    neutral_votes: int = 0


    warnings: list[str] = field(

        default_factory=list

    )


    confidence_grade: str = "UNKNOWN"




    # ==================================================
    # Decision Layer
    # ==================================================

    decision_bias: str = "neutral"

    market_regime: str = "UNCERTAIN"
    scenario: str = "NO_TRADE"
    statistical_context: dict[str, Any] = field(default_factory=dict)
    conflict_state: str = "INSUFFICIENT_EVIDENCE"
    signal_decay: str = "INVALID"
    crisis_mode: str = "NORMAL"
    macro_risk_level: str = "NORMAL"
    macro_events: list[dict[str, Any]] = field(default_factory=list)
    portfolio_risk_blocked: bool = False
    portfolio_risk_flags: list[str] = field(default_factory=list)


    risk_level: str = "normal"




    # ==================================================
    # Professional Risk Management
    # ==================================================

    entry_price: float | None = None


    stop_loss: float | None = None


    take_profit: float | None = None


    take_profit_1: float | None = None


    take_profit_2: float | None = None


    take_profit_3: float | None = None


    risk_reward: float | None = None


    position_size: float | None = None


    lot_size: float | None = None


    risk_amount: float | None = None


    risk_percent: float | None = None


    trailing_stop: float | None = None


    market_condition: str = "UNKNOWN"



    # Trade Quality

    trade_quality: float | None = None


    trade_grade: str = "UNKNOWN"




    # ==================================================
    # Smart Money Concepts
    # ==================================================

    smc_bias: str = "neutral"


    smc_structure: str = "unknown"


    order_block: dict[str, Any] | None = None


    liquidity: dict[str, Any] | None = None


    fair_value_gap: dict[str, Any] | None = None


    premium_discount: str = "unknown"




    # ==================================================
    # Explanation Layer
    # ==================================================

    reasons: list[str] = field(

        default_factory=list

    )


    analysis_text: str = ""




    # ==================================================
    # Indicators Snapshot
    # ==================================================

    indicators: dict[str, Any] = field(

        default_factory=dict

    )


    
    # ==================================================
    # Confidence Helpers
    # ==================================================

    def confidence_percentage(
        self,
    ) -> str:
        """
        Returns confidence as percentage.
        """


        value = int(

            self.confidence * 100

        )


        return f"{value}%"




    def confidence_label(
        self,
    ) -> str:
        """
        Converts confidence value
        into readable grade.
        """


        if self.confidence >= 0.85:

            return "VERY_HIGH"



        elif self.confidence >= 0.70:

            return "HIGH"



        elif self.confidence >= 0.50:

            return "MEDIUM"



        elif self.confidence >= 0.30:

            return "LOW"



        return "VERY_LOW"




    # ==================================================
    # Voting Summary
    # ==================================================

    def vote_summary(
        self,
    ) -> dict[str, int]:
        """
        Returns engine votes.
        """


        return {

            "bullish": self.bullish_votes,

            "bearish": self.bearish_votes,

            "neutral": self.neutral_votes,

        }




    # ==================================================
    # Signal Quality
    # ==================================================

    def is_strong_signal(
        self,
    ) -> bool:
        """
        Checks signal confirmation.
        """


        return (

            self.confidence >= 0.75

            and

            self.agreement >= 0.70

        )




    def is_high_quality_trade(
        self,
    ) -> bool:
        """
        Checks if trade quality is acceptable.

        Used by:

        - Trade Manager
        - Auto Execution
        - Filtering Layer
        """


        return (

            self.trade_quality is not None

            and

            self.trade_quality >= 80

            and

            self.trade_grade in (

                "A",

                "A+",

            )

        )




    # ==================================================
    # Risk Summary
    # ==================================================

    def risk_summary(
        self,
    ) -> dict[str, Any]:
        """
        Returns professional risk information.
        """


        return {

            "entry": self.entry_price,


            "stop_loss": self.stop_loss,


            "take_profit": self.take_profit,


            "take_profit_1": self.take_profit_1,


            "take_profit_2": self.take_profit_2,


            "take_profit_3": self.take_profit_3,


            "risk_reward": self.risk_reward,


            "position_size": self.position_size,


            "lot_size": self.lot_size,


            "risk_amount": self.risk_amount,


            "risk_percent": self.risk_percent,


            "trailing_stop": self.trailing_stop,


            "market_condition": self.market_condition,


            "trade_quality": self.trade_quality,


            "trade_grade": self.trade_grade,

        }




    # ==================================================
    # Alert Context
    # ==================================================

    def alert_context(self) -> dict[str, Any]:
        """Return a deterministic, transport-neutral alert contract."""
        signal = str(self.signal).upper()
        confidence = max(0.0, min(1.0, float(self.confidence)))
        executable = signal in {"BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}
        risk = str(self.macro_risk_level).upper()
        eligible = executable and (confidence >= 0.60 or risk in {"CRISIS", "EXTREME"})
        severity = "CRITICAL" if risk in {"CRISIS", "EXTREME"} else (
            "HIGH" if signal in {"STRONG_BUY", "STRONG_SELL"} and confidence >= 0.75
            else "MEDIUM" if eligible else "INFO"
        )
        return {
            "eligible": eligible,
            "symbol": self.symbol,
            "signal": signal,
            "confidence": confidence,
            "severity": severity,
            "risk_level": risk,
            "dedupe_key": f"{self.symbol}:{signal}:{severity}",
        }


    # ==================================================
    # Compact Output
    # ==================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Compact output for:

        - Telegram
        - API
        - AI layer
        - Dashboard
        """


        return {


            "symbol": self.symbol,


            "timeframe": self.timeframe,


            "trend": self.trend,


            "structure": self.structure,


            "signal": self.signal,


            "score": self.score,


            "confidence": self.confidence_percentage(),


            "confidence_grade": self.confidence_label(),


            "agreement": self.agreement,


            "votes": self.vote_summary(),


            "risk_level": self.risk_level,


            "decision_bias": self.decision_bias,
            "market_regime": self.market_regime,
            "scenario": self.scenario,
            "statistical_context": self.statistical_context,
            "conflict_state": self.conflict_state,
            "signal_decay": self.signal_decay,
            "crisis_mode": self.crisis_mode,
            "macro_risk_level": self.macro_risk_level,
            "macro_events": self.macro_events,
            "portfolio_risk_blocked": self.portfolio_risk_blocked,
            "portfolio_risk_flags": self.portfolio_risk_flags,


            "risk_management": self.risk_summary(),


            "smc": {

                "bias": self.smc_bias,

                "structure": self.smc_structure,

                "order_block": self.order_block,

                "liquidity": self.liquidity,

                "fair_value_gap": self.fair_value_gap,

                "premium_discount": self.premium_discount,

            },


            "trade": {

                "quality": self.trade_quality,

                "grade": self.trade_grade,

                "is_high_quality": (

                    self.is_high_quality_trade()

                ),

            },


            "reasons": self.reasons,


            "analysis_text": self.analysis_text,

        }
