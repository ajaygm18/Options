"""
Risk limits configuration and validation.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class RiskLimits(BaseModel):
    """Risk limits configuration."""
    
    # Position limits
    max_position_size: int = Field(100, gt=0, description="Maximum position size per symbol")
    max_notional_per_underlying: float = Field(
        100000, gt=0, description="Maximum notional per underlying"
    )
    max_portfolio_notional: float = Field(500000, gt=0, description="Maximum total notional")
    
    # Loss limits
    max_daily_loss: float = Field(10000, gt=0, description="Maximum daily loss")
    max_strategy_loss: float = Field(5000, gt=0, description="Maximum loss per strategy")
    
    # Greek limits
    max_delta_per_underlying: float = Field(500, description="Maximum delta per underlying")
    max_gamma_per_underlying: float = Field(100, gt=0, description="Maximum gamma")
    max_vega_per_underlying: float = Field(1000, gt=0, description="Maximum vega")
    max_theta_per_day: float = Field(-500, description="Maximum theta (negative)")
    max_portfolio_delta: float = Field(1000, description="Maximum portfolio delta")
    max_portfolio_gamma: float = Field(200, gt=0, description="Maximum portfolio gamma")
    max_portfolio_vega: float = Field(2000, gt=0, description="Maximum portfolio vega")
    
    # Margin and capital
    max_margin_utilization: float = Field(0.7, gt=0, le=1.0, description="Max margin usage")
    min_cash_balance: float = Field(10000, gt=0, description="Minimum cash balance")
    
    # Order limits
    max_order_value: float = Field(50000, gt=0, description="Maximum single order value")
    max_orders_per_second: int = Field(10, gt=0, description="Rate limit")
    
    # Concentration limits
    max_concentration_per_expiry: float = Field(
        0.3, gt=0, le=1.0, description="Max % in single expiry"
    )
    max_concentration_per_strike: float = Field(
        0.2, gt=0, le=1.0, description="Max % in single strike"
    )
    
    @validator('max_theta_per_day')
    def validate_theta(cls, v: float) -> float:
        """Theta should be negative (time decay is a cost)."""
        if v > 0:
            raise ValueError("max_theta_per_day should be negative")
        return v


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""
    
    enabled: bool = Field(True, description="Enable circuit breakers")
    
    # Drawdown thresholds
    drawdown_threshold: float = Field(
        0.05, gt=0, le=1.0, description="Drawdown % to trigger (e.g., 0.05 = 5%)"
    )
    
    # Data quality
    data_staleness_threshold_ms: int = Field(
        10000, gt=0, description="Max data age before stale"
    )
    
    # Execution quality
    broker_reject_rate_threshold: float = Field(
        0.3, gt=0, le=1.0, description="Reject rate % to trigger"
    )
    
    # Market conditions
    spread_multiplier_threshold: float = Field(
        3.0, gt=1.0, description="Spread vs average multiplier"
    )
    volatility_spike_threshold: float = Field(
        2.0, gt=1.0, description="Vol vs average multiplier"
    )
    
    # Recovery
    cooldown_period_s: int = Field(300, gt=0, description="Cooldown after trigger")
    auto_resume: bool = Field(False, description="Auto-resume after cooldown")


def load_risk_limits_from_config(config: Dict[str, Any]) -> RiskLimits:
    """Load risk limits from configuration dictionary."""
    limits_config = config.get('risk', {}).get('limits', {})
    return RiskLimits(**limits_config)


def load_circuit_breaker_config(config: Dict[str, Any]) -> CircuitBreakerConfig:
    """Load circuit breaker configuration."""
    cb_config = config.get('risk', {}).get('circuit_breakers', {})
    return CircuitBreakerConfig(**cb_config)


def validate_limits_consistency(limits: RiskLimits) -> tuple[bool, Optional[str]]:
    """
    Validate that risk limits are internally consistent.
    
    Returns:
        (is_valid, error_message)
    """
    # Portfolio limits should be >= individual limits
    if limits.max_portfolio_notional < limits.max_notional_per_underlying:
        return False, "Portfolio notional limit < per-underlying limit"
    
    if limits.max_portfolio_delta < abs(limits.max_delta_per_underlying):
        return False, "Portfolio delta limit < per-underlying delta limit"
    
    # Daily loss should be reasonable relative to capital
    if limits.max_daily_loss > limits.max_portfolio_notional * 0.5:
        return False, "Daily loss limit > 50% of portfolio notional"
    
    return True, None
