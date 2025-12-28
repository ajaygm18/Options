"""
Slippage models for backtesting.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..core.events import OrderSide, OrderType


class SlippageModel(ABC):
    """Base class for slippage models."""
    
    @abstractmethod
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """
        Calculate slippage for an order.
        
        Args:
            symbol: Symbol
            side: Buy or sell
            order_type: Order type
            quantity: Order quantity
            limit_price: Limit price (if limit order)
            bid: Current bid price
            ask: Current ask price
            bid_size: Bid size
            ask_size: Ask size
            volume: Recent volume
        
        Returns:
            Slippage amount (positive = worse price)
        """
        pass


class NoSlippage(SlippageModel):
    """No slippage - fill at mid price."""
    
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """No slippage."""
        return 0.0


class FixedSlippage(SlippageModel):
    """Fixed slippage per contract."""
    
    def __init__(self, slippage_per_contract: float = 0.01):
        """
        Initialize fixed slippage model.
        
        Args:
            slippage_per_contract: Fixed slippage amount per contract
        """
        self.slippage_per_contract = slippage_per_contract
    
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """Calculate fixed slippage."""
        return self.slippage_per_contract


class SpreadBasedSlippage(SlippageModel):
    """
    Slippage based on bid-ask spread.
    
    Market orders pay the spread.
    Limit orders have reduced slippage.
    """
    
    def __init__(self, market_order_spread_fraction: float = 0.5):
        """
        Initialize spread-based slippage.
        
        Args:
            market_order_spread_fraction: Fraction of spread paid for market orders
        """
        self.market_order_spread_fraction = market_order_spread_fraction
    
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """Calculate spread-based slippage."""
        spread = ask - bid
        mid = (bid + ask) / 2.0
        
        if order_type == OrderType.MARKET:
            # Market orders pay fraction of spread
            return spread * self.market_order_spread_fraction
        else:
            # Limit orders have less slippage
            return spread * 0.1  # 10% of spread


class VolumeBasedSlippage(SlippageModel):
    """
    Slippage based on order size relative to available liquidity.
    
    Larger orders relative to market depth incur more slippage.
    """
    
    def __init__(
        self,
        base_slippage: float = 0.01,
        impact_coefficient: float = 0.1
    ):
        """
        Initialize volume-based slippage.
        
        Args:
            base_slippage: Base slippage amount
            impact_coefficient: Coefficient for market impact
        """
        self.base_slippage = base_slippage
        self.impact_coefficient = impact_coefficient
    
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """Calculate volume-based slippage."""
        # Determine available liquidity
        if side == OrderSide.BUY:
            available_size = ask_size
        else:
            available_size = bid_size
        
        # Calculate impact based on order size vs available
        if available_size > 0:
            size_ratio = quantity / available_size
            impact = self.impact_coefficient * size_ratio
        else:
            impact = 0.5  # High impact if no size information
        
        spread = ask - bid
        mid = (bid + ask) / 2.0
        
        # Total slippage is base + impact-adjusted spread
        slippage = self.base_slippage + spread * impact
        
        return slippage


class RealisticSlippage(SlippageModel):
    """
    Realistic slippage model combining multiple factors.
    
    Considers:
    - Order type (market vs limit)
    - Order size vs market depth
    - Volatility (via spread)
    - Liquidity (via volume)
    """
    
    def __init__(self):
        """Initialize realistic slippage model."""
        self.spread_model = SpreadBasedSlippage()
        self.volume_model = VolumeBasedSlippage()
    
    def calculate_slippage(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: int,
        limit_price: Optional[float],
        bid: float,
        ask: float,
        bid_size: int,
        ask_size: int,
        volume: int
    ) -> float:
        """Calculate realistic slippage."""
        spread_slippage = self.spread_model.calculate_slippage(
            symbol, side, order_type, quantity, limit_price,
            bid, ask, bid_size, ask_size, volume
        )
        
        volume_slippage = self.volume_model.calculate_slippage(
            symbol, side, order_type, quantity, limit_price,
            bid, ask, bid_size, ask_size, volume
        )
        
        # Combine slippages (weighted average)
        total_slippage = 0.6 * spread_slippage + 0.4 * volume_slippage
        
        return total_slippage


def get_slippage_model(model_name: str) -> SlippageModel:
    """
    Get slippage model by name.
    
    Args:
        model_name: Name of the slippage model
    
    Returns:
        SlippageModel instance
    """
    models = {
        'none': NoSlippage,
        'fixed': FixedSlippage,
        'spread_based': SpreadBasedSlippage,
        'volume_based': VolumeBasedSlippage,
        'realistic': RealisticSlippage
    }
    
    model_class = models.get(model_name.lower(), SpreadBasedSlippage)
    return model_class()
