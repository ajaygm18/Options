"""
Portfolio optimizer using mean-variance optimization.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..core.events import Signal
from ..utils.logging import get_logger


class PortfolioOptimizer:
    """
    Portfolio optimizer for multi-strategy allocation.
    
    Uses mean-variance optimization with constraints to determine
    optimal position sizes across strategies.
    """
    
    def __init__(
        self,
        risk_aversion: float = 1.0,
        max_position_size: int = 10,
        max_portfolio_notional: float = 100000.0
    ):
        """
        Initialize portfolio optimizer.
        
        Args:
            risk_aversion: Risk aversion parameter (higher = more conservative)
            max_position_size: Maximum position size per symbol
            max_portfolio_notional: Maximum total portfolio notional
        """
        self.risk_aversion = risk_aversion
        self.max_position_size = max_position_size
        self.max_portfolio_notional = max_portfolio_notional
        self.logger = get_logger(__name__)
    
    def optimize(
        self,
        signals: List[Signal],
        current_positions: Dict[str, int],
        expected_returns: Optional[Dict[str, float]] = None,
        volatilities: Optional[Dict[str, float]] = None,
        current_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, int]:
        """
        Optimize portfolio allocation based on signals.
        
        Args:
            signals: List of trading signals
            current_positions: Current positions by symbol
            expected_returns: Expected returns by symbol (optional)
            volatilities: Volatility estimates by symbol (optional)
            current_prices: Current prices by symbol (optional)
        
        Returns:
            Target positions by symbol
        """
        if not signals:
            return current_positions
        
        # Group signals by symbol
        signals_by_symbol: Dict[str, List[Signal]] = {}
        for signal in signals:
            if signal.symbol not in signals_by_symbol:
                signals_by_symbol[signal.symbol] = []
            signals_by_symbol[signal.symbol].append(signal)
        
        # Calculate target positions
        target_positions = {}
        
        for symbol, symbol_signals in signals_by_symbol.items():
            # Use signal strength as a weight
            avg_strength = np.mean([s.strength for s in symbol_signals])
            
            # Determine direction from latest signal
            latest_signal = symbol_signals[-1]
            
            if latest_signal.signal_type.value == 'buy':
                direction = 1
            elif latest_signal.signal_type.value == 'sell':
                direction = -1
            elif latest_signal.signal_type.value == 'close':
                direction = 0
            else:
                direction = 0
            
            # Calculate target size based on strength and risk aversion
            if direction != 0:
                # Simple sizing: strength * max_size / risk_aversion
                target_size = int(avg_strength * self.max_position_size / self.risk_aversion)
                target_size = min(target_size, self.max_position_size)
                target_size = max(target_size, 1)  # At least 1 contract
                
                target_positions[symbol] = direction * target_size
            else:
                target_positions[symbol] = 0
        
        # Apply portfolio-level constraints
        target_positions = self._apply_constraints(
            target_positions,
            current_positions,
            current_prices
        )
        
        return target_positions
    
    def _apply_constraints(
        self,
        target_positions: Dict[str, int],
        current_positions: Dict[str, int],
        current_prices: Optional[Dict[str, float]]
    ) -> Dict[str, int]:
        """Apply portfolio-level constraints."""
        # Check total notional exposure
        if current_prices:
            total_notional = sum(
                abs(qty) * current_prices.get(symbol, 100) * 100  # 100 multiplier
                for symbol, qty in target_positions.items()
            )
            
            if total_notional > self.max_portfolio_notional:
                # Scale down all positions proportionally
                scale_factor = self.max_portfolio_notional / total_notional
                target_positions = {
                    symbol: int(qty * scale_factor)
                    for symbol, qty in target_positions.items()
                }
                
                self.logger.warning(
                    "Scaled down positions due to notional limit",
                    scale_factor=scale_factor
                )
        
        return target_positions
    
    def calculate_portfolio_metrics(
        self,
        positions: Dict[str, int],
        expected_returns: Dict[str, float],
        covariance_matrix: np.ndarray,
        symbols: List[str]
    ) -> Dict[str, float]:
        """
        Calculate portfolio-level metrics.
        
        Args:
            positions: Position sizes by symbol
            expected_returns: Expected returns by symbol
            covariance_matrix: Covariance matrix of returns
            symbols: List of symbols in order
        
        Returns:
            Portfolio metrics
        """
        # Build position vector
        position_vector = np.array([positions.get(s, 0) for s in symbols])
        return_vector = np.array([expected_returns.get(s, 0) for s in symbols])
        
        # Portfolio expected return
        portfolio_return = np.dot(position_vector, return_vector)
        
        # Portfolio variance
        portfolio_variance = np.dot(position_vector, np.dot(covariance_matrix, position_vector))
        portfolio_std = np.sqrt(portfolio_variance)
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe = portfolio_return / portfolio_std if portfolio_std > 0 else 0
        
        return {
            'expected_return': float(portfolio_return),
            'volatility': float(portfolio_std),
            'sharpe_ratio': float(sharpe)
        }


class KellyOptimizer:
    """
    Kelly Criterion optimizer for position sizing.
    
    Uses the Kelly criterion to determine optimal bet sizes
    based on win rate and payoff ratio.
    """
    
    def __init__(self, max_kelly_fraction: float = 0.25):
        """
        Initialize Kelly optimizer.
        
        Args:
            max_kelly_fraction: Maximum fraction of Kelly to use (for safety)
        """
        self.max_kelly_fraction = max_kelly_fraction
        self.logger = get_logger(__name__)
    
    def calculate_kelly_fraction(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly fraction.
        
        Args:
            win_rate: Probability of winning (0 to 1)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive)
        
        Returns:
            Kelly fraction (0 to 1)
        """
        if avg_loss == 0:
            return 0.0
        
        # Kelly formula: f = (p * b - q) / b
        # where p = win rate, q = 1 - p, b = avg_win / avg_loss
        b = avg_win / avg_loss
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b
        
        # Cap at max fraction for safety
        kelly = max(0, min(kelly, self.max_kelly_fraction))
        
        return kelly
    
    def calculate_position_size(
        self,
        capital: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        price_per_contract: float
    ) -> int:
        """
        Calculate position size in contracts.
        
        Args:
            capital: Available capital
            win_rate: Win rate (0 to 1)
            avg_win: Average win
            avg_loss: Average loss
            price_per_contract: Price per contract
        
        Returns:
            Number of contracts
        """
        kelly_fraction = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        
        position_value = capital * kelly_fraction
        num_contracts = int(position_value / price_per_contract)
        
        return max(0, num_contracts)
