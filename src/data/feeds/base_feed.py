"""
Base market data feed adapter.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ...core.events import Quote
from ...core.interfaces import IMarketDataFeed


class BaseFeed(IMarketDataFeed, ABC):
    """Base class for market data feed adapters."""
    
    def __init__(self, feed_name: str):
        """
        Initialize feed adapter.
        
        Args:
            feed_name: Name of the feed
        """
        self.feed_name = feed_name
        self.connected = False
        self.subscriptions: Dict[str, bool] = {}
        self.latest_quotes: Dict[str, Quote] = {}
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the market data feed.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the feed."""
        pass
    
    @abstractmethod
    def subscribe_symbol(self, symbol: str) -> None:
        """
        Subscribe to market data for a symbol.
        
        Args:
            symbol: Symbol to subscribe to
        """
        pass
    
    def unsubscribe_symbol(self, symbol: str) -> None:
        """
        Unsubscribe from a symbol.
        
        Args:
            symbol: Symbol to unsubscribe from
        """
        if symbol in self.subscriptions:
            del self.subscriptions[symbol]
            if symbol in self.latest_quotes:
                del self.latest_quotes[symbol]
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get the latest quote for a symbol.
        
        Args:
            symbol: Symbol to get quote for
        
        Returns:
            Latest quote or None if not available
        """
        return self.latest_quotes.get(symbol)
    
    def is_connected(self) -> bool:
        """Check if feed is connected."""
        return self.connected
    
    def get_subscriptions(self) -> List[str]:
        """Get list of subscribed symbols."""
        return list(self.subscriptions.keys())
    
    def _update_quote(self, symbol: str, quote: Quote) -> None:
        """
        Update latest quote for a symbol.
        
        Args:
            symbol: Symbol
            quote: New quote
        """
        self.latest_quotes[symbol] = quote


class SimulatedFeed(BaseFeed):
    """Simulated market data feed for testing."""
    
    def __init__(self):
        """Initialize simulated feed."""
        super().__init__("SimulatedFeed")
    
    def connect(self) -> bool:
        """Connect to simulated feed."""
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from simulated feed."""
        self.connected = False
    
    def subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to a symbol."""
        self.subscriptions[symbol] = True
    
    def inject_quote(self, symbol: str, bid: float, ask: float, bid_size: int = 100, ask_size: int = 100) -> None:
        """
        Inject a quote into the feed (for testing).
        
        Args:
            symbol: Symbol
            bid: Bid price
            ask: Ask price
            bid_size: Bid size
            ask_size: Ask size
        """
        from datetime import datetime
        
        quote = Quote(
            symbol=symbol,
            bid=bid,
            ask=ask,
            bid_size=bid_size,
            ask_size=ask_size
        )
        self._update_quote(symbol, quote)
