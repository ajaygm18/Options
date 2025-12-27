"""
Base strategy class for trading strategies.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.events import Fill, Quote, Signal
from ..core.interfaces import IStrategy
from ..utils.logging import get_logger


class BaseStrategy(IStrategy, ABC):
    """
    Base class for all trading strategies.
    
    Strategies should inherit from this class and implement:
    - on_market_data: Process market data and generate signals
    - on_fill: Handle fill events
    """
    
    def __init__(self, strategy_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy.
        
        Args:
            strategy_id: Unique identifier for this strategy
            config: Strategy configuration
        """
        self.strategy_id = strategy_id
        self.config = config or {}
        self.logger = get_logger(f"strategy.{strategy_id}")
        self.positions: Dict[str, int] = {}
        self.enabled = True
        self.initialize(self.config)
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize strategy with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.logger.info("Strategy initialized", strategy_id=self.strategy_id)
    
    @abstractmethod
    def on_market_data(self, quote: Quote) -> Optional[Signal]:
        """
        Process market data and optionally generate a signal.
        
        Args:
            quote: Market quote
        
        Returns:
            Signal or None
        """
        pass
    
    def on_fill(self, fill: Fill) -> None:
        """
        Handle fill events.
        
        Updates internal position tracking.
        
        Args:
            fill: Fill event
        """
        symbol = fill.symbol
        quantity_delta = fill.quantity if fill.side.value == 'buy' else -fill.quantity
        
        current_position = self.positions.get(symbol, 0)
        self.positions[symbol] = current_position + quantity_delta
        
        self.logger.info(
            "Position updated",
            symbol=symbol,
            fill_quantity=quantity_delta,
            new_position=self.positions[symbol],
            strategy_id=self.strategy_id
        )
    
    def get_name(self) -> str:
        """Get strategy name."""
        return self.strategy_id
    
    def get_position(self, symbol: str) -> int:
        """
        Get current position for a symbol.
        
        Args:
            symbol: Symbol
        
        Returns:
            Position size (positive = long, negative = short, 0 = flat)
        """
        return self.positions.get(symbol, 0)
    
    def get_all_positions(self) -> Dict[str, int]:
        """Get all positions."""
        return self.positions.copy()
    
    def enable(self) -> None:
        """Enable the strategy."""
        self.enabled = True
        self.logger.info("Strategy enabled", strategy_id=self.strategy_id)
    
    def disable(self) -> None:
        """Disable the strategy."""
        self.enabled = False
        self.logger.info("Strategy disabled", strategy_id=self.strategy_id)
    
    def is_enabled(self) -> bool:
        """Check if strategy is enabled."""
        return self.enabled
    
    def reset(self) -> None:
        """Reset strategy state."""
        self.positions.clear()
        self.logger.info("Strategy reset", strategy_id=self.strategy_id)


class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Example strategy using simple moving average crossover.
    
    This is a simple example for demonstration purposes.
    """
    
    def __init__(self, strategy_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize SMA strategy."""
        self.short_window = 10
        self.long_window = 30
        self.price_history: Dict[str, List[float]] = {}
        super().__init__(strategy_id, config)
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with config."""
        self.short_window = config.get('short_window', 10)
        self.long_window = config.get('long_window', 30)
        super().initialize(config)
    
    def on_market_data(self, quote: Quote) -> Optional[Signal]:
        """Generate signal based on SMA crossover."""
        if not self.enabled:
            return None
        
        symbol = quote.symbol
        price = quote.mid
        
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep only necessary history
        max_window = max(self.short_window, self.long_window)
        if len(self.price_history[symbol]) > max_window:
            self.price_history[symbol] = self.price_history[symbol][-max_window:]
        
        # Need enough data
        if len(self.price_history[symbol]) < self.long_window:
            return None
        
        # Calculate SMAs
        prices = self.price_history[symbol]
        short_sma = sum(prices[-self.short_window:]) / self.short_window
        long_sma = sum(prices[-self.long_window:]) / self.long_window
        
        # Generate signal
        current_position = self.get_position(symbol)
        
        # Bullish crossover and not already long
        if short_sma > long_sma and current_position <= 0:
            from ..core.events import SignalType
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=0.7,
                metadata={
                    'short_sma': short_sma,
                    'long_sma': long_sma,
                    'price': price
                }
            )
        
        # Bearish crossover and not already short
        elif short_sma < long_sma and current_position >= 0:
            from ..core.events import SignalType
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=0.7,
                metadata={
                    'short_sma': short_sma,
                    'long_sma': long_sma,
                    'price': price
                }
            )
        
        return None
