"""Risk model: ATR-tier stops, contract sizing, expectancy, optimal-risk
and stop-trading mathematics.

Public parameters (fxreplay's codification of JJ Simon's rules, see
docs/DOSSIER.md):
    1-minute ATR above 20  -> 50-point stop, 1 NQ contract
    1-minute ATR 7 to 20   -> 25-point stop, 2 NQ contracts
    1-minute ATR below 7   -> 16.5-point stop, 3 NQ contracts
    NQ = $20 per point, so every tier risks ~ $1,000; target is a fixed 1.5R
    with no trade management.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

NQ_POINT_VALUE = 20.0
MNQ_POINT_VALUE = 2.0

# (min_atr_inclusive, stop_points, contracts)
DEFAULT_ATR_TIERS: tuple[tuple[float, float, int], ...] = (
    (20.0, 50.0, 1),
    (7.0, 25.0, 2),
    (0.0, 16.5, 3),
)


@dataclass(frozen=True)
class Tier:
    name: str
    min_atr: float
    stop_points: float
    contracts: int


def atr_tier(atr_value: float, tiers=DEFAULT_ATR_TIERS) -> Tier:
    """Map a 1-minute ATR reading to its stop distance and contract count."""
    if atr_value is None or (isinstance(atr_value, float) and math.isnan(atr_value)):
        raise ValueError("ATR is NaN")
    ordered = sorted(tiers, key=lambda t: -t[0])
    for i, (lo, stop, n) in enumerate(ordered):
        if atr_value >= lo:
            return Tier(name=f"tier{i + 1}", min_atr=lo, stop_points=stop, contracts=n)
    lo, stop, n = ordered[-1]
    return Tier(name=f"tier{len(ordered)}", min_atr=lo, stop_points=stop, contracts=n)


def contracts_for_risk(risk_dollars: float, stop_points: float, point_value: float = NQ_POINT_VALUE, max_contracts: int | None = None) -> int:
    """Largest whole number of contracts whose stop-out loss is <= risk_dollars."""
    if stop_points <= 0 or point_value <= 0:
        raise ValueError("stop_points and point_value must be positive")
    n = int(risk_dollars // (stop_points * point_value))
    if max_contracts is not None:
        n = min(n, max_contracts)
    return max(n, 0)


def dollar_risk(stop_points: float, contracts: int, point_value: float = NQ_POINT_VALUE) -> float:
    return stop_points * contracts * point_value


# ---------------------------------------------------------------------------
# Edge mathematics
# ---------------------------------------------------------------------------

def implied_daily_r(payout_dollars: float, accounts: int, trading_days: int, risk_per_trade: float) -> dict:
    """Back out the per-account daily edge implied by a reported result.

    Example: "$105,700 in 3 weeks" across ~40 accounts at ~$1,000 risk per
    trade -> 105,700 / (40 * 15) / 1,000 = 0.176 R of PAYOUT per account per
    day. At 54% / 1.5R (0.35R per trade) that is what about 0.5 qualifying
    trades a day would produce if payouts equalled P&L; payouts are net of
    splits, caps, evaluation-phase accounts and breaches, so gross P&L and the
    trade count behind it are higher. It is nowhere near the 3.5 R/day that
    "10 trades a day at 54%" would produce.
    """
    per_account_day = payout_dollars / (accounts * trading_days)
    return {
        "dollars_per_account_day": per_account_day,
        "r_per_account_day": per_account_day / risk_per_trade,
        "dollars_per_day_all_accounts": payout_dollars / trading_days,
    }


def trades_per_day_for_daily_r(daily_r: float, p_win: float, rr: float) -> float:
    """Number of trades per day needed for a p / rr edge to produce daily_r."""
    e = expectancy_r(p_win, rr)
    return float("inf") if e <= 0 else daily_r / e


def expectancy_r(p_win: float, rr: float) -> float:
    """Expected R per trade for win probability p and reward:risk rr."""
    return p_win * rr - (1.0 - p_win)


def breakeven_winrate(rr: float) -> float:
    return 1.0 / (1.0 + rr)


def kelly_fraction(p_win: float, rr: float) -> float:
    """Full Kelly fraction of bankroll to risk per trade for a p / rr bet.
    For a prop account the relevant bankroll is the drawdown allowance,
    not the nominal account size."""
    return max(p_win - (1.0 - p_win) / rr, 0.0)


def expected_max_losing_streak(p_win: float, n_trades: int) -> float:
    """Schilling (1990) approximation of the expected longest run of losses in
    n trades: log_{1/q}(n p) + gamma / ln(1/q) - 1/2."""
    q = 1.0 - p_win
    if q <= 0 or n_trades <= 0 or n_trades * p_win <= 1:
        return 0.0
    ln_inv_q = math.log(1.0 / q)
    return math.log(n_trades * p_win) / ln_inv_q + 0.5772156649 / ln_inv_q - 0.5


def losing_streak_quantiles(p_win: float, n_trades: int, quantiles=(0.5, 0.9, 0.99), sims: int = 20000, seed: int = 0) -> dict[float, int]:
    """Monte Carlo quantiles of the longest losing streak over n_trades."""
    rng = np.random.default_rng(seed)
    outcomes = rng.random((sims, n_trades)) >= p_win  # True = loss
    longest = np.zeros(sims, dtype=int)
    run = np.zeros(sims, dtype=int)
    for j in range(n_trades):
        run = np.where(outcomes[:, j], run + 1, 0)
        longest = np.maximum(longest, run)
    return {q: int(np.quantile(longest, q)) for q in quantiles}


def risk_of_ruin(p_win: float, rr: float, risk_fraction: float, ruin_fraction: float = 1.0, n_trades: int = 1000, sims: int = 20000, seed: int = 0) -> float:
    """Probability that cumulative loss reaches `ruin_fraction` of the
    bankroll within n_trades when each trade risks `risk_fraction` of the
    STARTING bankroll (fixed-dollar sizing, which is what a fixed $1,000 risk
    per trade on a prop account is)."""
    rng = np.random.default_rng(seed)
    wins = rng.random((sims, n_trades)) < p_win
    pnl = np.where(wins, rr * risk_fraction, -risk_fraction)
    equity = np.cumsum(pnl, axis=1)
    ruined = (equity <= -ruin_fraction).any(axis=1)
    return float(ruined.mean())


def daily_stop_from_stats(p_win: float, rr: float, trades_per_day: float, risk_per_trade: float, quantile: float = 0.05, sims: int = 50000, seed: int = 0) -> dict:
    """"Knowing exactly when to stop": the daily loss at which a day has
    become statistically abnormal for an edge with these parameters.

    Simulates days with Poisson(trades_per_day) trades. `stop_r` is the
    `quantile` (default 5th percentile) of the day's RUNNING loss (the worst
    point reached during the day), which is the number to use as an intraday
    stop: a day whose running loss crosses it is outside what the edge should
    produce, so the trader stops. `close_quantile_r` is the same quantile of
    the day's closing P&L (less negative, since a day can recover). Also
    returns the expected daily P&L and the probability a day ends negative.
    """
    rng = np.random.default_rng(seed)
    n = rng.poisson(trades_per_day, size=sims)
    maxn = int(n.max()) if sims else 0
    wins = rng.random((sims, max(maxn, 1))) < p_win
    r = np.where(wins, rr, -1.0)
    mask = np.arange(max(maxn, 1))[None, :] < n[:, None]
    path = np.cumsum(r * mask, axis=1)
    daily_r = path[:, -1]
    run_min = np.minimum(0.0, path.min(axis=1))
    q_r = float(np.quantile(run_min, quantile))
    q_close = float(np.quantile(daily_r, quantile))
    return {
        "quantile": quantile,
        "stop_r": q_r,
        "stop_dollars": q_r * risk_per_trade,
        "close_quantile_r": q_close,
        "expected_daily_r": float(daily_r.mean()),
        "expected_daily_dollars": float(daily_r.mean() * risk_per_trade),
        "p_negative_day": float((daily_r < 0).mean()),
        "daily_r_std": float(daily_r.std()),
    }


def optimal_fixed_risk(p_win: float, rr: float, drawdown_allowance: float, target: float, trades_per_day: float, max_days: int, candidates=None, sims: int = 4000, seed: int = 0, drawdown_type: str = "static", lock_profit: float | None = None, daily_loss_limit: float | None = None) -> list[dict]:
    """P(pass the evaluation) versus fixed dollar risk per trade.

    drawdown_type: "static" (loss measured from the start balance),
    "trailing_eod" (the threshold trails the end-of-day equity peak) or
    "trailing_intraday" (it trails the intraday peak of the trade path).
    lock_profit: the trailing threshold stops rising once the peak reaches
    this profit (Topstep: lock_profit = drawdown, so it locks at the start).
    daily_loss_limit: a soft daily stop; the day ends at the limit.
    Consistency and minimum-day rules are not applied.
    """
    rng = np.random.default_rng(seed)
    if candidates is None:
        candidates = [drawdown_allowance * f for f in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50)]
    out = []
    trailing = drawdown_type in ("trailing_eod", "trailing_intraday")
    for risk in candidates:
        n = rng.poisson(trades_per_day, size=(sims, max_days))
        equity = np.zeros(sims)
        peak = np.zeros(sims)
        passed = np.zeros(sims, dtype=bool)
        failed = np.zeros(sims, dtype=bool)
        days_to_pass = np.full(sims, np.nan)
        for d in range(max_days):
            nd = n[:, d]
            maxn = int(nd.max()) if nd.size else 0
            if maxn == 0:
                continue
            wins = rng.random((sims, maxn)) < p_win
            r = np.where(wins, rr, -1.0) * risk
            mask = np.arange(maxn)[None, :] < nd[:, None]
            path = np.cumsum(r * mask, axis=1)
            if daily_loss_limit is not None:
                hit = path <= -daily_loss_limit
                any_hit = hit.any(axis=1)
                first = np.where(any_hit, hit.argmax(axis=1), maxn - 1)
                held = path[np.arange(sims), first][:, None]
                path = np.where(np.arange(maxn)[None, :] <= first[:, None], path, held)
                path = np.where(any_hit[:, None], np.maximum(path, -daily_loss_limit), path)  # liquidated at the limit
            eq_path = equity[:, None] + path
            alive = ~(passed | failed)
            if drawdown_type == "trailing_intraday":
                run_peak = np.maximum(peak[:, None], np.maximum.accumulate(eq_path, axis=1))
                if lock_profit is not None:
                    run_peak = np.minimum(run_peak, lock_profit)
                breach = alive & ((eq_path <= run_peak - drawdown_allowance).any(axis=1))
            else:
                ref = np.minimum(peak, lock_profit) if (trailing and lock_profit is not None) else (peak if trailing else 0.0)
                breach = alive & (eq_path.min(axis=1) <= ref - drawdown_allowance)
            failed |= breach
            alive = ~(passed | failed)
            equity = np.where(alive, eq_path[:, -1], equity)
            if trailing:
                day_peak = eq_path.max(axis=1) if drawdown_type == "trailing_intraday" else equity
                peak = np.where(alive, np.maximum(peak, day_peak), peak)
            newly = alive & (equity >= target)
            days_to_pass[newly] = d + 1
            passed |= newly
        out.append({
            "risk_per_trade": float(risk),
            "risk_pct_of_drawdown": float(risk / drawdown_allowance),
            "p_pass": float(passed.mean()),
            "p_fail": float(failed.mean()),
            "median_days_to_pass": float(np.nanmedian(days_to_pass)) if passed.any() else float("nan"),
        })
    return out


# ---------------------------------------------------------------------------
# JJ Simon's prop-firm arithmetic (his own framing, see docs/DOSSIER.md s.4)
# ---------------------------------------------------------------------------

def cost_to_funded(eval_fee: float, pass_rate: float) -> float:
    """Expected spend to get one funded account: fee / pass rate
    (his example: $100 / 0.30 = $333)."""
    return eval_fee / pass_rate if pass_rate > 0 else float("inf")


def cost_per_drawdown_dollar(eval_fee: float, drawdown: float) -> float:
    """Dollars paid per dollar of drawdown bought (his example: $750 for
    $4,500 of drawdown = $0.166 per $1)."""
    return eval_fee / drawdown


def eval_expected_value(p_payout: float, payout: float, eval_fee: float) -> float:
    """EV of buying one evaluation as JJ frames it: p * payout - (1 - p) * fee
    (his example: 10% x $2,000 - 90% x $100 = +$110). This is only the true EV
    when `payout` is the net result of a passing evaluation (after its fee);
    for a gross payout the EV is p * payout - fee, which makes his example
    +$100."""
    return p_payout * payout - (1.0 - p_payout) * eval_fee


def two_trade_pass_probability(p_win: float, strict: bool = True) -> float:
    """Evaluation posture: max risk, target cleared by two 1.5R wins.
    strict=True: pass only on win-win (his '1 in 4 at 50%').
    strict=False: two wins before two losses (WW, WLW, LWW)."""
    p, q = p_win, 1.0 - p_win
    return p * p if strict else p * p + 2 * p * p * q
