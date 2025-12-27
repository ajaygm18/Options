"""
Order state machine and order lifecycle management.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from ..core.events import OrderSide, OrderStatus, OrderType


class OrderState(Enum):
    """Order state in the state machine."""
    NEW = "new"
    PENDING_SUBMIT = "pending_submit"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    PENDING_CANCEL = "pending_cancel"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """
    Order object with state machine.
    
    State transitions:
    NEW -> PENDING_SUBMIT -> SUBMITTED -> ACKNOWLEDGED -> PARTIALLY_FILLED -> FILLED
                                                       -> PENDING_CANCEL -> CANCELLED
                                                       -> REJECTED
    """
    
    order_id: str = field(default_factory=lambda: str(uuid4()))
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.LIMIT
    quantity: int = 0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    
    state: OrderState = OrderState.NEW
    status: OrderStatus = OrderStatus.NEW
    
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    
    broker_order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    idempotency_key: str = field(default_factory=lambda: str(uuid4()))
    
    reject_reason: Optional[str] = None
    
    def submit(self) -> bool:
        """
        Transition to submitted state.
        
        Returns:
            True if transition successful
        """
        if self.state == OrderState.NEW:
            self.state = OrderState.PENDING_SUBMIT
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def acknowledge(self, broker_order_id: str) -> bool:
        """
        Acknowledge order with broker order ID.
        
        Args:
            broker_order_id: Broker's order ID
        
        Returns:
            True if transition successful
        """
        if self.state in (OrderState.PENDING_SUBMIT, OrderState.SUBMITTED):
            self.state = OrderState.ACKNOWLEDGED
            self.status = OrderStatus.ACKNOWLEDGED
            self.broker_order_id = broker_order_id
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def partial_fill(self, quantity: int, price: float) -> bool:
        """
        Record a partial fill.
        
        Args:
            quantity: Quantity filled
            price: Fill price
        
        Returns:
            True if transition successful
        """
        if self.state not in (OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED):
            return False
        
        if self.filled_quantity + quantity > self.quantity:
            return False
        
        # Update average fill price
        total_value = self.average_fill_price * self.filled_quantity + price * quantity
        self.filled_quantity += quantity
        self.average_fill_price = total_value / self.filled_quantity
        
        if self.filled_quantity < self.quantity:
            self.state = OrderState.PARTIALLY_FILLED
            self.status = OrderStatus.PARTIALLY_FILLED
        else:
            self.state = OrderState.FILLED
            self.status = OrderStatus.FILLED
        
        self.updated_at = datetime.utcnow()
        return True
    
    def fill(self, quantity: int, price: float) -> bool:
        """
        Fill the entire order.
        
        Args:
            quantity: Quantity filled
            price: Fill price
        
        Returns:
            True if transition successful
        """
        if self.state not in (OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED):
            return False
        
        if quantity != self.quantity - self.filled_quantity:
            return False
        
        self.filled_quantity = self.quantity
        self.average_fill_price = price
        self.state = OrderState.FILLED
        self.status = OrderStatus.FILLED
        self.updated_at = datetime.utcnow()
        return True
    
    def cancel(self) -> bool:
        """
        Cancel the order.
        
        Returns:
            True if transition successful
        """
        if self.state in (OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED):
            self.state = OrderState.PENDING_CANCEL
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def cancelled(self) -> bool:
        """
        Confirm cancellation.
        
        Returns:
            True if transition successful
        """
        if self.state == OrderState.PENDING_CANCEL:
            self.state = OrderState.CANCELLED
            self.status = OrderStatus.CANCELLED
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def reject(self, reason: str) -> bool:
        """
        Reject the order.
        
        Args:
            reason: Rejection reason
        
        Returns:
            True if transition successful
        """
        self.state = OrderState.REJECTED
        self.status = OrderStatus.REJECTED
        self.reject_reason = reason
        self.updated_at = datetime.utcnow()
        return True
    
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.state in (
            OrderState.NEW,
            OrderState.PENDING_SUBMIT,
            OrderState.SUBMITTED,
            OrderState.ACKNOWLEDGED,
            OrderState.PARTIALLY_FILLED,
            OrderState.PENDING_CANCEL
        )
    
    def is_complete(self) -> bool:
        """Check if order is complete (filled, cancelled, or rejected)."""
        return self.state in (
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.REJECTED,
            OrderState.EXPIRED
        )
    
    def remaining_quantity(self) -> int:
        """Get remaining unfilled quantity."""
        return self.quantity - self.filled_quantity
