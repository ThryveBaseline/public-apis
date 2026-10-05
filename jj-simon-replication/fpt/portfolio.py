"""Multi-account portfolio Monte Carlo: the "45 accounts" operation.

Every account receives the same trade signals (copy trading), sized by its
own risk_per_trade, and lives under its own firm rules. The simulation
tracks evaluation fees, resets, activation fees, breaches, passes and
payouts month by month, and reports the distribution of net cash flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .propfirm import EVAL, FIRM_PRESETS, FirmRules, PropAccount


@dataclass
class PortfolioConfig:
    accounts: list[tuple[str, int]] = field(default_factory=lambda: [("topstep_100k", 10)])
    risk_per_trade: float | dict[str, float] = 1000.0
    p_win: float = 0.54
    rr: float = 1.5
    trades_per_day: float = 1.5  # qualifying trades/day implied by the public backtests and his reported results; his '10 a day' includes lower-grade trades
    bootstrap_r: np.ndarray | None = None  # resample real trade R outcomes instead of parametric p/rr
    months: int = 6
    trading_days_per_month: int = 21
    sims: int = 2000
    seed: int = 0
    copy_trading: bool = True
    restart_failed: bool = True
    start_funded: bool = False
    daily_loss_stop_r: float | None = None
    max_consecutive_losses: int | None = None
    max_trades_per_day: int | None = None


def _day_outcomes(rng: np.random.Generator, cfg: PortfolioConfig, sims: int) -> tuple[np.ndarray, np.ndarray]:
    n = rng.poisson(cfg.trades_per_day, size=sims)
    if cfg.max_trades_per_day is not None:
        n = np.minimum(n, cfg.max_trades_per_day)
    maxn = int(n.max()) if sims else 0
    if maxn == 0:
        return np.zeros((sims, 1)), np.zeros((sims, 1), dtype=bool)
    if cfg.bootstrap_r is not None and len(cfg.bootstrap_r):
        r = rng.choice(np.asarray(cfg.bootstrap_r, float), size=(sims, maxn), replace=True)
    else:
        wins = rng.random((sims, maxn)) < cfg.p_win
        r = np.where(wins, cfg.rr, -1.0)
    mask = np.arange(maxn)[None, :] < n[:, None]
    # daily discipline rules (apply to the signal stream, hence to every copied account)
    if cfg.daily_loss_stop_r is not None or cfg.max_consecutive_losses is not None:
        cum = np.cumsum(np.where(mask, r, 0.0), axis=1)
        stop = np.zeros(sims, dtype=bool)
        consec = np.zeros(sims, dtype=int)
        for k in range(maxn):
            mask[:, k] &= ~stop
            if cfg.daily_loss_stop_r is not None:
                stop |= mask[:, k] & (cum[:, k] <= -abs(cfg.daily_loss_stop_r))
            if cfg.max_consecutive_losses is not None:
                consec = np.where(mask[:, k] & (r[:, k] < 0), consec + 1, np.where(mask[:, k], 0, consec))
                stop |= consec >= cfg.max_consecutive_losses
    return r, mask


def simulate_portfolio(cfg: PortfolioConfig, presets: dict[str, FirmRules] | None = None) -> dict:
    presets = presets or FIRM_PRESETS
    rng = np.random.default_rng(cfg.seed)
    sims = cfg.sims
    accounts: list[tuple[str, PropAccount]] = []
    for key, count in cfg.accounts:
        rules = presets[key]
        risk = cfg.risk_per_trade[key] if isinstance(cfg.risk_per_trade, dict) else cfg.risk_per_trade
        for i in range(count):
            accounts.append((key, PropAccount(rules, sims, risk, start_phase=1 if cfg.start_funded else EVAL, restart_failed=cfg.restart_failed)))
    total_days = cfg.months * cfg.trading_days_per_month
    monthly_cash = np.zeros((sims, cfg.months))
    monthly_costs = np.zeros((sims, cfg.months))
    funded_counts = np.zeros((sims, cfg.months))
    prev_costs = sum(a.costs_total for _, a in accounts)
    for day in range(total_days):
        if cfg.copy_trading:
            r, mask = _day_outcomes(rng, cfg, sims)
            for _, acct in accounts:
                acct.apply_day(r, mask)
        else:
            for _, acct in accounts:
                r, mask = _day_outcomes(rng, cfg, sims)
                acct.apply_day(r, mask)
        if (day + 1) % cfg.trading_days_per_month == 0:
            m = (day + 1) // cfg.trading_days_per_month - 1
            cash = np.zeros(sims)
            for _, acct in accounts:
                cash += acct.month_end()
            costs_now = sum(a.costs_total for _, a in accounts)
            monthly_cash[:, m] = cash
            monthly_costs[:, m] = costs_now - prev_costs
            prev_costs = costs_now
            funded_counts[:, m] = sum((a.phase == 1).astype(int) for _, a in accounts)
    payouts = sum(a.payouts_total for _, a in accounts)
    costs = sum(a.costs_total for _, a in accounts)
    net = payouts - costs
    breaches = sum(a.breaches for _, a in accounts)
    passes = sum(a.passes for _, a in accounts)
    monthly_net = monthly_cash - monthly_costs
    pct = lambda x, q: float(np.percentile(x, q))
    return {
        "accounts": int(len(accounts)),
        "months": cfg.months,
        "net_total": {"p5": pct(net, 5), "p25": pct(net, 25), "median": pct(net, 50), "p75": pct(net, 75), "p95": pct(net, 95), "mean": float(net.mean())},
        "payouts_total": {"median": pct(payouts, 50), "mean": float(payouts.mean()), "p5": pct(payouts, 5), "p95": pct(payouts, 95)},
        "costs_total": {"median": pct(costs, 50), "mean": float(costs.mean())},
        "p_net_positive": float((net > 0).mean()),
        "breaches_per_sim": {"mean": float(breaches.mean()), "median": pct(breaches, 50)},
        "passes_per_sim": {"mean": float(passes.mean())},
        "monthly_net_median": [pct(monthly_net[:, i], 50) for i in range(cfg.months)],
        "monthly_net_p5": [pct(monthly_net[:, i], 5) for i in range(cfg.months)],
        "monthly_net_p95": [pct(monthly_net[:, i], 95) for i in range(cfg.months)],
        "funded_accounts_median_by_month": [pct(funded_counts[:, i], 50) for i in range(cfg.months)],
        "p_month_positive": [float((monthly_net[:, i] > 0).mean()) for i in range(cfg.months)],
        "_arrays": {"net": net, "payouts": payouts, "costs": costs, "monthly_net": monthly_net},
    }


def optimal_risk_scan(cfg: PortfolioConfig, risks=(250, 500, 750, 1000, 1250, 1500, 2000), presets=None) -> list[dict]:
    """Scan fixed risk per trade and report the net cash-flow distribution
    for each: the empirical answer to "what is the optimal risk" for this
    account mix, edge and horizon."""
    rows = []
    for risk in risks:
        c = PortfolioConfig(**{**cfg.__dict__, "risk_per_trade": float(risk)})
        res = simulate_portfolio(c, presets)
        rows.append({
            "risk_per_trade": float(risk),
            "net_median": res["net_total"]["median"],
            "net_p5": res["net_total"]["p5"],
            "net_mean": res["net_total"]["mean"],
            "p_net_positive": res["p_net_positive"],
            "breaches_mean": res["breaches_per_sim"]["mean"],
            "payouts_mean": res["payouts_total"]["mean"],
        })
    return rows
