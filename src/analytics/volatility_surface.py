"""
Volatility surface construction and management.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.interpolate import RectBivariateSpline, griddata

from ..core.constants import (
    MAX_MONEYNESS,
    MAX_TIME_TO_EXPIRY,
    MIN_LIQUIDITY_SCORE,
    MIN_MONEYNESS,
    MIN_TIME_TO_EXPIRY,
)


class VolatilitySurface:
    """
    Implied volatility surface construction and interpolation.
    
    The surface is parameterized by:
    - Time to expiry (years)
    - Moneyness (strike / spot)
    """
    
    def __init__(
        self,
        underlying: str,
        spot_price: float,
        min_liquidity_score: float = MIN_LIQUIDITY_SCORE,
        check_arbitrage: bool = True
    ):
        """
        Initialize volatility surface.
        
        Args:
            underlying: Underlying symbol
            spot_price: Current spot price
            min_liquidity_score: Minimum liquidity score to include data point
            check_arbitrage: Whether to check for arbitrage violations
        """
        self.underlying = underlying
        self.spot_price = spot_price
        self.min_liquidity_score = min_liquidity_score
        self.check_arbitrage = check_arbitrage
        
        # Raw data points
        self.data_points: List[Dict] = []
        
        # Interpolation function
        self.surface_func: Optional[RectBivariateSpline] = None
        
        # Quality metrics
        self.quality_score: float = 0.0
    
    def add_data_point(
        self,
        strike: float,
        time_to_expiry: float,
        implied_vol: float,
        option_type: str,
        bid: float,
        ask: float,
        volume: int = 0,
        open_interest: int = 0
    ) -> None:
        """
        Add a data point to the surface.
        
        Args:
            strike: Strike price
            time_to_expiry: Time to expiry in years
            implied_vol: Implied volatility
            option_type: 'call' or 'put'
            bid: Bid price
            ask: Ask price
            volume: Trading volume
            open_interest: Open interest
        """
        moneyness = strike / self.spot_price
        spread = ask - bid
        mid_price = (bid + ask) / 2.0
        
        # Calculate liquidity score
        liquidity_score = self._calculate_liquidity_score(
            spread, mid_price, volume, open_interest
        )
        
        if liquidity_score >= self.min_liquidity_score:
            self.data_points.append({
                'strike': strike,
                'moneyness': moneyness,
                'time_to_expiry': time_to_expiry,
                'implied_vol': implied_vol,
                'option_type': option_type,
                'liquidity_score': liquidity_score,
                'spread': spread,
                'volume': volume,
                'open_interest': open_interest
            })
    
    def build_surface(
        self,
        smoothing_method: str = "cubic_spline"
    ) -> bool:
        """
        Build the volatility surface from data points.
        
        Args:
            smoothing_method: Interpolation method ('cubic_spline' or 'rbf')
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.data_points) < 4:
            # Need at least 4 points for surface fitting
            return False
        
        # Extract data
        moneyness = np.array([p['moneyness'] for p in self.data_points])
        time_to_expiry = np.array([p['time_to_expiry'] for p in self.data_points])
        implied_vol = np.array([p['implied_vol'] for p in self.data_points])
        weights = np.array([p['liquidity_score'] for p in self.data_points])
        
        # Filter valid range
        valid_mask = (
            (moneyness >= MIN_MONEYNESS) &
            (moneyness <= MAX_MONEYNESS) &
            (time_to_expiry >= MIN_TIME_TO_EXPIRY) &
            (time_to_expiry <= MAX_TIME_TO_EXPIRY)
        )
        
        if valid_mask.sum() < 4:
            return False
        
        moneyness = moneyness[valid_mask]
        time_to_expiry = time_to_expiry[valid_mask]
        implied_vol = implied_vol[valid_mask]
        weights = weights[valid_mask]
        
        # Create regular grid for interpolation
        num_points_m = 20
        num_points_t = 20
        grid_moneyness = np.linspace(moneyness.min(), moneyness.max(), num_points_m)
        grid_time = np.linspace(time_to_expiry.min(), time_to_expiry.max(), num_points_t)
        
        # Interpolate to regular grid
        grid_m, grid_t = np.meshgrid(grid_moneyness, grid_time)
        points = np.column_stack([moneyness, time_to_expiry])
        grid_vol = griddata(
            points,
            implied_vol,
            (grid_m, grid_t),
            method='cubic',
            fill_value=implied_vol.mean()
        )
        
        # Create spline interpolator
        try:
            self.surface_func = RectBivariateSpline(
                grid_time[:, 0],
                grid_moneyness[0, :],
                grid_vol,
                kx=3,
                ky=3
            )
        except Exception:
            return False
        
        # Check arbitrage if enabled
        if self.check_arbitrage:
            has_arbitrage = self._check_arbitrage_violations()
            if has_arbitrage:
                self.quality_score *= 0.5  # Penalize quality
        
        # Calculate quality score
        self.quality_score = self._calculate_quality_score(
            moneyness, time_to_expiry, weights
        )
        
        return True
    
    def get_volatility(
        self,
        strike: float,
        time_to_expiry: float
    ) -> Optional[float]:
        """
        Get interpolated volatility for a given strike and time to expiry.
        
        Args:
            strike: Strike price
            time_to_expiry: Time to expiry in years
        
        Returns:
            Implied volatility or None if surface not built
        """
        if self.surface_func is None:
            return None
        
        moneyness = strike / self.spot_price
        
        try:
            vol = float(self.surface_func(time_to_expiry, moneyness)[0, 0])
            return max(0.01, min(5.0, vol))  # Clamp to reasonable range
        except Exception:
            return None
    
    def get_term_structure(
        self,
        strike: float,
        num_points: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get volatility term structure for a given strike.
        
        Returns:
            (times, volatilities) arrays
        """
        if self.surface_func is None:
            return np.array([]), np.array([])
        
        times = np.linspace(MIN_TIME_TO_EXPIRY, MAX_TIME_TO_EXPIRY, num_points)
        vols = np.array([self.get_volatility(strike, t) for t in times])
        
        return times, vols
    
    def get_skew(
        self,
        time_to_expiry: float,
        num_points: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get volatility skew for a given expiry.
        
        Returns:
            (strikes, volatilities) arrays
        """
        if self.surface_func is None:
            return np.array([]), np.array([])
        
        strikes = self.spot_price * np.linspace(MIN_MONEYNESS, MAX_MONEYNESS, num_points)
        vols = np.array([self.get_volatility(k, time_to_expiry) for k in strikes])
        
        return strikes, vols
    
    def _calculate_liquidity_score(
        self,
        spread: float,
        mid_price: float,
        volume: int,
        open_interest: int
    ) -> float:
        """Calculate liquidity score for a data point."""
        # Spread component (lower is better)
        spread_pct = spread / mid_price if mid_price > 0 else 1.0
        spread_score = max(0, 1.0 - spread_pct * 10)
        
        # Volume component (higher is better)
        volume_score = min(1.0, volume / 100.0)
        
        # Open interest component (higher is better)
        oi_score = min(1.0, open_interest / 1000.0)
        
        # Weighted average
        liquidity_score = (
            0.5 * spread_score +
            0.3 * volume_score +
            0.2 * oi_score
        )
        
        return liquidity_score
    
    def _calculate_quality_score(
        self,
        moneyness: np.ndarray,
        time_to_expiry: np.ndarray,
        weights: np.ndarray
    ) -> float:
        """Calculate overall surface quality score."""
        # Coverage score (how much of the surface is covered)
        moneyness_range = moneyness.max() - moneyness.min()
        time_range = time_to_expiry.max() - time_to_expiry.min()
        coverage_score = min(1.0, (moneyness_range * time_range) / 2.0)
        
        # Data density score
        num_points = len(moneyness)
        density_score = min(1.0, num_points / 50.0)
        
        # Average liquidity score
        avg_liquidity = weights.mean()
        
        # Combined quality score
        quality = (
            0.4 * coverage_score +
            0.3 * density_score +
            0.3 * avg_liquidity
        )
        
        return quality
    
    def _check_arbitrage_violations(self) -> bool:
        """Check for common arbitrage violations in the surface."""
        # This is a simplified check
        # In production, would check:
        # 1. Calendar arbitrage (forward vols must be positive)
        # 2. Vertical spread arbitrage
        # 3. Butterfly arbitrage
        
        # For now, just check if volatilities are positive
        for point in self.data_points:
            if point['implied_vol'] <= 0:
                return True
        
        return False
