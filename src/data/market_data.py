"""
Market data manager for aggregating and distributing market data.
"""
from typing import Dict, List, Optional

from ..core.events import Quote
from ..core.interfaces import IEventBus, IMarketDataFeed
from ..utils.logging import get_logger


class MarketDataManager:
    """
    Manages market data from multiple feeds and distributes to subscribers.
    """
    
    def __init__(self, event_bus: Optional[IEventBus] = None):
        """
        Initialize market data manager.
        
        Args:
            event_bus: Event bus for publishing market data events
        """
        self.event_bus = event_bus
        self.feeds: Dict[str, IMarketDataFeed] = {}
        self.logger = get_logger(__name__)
        self.latest_quotes: Dict[str, Quote] = {}
    
    def add_feed(self, feed_name: str, feed: IMarketDataFeed) -> None:
        """
        Add a market data feed.
        
        Args:
            feed_name: Name to identify the feed
            feed: Feed instance
        """
        self.feeds[feed_name] = feed
        self.logger.info("Added market data feed", feed_name=feed_name)
    
    def connect_all(self) -> bool:
        """
        Connect to all registered feeds.
        
        Returns:
            True if all feeds connected successfully
        """
        success = True
        for feed_name, feed in self.feeds.items():
            try:
                if feed.connect():
                    self.logger.info("Connected to feed", feed_name=feed_name)
                else:
                    self.logger.error("Failed to connect to feed", feed_name=feed_name)
                    success = False
            except Exception as e:
                self.logger.error(
                    "Error connecting to feed",
                    feed_name=feed_name,
                    error=str(e)
                )
                success = False
        
        return success
    
    def disconnect_all(self) -> None:
        """Disconnect from all feeds."""
        for feed_name, feed in self.feeds.items():
            try:
                feed.disconnect()
                self.logger.info("Disconnected from feed", feed_name=feed_name)
            except Exception as e:
                self.logger.error(
                    "Error disconnecting from feed",
                    feed_name=feed_name,
                    error=str(e)
                )
    
    def subscribe_symbol(self, symbol: str, feed_names: Optional[List[str]] = None) -> None:
        """
        Subscribe to a symbol across feeds.
        
        Args:
            symbol: Symbol to subscribe to
            feed_names: Specific feeds to subscribe to (None = all feeds)
        """
        feeds_to_use = (
            {name: self.feeds[name] for name in feed_names if name in self.feeds}
            if feed_names
            else self.feeds
        )
        
        for feed_name, feed in feeds_to_use.items():
            try:
                feed.subscribe_symbol(symbol)
                self.logger.debug(
                    "Subscribed to symbol",
                    symbol=symbol,
                    feed_name=feed_name
                )
            except Exception as e:
                self.logger.error(
                    "Error subscribing to symbol",
                    symbol=symbol,
                    feed_name=feed_name,
                    error=str(e)
                )
    
    def get_quote(self, symbol: str, feed_name: Optional[str] = None) -> Optional[Quote]:
        """
        Get latest quote for a symbol.
        
        Args:
            symbol: Symbol to get quote for
            feed_name: Specific feed to use (None = first available)
        
        Returns:
            Latest quote or None
        """
        if feed_name and feed_name in self.feeds:
            return self.feeds[feed_name].get_quote(symbol)
        
        # Try all feeds
        for feed in self.feeds.values():
            quote = feed.get_quote(symbol)
            if quote:
                return quote
        
        # Return cached quote if available
        return self.latest_quotes.get(symbol)
    
    def update_quote(self, symbol: str, quote: Quote) -> None:
        """
        Update and publish a quote.
        
        Args:
            symbol: Symbol
            quote: New quote
        """
        self.latest_quotes[symbol] = quote
        
        if self.event_bus:
            self.event_bus.publish(quote)
    
    def get_all_quotes(self) -> Dict[str, Quote]:
        """Get all latest quotes."""
        return self.latest_quotes.copy()
    
    def get_active_symbols(self) -> List[str]:
        """Get list of all subscribed symbols."""
        symbols = set()
        for feed in self.feeds.values():
            symbols.update(feed.get_subscriptions())
        return list(symbols)
