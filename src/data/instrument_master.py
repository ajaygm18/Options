"""
Instrument master for managing option instrument metadata.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ..utils.logging import get_logger


@dataclass
class OptionInstrument:
    """Option instrument metadata."""
    symbol: str
    underlying: str
    strike: float
    expiry: datetime
    option_type: str  # 'call' or 'put'
    multiplier: int = 100
    exchange: str = ""
    trading_class: str = ""


class InstrumentMaster:
    """
    Instrument master database for options.
    
    Manages:
    - Symbol mappings
    - Expiration dates
    - Strike prices
    - Multipliers
    - Trading sessions
    """
    
    def __init__(self):
        """Initialize instrument master."""
        self.instruments: Dict[str, OptionInstrument] = {}
        self.by_underlying: Dict[str, List[str]] = {}
        self.logger = get_logger(__name__)
    
    def add_instrument(self, instrument: OptionInstrument) -> None:
        """
        Add an instrument to the master.
        
        Args:
            instrument: Option instrument to add
        """
        self.instruments[instrument.symbol] = instrument
        
        # Index by underlying
        if instrument.underlying not in self.by_underlying:
            self.by_underlying[instrument.underlying] = []
        
        if instrument.symbol not in self.by_underlying[instrument.underlying]:
            self.by_underlying[instrument.underlying].append(instrument.symbol)
        
        self.logger.debug("Added instrument", symbol=instrument.symbol)
    
    def get_instrument(self, symbol: str) -> Optional[OptionInstrument]:
        """
        Get instrument by symbol.
        
        Args:
            symbol: Option symbol
        
        Returns:
            OptionInstrument or None
        """
        return self.instruments.get(symbol)
    
    def get_chain(
        self,
        underlying: str,
        expiry: Optional[datetime] = None,
        option_type: Optional[str] = None
    ) -> List[OptionInstrument]:
        """
        Get option chain for an underlying.
        
        Args:
            underlying: Underlying symbol
            expiry: Filter by expiry date (None = all expiries)
            option_type: Filter by option type (None = both calls and puts)
        
        Returns:
            List of OptionInstrument
        """
        symbols = self.by_underlying.get(underlying, [])
        instruments = [self.instruments[s] for s in symbols if s in self.instruments]
        
        # Apply filters
        if expiry:
            instruments = [i for i in instruments if i.expiry.date() == expiry.date()]
        
        if option_type:
            instruments = [i for i in instruments if i.option_type == option_type]
        
        return instruments
    
    def get_expiries(self, underlying: str) -> List[datetime]:
        """
        Get all expiration dates for an underlying.
        
        Args:
            underlying: Underlying symbol
        
        Returns:
            Sorted list of expiry dates
        """
        chain = self.get_chain(underlying)
        expiries = sorted(set(i.expiry for i in chain))
        return expiries
    
    def get_strikes(
        self,
        underlying: str,
        expiry: datetime,
        option_type: Optional[str] = None
    ) -> List[float]:
        """
        Get all strike prices for a given underlying and expiry.
        
        Args:
            underlying: Underlying symbol
            expiry: Expiry date
            option_type: Filter by option type (None = both)
        
        Returns:
            Sorted list of strike prices
        """
        chain = self.get_chain(underlying, expiry, option_type)
        strikes = sorted(set(i.strike for i in chain))
        return strikes
    
    def find_atm_strike(
        self,
        underlying: str,
        expiry: datetime,
        spot_price: float
    ) -> Optional[float]:
        """
        Find the at-the-money strike.
        
        Args:
            underlying: Underlying symbol
            expiry: Expiry date
            spot_price: Current spot price
        
        Returns:
            Closest strike to spot price
        """
        strikes = self.get_strikes(underlying, expiry)
        if not strikes:
            return None
        
        # Find closest strike
        return min(strikes, key=lambda k: abs(k - spot_price))
    
    def build_option_symbol(
        self,
        underlying: str,
        expiry: datetime,
        strike: float,
        option_type: str
    ) -> str:
        """
        Build standardized option symbol.
        
        Format: UNDERLYING_YYMMDD_C/P_STRIKE
        Example: SPY_240115_C_450
        
        Args:
            underlying: Underlying symbol
            expiry: Expiry date
            strike: Strike price
            option_type: 'call' or 'put'
        
        Returns:
            Standardized option symbol
        """
        expiry_str = expiry.strftime("%y%m%d")
        opt_type = "C" if option_type.lower() == "call" else "P"
        strike_str = f"{strike:.2f}".replace(".", "")
        
        return f"{underlying}_{expiry_str}_{opt_type}_{strike_str}"
    
    def load_from_dict(self, instruments_data: List[Dict]) -> int:
        """
        Load instruments from a list of dictionaries.
        
        Args:
            instruments_data: List of instrument dictionaries
        
        Returns:
            Number of instruments loaded
        """
        count = 0
        for data in instruments_data:
            try:
                instrument = OptionInstrument(
                    symbol=data['symbol'],
                    underlying=data['underlying'],
                    strike=float(data['strike']),
                    expiry=datetime.fromisoformat(data['expiry']),
                    option_type=data['option_type'],
                    multiplier=data.get('multiplier', 100),
                    exchange=data.get('exchange', ''),
                    trading_class=data.get('trading_class', '')
                )
                self.add_instrument(instrument)
                count += 1
            except Exception as e:
                self.logger.error(
                    "Error loading instrument",
                    symbol=data.get('symbol', 'unknown'),
                    error=str(e)
                )
        
        self.logger.info("Loaded instruments", count=count)
        return count
