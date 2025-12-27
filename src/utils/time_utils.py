"""
Time and date utilities for the trading system.
"""
from datetime import datetime, time, timedelta
from typing import Optional

import pytz

from ..core.constants import (
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    TRADING_DAYS_PER_YEAR,
)


class TimeUtils:
    """Time and date utility functions."""
    
    @staticmethod
    def is_market_hours(dt: Optional[datetime] = None, timezone: str = "America/New_York") -> bool:
        """Check if the given datetime is during market hours."""
        if dt is None:
            dt = datetime.now(pytz.timezone(timezone))
        elif dt.tzinfo is None:
            dt = pytz.timezone(timezone).localize(dt)
        
        # Check if weekday (Monday=0, Sunday=6)
        if dt.weekday() >= 5:  # Saturday or Sunday
            return False
        
        market_open = time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
        market_close = time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)
        
        return market_open <= dt.time() <= market_close
    
    @staticmethod
    def next_market_open(dt: Optional[datetime] = None, timezone: str = "America/New_York") -> datetime:
        """Get the next market open datetime."""
        if dt is None:
            dt = datetime.now(pytz.timezone(timezone))
        elif dt.tzinfo is None:
            dt = pytz.timezone(timezone).localize(dt)
        
        # Start from tomorrow
        next_day = dt + timedelta(days=1)
        
        # Skip weekends
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        
        # Set to market open time
        market_open = next_day.replace(
            hour=MARKET_OPEN_HOUR,
            minute=MARKET_OPEN_MINUTE,
            second=0,
            microsecond=0
        )
        
        return market_open
    
    @staticmethod
    def time_to_expiry(expiry: datetime, current: Optional[datetime] = None) -> float:
        """
        Calculate time to expiry in years.
        
        Args:
            expiry: Expiry datetime
            current: Current datetime (default: now)
        
        Returns:
            Time to expiry in years
        """
        if current is None:
            current = datetime.utcnow()
        
        # Ensure both are timezone-aware or both naive
        if expiry.tzinfo is not None and current.tzinfo is None:
            current = pytz.UTC.localize(current)
        elif expiry.tzinfo is None and current.tzinfo is not None:
            expiry = pytz.UTC.localize(expiry)
        
        delta = expiry - current
        years = delta.total_seconds() / (365.25 * 24 * 3600)
        
        return max(0.0, years)
    
    @staticmethod
    def trading_days_between(start: datetime, end: datetime) -> int:
        """Calculate number of trading days between two dates."""
        days = 0
        current = start
        
        while current < end:
            if current.weekday() < 5:  # Weekday
                days += 1
            current += timedelta(days=1)
        
        return days
    
    @staticmethod
    def years_to_expiry(expiry: datetime, current: Optional[datetime] = None) -> float:
        """
        Calculate years to expiry using trading days.
        
        This is more accurate for options pricing than calendar days.
        """
        if current is None:
            current = datetime.utcnow()
        
        trading_days = TimeUtils.trading_days_between(current, expiry)
        return trading_days / TRADING_DAYS_PER_YEAR
    
    @staticmethod
    def format_timestamp(dt: datetime) -> str:
        """Format datetime as ISO 8601 timestamp."""
        return dt.isoformat()
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime."""
        return datetime.fromisoformat(timestamp)


def get_current_time(timezone: str = "UTC") -> datetime:
    """Get current time in specified timezone."""
    return datetime.now(pytz.timezone(timezone))


def get_market_time() -> datetime:
    """Get current time in market timezone (US Eastern)."""
    return get_current_time("America/New_York")
