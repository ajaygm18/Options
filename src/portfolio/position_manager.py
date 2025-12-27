"""
Position manager for tracking positions and P&L.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ..core.events import Fill, PositionUpdate
from ..utils.logging import get_logger


@dataclass
class Position:
    """Position information."""
    symbol: str
    quantity: int
    average_price: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class PositionManager:
    """
    Manages positions and tracks P&L.
    
    Responsibilities:
    - Track current positions
    - Calculate realized and unrealized P&L
    - Maintain fill history
    - Generate position update events
    """
    
    def __init__(self):
        """Initialize position manager."""
        self.positions: Dict[str, Position] = {}
        self.fills: List[Fill] = []
        self.logger = get_logger(__name__)
    
    def process_fill(self, fill: Fill) -> PositionUpdate:
        """
        Process a fill and update positions.
        
        Args:
            fill: Fill event
        
        Returns:
            PositionUpdate event
        """
        self.fills.append(fill)
        symbol = fill.symbol
        
        # Get or create position
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0,
                average_price=0.0
            )
        
        position = self.positions[symbol]
        
        # Calculate new position
        fill_quantity = fill.quantity if fill.side.value == 'buy' else -fill.quantity
        new_quantity = position.quantity + fill_quantity
        
        # Calculate realized P&L
        realized_pnl = 0.0
        if (position.quantity > 0 and fill_quantity < 0) or (position.quantity < 0 and fill_quantity > 0):
            # Closing or reducing position
            closed_quantity = min(abs(fill_quantity), abs(position.quantity))
            if position.quantity > 0:
                # Closing long
                realized_pnl = closed_quantity * (fill.price - position.average_price)
            else:
                # Closing short
                realized_pnl = closed_quantity * (position.average_price - fill.price)
            
            # Subtract commission
            realized_pnl -= fill.commission
        
        # Update average price
        if new_quantity == 0:
            average_price = 0.0
        elif (position.quantity >= 0 and fill_quantity > 0) or (position.quantity <= 0 and fill_quantity < 0):
            # Adding to position
            if position.quantity == 0:
                average_price = fill.price
            else:
                total_cost = (position.quantity * position.average_price + 
                             fill_quantity * fill.price)
                average_price = total_cost / new_quantity
        else:
            # Reducing position, keep same average
            average_price = position.average_price
        
        # Update position
        position.quantity = new_quantity
        position.average_price = average_price
        position.realized_pnl += realized_pnl
        position.last_updated = fill.timestamp
        
        self.logger.info(
            "Position updated from fill",
            symbol=symbol,
            quantity=position.quantity,
            average_price=position.average_price,
            realized_pnl=realized_pnl,
            total_realized_pnl=position.realized_pnl
        )
        
        # Create position update event
        return PositionUpdate(
            symbol=symbol,
            quantity=position.quantity,
            average_price=position.average_price,
            unrealized_pnl=position.unrealized_pnl,
            realized_pnl=position.realized_pnl
        )
    
    def update_market_value(self, symbol: str, current_price: float) -> None:
        """
        Update unrealized P&L based on current market price.
        
        Args:
            symbol: Symbol
            current_price: Current market price
        """
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        if position.quantity == 0:
            position.unrealized_pnl = 0.0
        else:
            position.unrealized_pnl = position.quantity * (
                current_price - position.average_price
            )
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.
        
        Args:
            symbol: Symbol
        
        Returns:
            Position or None
        """
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_total_pnl(self) -> Dict[str, float]:
        """
        Get total P&L across all positions.
        
        Returns:
            Dictionary with realized, unrealized, and total P&L
        """
        realized = sum(p.realized_pnl for p in self.positions.values())
        unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        
        return {
            'realized_pnl': realized,
            'unrealized_pnl': unrealized,
            'total_pnl': realized + unrealized
        }
    
    def get_notional_exposure(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total notional exposure.
        
        Args:
            current_prices: Dictionary of current prices by symbol
        
        Returns:
            Total notional exposure
        """
        total_notional = 0.0
        
        for symbol, position in self.positions.items():
            if symbol in current_prices and position.quantity != 0:
                notional = abs(position.quantity * current_prices[symbol])
                total_notional += notional
        
        return total_notional
    
    def clear_positions(self) -> None:
        """Clear all positions (use with caution!)."""
        self.positions.clear()
        self.logger.warning("All positions cleared")
