"""
Greeks calculator for options portfolios.
"""
from typing import Dict, List

import numpy as np

from ..core.constants import (
    GREEK_DELTA,
    GREEK_GAMMA,
    GREEK_RHO,
    GREEK_THETA,
    GREEK_VEGA,
)
from .pricing import BlackScholesModel


class GreeksCalculator:
    """Calculate and aggregate Greeks for options portfolios."""
    
    def __init__(self, pricing_model=None):
        """
        Initialize Greeks calculator.
        
        Args:
            pricing_model: Pricing model to use (default: BlackScholesModel)
        """
        self.pricing_model = pricing_model or BlackScholesModel()
    
    def calculate_position_greeks(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        dividend_yield: float,
        option_type: str,
        quantity: int
    ) -> Dict[str, float]:
        """
        Calculate Greeks for a single position.
        
        Args:
            spot: Current spot price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            risk_free_rate: Risk-free rate
            dividend_yield: Dividend yield
            option_type: 'call' or 'put'
            quantity: Position size (positive for long, negative for short)
        
        Returns:
            Dictionary with position Greeks
        """
        greeks = self.pricing_model.greeks(
            spot=spot,
            strike=strike,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=option_type
        )
        
        # Scale by position size
        return {
            greek: value * quantity
            for greek, value in greeks.items()
        }
    
    def aggregate_portfolio_greeks(
        self,
        positions: List[Dict]
    ) -> Dict[str, float]:
        """
        Aggregate Greeks across a portfolio of positions.
        
        Args:
            positions: List of position dictionaries, each containing:
                - spot: float
                - strike: float
                - time_to_expiry: float
                - volatility: float
                - risk_free_rate: float
                - dividend_yield: float
                - option_type: str
                - quantity: int
        
        Returns:
            Dictionary with portfolio-level Greeks
        """
        portfolio_greeks = {
            GREEK_DELTA: 0.0,
            GREEK_GAMMA: 0.0,
            GREEK_THETA: 0.0,
            GREEK_VEGA: 0.0,
            GREEK_RHO: 0.0,
        }
        
        for position in positions:
            position_greeks = self.calculate_position_greeks(**position)
            
            for greek in portfolio_greeks:
                portfolio_greeks[greek] += position_greeks.get(greek, 0.0)
        
        return portfolio_greeks
    
    def calculate_greeks_by_underlying(
        self,
        positions: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate Greeks by underlying symbol.
        
        Args:
            positions: List of position dictionaries with 'underlying' field
        
        Returns:
            Dictionary mapping underlying -> Greeks
        """
        greeks_by_underlying = {}
        
        for position in positions:
            underlying = position.get('underlying', 'UNKNOWN')
            
            if underlying not in greeks_by_underlying:
                greeks_by_underlying[underlying] = {
                    GREEK_DELTA: 0.0,
                    GREEK_GAMMA: 0.0,
                    GREEK_THETA: 0.0,
                    GREEK_VEGA: 0.0,
                    GREEK_RHO: 0.0,
                }
            
            position_greeks = self.calculate_position_greeks(
                spot=position['spot'],
                strike=position['strike'],
                time_to_expiry=position['time_to_expiry'],
                volatility=position['volatility'],
                risk_free_rate=position['risk_free_rate'],
                dividend_yield=position.get('dividend_yield', 0.0),
                option_type=position['option_type'],
                quantity=position['quantity']
            )
            
            for greek in greeks_by_underlying[underlying]:
                greeks_by_underlying[underlying][greek] += position_greeks.get(greek, 0.0)
        
        return greeks_by_underlying
    
    def calculate_dollar_greeks(
        self,
        greeks: Dict[str, float],
        spot: float
    ) -> Dict[str, float]:
        """
        Convert Greeks to dollar values.
        
        Args:
            greeks: Dictionary of Greeks
            spot: Current spot price
        
        Returns:
            Dictionary with dollar Greeks
        """
        return {
            f"{greek}_dollar": value * spot / 100  # Per 1% move
            for greek, value in greeks.items()
        }
    
    def estimate_pnl_change(
        self,
        greeks: Dict[str, float],
        spot_change: float = 0.0,
        vol_change: float = 0.0,
        time_decay_days: float = 0.0
    ) -> float:
        """
        Estimate P&L change from Greeks.
        
        Args:
            greeks: Portfolio Greeks
            spot_change: Change in spot price
            vol_change: Change in volatility (in percentage points)
            time_decay_days: Time decay in days
        
        Returns:
            Estimated P&L change
        """
        pnl_change = 0.0
        
        # Delta contribution
        pnl_change += greeks[GREEK_DELTA] * spot_change
        
        # Gamma contribution (second order)
        pnl_change += 0.5 * greeks[GREEK_GAMMA] * (spot_change ** 2)
        
        # Vega contribution
        pnl_change += greeks[GREEK_VEGA] * vol_change
        
        # Theta contribution
        pnl_change += greeks[GREEK_THETA] * time_decay_days
        
        return pnl_change


def calculate_hedge_ratio(
    portfolio_delta: float,
    target_delta: float = 0.0
) -> int:
    """
    Calculate number of shares needed to hedge delta.
    
    Args:
        portfolio_delta: Current portfolio delta
        target_delta: Target delta (default: 0 for delta-neutral)
    
    Returns:
        Number of shares to buy/sell (positive = buy, negative = sell)
    """
    return -int(portfolio_delta - target_delta)
