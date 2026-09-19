from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from uuid import uuid4

from services.paper_store import PaperTradingStore
from services.shadow_store import ShadowComparisonStore


@dataclass(frozen=True, slots=True)
class PaperPosition:
    position_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    opened_at: str


@dataclass(frozen=True, slots=True)
class ClosedPaperTrade:
    position_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    closed_at: str


class PaperTradingEngine:
    """Deterministic paper-trading ledger isolated from live execution."""

    def __init__(self, store: PaperTradingStore | None = None) -> None:
        self._store = store
        self._open: dict[str, PaperPosition] = {}
        self._closed: list[ClosedPaperTrade] = []
        if store is not None:
            snapshot = store.load()
            self._open = {item["position_id"]: PaperPosition(**item) for item in snapshot.get("open", [])}
            self._closed = [ClosedPaperTrade(**item) for item in snapshot.get("closed", [])]

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save(self.snapshot())

    @staticmethod
    def _positive(value: object, name: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be finite and positive") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"{name} must be finite and positive")
        return number

    def open(self, symbol: str, side: str, quantity: float, entry_price: float, opened_at: str, *, position_id: str | None = None) -> PaperPosition:
        normalized_side = str(side).upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("paper side must be BUY or SELL")
        if not str(symbol).strip():
            raise ValueError("paper symbol is required")
        position = PaperPosition(
            position_id=position_id or uuid4().hex,
            symbol=str(symbol).strip().upper(),
            side=normalized_side,
            quantity=self._positive(quantity, "quantity"),
            entry_price=self._positive(entry_price, "entry_price"),
            opened_at=str(opened_at),
        )
        if position.position_id in self._open:
            raise ValueError("position_id already exists")
        self._open[position.position_id] = position
        self._persist()
        return position

    def close(self, position_id: str, exit_price: float, closed_at: str) -> ClosedPaperTrade:
        position = self._open.pop(position_id, None)
        if position is None:
            raise KeyError("paper position not found")
        exit_value = self._positive(exit_price, "exit_price")
        direction = 1.0 if position.side == "BUY" else -1.0
        pnl = (exit_value - position.entry_price) * position.quantity * direction
        if not math.isfinite(pnl):
            raise ValueError("paper PnL is not finite")
        trade = ClosedPaperTrade(
            position.position_id, position.symbol, position.side, position.quantity,
            position.entry_price, exit_value, pnl, str(closed_at),
        )
        self._closed.append(trade)
        self._persist()
        return trade

    def mark_to_market(self, prices: dict[str, float]) -> float:
        """Return unrealized PnL for currently open positions using supplied prices."""
        total = 0.0
        for position in self._open.values():
            try:
                price = float(prices[position.symbol])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"missing or invalid mark price for {position.symbol}") from exc
            if not math.isfinite(price) or price <= 0:
                raise ValueError(f"mark price for {position.symbol} must be finite and positive")
            direction = 1.0 if position.side == "BUY" else -1.0
            total += (price - position.entry_price) * position.quantity * direction
        return total

    def equity_snapshot(self, prices: dict[str, float]) -> dict[str, float]:
        realized = float(sum(trade.pnl for trade in self._closed))
        unrealized = float(self.mark_to_market(prices))
        equity = realized + unrealized
        return {
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "equity_pnl": equity,
        }

    def snapshot(self, prices: dict[str, float] | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "open": [asdict(position) for position in self._open.values()],
            "closed": [asdict(trade) for trade in self._closed],
            "realized_pnl": sum(trade.pnl for trade in self._closed),
        }
        if prices is not None:
            payload["equity"] = self.equity_snapshot(prices)
        return payload


@dataclass(frozen=True, slots=True)
class ShadowComparison:
    paper_decision: str
    reference_decision: str
    agreement: bool


def compare_shadow_decision(paper_decision: str, reference_decision: str) -> ShadowComparison:
    paper = str(paper_decision).upper()
    reference = str(reference_decision).upper()
    return ShadowComparison(paper, reference, paper == reference)


@dataclass(frozen=True, slots=True)
class ShadowObservation:
    timestamp: str
    paper_decision: str
    reference_decision: str
    agreement: bool


class ShadowComparisonLedger:
    """Deterministic paper/reference comparison ledger with optional durable storage."""

    def __init__(self, store: ShadowComparisonStore | None = None) -> None:
        self._store = store
        self._observations: list[ShadowObservation] = []
        if store is not None:
            self._observations = self._deserialize(store.load_all())

    @staticmethod
    def _deserialize(items: list[dict]) -> list[ShadowObservation]:
        observations: list[ShadowObservation] = []
        for item in items:
            try:
                observation = ShadowObservation(
                    timestamp=str(item["timestamp"]),
                    paper_decision=str(item["paper_decision"]).upper(),
                    reference_decision=str(item["reference_decision"]).upper(),
                    agreement=bool(item["agreement"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("invalid persisted shadow comparison observation") from error
            observations.append(observation)
        return observations

    def _persist(self) -> None:
        if self._store is not None:
            self._store.save_all([asdict(item) for item in self._observations])

    def record(self, paper_decision: str, reference_decision: str, timestamp: str) -> ShadowObservation:
        comparison = compare_shadow_decision(paper_decision, reference_decision)
        observation = ShadowObservation(
            timestamp=str(timestamp),
            paper_decision=comparison.paper_decision,
            reference_decision=comparison.reference_decision,
            agreement=comparison.agreement,
        )
        self._observations.append(observation)
        self._persist()
        return observation

    def summary(self) -> dict[str, object]:
        total = len(self._observations)
        agreements = sum(1 for item in self._observations if item.agreement)
        return {
            "total": total,
            "agreements": agreements,
            "disagreements": total - agreements,
            "agreement_rate": agreements / total if total else 0.0,
            "observations": [asdict(item) for item in self._observations],
        }

    def clear(self) -> None:
        self._observations.clear()
        self._persist()


__all__ = [
    "PaperPosition",
    "ClosedPaperTrade",
    "PaperTradingEngine",
    "ShadowComparison",
    "compare_shadow_decision",
    "ShadowObservation",
    "ShadowComparisonLedger",
]
