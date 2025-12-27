from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if SRC_PATH.exists():
    sys.path.insert(0, str(SRC_PATH))

from options.engine import EventBus
from options.execution import OrderManager
from options.portfolio import Portfolio
from options.risk import RiskEngine, RiskLimits
from options.runner import TradingSystem
from options.strategy import MeanReversionStrategy, StrategyContext
from options.events import MarketTick


def build_system() -> TradingSystem:
    portfolio = Portfolio(cash=1_000_000.0)
    risk_limits = RiskLimits(max_position_size=10, max_notional=50_000.0, max_daily_loss=5_000.0)
    risk_engine = RiskEngine(limits=risk_limits, portfolio=portfolio)
    event_bus = EventBus()
    order_manager = OrderManager()
    strategies = [MeanReversionStrategy(StrategyContext("mean_rev"), threshold=0.01)]
    system = TradingSystem(
        event_bus=event_bus,
        portfolio=portfolio,
        risk_engine=risk_engine,
        order_manager=order_manager,
        strategies=strategies,
    )
    system.wire()
    return system


def main() -> None:
    system = build_system()
    now = datetime.utcnow()
    ticks = [
        MarketTick(symbol="SPY_20240119C450", price=2.5, bid=2.4, ask=2.6, timestamp=now),
        MarketTick(
            symbol="SPY_20240119C450",
            price=2.7,
            bid=2.6,
            ask=2.8,
            timestamp=now + timedelta(seconds=1),
        ),
        MarketTick(
            symbol="SPY_20240119C450",
            price=2.45,
            bid=2.4,
            ask=2.5,
            timestamp=now + timedelta(seconds=2),
        ),
    ]
    system.submit_ticks(ticks)
    print("Cash:", system.portfolio.cash)
    print("Positions:", system.portfolio.positions)
    print("Realized PnL:", system.portfolio.realized_pnl)


if __name__ == "__main__":
    main()
