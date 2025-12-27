from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    MARKET_TICK = "market_tick"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"
    RISK_ALERT = "risk_alert"
    SYSTEM = "system"


@dataclass(frozen=True)
class Event:
    event_type: EventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "core"


@dataclass(frozen=True)
class MarketTick:
    symbol: str
    price: float
    bid: float
    ask: float
    timestamp: datetime


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: str
    quantity: int
    confidence: float
    rationale: str


@dataclass(frozen=True)
class Order:
    order_id: str
    symbol: str
    side: str
    quantity: int
    limit_price: float | None
    strategy_id: str


@dataclass(frozen=True)
class Fill:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    timestamp: datetime
