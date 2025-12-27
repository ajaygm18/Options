"""
Abstract interfaces and protocols for the options trading system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .events import BaseEvent, Fill, Order, Quote, Signal


class IEventBus(ABC):
    """Interface for event bus implementation."""
    
    @abstractmethod
    def publish(self, event: BaseEvent) -> None:
        """Publish an event to the bus."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to events of a specific type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from events."""
        pass


class IMarketDataFeed(ABC):
    """Interface for market data feed."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the market data feed."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the feed."""
        pass
    
    @abstractmethod
    def subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to market data for a symbol."""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get the latest quote for a symbol."""
        pass


class IStrategy(ABC):
    """Interface for trading strategies."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the strategy with configuration."""
        pass
    
    @abstractmethod
    def on_market_data(self, quote: Quote) -> Optional[Signal]:
        """Process market data and generate signals."""
        pass
    
    @abstractmethod
    def on_fill(self, fill: Fill) -> None:
        """Handle fill events."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass


class IBroker(ABC):
    """Interface for broker connectivity."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the broker."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass
    
    @abstractmethod
    def submit_order(self, order: Order) -> str:
        """Submit an order and return broker order ID."""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance information."""
        pass


class IRiskEngine(ABC):
    """Interface for risk engine."""
    
    @abstractmethod
    def check_pre_trade(self, order: Order) -> tuple[bool, Optional[str]]:
        """
        Perform pre-trade risk checks.
        
        Returns:
            (approved, reason_if_rejected)
        """
        pass
    
    @abstractmethod
    def update_position(self, fill: Fill) -> None:
        """Update positions after a fill."""
        pass
    
    @abstractmethod
    def check_circuit_breakers(self) -> List[str]:
        """Check if any circuit breakers should be triggered."""
        pass
    
    @abstractmethod
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics."""
        pass


class IPortfolioOptimizer(ABC):
    """Interface for portfolio optimizer."""
    
    @abstractmethod
    def optimize(
        self,
        signals: List[Signal],
        current_positions: Dict[str, int],
        constraints: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Optimize portfolio allocation.
        
        Returns:
            Target positions by symbol
        """
        pass


class IPricingModel(ABC):
    """Interface for option pricing models."""
    
    @abstractmethod
    def price(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float,
        option_type: str
    ) -> float:
        """Calculate option price."""
        pass
    
    @abstractmethod
    def greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float,
        option_type: str
    ) -> Dict[str, float]:
        """Calculate option Greeks."""
        pass
