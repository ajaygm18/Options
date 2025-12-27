from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from .events import Event, EventType, Fill, Order


@dataclass
class ExecutionReport:
    order: Order
    fill: Fill | None
    status: str


class OrderManager:
    def __init__(self) -> None:
        self.open_orders: dict[str, Order] = {}

    def create_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: float | None,
        strategy_id: str,
    ) -> Order:
        order = Order(
            order_id=str(uuid4()),
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=limit_price,
            strategy_id=strategy_id,
        )
        self.open_orders[order.order_id] = order
        return order

    def execute(self, order: Order, market_price: float) -> ExecutionReport:
        fill_price = order.limit_price if order.limit_price is not None else market_price
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=datetime.utcnow(),
        )
        self.open_orders.pop(order.order_id, None)
        return ExecutionReport(order=order, fill=fill, status="filled")

    def fill_event(self, report: ExecutionReport) -> Event:
        return Event(event_type=EventType.FILL, payload={"fill": report.fill})
