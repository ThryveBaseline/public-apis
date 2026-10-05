"""fpt - a from-scratch replication of JJ Simon's "Fair Pricing Theory" NQ
day-trading method, his ATR-tier risk model, and his multi-account prop-firm
operation.

Everything here is reconstructed from public sources (his own videos and
landing pages, podcast appearances, and third-party backtests). See
docs/DOSSIER.md for the evidence behind every parameter and
docs/ASSUMPTIONS.md for the places where the public record is silent and a
choice had to be made.
"""

from .data import load_minute_bars, synthetic_minute_bars
from .strategy import StrategyConfig, generate_trades
from .backtest import run_backtest, BacktestResult
from .risk import (
    atr_tier,
    contracts_for_risk,
    expectancy_r,
    kelly_fraction,
    expected_max_losing_streak,
    losing_streak_quantiles,
    daily_stop_from_stats,
    risk_of_ruin,
)
from .propfirm import FirmRules, FIRM_PRESETS, PropAccount
from .portfolio import PortfolioConfig, simulate_portfolio, optimal_risk_scan

__all__ = [
    "load_minute_bars",
    "synthetic_minute_bars",
    "StrategyConfig",
    "generate_trades",
    "run_backtest",
    "BacktestResult",
    "atr_tier",
    "contracts_for_risk",
    "expectancy_r",
    "kelly_fraction",
    "expected_max_losing_streak",
    "losing_streak_quantiles",
    "daily_stop_from_stats",
    "risk_of_ruin",
    "FirmRules",
    "FIRM_PRESETS",
    "PropAccount",
    "PortfolioConfig",
    "simulate_portfolio",
    "optimal_risk_scan",
]

__version__ = "0.1.0"
