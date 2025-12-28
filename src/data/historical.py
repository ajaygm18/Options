"""
Historical data handlers for backtesting and analysis.
"""
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from ..core.events import MarketTick, Quote
from ..utils.logging import get_logger


class HistoricalDataHandler:
    """Handler for historical market data."""
    
    def __init__(self):
        """Initialize historical data handler."""
        self.logger = get_logger(__name__)
        self.data: Dict[str, pd.DataFrame] = {}
    
    def load_csv(
        self,
        symbol: str,
        filepath: str,
        date_column: str = 'timestamp',
        parse_dates: bool = True
    ) -> bool:
        """
        Load historical data from CSV file.
        
        Args:
            symbol: Symbol to load data for
            filepath: Path to CSV file
            date_column: Name of the date/timestamp column
            parse_dates: Whether to parse dates
        
        Returns:
            True if loaded successfully
        """
        try:
            df = pd.read_csv(filepath)
            if parse_dates and date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column])
                df.set_index(date_column, inplace=True)
            
            self.data[symbol] = df
            self.logger.info(
                "Loaded historical data",
                symbol=symbol,
                rows=len(df),
                filepath=filepath
            )
            return True
        except Exception as e:
            self.logger.error(
                "Error loading historical data",
                symbol=symbol,
                filepath=filepath,
                error=str(e)
            )
            return False
    
    def load_dataframe(self, symbol: str, df: pd.DataFrame) -> None:
        """
        Load historical data from DataFrame.
        
        Args:
            symbol: Symbol
            df: DataFrame with historical data
        """
        self.data[symbol] = df.copy()
        self.logger.info("Loaded historical data", symbol=symbol, rows=len(df))
    
    def get_data(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Symbol
            start: Start date (None = from beginning)
            end: End date (None = to end)
        
        Returns:
            DataFrame or None if not available
        """
        if symbol not in self.data:
            return None
        
        df = self.data[symbol]
        
        # Apply date filters if index is datetime
        if isinstance(df.index, pd.DatetimeIndex):
            if start:
                df = df[df.index >= start]
            if end:
                df = df[df.index <= end]
        
        return df
    
    def get_quote_at(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[Quote]:
        """
        Get quote at a specific timestamp.
        
        Args:
            symbol: Symbol
            timestamp: Timestamp
        
        Returns:
            Quote or None if not available
        """
        if symbol not in self.data:
            return None
        
        df = self.data[symbol]
        
        if not isinstance(df.index, pd.DatetimeIndex):
            return None
        
        # Find nearest timestamp
        idx = df.index.searchsorted(timestamp)
        
        if idx >= len(df):
            return None
        
        row = df.iloc[idx]
        
        # Construct quote from row
        try:
            quote = Quote(
                timestamp=df.index[idx].to_pydatetime(),
                symbol=symbol,
                bid=float(row.get('bid', row.get('close', 0))),
                ask=float(row.get('ask', row.get('close', 0))),
                bid_size=int(row.get('bid_size', 100)),
                ask_size=int(row.get('ask_size', 100))
            )
            return quote
        except Exception as e:
            self.logger.error(
                "Error constructing quote",
                symbol=symbol,
                timestamp=timestamp,
                error=str(e)
            )
            return None
    
    def get_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime
    ) -> List[MarketTick]:
        """
        Get market ticks for a time range.
        
        Args:
            symbol: Symbol
            start: Start time
            end: End time
        
        Returns:
            List of MarketTick events
        """
        df = self.get_data(symbol, start, end)
        if df is None or df.empty:
            return []
        
        ticks = []
        for idx, row in df.iterrows():
            try:
                timestamp = idx if isinstance(idx, datetime) else datetime.now()
                tick = MarketTick(
                    timestamp=timestamp,
                    symbol=symbol,
                    price=float(row.get('close', row.get('price', 0))),
                    volume=int(row.get('volume', 0)),
                    bid=float(row.get('bid', 0)) if 'bid' in row else None,
                    ask=float(row.get('ask', 0)) if 'ask' in row else None,
                    bid_size=int(row.get('bid_size', 0)) if 'bid_size' in row else None,
                    ask_size=int(row.get('ask_size', 0)) if 'ask_size' in row else None
                )
                ticks.append(tick)
            except Exception as e:
                self.logger.error(
                    "Error creating tick",
                    symbol=symbol,
                    error=str(e)
                )
        
        return ticks
    
    def available_symbols(self) -> List[str]:
        """Get list of available symbols."""
        return list(self.data.keys())
    
    def clear(self) -> None:
        """Clear all loaded data."""
        self.data.clear()
        self.logger.info("Cleared all historical data")
