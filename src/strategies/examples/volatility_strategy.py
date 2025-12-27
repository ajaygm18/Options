"""
Example volatility-based trading strategy.

This strategy trades based on the relationship between implied volatility (IV)
and realized volatility (RV).
"""
from typing import Any, Dict, List, Optional

import numpy as np

from ...core.events import Quote, Signal, SignalType
from ..base_strategy import BaseStrategy


class VolatilityStrategy(BaseStrategy):
    """
    Volatility mean reversion strategy.
    
    Strategy logic:
    - Buy volatility (long options) when IV < RV and IV is below its mean
    - Sell volatility (short options) when IV > RV and IV is above its mean
    
    This is a simplified example for demonstration.
    """
    
    def __init__(self, strategy_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize volatility strategy."""
        self.lookback_period = 20
        self.iv_threshold = 0.05  # 5% deviation from mean
        self.min_signal_strength = 0.5
        
        # Track historical data
        self.price_history: Dict[str, List[float]] = {}
        self.iv_history: Dict[str, List[float]] = {}
        
        super().__init__(strategy_id, config)
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration."""
        self.lookback_period = config.get('lookback_period', 20)
        self.iv_threshold = config.get('iv_threshold', 0.05)
        self.min_signal_strength = config.get('min_signal_strength', 0.5)
        super().initialize(config)
    
    def on_market_data(self, quote: Quote) -> Optional[Signal]:
        """Generate signal based on IV vs RV analysis."""
        if not self.enabled:
            return None
        
        symbol = quote.symbol
        price = quote.mid
        
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep only lookback period
        if len(self.price_history[symbol]) > self.lookback_period * 2:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_period * 2:]
        
        # Need enough data
        if len(self.price_history[symbol]) < self.lookback_period:
            return None
        
        # Calculate realized volatility
        rv = self._calculate_realized_volatility(symbol)
        if rv is None:
            return None
        
        # Get implied volatility (simulated for this example)
        # In production, this would come from option chain data
        iv = self._get_implied_volatility(symbol)
        if iv is None:
            return None
        
        # Update IV history
        if symbol not in self.iv_history:
            self.iv_history[symbol] = []
        self.iv_history[symbol].append(iv)
        
        if len(self.iv_history[symbol]) > self.lookback_period:
            self.iv_history[symbol] = self.iv_history[symbol][-self.lookback_period:]
        
        # Calculate IV mean
        if len(self.iv_history[symbol]) < self.lookback_period:
            return None
        
        iv_mean = np.mean(self.iv_history[symbol])
        iv_std = np.std(self.iv_history[symbol])
        
        # Generate signal
        iv_deviation = (iv - iv_mean) / iv_std if iv_std > 0 else 0
        vol_spread = iv - rv
        
        signal_strength = min(1.0, abs(iv_deviation) / 2.0)
        
        if signal_strength < self.min_signal_strength:
            return None
        
        current_position = self.get_position(symbol)
        
        # Buy volatility (long options) when IV is cheap
        if iv < rv and iv_deviation < -self.iv_threshold and current_position <= 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=signal_strength,
                metadata={
                    'iv': iv,
                    'rv': rv,
                    'iv_mean': iv_mean,
                    'iv_deviation': iv_deviation,
                    'vol_spread': vol_spread,
                    'reason': 'iv_cheap'
                }
            )
        
        # Sell volatility (short options) when IV is expensive
        elif iv > rv and iv_deviation > self.iv_threshold and current_position >= 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=signal_strength,
                metadata={
                    'iv': iv,
                    'rv': rv,
                    'iv_mean': iv_mean,
                    'iv_deviation': iv_deviation,
                    'vol_spread': vol_spread,
                    'reason': 'iv_expensive'
                }
            )
        
        # Close position when spread normalizes
        elif abs(vol_spread) < 0.02 and current_position != 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.CLOSE,
                strength=0.5,
                metadata={
                    'iv': iv,
                    'rv': rv,
                    'vol_spread': vol_spread,
                    'reason': 'spread_normalized'
                }
            )
        
        return None
    
    def _calculate_realized_volatility(self, symbol: str) -> Optional[float]:
        """
        Calculate realized volatility from price history.
        
        Args:
            symbol: Symbol
        
        Returns:
            Annualized realized volatility
        """
        if symbol not in self.price_history:
            return None
        
        prices = self.price_history[symbol]
        if len(prices) < 2:
            return None
        
        # Calculate log returns
        returns = np.diff(np.log(prices))
        
        if len(returns) < 2:
            return None
        
        # Annualized volatility (assuming daily data)
        rv = np.std(returns) * np.sqrt(252)
        
        return float(rv)
    
    def _get_implied_volatility(self, symbol: str) -> Optional[float]:
        """
        Get implied volatility for the symbol.
        
        In production, this would retrieve IV from option chain data.
        For this example, we simulate it based on RV + noise.
        
        Args:
            symbol: Symbol
        
        Returns:
            Implied volatility
        """
        rv = self._calculate_realized_volatility(symbol)
        if rv is None:
            return None
        
        # Simulate IV as RV + random noise
        noise = np.random.normal(0, 0.05)
        iv = rv + noise
        
        return max(0.05, min(2.0, iv))  # Clamp to reasonable range
