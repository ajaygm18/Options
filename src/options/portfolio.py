from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_price: float = 0.0

    def apply_fill(self, quantity: int, price: float) -> None:
        if self.quantity + quantity == 0:
            self.quantity = 0
            self.avg_price = 0.0
            return
        new_total = self.quantity + quantity
        weighted_cost = (self.avg_price * self.quantity) + (price * quantity)
        self.quantity = new_total
        self.avg_price = weighted_cost / new_total


@dataclass
class Portfolio:
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl: float = 0.0

    def apply_fill(self, symbol: str, side: str, quantity: int, price: float) -> None:
        signed_qty = quantity if side.lower() == "buy" else -quantity
        position = self.positions.get(symbol, Position(symbol=symbol))
        prev_qty = position.quantity
        position.apply_fill(signed_qty, price)
        self.positions[symbol] = position

        cash_delta = -signed_qty * price
        self.cash += cash_delta

        if prev_qty != 0 and (prev_qty > 0) != (position.quantity > 0):
            # Close or flip: realize PnL for closed portion.
            closed_qty = -prev_qty if abs(prev_qty) < abs(signed_qty) else signed_qty
            self.realized_pnl += closed_qty * (position.avg_price - price)

    def exposure(self) -> float:
        return sum(pos.quantity * pos.avg_price for pos in self.positions.values())
