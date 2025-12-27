"""
Tests for Black-Scholes pricing model.
"""
import pytest

from src.analytics.pricing import BlackScholesModel


class TestBlackScholesModel:
    """Test Black-Scholes pricing and Greeks."""
    
    def test_call_option_price(self, sample_option_params):
        """Test call option pricing."""
        price = BlackScholesModel.price(**sample_option_params)
        
        # Price should be positive
        assert price > 0
        
        # Price should be less than spot (for reasonable parameters)
        assert price < sample_option_params['spot']
    
    def test_put_option_price(self, sample_option_params):
        """Test put option pricing."""
        params = sample_option_params.copy()
        params['option_type'] = 'put'
        
        price = BlackScholesModel.price(**params)
        
        # Price should be positive
        assert price > 0
    
    def test_put_call_parity(self, sample_option_params):
        """Test put-call parity relationship."""
        call_price = BlackScholesModel.price(**sample_option_params)
        
        params = sample_option_params.copy()
        params['option_type'] = 'put'
        put_price = BlackScholesModel.price(**params)
        
        # Put-call parity: C - P = S - K * exp(-r*T)
        spot = params['spot']
        strike = params['strike']
        r = params['risk_free_rate']
        T = params['time_to_expiry']
        q = params['dividend_yield']
        
        import numpy as np
        
        lhs = call_price - put_price
        rhs = spot * np.exp(-q * T) - strike * np.exp(-r * T)
        
        # Should be approximately equal
        assert abs(lhs - rhs) < 0.01
    
    def test_greeks_calculation(self, sample_option_params):
        """Test Greeks calculation."""
        greeks = BlackScholesModel.greeks(**sample_option_params)
        
        # Check all Greeks are present
        assert 'delta' in greeks
        assert 'gamma' in greeks
        assert 'theta' in greeks
        assert 'vega' in greeks
        assert 'rho' in greeks
        
        # Delta should be between 0 and 1 for call
        assert 0 <= greeks['delta'] <= 1
        
        # Gamma should be positive
        assert greeks['gamma'] >= 0
        
        # Vega should be positive
        assert greeks['vega'] >= 0
    
    def test_at_expiry_call(self, sample_option_params):
        """Test call option value at expiry."""
        params = sample_option_params.copy()
        params['time_to_expiry'] = 0.0
        
        price = BlackScholesModel.price(**params)
        
        # At expiry, call value is max(S - K, 0)
        intrinsic = max(0, params['spot'] - params['strike'])
        assert abs(price - intrinsic) < 0.01
    
    def test_implied_volatility(self, sample_option_params):
        """Test implied volatility calculation."""
        # Calculate a price
        true_vol = sample_option_params['volatility']
        market_price = BlackScholesModel.price(**sample_option_params)
        
        # Calculate implied vol
        params = sample_option_params.copy()
        implied_vol = BlackScholesModel.implied_volatility(
            market_price=market_price,
            spot=params['spot'],
            strike=params['strike'],
            time_to_expiry=params['time_to_expiry'],
            risk_free_rate=params['risk_free_rate'],
            dividend_yield=params['dividend_yield'],
            option_type=params['option_type']
        )
        
        # Should recover the original volatility
        assert abs(implied_vol - true_vol) < 0.01
