# Options Trading System

An enterprise-grade options trading system designed as a regulated, safety-critical distributed system with industrial-strength risk controls and observability.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/ajaygm18/Options.git
cd Options

# Install dependencies
pip install -r requirements.txt

# Run the demo
python scripts/demo.py
```

**Expected Output:**
- ✅ Option pricing: Call option priced at ~$17
- ✅ Portfolio Greeks calculated (Delta, Gamma, Theta, Vega)
- ✅ Volatility surface built and interpolated
- ✅ Stress testing: 8 scenarios executed
- ✅ VaR/CVaR calculated using Monte Carlo (1000 simulations)

## Overview

This system implements a complete options trading platform following the specifications in `Ins.txt`, with emphasis on:

- **Safety first**: Hard risk limits, kill switches, circuit breakers, auditability
- **Separation of concerns**: Research ≠ backtesting ≠ execution ≠ risk ≠ monitoring
- **Determinism & reproducibility**: Every decision traceable to inputs, model version, config, and code hash
- **Event-driven design**: Market data → signals → orders → fills → positions/risk updates
- **Multi-environment parity**: sim/paper/live share the same interfaces
- **Options-native analytics**: Volatility surface, Greeks, portfolio-level exposures, scenario/stress testing
- **Defense-in-depth security**: Secrets, least privilege, immutable logs, data lineage
- **Regime awareness**: Strategies selected/weighted by market regime and liquidity conditions

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Event Bus (Core Events)                  │
└─────────────────────────────────────────────────────────────┘
         ▲                  ▲                  ▲
         │                  │                  │
         │                  │                  │
    ┌────┴────┐      ┌─────┴──────┐     ┌────┴─────┐
    │  Data   │      │ Analytics  │     │   Risk   │
    │  Layer  │      │            │     │  Engine  │
    └────┬────┘      └─────┬──────┘     └────┬─────┘
         │                  │                  │
         ▼                  ▼                  ▼
    ┌────────────────────────────────────────────┐
    │           Strategy Engine                  │
    └────────────────┬───────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Portfolio Optimizer  │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │    Execution (OMS)    │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Broker Adapters      │
         └───────────────────────┘
```

## Project Structure

```
options_trading_system/
├── README.md                    # This file
├── Ins.txt                      # Original specifications
├── pyproject.toml               # Project metadata and dependencies
├── requirements.txt             # Python dependencies
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
│
├── .github/workflows/
│   └── ci.yml                   # CI/CD pipeline
│
├── config/
│   ├── base.yaml               # Base configuration
│   ├── development.yaml        # Development environment
│   ├── paper.yaml              # Paper trading environment
│   └── production.yaml         # Production environment
│
├── src/
│   ├── core/
│   │   ├── events.py           # Event types and base classes
│   │   ├── interfaces.py       # Abstract interfaces/protocols
│   │   └── constants.py        # System-wide constants
│   │
│   ├── data/
│   │   ├── market_data.py      # Market data ingestion
│   │   ├── instrument_master.py # Symbol mappings, expiries
│   │   ├── historical.py       # Historical data handlers
│   │   └── feeds/
│   │       └── base_feed.py    # Base feed adapter
│   │
│   ├── analytics/
│   │   ├── greeks.py           # Options Greeks calculations
│   │   ├── volatility_surface.py # IV surface engine
│   │   ├── pricing.py          # Option pricing models
│   │   └── scenarios.py        # Stress testing and scenarios
│   │
│   ├── strategies/
│   │   ├── base_strategy.py    # Base strategy class
│   │   ├── signals.py          # Signal generation
│   │   └── examples/
│   │       ├── volatility_strategy.py
│   │       └── spread_strategy.py
│   │
│   ├── portfolio/
│   │   ├── optimizer.py        # Portfolio optimization
│   │   ├── position_manager.py # Position tracking
│   │   ├── risk_budgets.py     # Risk budget allocation
│   │   └── constraints.py      # Portfolio constraints
│   │
│   ├── risk/
│   │   ├── risk_engine.py      # Main risk engine
│   │   ├── pre_trade.py        # Pre-trade risk checks
│   │   ├── circuit_breakers.py # Kill switches and circuit breakers
│   │   ├── var.py              # VaR/CVaR calculations
│   │   └── limits.py           # Risk limits configuration
│   │
│   ├── execution/
│   │   ├── oms.py              # Order Management System
│   │   ├── ems.py              # Execution Management System
│   │   ├── order.py            # Order state machine
│   │   └── brokers/
│   │       ├── base_broker.py  # Base broker adapter
│   │       └── paper_broker.py # Paper trading broker
│   │
│   ├── backtesting/
│   │   ├── engine.py           # Backtesting engine
│   │   ├── simulator.py        # Event-driven simulator
│   │   ├── slippage.py         # Slippage models
│   │   └── results.py          # Backtest results analysis
│   │
│   ├── monitoring/
│   │   ├── metrics.py          # Metrics collection
│   │   ├── alerts.py           # Alerting system
│   │   ├── audit.py            # Audit trail logging
│   │   └── dashboard.py        # Dashboard data
│   │
│   └── utils/
│       ├── logging.py          # Structured logging
│       ├── time_utils.py       # Time/date utilities
│       └── validation.py       # Input validation
│
├── tests/
│   ├── conftest.py
│   ├── test_analytics/
│   ├── test_risk/
│   ├── test_execution/
│   └── test_backtesting/
│
└── scripts/
    ├── run_backtest.py
    ├── run_paper_trading.py
    └── run_live.py
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or conda

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/ajaygm18/Options.git
cd Options
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Install the package in development mode:**

```bash
pip install -e .
```

### Docker Setup

Alternatively, use Docker:

```bash
docker-compose up
```

## Configuration

The system uses YAML-based configuration with environment overlays:

- `config/base.yaml`: Base configuration shared across all environments
- `config/development.yaml`: Development-specific settings
- `config/paper.yaml`: Paper trading configuration
- `config/production.yaml`: Production settings

### Key Configuration Sections

#### Risk Limits

```yaml
risk:
  limits:
    max_daily_loss: 10000
    max_position_size: 100
    max_notional_per_underlying: 100000
    max_portfolio_notional: 500000
    max_margin_utilization: 0.7
    max_delta_per_underlying: 500
    max_gamma_per_underlying: 100
    max_vega_per_underlying: 1000
```

#### Circuit Breakers

```yaml
risk:
  circuit_breakers:
    enabled: true
    drawdown_threshold: 0.05
    data_staleness_threshold_ms: 10000
    broker_reject_rate_threshold: 0.3
    spread_multiplier_threshold: 3.0
```

## Core Components

### 1. Event System (`src/core/events.py`)

Immutable event-driven architecture with full traceability:

- `MarketTick`: Real-time price updates
- `Quote`: Bid/ask quotes
- `OptionChain`: Full option chain data
- `IVSurface`: Implied volatility surface
- `Signal`: Trading signals from strategies
- `Order`: Order events
- `Fill`: Fill confirmations
- `PositionUpdate`: Position changes
- `RiskUpdate`: Risk metric updates
- `CircuitBreaker`: Circuit breaker triggers

### 2. Options Analytics (`src/analytics/`)

#### Greeks Calculator (`greeks.py`)

Calculate and aggregate Greeks at position and portfolio levels:

```python
from src.analytics.greeks import GreeksCalculator

calculator = GreeksCalculator()
greeks = calculator.calculate_position_greeks(
    spot=100,
    strike=105,
    time_to_expiry=0.25,
    volatility=0.25,
    risk_free_rate=0.05,
    dividend_yield=0.0,
    option_type='call',
    quantity=10
)
```

#### Volatility Surface (`volatility_surface.py`)

Build and interpolate implied volatility surfaces:

```python
from src.analytics.volatility_surface import VolatilitySurface

surface = VolatilitySurface(underlying='SPY', spot_price=450)
surface.add_data_point(
    strike=455,
    time_to_expiry=0.25,
    implied_vol=0.20,
    option_type='call',
    bid=5.0,
    ask=5.2,
    volume=1000
)
surface.build_surface()
vol = surface.get_volatility(strike=460, time_to_expiry=0.25)
```

#### Pricing Models (`pricing.py`)

- **Black-Scholes**: European options pricing and Greeks
- **Binomial Tree**: American options pricing

```python
from src.analytics.pricing import BlackScholesModel

price = BlackScholesModel.price(
    spot=100,
    strike=105,
    time_to_expiry=0.25,
    volatility=0.25,
    risk_free_rate=0.05,
    option_type='call'
)

greeks = BlackScholesModel.greeks(
    spot=100,
    strike=105,
    time_to_expiry=0.25,
    volatility=0.25,
    risk_free_rate=0.05,
    option_type='call'
)
```

#### Scenario Engine (`scenarios.py`)

Stress testing and VaR calculation:

```python
from src.analytics.scenarios import ScenarioEngine

engine = ScenarioEngine()
results = engine.stress_test(positions)
var_results = engine.calculate_var(positions, confidence_level=0.95)
```

### 3. Risk Management (`src/risk/`)

Multi-layered risk controls:

- **Pre-trade checks**: Validate orders before submission
- **Real-time risk**: Portfolio Greeks, VaR/CVaR monitoring
- **Circuit breakers**: Automated kill switches for exceptional conditions
- **Risk limits**: Configurable limits with validation

### 4. Execution System (`src/execution/`)

- **OMS**: Order state machine with idempotency
- **EMS**: Smart execution tactics
- **Broker adapters**: Pluggable broker connectivity

### 5. Portfolio Management (`src/portfolio/`)

- **Optimizer**: Mean-variance optimization with constraints
- **Position manager**: Real-time position tracking
- **Risk budgets**: Strategy-level risk allocation

### 6. Backtesting (`src/backtesting/`)

Event-driven backtesting with realistic execution modeling:

- Spread crossing simulation
- Partial fills
- Slippage models
- Walk-forward validation support

## Usage Examples

### Running a Backtest

```python
# Coming soon: scripts/run_backtest.py
```

### Paper Trading

```python
# Coming soon: scripts/run_paper_trading.py
```

### Live Trading

```python
# Coming soon: scripts/run_live.py
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run tests with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=html
```

## Development

### Code Style

The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatting:

```bash
black src tests
isort src tests
```

Run linting:

```bash
flake8 src tests
mypy src
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Monitoring and Observability

### Structured Logging

All components use structured JSON logging:

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("Order placed", order_id="12345", symbol="SPY", quantity=10)
```

### Audit Trail

Critical decisions are logged to immutable audit trail:

```python
from src.utils.logging import AuditLogger

audit = AuditLogger()
audit.log_decision(
    decision_type="order_placement",
    strategy_id="vol_strategy_1",
    inputs={"signal": 0.8},
    output={"order_id": "12345"},
    model_version="1.0.0",
    config_version="1.0.0"
)
```

## Risk Controls

### Hard Limits

- Maximum position size per symbol
- Maximum notional per underlying
- Maximum portfolio notional
- Maximum daily loss
- Greek limits (delta, gamma, vega, theta)
- Margin utilization limits

### Circuit Breakers

Automatic trading halts triggered by:

1. **Drawdown threshold** breach
2. **Data staleness** detection
3. **High broker reject rate**
4. **Spread blowout**
5. **Volatility spike**

### Kill Switch

Manual or automated position flattening capability.

## Security

- Secrets managed via environment variables
- No hardcoded credentials
- Structured audit logging
- Input validation on all external data
- Least-privilege access controls

## Performance Considerations

- Vectorized computations using NumPy
- Optional numba JIT compilation for hot paths
- Efficient data structures for real-time operations
- Caching of expensive calculations

## Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Core events system
- [x] Configuration management
- [x] Utilities (logging, time, validation)

### Phase 2: Analytics ✅
- [x] Black-Scholes pricing
- [x] Greeks calculator
- [x] Volatility surface
- [x] Scenario engine

### Phase 3: Risk & Execution (In Progress)
- [x] Risk limits configuration
- [ ] Pre-trade risk checks
- [ ] Circuit breakers
- [ ] Order Management System
- [ ] Paper broker implementation

### Phase 4: Strategy & Portfolio (Planned)
- [ ] Base strategy framework
- [ ] Portfolio optimizer
- [ ] Position manager
- [ ] Example strategies

### Phase 5: Backtesting (Planned)
- [ ] Event-driven simulator
- [ ] Slippage models
- [ ] Results analysis

### Phase 6: Production (Planned)
- [ ] Live broker adapters
- [ ] Real-time monitoring
- [ ] Alerting system
- [ ] Performance optimization

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Disclaimer

This software is for educational and research purposes only. Trading options involves substantial risk of loss. Use at your own risk. The authors are not responsible for any financial losses incurred while using this software.

## References

- Black, F., & Scholes, M. (1973). The Pricing of Options and Corporate Liabilities
- Hull, J. C. (2018). Options, Futures, and Other Derivatives
- Taleb, N. N. (1997). Dynamic Hedging: Managing Vanilla and Exotic Options

## Support

For questions and support:
- Open an issue on GitHub
- Review the `Ins.txt` file for detailed specifications

---

**Built with safety, precision, and professional-grade risk management.**
