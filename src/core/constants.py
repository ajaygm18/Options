"""
System-wide constants for the options trading system.
"""

# Trading constants
TRADING_DAYS_PER_YEAR = 252
HOURS_PER_TRADING_DAY = 6.5
SECONDS_PER_TRADING_DAY = int(HOURS_PER_TRADING_DAY * 3600)

# Market hours (US Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# Option types
OPTION_TYPE_CALL = "call"
OPTION_TYPE_PUT = "put"

# Option styles
OPTION_STYLE_AMERICAN = "american"
OPTION_STYLE_EUROPEAN = "european"

# Greeks
GREEK_DELTA = "delta"
GREEK_GAMMA = "gamma"
GREEK_THETA = "theta"
GREEK_VEGA = "vega"
GREEK_RHO = "rho"

# Risk metrics
METRIC_VAR = "var"
METRIC_CVAR = "cvar"
METRIC_SHARPE = "sharpe"
METRIC_SORTINO = "sortino"
METRIC_MAX_DRAWDOWN = "max_drawdown"

# Precision
PRICE_PRECISION = 2
QUANTITY_PRECISION = 0
GREEK_PRECISION = 4
VOLATILITY_PRECISION = 4

# Limits (default values, overridden by config)
DEFAULT_MAX_POSITION_SIZE = 100
DEFAULT_MAX_PORTFOLIO_VALUE = 1000000
DEFAULT_MAX_ORDER_VALUE = 100000

# Timeouts (milliseconds)
DEFAULT_ORDER_TIMEOUT_MS = 5000
DEFAULT_DATA_TIMEOUT_MS = 1000

# Slippage models
SLIPPAGE_NONE = "none"
SLIPPAGE_FIXED = "fixed"
SLIPPAGE_SPREAD_BASED = "spread_based"
SLIPPAGE_VOLUME_BASED = "volume_based"

# Commission models
COMMISSION_PER_CONTRACT = 0.65
COMMISSION_MINIMUM = 1.00

# Volatility surface
MIN_TIME_TO_EXPIRY = 1.0 / TRADING_DAYS_PER_YEAR  # 1 day
MAX_TIME_TO_EXPIRY = 2.0  # 2 years
MIN_MONEYNESS = 0.5
MAX_MONEYNESS = 2.0

# Data quality
MIN_LIQUIDITY_SCORE = 0.3
MAX_SPREAD_MULTIPLIER = 5.0

# Logging
LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"

# Status codes
STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"
STATUS_CRITICAL = "critical"
