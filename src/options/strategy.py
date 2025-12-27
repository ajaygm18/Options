from __future__ import annotations

from dataclasses import dataclass

from .events import Event, EventType, Signal


@dataclass
class StrategyContext:
    strategy_id: str


class Strategy:
    def __init__(self, context: StrategyContext) -> None:
        self.context = context

    def on_market_tick(self, event: Event) -> Signal | None:
        raise NotImplementedError


class MeanReversionStrategy(Strategy):
    def __init__(self, context: StrategyContext, threshold: float) -> None:
        super().__init__(context)
        self.threshold = threshold
        self.last_price: dict[str, float] = {}

    def on_market_tick(self, event: Event) -> Signal | None:
        tick = event.payload["tick"]
        prev = self.last_price.get(tick.symbol, tick.price)
        self.last_price[tick.symbol] = tick.price

        delta = (tick.price - prev) / prev if prev else 0.0
        if abs(delta) < self.threshold:
            return None

        side = "sell" if delta > 0 else "buy"
        return Signal(
            symbol=tick.symbol,
            side=side,
            quantity=1,
            confidence=min(abs(delta), 1.0),
            rationale=f"mean_reversion delta={delta:.4f}",
        )


def signal_event(signal: Signal) -> Event:
    return Event(event_type=EventType.SIGNAL, payload={"signal": signal})
