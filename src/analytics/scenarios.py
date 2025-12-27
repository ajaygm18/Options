"""
Scenario analysis and stress testing for options portfolios.
"""
from typing import Dict, List, Optional

import numpy as np

from .greeks import GreeksCalculator
from .pricing import BlackScholesModel


class ScenarioEngine:
    """Scenario analysis and stress testing engine."""
    
    def __init__(self, pricing_model=None):
        """
        Initialize scenario engine.
        
        Args:
            pricing_model: Pricing model to use (default: BlackScholesModel)
        """
        self.pricing_model = pricing_model or BlackScholesModel()
        self.greeks_calculator = GreeksCalculator(pricing_model)
    
    def price_scenario(
        self,
        positions: List[Dict],
        spot_shock: float = 0.0,
        vol_shock: float = 0.0,
        time_decay_days: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate portfolio value and Greeks under a scenario.
        
        Args:
            positions: List of position dictionaries
            spot_shock: Percentage change in spot price (e.g., -0.05 for -5%)
            vol_shock: Absolute change in volatility (e.g., 0.1 for +10 vol points)
            time_decay_days: Days of time decay
        
        Returns:
            Dictionary with scenario results
        """
        total_value = 0.0
        
        for position in positions:
            spot = position['spot']
            volatility = position['volatility']
            time_to_expiry = position['time_to_expiry']
            
            # Apply shocks
            shocked_spot = spot * (1 + spot_shock)
            shocked_vol = max(0.01, volatility + vol_shock)
            shocked_time = max(0.0, time_to_expiry - time_decay_days / 365.0)
            
            # Price the option under scenario
            price = self.pricing_model.price(
                spot=shocked_spot,
                strike=position['strike'],
                time_to_expiry=shocked_time,
                volatility=shocked_vol,
                risk_free_rate=position['risk_free_rate'],
                dividend_yield=position.get('dividend_yield', 0.0),
                option_type=position['option_type']
            )
            
            total_value += price * position['quantity']
        
        # Calculate Greeks under scenario
        scenario_positions = []
        for position in positions:
            scenario_position = position.copy()
            scenario_position['spot'] = position['spot'] * (1 + spot_shock)
            scenario_position['volatility'] = max(0.01, position['volatility'] + vol_shock)
            scenario_position['time_to_expiry'] = max(
                0.0, position['time_to_expiry'] - time_decay_days / 365.0
            )
            scenario_positions.append(scenario_position)
        
        greeks = self.greeks_calculator.aggregate_portfolio_greeks(scenario_positions)
        
        return {
            'portfolio_value': total_value,
            **greeks
        }
    
    def stress_test(
        self,
        positions: List[Dict],
        scenarios: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Run multiple stress test scenarios.
        
        Args:
            positions: List of position dictionaries
            scenarios: List of scenario dictionaries with shocks
                      If None, uses default stress scenarios
        
        Returns:
            List of scenario results
        """
        if scenarios is None:
            scenarios = self._default_stress_scenarios()
        
        results = []
        
        # Calculate base case
        base_result = self.price_scenario(positions)
        base_value = base_result['portfolio_value']
        
        for scenario in scenarios:
            result = self.price_scenario(
                positions,
                spot_shock=scenario.get('spot_shock', 0.0),
                vol_shock=scenario.get('vol_shock', 0.0),
                time_decay_days=scenario.get('time_decay_days', 0.0)
            )
            
            pnl_change = result['portfolio_value'] - base_value
            pnl_pct = (pnl_change / abs(base_value) * 100) if base_value != 0 else 0.0
            
            results.append({
                'scenario_name': scenario.get('name', 'Unnamed'),
                'spot_shock': scenario.get('spot_shock', 0.0),
                'vol_shock': scenario.get('vol_shock', 0.0),
                'time_decay_days': scenario.get('time_decay_days', 0.0),
                'portfolio_value': result['portfolio_value'],
                'pnl_change': pnl_change,
                'pnl_pct': pnl_pct,
                'greeks': {k: v for k, v in result.items() if k != 'portfolio_value'}
            })
        
        return results
    
    def _default_stress_scenarios(self) -> List[Dict]:
        """Define default stress test scenarios."""
        return [
            {
                'name': 'Market Crash -10%',
                'spot_shock': -0.10,
                'vol_shock': 0.15
            },
            {
                'name': 'Market Crash -20%',
                'spot_shock': -0.20,
                'vol_shock': 0.25
            },
            {
                'name': 'Market Rally +10%',
                'spot_shock': 0.10,
                'vol_shock': -0.05
            },
            {
                'name': 'Volatility Spike',
                'spot_shock': 0.0,
                'vol_shock': 0.20
            },
            {
                'name': 'Volatility Collapse',
                'spot_shock': 0.0,
                'vol_shock': -0.15
            },
            {
                'name': 'Time Decay 1 Day',
                'spot_shock': 0.0,
                'vol_shock': 0.0,
                'time_decay_days': 1.0
            },
            {
                'name': 'Time Decay 7 Days',
                'spot_shock': 0.0,
                'vol_shock': 0.0,
                'time_decay_days': 7.0
            },
            {
                'name': 'Crash + Vol Spike',
                'spot_shock': -0.15,
                'vol_shock': 0.20
            },
        ]
    
    def calculate_var(
        self,
        positions: List[Dict],
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        holding_period_days: int = 1
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk using Monte Carlo simulation.
        
        Args:
            positions: List of position dictionaries
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            num_simulations: Number of Monte Carlo paths
            holding_period_days: Holding period in days
        
        Returns:
            Dictionary with VaR and CVaR
        """
        # Calculate base portfolio value
        base_result = self.price_scenario(positions)
        base_value = base_result['portfolio_value']
        
        # Estimate volatility from positions (weighted average)
        total_notional = sum(abs(p['spot'] * p['quantity']) for p in positions)
        if total_notional == 0:
            return {'var': 0.0, 'cvar': 0.0}
        
        avg_vol = sum(
            p['volatility'] * abs(p['spot'] * p['quantity']) / total_notional
            for p in positions
        )
        
        # Generate random price shocks
        dt = holding_period_days / 252.0  # Trading days in a year
        daily_vol = avg_vol * np.sqrt(dt)
        
        price_shocks = np.random.normal(0, daily_vol, num_simulations)
        
        # Calculate portfolio values under each shock
        portfolio_values = []
        for shock in price_shocks:
            # Also shock volatility (correlated with price moves)
            vol_shock = -shock * 0.5  # Negative correlation
            
            result = self.price_scenario(
                positions,
                spot_shock=shock,
                vol_shock=vol_shock,
                time_decay_days=holding_period_days
            )
            
            portfolio_values.append(result['portfolio_value'])
        
        portfolio_values = np.array(portfolio_values)
        pnl_changes = portfolio_values - base_value
        
        # Calculate VaR (loss at confidence level)
        var_percentile = (1 - confidence_level) * 100
        var = -np.percentile(pnl_changes, var_percentile)
        
        # Calculate CVaR (expected loss beyond VaR)
        losses = -pnl_changes[pnl_changes < -var]
        cvar = losses.mean() if len(losses) > 0 else var
        
        return {
            'var': float(var),
            'cvar': float(cvar),
            'worst_case': float(-pnl_changes.min()),
            'best_case': float(-pnl_changes.max()),
            'expected_pnl': float(pnl_changes.mean())
        }
    
    def scenario_heatmap(
        self,
        positions: List[Dict],
        spot_shocks: List[float],
        vol_shocks: List[float]
    ) -> np.ndarray:
        """
        Create a heatmap of P&L across spot and vol shocks.
        
        Args:
            positions: List of position dictionaries
            spot_shocks: List of spot price shocks (e.g., [-0.1, -0.05, 0, 0.05, 0.1])
            vol_shocks: List of volatility shocks (e.g., [-0.1, 0, 0.1, 0.2])
        
        Returns:
            2D array of P&L values
        """
        base_result = self.price_scenario(positions)
        base_value = base_result['portfolio_value']
        
        heatmap = np.zeros((len(vol_shocks), len(spot_shocks)))
        
        for i, vol_shock in enumerate(vol_shocks):
            for j, spot_shock in enumerate(spot_shocks):
                result = self.price_scenario(
                    positions,
                    spot_shock=spot_shock,
                    vol_shock=vol_shock
                )
                pnl = result['portfolio_value'] - base_value
                heatmap[i, j] = pnl
        
        return heatmap
