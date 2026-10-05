"""Backtest runner and performance statistics."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategy import StrategyConfig, generate_trades


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    summary: dict
    equity: pd.Series
    daily: pd.DataFrame
    monthly: pd.DataFrame
    by_setup: pd.DataFrame
    by_grade: pd.DataFrame
    by_tier: pd.DataFrame
    by_exit: pd.DataFrame

    def report(self) -> str:
        return format_report(self)


def run_backtest(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> BacktestResult:
    cfg = cfg or StrategyConfig()
    trades = generate_trades(df, cfg)
    n_days = len(np.unique(df.index.tz_convert("America/New_York").normalize().asi8))
    summary = summarize(trades, n_days)
    equity = trades.set_index("exit_time")["pnl_dollars"].cumsum() if len(trades) else pd.Series(dtype=float)
    daily = daily_table(trades)
    return BacktestResult(
        trades=trades,
        summary=summary,
        equity=equity,
        daily=daily,
        monthly=monthly_table(trades),
        by_setup=group_stats(trades, "setup"),
        by_grade=group_stats(trades, "grade"),
        by_tier=group_stats(trades, "tier"),
        by_exit=group_stats(trades, "exit_reason"),
    )


def streaks(wins: np.ndarray) -> tuple[int, int]:
    max_w = max_l = cur_w = cur_l = 0
    for w in wins:
        if w:
            cur_w += 1
            cur_l = 0
        else:
            cur_l += 1
            cur_w = 0
        max_w = max(max_w, cur_w)
        max_l = max(max_l, cur_l)
    return max_w, max_l


def max_drawdown(pnl: np.ndarray) -> float:
    if len(pnl) == 0:
        return 0.0
    eq = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.maximum(eq, 0.0))
    return float((peak - eq).max())


def summarize(trades: pd.DataFrame, n_days: int | None = None) -> dict:
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    pnl = trades["pnl_dollars"].to_numpy(float)
    r = trades["r"].to_numpy(float)
    wins = pnl > 0
    gross_profit = float(pnl[wins].sum())
    gross_loss = float(-pnl[~wins].sum())
    mw, ml = streaks(wins)
    days = trades["exit_time"].dt.tz_convert("America/New_York").dt.normalize().nunique()
    daily = trades.groupby(trades["exit_time"].dt.tz_convert("America/New_York").dt.normalize())["pnl_dollars"].sum()
    return {
        "trades": int(n),
        "wins": int(wins.sum()),
        "losses": int((~wins).sum()),
        "win_rate": float(wins.mean()),
        "net_pnl": float(pnl.sum()),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": float(gross_profit / gross_loss) if gross_loss > 0 else float("inf"),
        "avg_r": float(r.mean()),
        "avg_win_r": float(r[wins].mean()) if wins.any() else 0.0,
        "avg_loss_r": float(r[~wins].mean()) if (~wins).any() else 0.0,
        "expectancy_dollars": float(pnl.mean()),
        "max_drawdown_dollars": max_drawdown(pnl),
        "max_drawdown_r": max_drawdown(r),
        "max_win_streak": mw,
        "max_loss_streak": ml,
        "trading_days_with_trades": int(days),
        "calendar_days_in_data": int(n_days) if n_days is not None else None,
        "trades_per_active_day": float(n / days) if days else 0.0,
        "best_day": float(daily.max()),
        "worst_day": float(daily.min()),
        "p_negative_day": float((daily < 0).mean()),
        "daily_sharpe_like": float(daily.mean() / daily.std() * np.sqrt(252)) if daily.std() > 0 else 0.0,
        "avg_bars_held": float(trades["bars_held"].mean()),
    }


def group_stats(trades: pd.DataFrame, key: str) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame(columns=["n", "win_rate", "profit_factor", "net_pnl", "avg_r"])
    rows = {}
    for g, sub in trades.groupby(key):
        pnl = sub["pnl_dollars"].to_numpy(float)
        wins = pnl > 0
        gp = pnl[wins].sum()
        gl = -pnl[~wins].sum()
        rows[g] = {
            "n": len(sub),
            "win_rate": float(wins.mean()),
            "profit_factor": float(gp / gl) if gl > 0 else float("inf"),
            "net_pnl": float(pnl.sum()),
            "avg_r": float(sub["r"].mean()),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def daily_table(trades: pd.DataFrame) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame(columns=["trades", "net_pnl", "r"])
    d = trades["exit_time"].dt.tz_convert("America/New_York").dt.normalize()
    g = trades.groupby(d)
    out = pd.DataFrame({"trades": g.size(), "net_pnl": g["pnl_dollars"].sum(), "r": g["r"].sum()})
    out.index.name = "date"
    return out


def monthly_table(trades: pd.DataFrame) -> pd.DataFrame:
    if len(trades) == 0:
        return pd.DataFrame(columns=["trades", "win_rate", "net_pnl", "r"])
    m = trades["exit_time"].dt.tz_convert("America/New_York").dt.tz_localize(None).dt.to_period("M")
    g = trades.groupby(m)
    out = pd.DataFrame({
        "trades": g.size(),
        "win_rate": g["pnl_dollars"].apply(lambda s: float((s > 0).mean())),
        "net_pnl": g["pnl_dollars"].sum(),
        "r": g["r"].sum(),
    })
    out.index.name = "month"
    return out


def format_report(res: BacktestResult) -> str:
    s = res.summary
    if s.get("trades", 0) == 0:
        return "No trades generated."
    lines = ["# Backtest report", ""]
    lines.append("| metric | value |")
    lines.append("|---|---|")
    for k, v in s.items():
        if isinstance(v, float):
            v = f"{v:,.3f}"
        lines.append(f"| {k} | {v} |")
    for title, tbl in (("By setup", res.by_setup), ("By grade", res.by_grade), ("By ATR tier", res.by_tier), ("By exit", res.by_exit), ("By month", res.monthly)):
        lines += ["", f"## {title}", "", tbl.to_markdown(floatfmt=",.3f") if hasattr(tbl, "to_markdown") else tbl.to_string()]
    return "\n".join(lines)
