"""
pytest configuration and fixtures.
"""
import pytest

from src.analytics.greeks import GreeksCalculator
from src.analytics.pricing import BlackScholesModel
from src.data.feeds.base_feed import SimulatedFeed
from src.data.historical import HistoricalDataHandler
from src.data.instrument_master import InstrumentMaster
from src.data.market_data import MarketDataManager


@pytest.fixture
def black_scholes_model():
    """Black-Scholes pricing model fixture."""
    return BlackScholesModel()


@pytest.fixture
def greeks_calculator():
    """Greeks calculator fixture."""
    return GreeksCalculator()


@pytest.fixture
def simulated_feed():
    """Simulated market data feed fixture."""
    feed = SimulatedFeed()
    feed.connect()
    return feed


@pytest.fixture
def market_data_manager():
    """Market data manager fixture."""
    return MarketDataManager()


@pytest.fixture
def instrument_master():
    """Instrument master fixture."""
    return InstrumentMaster()


@pytest.fixture
def historical_data_handler():
    """Historical data handler fixture."""
    return HistoricalDataHandler()


@pytest.fixture
def sample_option_params():
    """Sample option parameters for testing."""
    return {
        'spot': 100.0,
        'strike': 105.0,
        'time_to_expiry': 0.25,  # 3 months
        'volatility': 0.25,  # 25% annualized
        'risk_free_rate': 0.05,  # 5%
        'dividend_yield': 0.0,
        'option_type': 'call'
    }


@pytest.fixture
def sample_positions():
    """Sample positions for portfolio testing."""
    return [
        {
            'underlying': 'SPY',
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
            'underlying': 'SPY',
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
