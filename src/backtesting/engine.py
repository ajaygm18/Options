"""
Event-driven backtesting engine for options trading strategies.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.events import Fill, Order, OrderSide, OrderStatus, Quote, Signal
from ..data.historical import HistoricalDataHandler
from ..execution.order import Order as OrderObj
from ..portfolio.position_manager import PositionManager
from ..strategies.base_strategy import BaseStrategy
from ..utils.logging import get_logger
from .slippage import SlippageModel, get_slippage_model


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    Simulates realistic order execution with slippage and partial fills.
    Tracks performance metrics and generates detailed reports.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_per_contract: float = 0.65,
        slippage_model: str = "spread_based"
    ):
        """
        Initialize backtest engine.
        
        Args:
            initial_capital: Starting capital
            commission_per_contract: Commission per contract
            slippage_model: Slippage model to use
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_per_contract = commission_per_contract
        
        self.slippage_model = get_slippage_model(slippage_model)
        self.position_manager = PositionManager()
        self.historical_data = HistoricalDataHandler()
        
        self.strategies: List[BaseStrategy] = []
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        self.logger = get_logger(__name__)
    
    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a strategy to the backtest."""
        self.strategies.append(strategy)
        self.logger.info("Added strategy", strategy_id=strategy.strategy_id)
    
    def load_data(self, symbol: str, data: pd.DataFrame) -> None:
        """Load historical data for a symbol."""
        self.historical_data.load_dataframe(symbol, data)
    
    def run(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run the backtest.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            symbols: List of symbols to trade
        
        Returns:
            Dictionary with backtest results
        """
        self.logger.info(
            "Starting backtest",
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital
        )
        
        if symbols is None:
            symbols = self.historical_data.available_symbols()
        
        # Get all timestamps from all symbols
        all_timestamps = set()
        for symbol in symbols:
            data = self.historical_data.get_data(symbol, start_date, end_date)
            if data is not None and isinstance(data.index, pd.DatetimeIndex):
                all_timestamps.update(data.index)
        
        # Sort timestamps
        timestamps = sorted(all_timestamps)
        
        if not timestamps:
            self.logger.error("No data available for backtest")
            return self._generate_results()
        
        # Event loop
        for timestamp in timestamps:
            # Update positions with market prices
            for symbol in symbols:
                quote = self.historical_data.get_quote_at(symbol, timestamp)
                if quote:
                    self._update_position_values(symbol, quote.mid)
            
            # Record equity
            self._record_equity(timestamp)
            
            # Generate signals from strategies
            for symbol in symbols:
                quote = self.historical_data.get_quote_at(symbol, timestamp)
                if quote:
                    for strategy in self.strategies:
                        if strategy.is_enabled():
                            signal = strategy.on_market_data(quote)
                            if signal:
                                self._process_signal(signal, quote, timestamp)
        
        self.logger.info(
            "Backtest completed",
            total_trades=len(self.trades),
            final_capital=self.current_capital
        )
        
        return self._generate_results()
    
    def _process_signal(
        self,
        signal: Signal,
        quote: Quote,
        timestamp: datetime
    ) -> None:
        """Process a trading signal."""
        # Simple signal to order conversion
        # In production, this would go through portfolio optimizer
        
        if signal.signal_type.value == 'buy':
            side = OrderSide.BUY
            quantity = 1  # Simple: 1 contract
        elif signal.signal_type.value == 'sell':
            side = OrderSide.SELL
            quantity = 1
        elif signal.signal_type.value == 'close':
            # Close existing position
            current_position = self.position_manager.get_position(signal.symbol)
            if current_position and current_position.quantity != 0:
                side = OrderSide.SELL if current_position.quantity > 0 else OrderSide.BUY
                quantity = abs(current_position.quantity)
            else:
                return
        else:
            return
        
        # Check if we have enough capital
        estimated_cost = quantity * quote.mid * 100  # 100 multiplier for options
        if side == OrderSide.BUY and estimated_cost > self.current_capital:
            self.logger.warning(
                "Insufficient capital for trade",
                symbol=signal.symbol,
                required=estimated_cost,
                available=self.current_capital
            )
            return
        
        # Simulate order execution
        self._execute_order(
            symbol=signal.symbol,
            side=side,
            quantity=quantity,
            quote=quote,
            timestamp=timestamp,
            strategy_id=signal.strategy_id
        )
    
    def _execute_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        quote: Quote,
        timestamp: datetime,
        strategy_id: str
    ) -> None:
        """Simulate order execution with slippage."""
        # Calculate slippage
        slippage = self.slippage_model.calculate_slippage(
            symbol=symbol,
            side=side,
            order_type=None,
            quantity=quantity,
            limit_price=None,
            bid=quote.bid,
            ask=quote.ask,
            bid_size=quote.bid_size,
            ask_size=quote.ask_size,
            volume=0
        )
        
        # Determine fill price
        if side == OrderSide.BUY:
            fill_price = quote.ask + slippage
        else:
            fill_price = quote.bid - slippage
        
        # Calculate commission
        commission = quantity * self.commission_per_contract
        
        # Create fill event
        fill = Fill(
            timestamp=timestamp,
            order_id=f"backtest_{len(self.trades)}",
            fill_id=f"fill_{len(self.trades)}",
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=fill_price,
            commission=commission,
            is_partial=False
        )
        
        # Update positions
        position_update = self.position_manager.process_fill(fill)
        
        # Update capital
        if side == OrderSide.BUY:
            self.current_capital -= (quantity * fill_price * 100 + commission)
        else:
            self.current_capital += (quantity * fill_price * 100 - commission)
        
        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'side': side.value,
            'quantity': quantity,
            'price': fill_price,
            'commission': commission,
            'strategy_id': strategy_id,
            'capital': self.current_capital
        })
        
        self.logger.debug(
            "Trade executed",
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            price=fill_price
        )
    
    def _update_position_values(self, symbol: str, current_price: float) -> None:
        """Update unrealized P&L for positions."""
        self.position_manager.update_market_value(symbol, current_price)
    
    def _record_equity(self, timestamp: datetime) -> None:
        """Record current equity for equity curve."""
        pnl = self.position_manager.get_total_pnl()
        total_equity = self.current_capital + pnl['unrealized_pnl']
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity,
            'cash': self.current_capital,
            'unrealized_pnl': pnl['unrealized_pnl'],
            'realized_pnl': pnl['realized_pnl']
        })
    
    def _generate_results(self) -> Dict[str, Any]:
        """Generate backtest results and performance metrics."""
        if not self.equity_curve:
            return {
                'total_return': 0.0,
                'trades': 0,
                'metrics': {}
            }
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        final_equity = equity_df['equity'].iloc[-1] if len(equity_df) > 0 else self.initial_capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital
        
        # Calculate returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        
        # Calculate metrics
        metrics = self._calculate_metrics(equity_df)
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': len(self.trades),
            'metrics': metrics,
            'equity_curve': equity_df,
            'trades': pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        }
    
    def _calculate_metrics(self, equity_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance metrics."""
        import numpy as np
        
        returns = equity_df['returns'].dropna()
        
        if len(returns) == 0:
            return {}
        
        # Sharpe ratio (annualized, assuming daily data)
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        if len(self.trades) > 0:
            trades_df = pd.DataFrame(self.trades)
            # Simple win rate based on P&L
            wins = 0
            losses = 0
            for i in range(len(self.trades)):
                if i > 0:
                    pnl_change = self.trades[i]['capital'] - self.trades[i-1]['capital']
                    if pnl_change > 0:
                        wins += 1
                    elif pnl_change < 0:
                        losses += 1
            
            win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        else:
            win_rate = 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        sortino = (returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        return {
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'max_drawdown': float(max_drawdown),
            'max_drawdown_pct': float(max_drawdown * 100),
            'win_rate': float(win_rate),
            'avg_return': float(returns.mean()),
            'volatility': float(returns.std()),
            'total_trades': len(self.trades)
        }
