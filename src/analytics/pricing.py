"""
Options pricing models including Black-Scholes and binomial trees.
"""
import math
from typing import Dict

import numpy as np
from scipy.stats import norm

from ..core.constants import (
    GREEK_DELTA,
    GREEK_GAMMA,
    GREEK_RHO,
    GREEK_THETA,
    GREEK_VEGA,
    OPTION_TYPE_CALL,
    OPTION_TYPE_PUT,
)


class BlackScholesModel:
    """Black-Scholes option pricing model for European options."""
    
    @staticmethod
    def price(
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        option_type: str = OPTION_TYPE_CALL
    ) -> float:
        """
        Calculate option price using Black-Scholes formula.
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Annualized volatility (sigma)
            risk_free_rate: Risk-free interest rate
            dividend_yield: Continuous dividend yield
            option_type: 'call' or 'put'
        
        Returns:
            Option price
        """
        if time_to_expiry <= 0:
            # At expiry, option value is intrinsic value
            if option_type == OPTION_TYPE_CALL:
                return max(0.0, spot - strike)
            else:
                return max(0.0, strike - spot)
        
        d1, d2 = BlackScholesModel._calculate_d1_d2(
            spot, strike, time_to_expiry, volatility, risk_free_rate, dividend_yield
        )
        
        if option_type == OPTION_TYPE_CALL:
            price = (
                spot * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
                - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            )
        else:  # put
            price = (
                strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
                - spot * np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
            )
        
        return float(price)
    
    @staticmethod
    def greeks(
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        option_type: str = OPTION_TYPE_CALL
    ) -> Dict[str, float]:
        """
        Calculate option Greeks using Black-Scholes formula.
        
        Returns:
            Dictionary with delta, gamma, theta, vega, rho
        """
        if time_to_expiry <= 0:
            return {
                GREEK_DELTA: 0.0,
                GREEK_GAMMA: 0.0,
                GREEK_THETA: 0.0,
                GREEK_VEGA: 0.0,
                GREEK_RHO: 0.0,
            }
        
        d1, d2 = BlackScholesModel._calculate_d1_d2(
            spot, strike, time_to_expiry, volatility, risk_free_rate, dividend_yield
        )
        
        # Delta
        if option_type == OPTION_TYPE_CALL:
            delta = np.exp(-dividend_yield * time_to_expiry) * norm.cdf(d1)
        else:
            delta = -np.exp(-dividend_yield * time_to_expiry) * norm.cdf(-d1)
        
        # Gamma (same for calls and puts)
        gamma = (
            np.exp(-dividend_yield * time_to_expiry) * norm.pdf(d1)
            / (spot * volatility * np.sqrt(time_to_expiry))
        )
        
        # Vega (same for calls and puts)
        vega = (
            spot * np.exp(-dividend_yield * time_to_expiry)
            * norm.pdf(d1) * np.sqrt(time_to_expiry) / 100  # Per 1% vol change
        )
        
        # Theta
        term1 = -(
            spot * norm.pdf(d1) * volatility * np.exp(-dividend_yield * time_to_expiry)
            / (2 * np.sqrt(time_to_expiry))
        )
        
        if option_type == OPTION_TYPE_CALL:
            term2 = (
                -risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry)
                * norm.cdf(d2)
            )
            term3 = (
                dividend_yield * spot * np.exp(-dividend_yield * time_to_expiry)
                * norm.cdf(d1)
            )
            theta = (term1 + term2 + term3) / 365  # Per day
        else:
            term2 = (
                risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry)
                * norm.cdf(-d2)
            )
            term3 = (
                -dividend_yield * spot * np.exp(-dividend_yield * time_to_expiry)
                * norm.cdf(-d1)
            )
            theta = (term1 + term2 + term3) / 365  # Per day
        
        # Rho
        if option_type == OPTION_TYPE_CALL:
            rho = (
                strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry)
                * norm.cdf(d2) / 100  # Per 1% rate change
            )
        else:
            rho = (
                -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry)
                * norm.cdf(-d2) / 100
            )
        
        return {
            GREEK_DELTA: float(delta),
            GREEK_GAMMA: float(gamma),
            GREEK_THETA: float(theta),
            GREEK_VEGA: float(vega),
            GREEK_RHO: float(rho),
        }
    
    @staticmethod
    def implied_volatility(
        market_price: float,
        spot: float,
        strike: float,
        time_to_expiry: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        option_type: str = OPTION_TYPE_CALL,
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> float:
        """
        Calculate implied volatility using Newton-Raphson method.
        
        Returns:
            Implied volatility (annualized)
        """
        # Initial guess
        vol = 0.3
        
        for _ in range(max_iterations):
            price = BlackScholesModel.price(
                spot, strike, time_to_expiry, vol, risk_free_rate, dividend_yield, option_type
            )
            
            diff = market_price - price
            
            if abs(diff) < tolerance:
                return vol
            
            # Vega for Newton-Raphson iteration
            greeks = BlackScholesModel.greeks(
                spot, strike, time_to_expiry, vol, risk_free_rate, dividend_yield, option_type
            )
            vega = greeks[GREEK_VEGA] * 100  # Convert back to full vega
            
            if vega < 1e-10:
                break
            
            vol = vol + diff / vega
            
            # Keep volatility in reasonable range
            vol = max(0.01, min(5.0, vol))
        
        return vol
    
    @staticmethod
    def _calculate_d1_d2(
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float
    ) -> tuple[float, float]:
        """Calculate d1 and d2 for Black-Scholes formula."""
        d1 = (
            np.log(spot / strike)
            + (risk_free_rate - dividend_yield + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * np.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        return float(d1), float(d2)


class BinomialTreeModel:
    """Binomial tree model for American options."""
    
    @staticmethod
    def price(
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float = 0.0,
        option_type: str = OPTION_TYPE_CALL,
        steps: int = 100
    ) -> float:
        """
        Calculate American option price using binomial tree.
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Annualized volatility
            risk_free_rate: Risk-free interest rate
            dividend_yield: Continuous dividend yield
            option_type: 'call' or 'put'
            steps: Number of time steps in the tree
        
        Returns:
            Option price
        """
        dt = time_to_expiry / steps
        u = np.exp(volatility * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((risk_free_rate - dividend_yield) * dt) - d) / (u - d)
        discount = np.exp(-risk_free_rate * dt)
        
        # Initialize asset prices at maturity
        asset_prices = np.zeros(steps + 1)
        for i in range(steps + 1):
            asset_prices[i] = spot * (u ** (steps - i)) * (d ** i)
        
        # Initialize option values at maturity
        option_values = np.zeros(steps + 1)
        for i in range(steps + 1):
            if option_type == OPTION_TYPE_CALL:
                option_values[i] = max(0.0, asset_prices[i] - strike)
            else:
                option_values[i] = max(0.0, strike - asset_prices[i])
        
        # Backward induction
        for step in range(steps - 1, -1, -1):
            for i in range(step + 1):
                # European value
                hold_value = discount * (p * option_values[i] + (1 - p) * option_values[i + 1])
                
                # Early exercise value
                asset_price = spot * (u ** (step - i)) * (d ** i)
                if option_type == OPTION_TYPE_CALL:
                    exercise_value = max(0.0, asset_price - strike)
                else:
                    exercise_value = max(0.0, strike - asset_price)
                
                # American option: max of hold and exercise
                option_values[i] = max(hold_value, exercise_value)
        
        return float(option_values[0])
