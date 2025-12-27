"""
Core event types for the options trading system.

All events are immutable and include timestamps for traceability.
"""
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class EventType(Enum):
    """Event type enumeration."""
    MARKET_TICK = "market_tick"
    QUOTE = "quote"
    OPTION_CHAIN = "option_chain"
    IV_SURFACE = "iv_surface"
    SIGNAL = "signal"
    ORDER = "order"
    ORDER_ACK = "order_ack"
    FILL = "fill"
    PARTIAL_FILL = "partial_fill"
    CANCEL = "cancel"
    REJECT = "reject"
    POSITION_UPDATE = "position_update"
    RISK_UPDATE = "risk_update"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass(frozen=True)
class BaseEvent(ABC):
    """Base class for all events."""
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: EventType = field(init=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
        }


@dataclass(frozen=True)
class MarketTick(BaseEvent):
    """Market tick event with latest price data."""
    event_type: EventType = field(default=EventType.MARKET_TICK, init=False)
    symbol: str = ""
    price: float = 0.0
    volume: int = 0
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None


@dataclass(frozen=True)
class Quote(BaseEvent):
    """Quote event with bid/ask data."""
    event_type: EventType = field(default=EventType.QUOTE, init=False)
    symbol: str = ""
    bid: float = 0.0
    ask: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    mid: float = field(init=False)
    spread: float = field(init=False)
    
    def __post_init__(self) -> None:
        """Calculate derived fields."""
        object.__setattr__(self, 'mid', (self.bid + self.ask) / 2.0)
        object.__setattr__(self, 'spread', self.ask - self.bid)


@dataclass(frozen=True)
class OptionChain(BaseEvent):
    """Option chain data for an underlying."""
    event_type: EventType = field(default=EventType.OPTION_CHAIN, init=False)
    underlying: str = ""
    expiry: datetime = field(default_factory=datetime.utcnow)
    options: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class IVSurface(BaseEvent):
    """Implied volatility surface."""
    event_type: EventType = field(default=EventType.IV_SURFACE, init=False)
    underlying: str = ""
    surface_data: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0


class SignalType(Enum):
    """Signal type enumeration."""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    HEDGE = "hedge"


@dataclass(frozen=True)
class Signal(BaseEvent):
    """Trading signal from a strategy."""
    event_type: EventType = field(default=EventType.SIGNAL, init=False)
    strategy_id: str = ""
    symbol: str = ""
    signal_type: SignalType = SignalType.BUY
    strength: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Order(BaseEvent):
    """Order event."""
    event_type: EventType = field(default=EventType.ORDER, init=False)
    order_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.LIMIT
    quantity: int = 0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.NEW
    strategy_id: Optional[str] = None
    idempotency_key: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class OrderAck(BaseEvent):
    """Order acknowledgment event."""
    event_type: EventType = field(default=EventType.ORDER_ACK, init=False)
    order_id: str = ""
    broker_order_id: str = ""
    status: OrderStatus = OrderStatus.ACKNOWLEDGED


@dataclass(frozen=True)
class Fill(BaseEvent):
    """Fill event."""
    event_type: EventType = field(default=EventType.FILL, init=False)
    order_id: str = ""
    fill_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    quantity: int = 0
    price: float = 0.0
    commission: float = 0.0
    is_partial: bool = False


@dataclass(frozen=True)
class PositionUpdate(BaseEvent):
    """Position update event."""
    event_type: EventType = field(default=EventType.POSITION_UPDATE, init=False)
    symbol: str = ""
    quantity: int = 0
    average_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass(frozen=True)
class RiskUpdate(BaseEvent):
    """Risk metrics update event."""
    event_type: EventType = field(default=EventType.RISK_UPDATE, init=False)
    portfolio_delta: float = 0.0
    portfolio_gamma: float = 0.0
    portfolio_theta: float = 0.0
    portfolio_vega: float = 0.0
    var: float = 0.0
    cvar: float = 0.0
    margin_used: float = 0.0


class CircuitBreakerReason(Enum):
    """Circuit breaker trigger reasons."""
    DRAWDOWN = "drawdown"
    DATA_STALE = "data_stale"
    BROKER_REJECTS = "broker_rejects"
    SPREAD_BLOWOUT = "spread_blowout"
    VOLATILITY_SPIKE = "volatility_spike"
    MANUAL = "manual"


@dataclass(frozen=True)
class CircuitBreaker(BaseEvent):
    """Circuit breaker triggered event."""
    event_type: EventType = field(default=EventType.CIRCUIT_BREAKER, init=False)
    reason: CircuitBreakerReason = CircuitBreakerReason.MANUAL
    severity: str = "warning"  # warning, critical
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
