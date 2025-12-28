#!/usr/bin/env python3
"""
Simple demo script showing basic system capabilities.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime

from src.analytics.greeks import GreeksCalculator
from src.analytics.pricing import BlackScholesModel
from src.analytics.scenarios import ScenarioEngine
from src.analytics.volatility_surface import VolatilitySurface
from src.data.feeds.base_feed import SimulatedFeed
from src.data.instrument_master import InstrumentMaster, OptionInstrument
from src.data.market_data import MarketDataManager
from src.utils.logging import get_logger


def main():
    """Run demo."""
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("Options Trading System Demo")
    logger.info("=" * 60)
    
    # 1. Setup market data
    logger.info("\n1. Setting up market data feed...")
    feed = SimulatedFeed()
    feed.connect()
    
    market_data = MarketDataManager()
    market_data.add_feed("sim", feed)
    
    # Inject some sample quotes
    feed.inject_quote("SPY", bid=450.0, ask=450.2)
    feed.inject_quote("AAPL", bid=180.0, ask=180.1)
    
    logger.info("Market data setup complete")
    
    # 2. Setup instrument master
    logger.info("\n2. Setting up instrument master...")
    instrument_master = InstrumentMaster()
    
    # Add sample options
    expiry = datetime(2024, 6, 21)
    for strike in [440, 445, 450, 455, 460]:
        for opt_type in ['call', 'put']:
            symbol = instrument_master.build_option_symbol('SPY', expiry, strike, opt_type)
            instrument = OptionInstrument(
                symbol=symbol,
                underlying='SPY',
                strike=strike,
                expiry=expiry,
                option_type=opt_type
            )
            instrument_master.add_instrument(instrument)
    
    logger.info(f"Loaded {len(instrument_master.instruments)} instruments")
    
    # 3. Calculate option prices and Greeks
    logger.info("\n3. Calculating option prices and Greeks...")
    model = BlackScholesModel()
    
    params = {
        'spot': 450.0,
        'strike': 455.0,
        'time_to_expiry': 0.25,
        'volatility': 0.20,
        'risk_free_rate': 0.05,
        'dividend_yield': 0.02,
        'option_type': 'call'
    }
    
    price = model.price(**params)
    greeks = model.greeks(**params)
    
    logger.info(f"Call option price: ${price:.2f}")
    logger.info(f"Greeks: Delta={greeks['delta']:.4f}, Gamma={greeks['gamma']:.4f}, "
                f"Theta={greeks['theta']:.4f}, Vega={greeks['vega']:.4f}")
    
    # 4. Build volatility surface
    logger.info("\n4. Building volatility surface...")
    surface = VolatilitySurface(underlying='SPY', spot_price=450.0)
    
    # Add sample data points
    for strike in [440, 445, 450, 455, 460]:
        for tte in [0.1, 0.25, 0.5]:
            vol = 0.20 + (strike - 450) * 0.001 + tte * 0.02
            surface.add_data_point(
                strike=strike,
                time_to_expiry=tte,
                implied_vol=vol,
                option_type='call',
                bid=5.0,
                ask=5.2,
                volume=100
            )
    
    if surface.build_surface():
        logger.info("Volatility surface built successfully")
        logger.info(f"Surface quality score: {surface.quality_score:.2f}")
        
        # Get interpolated volatility
        vol = surface.get_volatility(strike=452.5, time_to_expiry=0.3)
        if vol:
            logger.info(f"Interpolated IV at K=452.5, T=0.3: {vol:.4f}")
    
    # 5. Portfolio Greeks calculation
    logger.info("\n5. Calculating portfolio Greeks...")
    calculator = GreeksCalculator()
    
    positions = [
        {
            'spot': 450.0,
            'strike': 455.0,
            'time_to_expiry': 0.25,
            'volatility': 0.20,
            'risk_free_rate': 0.05,
            'dividend_yield': 0.02,
            'option_type': 'call',
            'quantity': 10
        },
        {
            'spot': 450.0,
            'strike': 445.0,
            'time_to_expiry': 0.25,
            'volatility': 0.22,
            'risk_free_rate': 0.05,
            'dividend_yield': 0.02,
            'option_type': 'put',
            'quantity': -5
        }
    ]
    
    portfolio_greeks = calculator.aggregate_portfolio_greeks(positions)
    logger.info(f"Portfolio Greeks:")
    for greek, value in portfolio_greeks.items():
        logger.info(f"  {greek}: {value:.4f}")
    
    # 6. Stress testing
    logger.info("\n6. Running stress tests...")
    engine = ScenarioEngine()
    
    stress_results = engine.stress_test(positions)
    logger.info(f"Stress test scenarios completed: {len(stress_results)}")
    
    for result in stress_results[:3]:  # Show first 3
        logger.info(f"  {result['scenario_name']}: P&L = ${result['pnl_change']:.2f} "
                   f"({result['pnl_pct']:.2f}%)")
    
    # 7. VaR calculation
    logger.info("\n7. Calculating Value at Risk...")
    var_results = engine.calculate_var(positions, confidence_level=0.95, num_simulations=1000)
    logger.info(f"95% VaR: ${var_results['var']:.2f}")
    logger.info(f"95% CVaR: ${var_results['cvar']:.2f}")
    logger.info(f"Expected P&L: ${var_results['expected_pnl']:.2f}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Demo completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
