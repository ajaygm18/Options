from __future__ import annotations

from dataclasses import dataclass

from .events import Event, EventType, Order
from .portfolio import Portfolio


@dataclass(frozen=True)
class RiskLimits:
    max_position_size: int
    max_notional: float
    max_daily_loss: float


@dataclass
class RiskDecision:
    approved: bool
    reason: str


class RiskEngine:
    def __init__(self, limits: RiskLimits, portfolio: Portfolio) -> None:
        self.limits = limits
        self.portfolio = portfolio
        self.daily_pnl = 0.0

    def evaluate_order(self, order: Order, est_price: float) -> RiskDecision:
        position = self.portfolio.positions.get(order.symbol)
        current_qty = position.quantity if position else 0
        projected_qty = current_qty + (order.quantity if order.side == "buy" else -order.quantity)
        if abs(projected_qty) > self.limits.max_position_size:
            return RiskDecision(False, "position_size_limit")

        projected_notional = abs(projected_qty * est_price)
        if projected_notional > self.limits.max_notional:
            return RiskDecision(False, "notional_limit")

        if self.daily_pnl <= -self.limits.max_daily_loss:
            return RiskDecision(False, "daily_loss_limit")

        return RiskDecision(True, "approved")

    def handle_fill(self, event: Event) -> None:
        fill = event.payload["fill"]
        self.daily_pnl = self.portfolio.realized_pnl

    def alert_event(self, reason: str) -> Event:
        return Event(event_type=EventType.RISK_ALERT, payload={"reason": reason})
