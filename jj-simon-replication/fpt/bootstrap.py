"""Bootstrap growth: from one cheap evaluation to a multi-account operation
using payouts only.

JJ's operation runs 40-45 accounts and he says he spent several hundred
thousand dollars on evaluations along the way. This module asks the
question for someone starting with a few hundred dollars: with his edge,
his evaluation posture and the firms' rules, how fast does an account base
grow if every payout is reinvested in new evaluations, how often does the
bankroll die, and when does it start paying an income?

Mechanics (vectorised over `sims` paths):
  * A ladder of (preset, max_accounts) in purchase priority order. Each
    rung is a block of PropAccount slots that start INACTIVE.
  * Each trading day, at most `max_buys_per_day` new evaluations are bought
    per path when cash >= eval_cost + reserve, cheapest-first in ladder
    order. Monthly subscriptions, activation fees and resets are paid from
    cash as they fall due.
  * Failed accounts free their slot (no automatic re-buy); the policy buys
    again when cash allows.
  * Payouts add to cash. Once `income_after_funded` funded accounts exist,
    `income_take` of each month's payouts is taken out as income; the rest
    keeps compounding.
  * A path is bust when cash cannot cover the cheapest rung and no account
    is live.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .portfolio import _day_outcomes
from .propfirm import EVAL, FAILED, FIRM_PRESETS, FUNDED, INACTIVE, FirmRules, PropAccount

DEFAULT_LADDER = [  # cheapest one-time or low-subscription rungs first, his S/A tiers, within each firm's funded cap
    ("fundednext_50k_flex", 3),
    ("topstep_50k", 5),
    ("tradeify_100k_growth", 5),
    ("lucid_100k_flex", 5),
    ("e8_100k_signature", 3),
    ("alpha_100k_standard", 5),
    ("mffu_100k_pro", 3),
    ("apex_100k_intraday", 20),
]


@dataclass
class GrowthConfig:
    start_cash: float = 500.0
    monthly_contribution: float = 0.0  # fresh money added each month (0 = payouts only)
    ladder: list[tuple[str, int]] = field(default_factory=lambda: list(DEFAULT_LADDER))
    reserve: float = 0.0  # cash kept back after a purchase
    max_buys_per_day: int = 1
    p_win: float = 0.54
    rr: float = 1.5
    trades_per_day: float = 1.5  # qualifying signals per account per day (copy mode) ; see README calibration
    bootstrap_r: np.ndarray | None = None  # resample real trade R outcomes instead of parametric p/rr
    eval_risk_mode: str = "two_trade"  # his evaluation posture: target / (2 * rr) per trade; "fixed" = eval_risk per trade
    eval_risk: float = 500.0  # per-trade risk on evaluations when eval_risk_mode == "fixed"
    funded_risk: float = 1000.0
    months: int = 24
    trading_days_per_month: int = 21
    sims: int = 2000
    seed: int = 0
    income_after_funded: int = 5  # start taking income once this many funded accounts exist
    income_take: float = 0.5  # share of each month's payouts taken as income after that
    daily_loss_stop_r: float | None = None
    max_consecutive_losses: int | None = None
    max_trades_per_day: int | None = None


def simulate_growth(cfg: GrowthConfig, presets: dict[str, FirmRules] | None = None) -> dict:
    presets = presets or FIRM_PRESETS
    rng = np.random.default_rng(cfg.seed)
    sims = cfg.sims
    slots: list[tuple[str, PropAccount]] = []
    for key, cap in cfg.ladder:
        rules = presets[key]
        eval_risk = rules.profit_target / (2.0 * cfg.rr) if cfg.eval_risk_mode == "two_trade" else cfg.eval_risk
        for _ in range(cap):
            slots.append((key, PropAccount(rules, sims, cfg.funded_risk, start_phase=INACTIVE, restart_failed=False, eval_risk=eval_risk)))
    cheapest = min(presets[k].eval_cost for k, _ in cfg.ladder)
    cash = np.full(sims, float(cfg.start_cash))
    income_total = np.zeros(sims)
    invested = np.zeros(sims)
    bust = np.zeros(sims, dtype=bool)
    first_payout_month = np.full(sims, np.nan)
    months_to_k = {k: np.full(sims, np.nan) for k in (1, 5, 10, 20)}
    monthly_income = np.zeros((sims, cfg.months))
    monthly_payouts = np.zeros((sims, cfg.months))
    funded_by_month = np.zeros((sims, cfg.months))
    live_by_month = np.zeros((sims, cfg.months))
    cash_by_month = np.zeros((sims, cfg.months))
    prev_costs = sum(a.costs_total for _, a in slots)

    def live_count():
        return sum(((a.phase == EVAL) | (a.phase == FUNDED)).astype(int) for _, a in slots)

    def funded_count():
        return sum((a.phase == FUNDED).astype(int) for _, a in slots)

    for day in range(cfg.months * cfg.trading_days_per_month):
        m = day // cfg.trading_days_per_month
        if day % cfg.trading_days_per_month == 0:
            cash += cfg.monthly_contribution
        # purchases: ladder order, at most max_buys_per_day per path
        buys = np.zeros(sims, dtype=int)
        for key, acct in slots:
            cost = presets[key].eval_cost
            can = ~bust & (acct.phase == INACTIVE) & (buys < cfg.max_buys_per_day) & (cash >= cost + cfg.reserve)
            if can.any():
                acct.purchase(can)
                cash -= np.where(can, cost, 0.0)
                invested += np.where(can, cost, 0.0)
                buys += can.astype(int)
        # trade
        r, mask = _day_outcomes(rng, cfg, sims)
        for _, acct in slots:
            acct.apply_day(r, mask)
            acct.release_failed()
        costs_now = sum(a.costs_total for _, a in slots)
        cash -= costs_now - prev_costs  # activation fees charged inside apply_day
        prev_costs = costs_now
        if (day + 1) % cfg.trading_days_per_month == 0:
            paid = np.zeros(sims)
            for _, acct in slots:
                paid += acct.month_end()  # subscriptions charged, payouts received
            costs_now = sum(a.costs_total for _, a in slots)
            cash -= costs_now - prev_costs
            prev_costs = costs_now
            fc = funded_count()
            take = np.where(fc >= cfg.income_after_funded, cfg.income_take, 0.0) * paid
            cash += paid - take
            income_total += take
            monthly_income[:, m] = take
            monthly_payouts[:, m] = paid
            newly = np.isnan(first_payout_month) & (paid > 0)
            first_payout_month[newly] = m + 1
            for k, arr in months_to_k.items():
                hit = np.isnan(arr) & (fc >= k)
                arr[hit] = m + 1
            lc = live_count()
            bust |= (lc == 0) & (cash < cheapest)
            funded_by_month[:, m] = fc
            live_by_month[:, m] = lc
            cash_by_month[:, m] = cash
    pct = lambda x, q: float(np.nanpercentile(x, q)) if np.isfinite(x).any() else float("nan")
    last = cfg.months - 1
    return {
        "months": cfg.months,
        "start_cash": cfg.start_cash,
        "p_bust": float(bust.mean()),
        "p_first_payout_within_3_months": float((first_payout_month <= 3).mean()),
        "first_payout_month": {"median": pct(first_payout_month, 50), "p25": pct(first_payout_month, 25), "p75": pct(first_payout_month, 75), "p_never": float(np.isnan(first_payout_month).mean())},
        "months_to_funded": {str(k): {"median": pct(v, 50), "p_reached": float(np.isfinite(v).mean())} for k, v in months_to_k.items()},
        "funded_accounts_last_month": {"median": pct(funded_by_month[:, last], 50), "p25": pct(funded_by_month[:, last], 25), "p75": pct(funded_by_month[:, last], 75)},
        "monthly_payouts_last_month": {"median": pct(monthly_payouts[:, last], 50), "p25": pct(monthly_payouts[:, last], 25), "p75": pct(monthly_payouts[:, last], 75)},
        "income_total": {"median": pct(income_total, 50), "p25": pct(income_total, 25), "p75": pct(income_total, 75)},
        "invested_total": {"median": pct(invested, 50), "mean": float(invested.mean())},
        "cash_last_month": {"median": pct(cash_by_month[:, last], 50), "p5": pct(cash_by_month[:, last], 5)},
        "funded_median_by_month": [pct(funded_by_month[:, i], 50) for i in range(cfg.months)],
        "payouts_median_by_month": [pct(monthly_payouts[:, i], 50) for i in range(cfg.months)],
        "_arrays": {"bust": bust, "funded_by_month": funded_by_month, "monthly_payouts": monthly_payouts, "cash_by_month": cash_by_month},
    }


def growth_scan(cfg: GrowthConfig, start_cash=(250.0, 500.0, 1000.0, 2500.0, 5000.0), modes=("two_trade", "fixed"), presets=None) -> list[dict]:
    """P(bust), time to a funded base and month-12 payouts across starting bankrolls and evaluation postures."""
    from dataclasses import replace
    rows = []
    for mode in modes:
        for c in start_cash:
            r = simulate_growth(replace(cfg, start_cash=c, eval_risk_mode=mode), presets)
            rows.append({
                "eval_risk_mode": mode, "start_cash": c, "p_bust": r["p_bust"],
                "p_5_funded": r["months_to_funded"]["5"]["p_reached"], "months_to_5_funded_median": r["months_to_funded"]["5"]["median"],
                "funded_last_median": r["funded_accounts_last_month"]["median"], "payouts_last_p25": r["monthly_payouts_last_month"]["p25"],
                "payouts_last_median": r["monthly_payouts_last_month"]["median"], "income_median": r["income_total"]["median"],
            })
    return rows
