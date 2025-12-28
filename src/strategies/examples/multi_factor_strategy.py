"""
Advanced multi-factor options trading strategy.

Combines volatility analysis, momentum, and mean reversion.
"""
from typing import Any, Dict, List, Optional

import numpy as np

from ...core.events import Quote, Signal, SignalType
from ..base_strategy import BaseStrategy


class MultiFactorStrategy(BaseStrategy):
    """
    Multi-factor strategy combining:
    - Volatility mean reversion (IV vs RV)
    - Price momentum
    - Technical indicators (RSI, Bollinger Bands)
    
    Generates stronger signals when multiple factors align.
    """
    
    def __init__(self, strategy_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-factor strategy."""
        # Lookback periods
        self.volatility_lookback = 20
        self.momentum_lookback = 10
        self.rsi_period = 14
        
        # Thresholds
        self.iv_threshold = 0.05
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.momentum_threshold = 0.02
        
        # Signal weights
        self.volatility_weight = 0.4
        self.momentum_weight = 0.3
        self.technical_weight = 0.3
        
        # Historical data storage
        self.price_history: Dict[str, List[float]] = {}
        self.iv_history: Dict[str, List[float]] = {}
        
        super().__init__(strategy_id, config)
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with configuration."""
        self.volatility_lookback = config.get('volatility_lookback', 20)
        self.momentum_lookback = config.get('momentum_lookback', 10)
        self.rsi_period = config.get('rsi_period', 14)
        
        self.iv_threshold = config.get('iv_threshold', 0.05)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        self.volatility_weight = config.get('volatility_weight', 0.4)
        self.momentum_weight = config.get('momentum_weight', 0.3)
        self.technical_weight = config.get('technical_weight', 0.3)
        
        super().initialize(config)
    
    def on_market_data(self, quote: Quote) -> Optional[Signal]:
        """Generate multi-factor signal."""
        if not self.enabled:
            return None
        
        symbol = quote.symbol
        price = quote.mid
        
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(price)
        
        # Keep limited history
        max_lookback = max(self.volatility_lookback, self.rsi_period) * 2
        if len(self.price_history[symbol]) > max_lookback:
            self.price_history[symbol] = self.price_history[symbol][-max_lookback:]
        
        # Need minimum data
        if len(self.price_history[symbol]) < max_lookback:
            return None
        
        # Calculate factor signals
        vol_signal, vol_strength = self._volatility_signal(symbol)
        momentum_signal, momentum_strength = self._momentum_signal(symbol)
        technical_signal, technical_strength = self._technical_signal(symbol)
        
        # Combine signals with weights
        signals = [vol_signal, momentum_signal, technical_signal]
        strengths = [vol_strength, momentum_strength, technical_strength]
        weights = [self.volatility_weight, self.momentum_weight, self.technical_weight]
        
        # Count bullish vs bearish signals
        bullish_score = sum(w * s for w, s, sig in zip(weights, strengths, signals) if sig == 1)
        bearish_score = sum(w * s for w, s, sig in zip(weights, strengths, signals) if sig == -1)
        
        # Combined signal strength
        if bullish_score > bearish_score and bullish_score > 0.3:
            combined_signal = 1
            combined_strength = min(bullish_score, 1.0)
        elif bearish_score > bullish_score and bearish_score > 0.3:
            combined_signal = -1
            combined_strength = min(bearish_score, 1.0)
        else:
            combined_signal = 0
            combined_strength = 0.0
        
        # Generate trading signal
        current_position = self.get_position(symbol)
        
        if combined_signal == 1 and current_position <= 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.BUY,
                strength=combined_strength,
                metadata={
                    'vol_signal': vol_signal,
                    'momentum_signal': momentum_signal,
                    'technical_signal': technical_signal,
                    'bullish_score': bullish_score,
                    'bearish_score': bearish_score,
                    'price': price
                }
            )
        elif combined_signal == -1 and current_position >= 0:
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.SELL,
                strength=combined_strength,
                metadata={
                    'vol_signal': vol_signal,
                    'momentum_signal': momentum_signal,
                    'technical_signal': technical_signal,
                    'bullish_score': bullish_score,
                    'bearish_score': bearish_score,
                    'price': price
                }
            )
        elif current_position != 0 and abs(bullish_score - bearish_score) < 0.1:
            # Close position when signals are mixed
            return Signal(
                strategy_id=self.strategy_id,
                symbol=symbol,
                signal_type=SignalType.CLOSE,
                strength=0.5,
                metadata={'reason': 'mixed_signals'}
            )
        
        return None
    
    def _volatility_signal(self, symbol: str) -> tuple[int, float]:
        """
        Generate volatility-based signal.
        
        Returns:
            (signal: -1/0/1, strength: 0-1)
        """
        rv = self._calculate_realized_volatility(symbol)
        if rv is None:
            return 0, 0.0
        
        iv = self._get_implied_volatility(symbol)
        if iv is None:
            return 0, 0.0
        
        # Track IV history
        if symbol not in self.iv_history:
            self.iv_history[symbol] = []
        self.iv_history[symbol].append(iv)
        
        if len(self.iv_history[symbol]) > self.volatility_lookback:
            self.iv_history[symbol] = self.iv_history[symbol][-self.volatility_lookback:]
        
        if len(self.iv_history[symbol]) < self.volatility_lookback:
            return 0, 0.0
        
        iv_mean = np.mean(self.iv_history[symbol])
        iv_std = np.std(self.iv_history[symbol])
        
        if iv_std == 0:
            return 0, 0.0
        
        iv_z_score = (iv - iv_mean) / iv_std
        
        # Buy volatility when IV is cheap (below mean and below RV)
        if iv < rv and iv_z_score < -self.iv_threshold:
            strength = min(abs(iv_z_score), 2.0) / 2.0  # Normalize to 0-1
            return 1, strength
        # Sell volatility when IV is expensive
        elif iv > rv and iv_z_score > self.iv_threshold:
            strength = min(abs(iv_z_score), 2.0) / 2.0
            return -1, strength
        
        return 0, 0.0
    
    def _momentum_signal(self, symbol: str) -> tuple[int, float]:
        """
        Generate momentum-based signal.
        
        Returns:
            (signal: -1/0/1, strength: 0-1)
        """
        if len(self.price_history[symbol]) < self.momentum_lookback:
            return 0, 0.0
        
        prices = self.price_history[symbol]
        current_price = prices[-1]
        past_price = prices[-self.momentum_lookback]
        
        # Calculate momentum
        momentum = (current_price - past_price) / past_price
        
        # Positive momentum = bullish
        if momentum > self.momentum_threshold:
            strength = min(abs(momentum) / 0.1, 1.0)  # Normalize
            return 1, strength
        # Negative momentum = bearish
        elif momentum < -self.momentum_threshold:
            strength = min(abs(momentum) / 0.1, 1.0)
            return -1, strength
        
        return 0, 0.0
    
    def _technical_signal(self, symbol: str) -> tuple[int, float]:
        """
        Generate technical indicator signal (RSI).
        
        Returns:
            (signal: -1/0/1, strength: 0-1)
        """
        rsi = self._calculate_rsi(symbol)
        if rsi is None:
            return 0, 0.0
        
        # RSI oversold = bullish
        if rsi < self.rsi_oversold:
            strength = (self.rsi_oversold - rsi) / self.rsi_oversold
            return 1, min(strength, 1.0)
        # RSI overbought = bearish
        elif rsi > self.rsi_overbought:
            strength = (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            return -1, min(strength, 1.0)
        
        return 0, 0.0
    
    def _calculate_rsi(self, symbol: str, period: Optional[int] = None) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if period is None:
            period = self.rsi_period
        
        prices = self.price_history[symbol]
        if len(prices) < period + 1:
            return None
        
        # Calculate price changes
        deltas = np.diff(prices[-period-1:])
        
        # Separate gains and losses
        gains = deltas.copy()
        gains[gains < 0] = 0
        losses = -deltas.copy()
        losses[losses < 0] = 0
        
        # Calculate average gain and loss
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _calculate_realized_volatility(self, symbol: str) -> Optional[float]:
        """Calculate realized volatility."""
        if len(self.price_history[symbol]) < 2:
            return None
        
        prices = self.price_history[symbol][-self.volatility_lookback:]
        returns = np.diff(np.log(prices))
        
        if len(returns) < 2:
            return None
        
        rv = np.std(returns) * np.sqrt(252)
        return float(rv)
    
    def _get_implied_volatility(self, symbol: str) -> Optional[float]:
        """Get implied volatility (simulated)."""
        rv = self._calculate_realized_volatility(symbol)
        if rv is None:
            return None
        
        # Simulate IV with noise
        noise = np.random.normal(0, 0.05)
        iv = rv + noise
        
        return max(0.05, min(2.0, iv))
