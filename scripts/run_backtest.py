#!/usr/bin/env python3
"""
Run backtest with multiple strategies and analyze performance.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.backtesting.engine import BacktestEngine
from src.strategies.base_strategy import SimpleMovingAverageStrategy
from src.strategies.examples.volatility_strategy import VolatilityStrategy
from src.strategies.examples.multi_factor_strategy import MultiFactorStrategy
from src.utils.logging import get_logger


def generate_synthetic_price_data(
    symbol: str,
    start_date: datetime,
    days: int = 252,
    initial_price: float = 100.0,
    volatility: float = 0.25,
    drift: float = 0.10
) -> pd.DataFrame:
    """
    Generate synthetic price data using geometric Brownian motion.
    
    Args:
        symbol: Symbol name
        start_date: Start date
        days: Number of trading days
        initial_price: Initial price
        volatility: Annual volatility
        drift: Annual drift (expected return)
    
    Returns:
        DataFrame with OHLCV data
    """
    dt = 1/252  # Daily time step
    
    # Generate random returns
    returns = np.random.normal(drift * dt, volatility * np.sqrt(dt), days)
    
    # Generate price path
    prices = initial_price * np.exp(np.cumsum(returns))
    
    # Add some intraday variation for OHLC
    highs = prices * (1 + np.abs(np.random.normal(0, volatility/10, days)))
    lows = prices * (1 - np.abs(np.random.normal(0, volatility/10, days)))
    opens = prices * (1 + np.random.normal(0, volatility/20, days))
    
    # Generate volume
    volume = np.random.randint(100000, 1000000, days)
    
    # Create dates
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Create DataFrame
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volume,
        'bid': prices * 0.998,  # Bid slightly below close
        'ask': prices * 1.002,  # Ask slightly above close
        'bid_size': 100,
        'ask_size': 100
    }, index=dates)
    
    return df


def run_backtest():
    """Run comprehensive backtest."""
    logger = get_logger(__name__)
    
    logger.info("="*60)
    logger.info("Options Trading System - Backtest")
    logger.info("="*60)
    
    # Configuration
    initial_capital = 100000.0
    symbols = ['SPY', 'QQQ', 'IWM']
    
    # Generate synthetic data for multiple symbols
    logger.info("\nGenerating synthetic market data...")
    start_date = datetime(2023, 1, 1)
    
    data = {}
    for symbol in symbols:
        # Different characteristics for each symbol
        if symbol == 'SPY':
            data[symbol] = generate_synthetic_price_data(
                symbol, start_date, days=252, initial_price=450, volatility=0.18, drift=0.12
            )
        elif symbol == 'QQQ':
            data[symbol] = generate_synthetic_price_data(
                symbol, start_date, days=252, initial_price=380, volatility=0.22, drift=0.15
            )
        else:  # IWM
            data[symbol] = generate_synthetic_price_data(
                symbol, start_date, days=252, initial_price=200, volatility=0.25, drift=0.08
            )
        
        logger.info(f"  {symbol}: {len(data[symbol])} days, "
                   f"${data[symbol]['close'].iloc[0]:.2f} → ${data[symbol]['close'].iloc[-1]:.2f}")
    
    # Run backtests with different strategies
    strategies_to_test = [
        ('SMA', SimpleMovingAverageStrategy, {'short_window': 5, 'long_window': 20}),
        ('Volatility', VolatilityStrategy, {'lookback_period': 20, 'iv_threshold': 0.05}),
        ('MultiFactor', MultiFactorStrategy, {'volatility_weight': 0.4, 'momentum_weight': 0.3}),
    ]
    
    results = {}
    
    for strategy_name, strategy_class, config in strategies_to_test:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {strategy_name} Strategy")
        logger.info(f"{'='*60}")
        
        # Initialize backtest engine
        engine = BacktestEngine(
            initial_capital=initial_capital,
            commission_per_contract=0.65,
            slippage_model='realistic'
        )
        
        # Load data
        for symbol, df in data.items():
            engine.load_data(symbol, df)
        
        # Add strategy
        strategy = strategy_class(f'{strategy_name.lower()}_strategy', config)
        engine.add_strategy(strategy)
        
        # Run backtest
        result = engine.run(symbols=symbols)
        results[strategy_name] = result
        
        # Display results
        logger.info(f"\nPerformance Summary:")
        logger.info(f"  Initial Capital: ${result['initial_capital']:,.2f}")
        logger.info(f"  Final Equity: ${result['final_equity']:,.2f}")
        logger.info(f"  Total Return: {result['total_return_pct']:.2f}%")
        logger.info(f"  Total Trades: {result['total_trades']}")
        
        if result['metrics']:
            logger.info(f"\nRisk Metrics:")
            logger.info(f"  Sharpe Ratio: {result['metrics'].get('sharpe_ratio', 0):.2f}")
            logger.info(f"  Sortino Ratio: {result['metrics'].get('sortino_ratio', 0):.2f}")
            logger.info(f"  Max Drawdown: {result['metrics'].get('max_drawdown_pct', 0):.2f}%")
            logger.info(f"  Win Rate: {result['metrics'].get('win_rate', 0)*100:.1f}%")
            logger.info(f"  Volatility: {result['metrics'].get('volatility', 0)*100:.2f}%")
    
    # Compare strategies
    logger.info(f"\n{'='*60}")
    logger.info("Strategy Comparison")
    logger.info(f"{'='*60}")
    logger.info(f"\n{'Strategy':<15} {'Return %':<12} {'Sharpe':<10} {'MaxDD %':<12} {'Trades':<8}")
    logger.info("-" * 60)
    
    for strategy_name, result in results.items():
        sharpe = result['metrics'].get('sharpe_ratio', 0) if result['metrics'] else 0
        max_dd = result['metrics'].get('max_drawdown_pct', 0) if result['metrics'] else 0
        
        logger.info(f"{strategy_name:<15} {result['total_return_pct']:<12.2f} "
                   f"{sharpe:<10.2f} {max_dd:<12.2f} {result['total_trades']:<8}")
    
    # Find best strategy
    best_strategy = max(results.items(), key=lambda x: x[1]['total_return_pct'])
    logger.info(f"\n{'='*60}")
    logger.info(f"Best Performing Strategy: {best_strategy[0]}")
    logger.info(f"Return: {best_strategy[1]['total_return_pct']:.2f}%")
    logger.info(f"{'='*60}")
    
    # Calculate annualized return
    days_traded = 252
    years = days_traded / 252
    best_annual_return = (1 + best_strategy[1]['total_return']) ** (1/years) - 1
    logger.info(f"\nAnnualized Return: {best_annual_return * 100:.2f}%")
    logger.info(f"Monthly Return (average): {best_annual_return / 12 * 100:.2f}%")
    
    logger.info("\n" + "="*60)
    logger.info("Backtest Complete!")
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    results = run_backtest()
