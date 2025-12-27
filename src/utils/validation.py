"""
Input validation utilities.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class OrderValidation(BaseModel):
    """Validation for order parameters."""
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    
    @validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        """Validate symbol format."""
        return v.upper().strip()


class PositionValidation(BaseModel):
    """Validation for position parameters."""
    symbol: str = Field(..., min_length=1)
    quantity: int = Field(...)
    average_price: float = Field(..., gt=0)


class RiskLimitsValidation(BaseModel):
    """Validation for risk limits."""
    max_position_size: int = Field(..., gt=0)
    max_notional: float = Field(..., gt=0)
    max_daily_loss: float = Field(..., gt=0)
    max_margin_utilization: float = Field(..., gt=0, le=1.0)


def validate_price(price: float) -> bool:
    """Validate that price is positive and reasonable."""
    if price <= 0:
        return False
    if price > 1e6:  # Sanity check
        return False
    return True


def validate_quantity(quantity: int) -> bool:
    """Validate that quantity is positive."""
    return quantity > 0


def validate_greeks(greeks: Dict[str, float]) -> bool:
    """Validate Greek values are within reasonable ranges."""
    if "delta" in greeks and abs(greeks["delta"]) > 1.0:
        return False
    if "gamma" in greeks and greeks["gamma"] < 0:
        return False
    return True


def validate_volatility(vol: float) -> bool:
    """Validate volatility is within reasonable range."""
    return 0.0 < vol < 5.0  # 0% to 500%


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate configuration dictionary.
    
    Returns:
        (is_valid, error_message)
    """
    for key in required_keys:
        if key not in config:
            return False, f"Missing required config key: {key}"
    return True, None


def sanitize_symbol(symbol: str) -> str:
    """Sanitize symbol string."""
    return symbol.upper().strip()


def validate_symbol(symbol: str) -> bool:
    """Validate symbol format."""
    if not symbol:
        return False
    if len(symbol) > 20:
        return False
    # Allow alphanumeric and common option symbols
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
    return all(c in allowed_chars for c in symbol.upper())
