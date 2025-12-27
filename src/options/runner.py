from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .engine import EventBus
from .events import Event, EventType, MarketTick, Order
from .execution import OrderManager
from .portfolio import Portfolio
from .risk import RiskEngine
from .strategy import Strategy


@dataclass
class TradingSystem:
    event_bus: EventBus
    portfolio: Portfolio
    risk_engine: RiskEngine
    order_manager: OrderManager
    strategies: list[Strategy]

    def wire(self) -> None:
        self.event_bus.subscribe(EventType.MARKET_TICK, self._handle_market_tick)
        self.event_bus.subscribe(EventType.FILL, self._handle_fill)

    def _handle_market_tick(self, event: Event) -> None:
        for strategy in self.strategies:
            signal = strategy.on_market_tick(event)
            if signal is None:
                continue
            order = self.order_manager.create_order(
                symbol=signal.symbol,
                side=signal.side,
                quantity=signal.quantity,
                limit_price=None,
                strategy_id=strategy.context.strategy_id,
            )
            decision = self.risk_engine.evaluate_order(order, est_price=event.payload["tick"].price)
            if not decision.approved:
                self.event_bus.publish(self.risk_engine.alert_event(decision.reason))
                continue
            report = self.order_manager.execute(order, market_price=event.payload["tick"].price)
            self.event_bus.publish(self.order_manager.fill_event(report))

    def _handle_fill(self, event: Event) -> None:
        fill = event.payload["fill"]
        self.portfolio.apply_fill(
            symbol=fill.symbol,
            side=fill.side,
            quantity=fill.quantity,
            price=fill.price,
        )
        self.risk_engine.handle_fill(event)

    def submit_ticks(self, ticks: Iterable[MarketTick]) -> None:
        for tick in ticks:
            event = Event(event_type=EventType.MARKET_TICK, payload={"tick": tick})
            self.event_bus.publish(event)
            self.event_bus.drain()
