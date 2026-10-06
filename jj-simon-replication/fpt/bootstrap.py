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
    p_win: float = 0.42  # his own latest explicit figure at 1.5R (4IGbxmKJ4BU ~0:56 L68); 0.54 is the third-party fxreplay variant and is NOT transferable to these rules
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


# ---------------------------------------------------------------------------
# His own account-level arithmetic: (1) the calculator exactly as he states it,
# (2) the same inputs run as an explicit state process in trading days.
# ---------------------------------------------------------------------------

def his_calculator(eval_cost: float = 100.0, pass_rate: float = 0.33, payout_rate: float = 0.33, payout_size: float = 2000.0,
                   evals_per_month: float | None = None) -> dict:
    """The calculator in his words (XhsbfEdJBAc ~0:49 L58, ~2:02 L100, ~2:09 L104):
    spend `eval_cost`, pass with `pass_rate`, a funded account reaches ONE payout
    with `payout_rate`, the payout is `payout_size`. No profit split, no repeat
    payouts: 0.33 x 0.33 x $2,000 = $217.80 back per $100 spent, +$117.80.
    `evals_per_month` only scales that expectation to a steady-state month
    (evaluations bought per month x EV per evaluation); it is not divided by any
    cycle length, because timing is the job of `simulate_his_stats`.
    """
    if eval_cost <= 0 or payout_size <= 0:
        raise ValueError("eval_cost and payout_size must be positive")
    if not (0.0 <= pass_rate <= 1.0 and 0.0 <= payout_rate <= 1.0):
        raise ValueError("pass_rate and payout_rate are probabilities in [0, 1]")
    p_first = pass_rate * payout_rate
    gross = p_first * payout_size
    out = {
        "gross_return_per_eval": gross,
        "ev_per_eval": gross - eval_cost,
        "return_multiple": gross / eval_cost,
        "p_payout_per_eval": p_first,
        "cost_per_funded_account": eval_cost / pass_rate if pass_rate > 0 else float("inf"),
        "expected_payout_per_funded_account": payout_rate * payout_size,
        "breakeven_payouts_per_100_evals": 100.0 * eval_cost / payout_size,
        "p_zero_payouts": {n: (1.0 - p_first) ** n for n in (5, 10, 20, 50, 100)},
    }
    if evals_per_month:
        out["monthly_profit"] = evals_per_month * (gross - eval_cost)
        out["annual_profit"] = 12 * out["monthly_profit"]
    return out


@dataclass
class HisStatsConfig:
    """The calculator's inputs run as a literal state process in trading days:
    purchase -> evaluation (eval_days) -> pass/fail -> funded -> qualifying
    period (qualifying_days, e.g. five winning days of $150+) -> payout decision
    -> payout. funded_mode "single" retires an account after its payout
    decision, which is the calculator's model (one payout per funded account);
    "repeat" is the separate lifetime model: a paid account starts another
    qualifying period and is lost with probability (1 - payout_rate) at each
    decision. Everything is reinvested; a path is bust when no account is live
    and cash cannot buy an evaluation."""
    start_cash: float = 500.0
    eval_cost: float = 100.0
    pass_rate: float = 0.33
    payout_rate: float = 0.33
    payout_size: float = 2000.0
    eval_days: int = 4  # trading days from purchase to pass/fail (he passes aggressively in 2-4 days; 0uAQUHEB_L8 ~14:17 L541)
    qualifying_days: int = 10  # trading days from funded to the payout decision (five winning days at a 50% daily win rate ~ 10 days; 0uAQUHEB_L8 ~8:47 L345)
    payout_processing_days: int = 0
    funded_mode: str = "single"  # "single": the calculator (one payout per funded account) | "repeat": lifetime model
    profit_split: float = 1.0  # the calculator takes payouts gross; set 0.9 for a 90/10 firm
    max_live_accounts: int = 100
    buys_per_day: int = 100
    months: int = 12
    trading_days_per_month: int = 22
    sims: int = 5000
    seed: int = 0
    income_after_cash: float = 10_000.0  # once cash exceeds this, take income_take of each payout
    income_take: float = 0.5


def simulate_his_stats(cfg: HisStatsConfig) -> dict:
    if cfg.eval_days < 1 or cfg.qualifying_days < 1 or cfg.payout_processing_days < 0:
        raise ValueError("eval_days and qualifying_days are whole trading days >= 1 (pass/fail lands eval_days after the purchase, "
                         "the payout decision qualifying_days after funding); payout_processing_days >= 0")
    if cfg.funded_mode not in ("single", "repeat"):
        raise ValueError("funded_mode is 'single' (the calculator: one payout per funded account) or 'repeat' (the lifetime model)")
    if not (0.0 <= cfg.pass_rate <= 1.0 and 0.0 <= cfg.payout_rate <= 1.0):
        raise ValueError("pass_rate and payout_rate are probabilities in [0, 1]")
    rng = np.random.default_rng(cfg.seed)
    n = cfg.sims
    E, Q, P = cfg.eval_days, cfg.qualifying_days, cfg.payout_processing_days
    cash = np.full(n, float(cfg.start_cash))
    evals = np.zeros((n, E), dtype=int)  # column k: evaluations resolving in k+1 days
    funded = np.zeros((n, Q), dtype=int)  # column k: funded accounts whose payout decision is in k+1 days
    pending = np.zeros((n, P), dtype=int) if P else None  # payouts in processing
    income = np.zeros(n)
    invested = np.zeros(n)
    bust = np.zeros(n, dtype=bool)
    first_payout_day = np.full(n, np.nan)
    first_funded_day = np.full(n, np.nan)
    months_to_k = {k: np.full(n, np.nan) for k in (1, 5, 10, 20)}
    T = cfg.months * cfg.trading_days_per_month
    funded_by_month = np.zeros((n, cfg.months))
    payouts_by_month = np.zeros((n, cfg.months))
    cash_by_month = np.zeros((n, cfg.months))
    month_pay = np.zeros(n)
    n_payouts = np.zeros(n, dtype=int)
    for day in range(T):
        m = day // cfg.trading_days_per_month
        # 1. evaluations bought `eval_days` trading days ago resolve
        resolving = evals[:, 0].copy()
        evals = np.roll(evals, -1, axis=1)
        evals[:, E - 1] = 0
        passed = rng.binomial(resolving, cfg.pass_rate)
        newly = np.isnan(first_funded_day) & (passed > 0)
        first_funded_day[newly] = day
        # 2. funded accounts that completed their qualifying period get their payout decision
        deciding = funded[:, 0].copy()
        funded = np.roll(funded, -1, axis=1)
        funded[:, Q - 1] = 0
        paid = rng.binomial(deciding, cfg.payout_rate)
        if cfg.funded_mode == "repeat":
            funded[:, Q - 1] += paid  # a paid account starts another qualifying period
        if P:
            arriving = pending[:, 0].copy()
            pending = np.roll(pending, -1, axis=1)
            pending[:, P - 1] = paid
        else:
            arriving = paid
        gross = arriving * cfg.payout_size * cfg.profit_split
        take = np.where(cash > cfg.income_after_cash, cfg.income_take, 0.0) * gross
        cash += gross - take
        income += take
        month_pay += gross
        n_payouts += arriving
        newly = np.isnan(first_payout_day) & (arriving > 0)
        first_payout_day[newly] = day
        # 3. accounts that passed today start their qualifying period (a full `qualifying_days` from tomorrow)
        funded[:, Q - 1] += passed
        # 4. purchases with today's cash (resolve a full `eval_days` from tomorrow)
        fc = funded.sum(axis=1)
        live = evals.sum(axis=1) + fc + (pending.sum(axis=1) if P else 0)
        room = np.maximum(0, cfg.max_live_accounts - live)
        afford = np.floor(np.maximum(cash, 0.0) / cfg.eval_cost).astype(int)
        buy = np.where(bust, 0, np.minimum(np.minimum(room, afford), cfg.buys_per_day))
        cash -= buy * cfg.eval_cost
        invested += buy * cfg.eval_cost
        evals[:, E - 1] += buy
        # 5. bookkeeping
        for k, arr in months_to_k.items():
            hit = np.isnan(arr) & (fc >= k)
            arr[hit] = m + 1
        live = evals.sum(axis=1) + fc + (pending.sum(axis=1) if P else 0)
        bust |= (live == 0) & (cash < cfg.eval_cost)
        if (day + 1) % cfg.trading_days_per_month == 0:
            funded_by_month[:, m] = fc
            payouts_by_month[:, m] = month_pay
            cash_by_month[:, m] = cash
            month_pay = np.zeros(n)
    pct = lambda x, q: float(np.nanpercentile(x, q)) if np.isfinite(x).any() else float("nan")
    last = cfg.months - 1
    calc = his_calculator(cfg.eval_cost, cfg.pass_rate, cfg.payout_rate, cfg.payout_size)
    # expected value still in flight at the end (evaluations and funded accounts not yet resolved), so the
    # realised return per evaluation is not biased down by the money tied up at the cut-off. It is valued under
    # THIS run's funded mode and profit split: "single" = one payout decision per funded account (the calculator),
    # "repeat" = a geometric number of payouts, payout_rate / (1 - payout_rate) per funded account.
    if cfg.funded_mode == "repeat":
        payouts_per_funded = cfg.payout_rate / (1.0 - cfg.payout_rate) if cfg.payout_rate < 1.0 else float("inf")
    else:
        payouts_per_funded = cfg.payout_rate
    funded_value = payouts_per_funded * cfg.payout_size * cfg.profit_split
    eval_value = cfg.pass_rate * funded_value
    inflight = np.zeros(n)
    for count, value in ((evals.sum(axis=1), eval_value), (funded.sum(axis=1), funded_value)):
        if np.isfinite(value):
            inflight += count * value
        else:
            inflight[count > 0] = np.inf
    if P:
        inflight = inflight + pending.sum(axis=1) * cfg.payout_size * cfg.profit_split
    path_multiple = (income + cash + inflight - cfg.start_cash) / np.maximum(invested, cfg.eval_cost)  # each path's own return multiple
    # per evaluation: every dollar invested on every path, pooled. This is the figure the calculator predicts (ev / cost) and it is
    # NOT lowered by bust: a path that buys five evaluations and loses them all is five evaluations at -1x, not a -1x path.
    pooled = float((income + cash + inflight - cfg.start_cash).sum() / max(invested.sum(), cfg.eval_cost))
    benchmark = (eval_value - cfg.eval_cost) / cfg.eval_cost  # the no-bust expectation for this mode and split; ev / cost for the calculator
    return {
        "inputs": {k: getattr(cfg, k) for k in ("start_cash", "eval_cost", "pass_rate", "payout_rate", "payout_size", "eval_days", "qualifying_days", "payout_processing_days", "funded_mode", "profit_split", "max_live_accounts")},
        "calculator": calc,
        "p_bust": float(bust.mean()),
        "first_payout": {"p_within_3_months": float((first_payout_day < 3 * cfg.trading_days_per_month).mean()), "median_trading_days": pct(first_payout_day, 50), "p_never": float(np.isnan(first_payout_day).mean())},
        "first_funded": {"median_trading_days": pct(first_funded_day, 50), "p_never": float(np.isnan(first_funded_day).mean())},
        "months_to_funded": {str(k): {"median": pct(v, 50), "p_reached": float(np.isfinite(v).mean())} for k, v in months_to_k.items()},
        "funded_last_month": {"p25": pct(funded_by_month[:, last], 25), "median": pct(funded_by_month[:, last], 50), "p75": pct(funded_by_month[:, last], 75)},
        "payouts_last_month": {"p25": pct(payouts_by_month[:, last], 25), "median": pct(payouts_by_month[:, last], 50), "p75": pct(payouts_by_month[:, last], 75)},
        "payouts_count": {"median": pct(n_payouts.astype(float), 50), "mean": float(n_payouts.mean())},
        "cash_last_month": {"p5": pct(cash_by_month[:, last], 5), "median": pct(cash_by_month[:, last], 50)},
        "income_total": {"median": pct(income, 50), "p75": pct(income, 75)},
        "invested_total": {"median": pct(invested, 50), "mean": float(invested.mean())},
        "realised_return_per_eval": pooled,  # sum over paths of (income + cash + in-flight value - start) / sum of invested: the realised ev / cost, which the calculator predicts whatever the bust rate
        "mean_path_return_multiple": float(path_multiple.mean()),  # the average PATH's multiple: dominated by bust paths that invested only their starting cash, so it falls with P(bust) even though the return per evaluation does not
        "benchmark_return_per_eval": float(benchmark),  # single mode, no split: the calculator's ev / cost (+1.178 at his base case)
        "expected_payouts_per_funded_account": float(payouts_per_funded),  # single: payout_rate; repeat: payout_rate / (1 - payout_rate)
        "inflight_value_last": {"median": pct(inflight, 50)},
        "funded_median_by_month": [pct(funded_by_month[:, i], 50) for i in range(cfg.months)],
        "payouts_median_by_month": [pct(payouts_by_month[:, i], 50) for i in range(cfg.months)],
    }


def his_stats_scan(cfg: HisStatsConfig, start_cash=(250.0, 500.0, 1000.0, 2000.0, 5000.0), pass_rates=(0.25, 0.33, 0.40), payout_rates=(0.33,)) -> list[dict]:
    """Bust probability and outcomes across starting bankrolls for every
    combination of `pass_rates` x `payout_rates`; every row labels both rates.
    To vary the evaluation pass rate and the funded payout rate independently
    (one at a time against the base case) hold one list at a single value,
    which is the CLI default (`payout_rates=(0.33,)`) and what
    `--pass-rates 0.33 --payout-rates ...` does for the other axis. Each row
    also carries the closed-form check: P(zero payouts from the evaluations
    the starting cash buys) = (1 - pass x payout) ^ (cash / cost)."""
    from dataclasses import replace
    rows = []
    for pr in pass_rates:
        for qr in payout_rates:
            for c in start_cash:
                r = simulate_his_stats(replace(cfg, start_cash=c, pass_rate=pr, payout_rate=qr))
                n0 = int(c // cfg.eval_cost)
                rows.append({
                    "pass_rate": pr, "payout_rate": qr, "start_cash": c, "ev_per_eval": r["calculator"]["ev_per_eval"],
                    "p_zero_payouts_first_batch": (1.0 - pr * qr) ** n0 if n0 else 1.0,
                    "p_bust": r["p_bust"], "first_payout_median_days": r["first_payout"]["median_trading_days"],
                    "p_5_funded": r["months_to_funded"]["5"]["p_reached"], "funded_last_median": r["funded_last_month"]["median"],
                    "payouts_last_p25": r["payouts_last_month"]["p25"], "payouts_last_median": r["payouts_last_month"]["median"],
                    "income_median": r["income_total"]["median"],
                })
    return rows
