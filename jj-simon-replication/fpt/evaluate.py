"""Walk-forward evaluation of the implemented rules on real trade sequences.

The question JJ says matters is not the win rate but the pass rate: how often
an evaluation reaches its profit target before its drawdown under the firm's
exact rules. This module measures that on the ACTUAL sequence of trades the
backtester produced, day by day, with no independence assumption:

  * `walk_forward_pass_probability`: start one evaluation on every trading day
    of the sample and follow the real subsequent days under `FirmRules` (EOD
    trailing drawdown, soft daily loss limit, consistency, minimum days) until
    it passes, fails or runs out of days. The fraction that pass within the
    horizon is the pass probability; the distribution of days to pass is the
    evaluation time.
  * `walk_forward_payout_probability`: the same for a freshly funded account:
    the fraction that reach a payout (winning days of $150+, buffer, cap)
    before breaching, and the days it takes.
  * `r_distribution_breakdown`: win rate, expectancy, profit factor by year,
    quarter, volatility regime, session and setup.
  * `evaluate_trades`: the whole pipeline with an untouched out-of-sample tail
    (the last `oos_months`) reported separately and never used for tuning.

Days are TRADING days in New York wall-clock time. A trading day on which the
strategy produced no trade still passes (it is a day of the path on which
nothing happened and it does not count toward a firm's minimum trading days),
so the walk-forward functions take the trading-day calendar (`trading_days`,
normally the days present in the bar data); without one they can only see the
days that carry a trade.

Outcome per start: "pass" / "fail" ("payout" / "bust" for a funded start),
"open" when the path used the whole `max_days` horizon without resolving, and
"censored" when the data ended before the path resolved and before the
horizon. Rates are P(outcome within max_days) over the starts that had the
full horizon of data (open counts as not reached); censored starts are
excluded. Neighbouring starts share almost all of their days, so the standard
error is a Newey-West (Bartlett) long-run estimate with bandwidth equal to the
longest path, not the binomial p(1-p)/n of independent trials.

Outputs feed `fpt.bootstrap.simulate_his_stats` with MEASURED pass rate, payout
rate and durations instead of assumed ones.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .bootstrap import HisStatsConfig, his_calculator, simulate_his_stats
from .propfirm import EVAL, FAILED, FIRM_PRESETS, FUNDED, FirmRules, PropAccount

NY = "America/New_York"


def _ny_naive(s: pd.Series) -> pd.Series:
    """New York wall-clock time without tz info: the day key used everywhere in this module.
    tz-aware timestamps in any zone are converted first (a 20:05 ET trade is 01:05 UTC the next day)."""
    if s.dt.tz is not None:
        s = s.dt.tz_convert(NY)
    return s.dt.tz_localize(None)


def _ny_naive_index(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(idx)
    if idx.tz is not None:
        idx = idx.tz_convert(NY)
    return idx.tz_localize(None)


def trading_days_of(bars: pd.DataFrame) -> pd.DatetimeIndex:
    """The trading-day calendar of a bar table: every New York date that has a bar."""
    return pd.DatetimeIndex(_ny_naive_index(bars.index).normalize().unique()).sort_values()


def _calendar(trading_days) -> pd.DatetimeIndex | None:
    if trading_days is None:
        return None
    return pd.DatetimeIndex(_ny_naive_index(pd.DatetimeIndex(trading_days)).normalize().unique()).sort_values()


def _daily_r(trades: pd.DataFrame, trading_days=None) -> tuple[list, list[np.ndarray]]:
    """Trades grouped by New York entry date, in entry order: (dates, [R arrays]).
    With a `trading_days` calendar every calendar day is a row (an empty array on a day without trades)."""
    if trades.empty:
        return [], []
    t = trades.sort_values("entry_time")
    keys = _ny_naive(t["entry_time"]).dt.normalize()
    groups = {d: g["r"].to_numpy(float) for d, g in t.groupby(keys, sort=True)}
    cal = _calendar(trading_days)
    dates = sorted(set(groups) | (set(cal) if cal is not None else set()))
    return dates, [groups.get(d, np.zeros(0)) for d in dates]


def _matrix(rs: list[np.ndarray], idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Day rows for each sim: sim i takes day idx[i] (or nothing if out of range)."""
    rows = [rs[j] if 0 <= j < len(rs) else np.zeros(0) for j in idx]
    maxn = max((len(r) for r in rows), default=0)
    if maxn == 0:
        return np.zeros((len(idx), 1)), np.zeros((len(idx), 1), dtype=bool)
    r = np.zeros((len(idx), maxn))
    mask = np.zeros((len(idx), maxn), dtype=bool)
    for i, row in enumerate(rows):
        r[i, : len(row)] = row
        mask[i, : len(row)] = True
    return r, mask


def walk_forward_pass_probability(trades: pd.DataFrame, rules: FirmRules, eval_risk: float, max_days: int = 30, trading_days=None) -> pd.DataFrame:
    """One evaluation started on every trading day; outcome per start day.

    `days` is the number of trading days the path used, the pass/fail day included; with a `trading_days`
    calendar it counts days without trades too (they do not count toward `rules.min_trading_days`)."""
    dates, rs = _daily_r(trades, trading_days)
    n = len(dates)
    if n == 0:
        return pd.DataFrame(columns=["start", "outcome", "days"])
    acct = PropAccount(rules, sims=n, risk_per_trade=eval_risk, start_phase=EVAL, restart_failed=False, eval_risk=eval_risk)
    outcome = np.array(["open"] * n, dtype=object)
    days = np.full(n, np.nan)
    starts = np.arange(n)
    for k in range(max_days):
        r, mask = _matrix(rs, starts + k)
        alive_before = acct.phase == EVAL
        acct.apply_day(r, mask)
        passed = alive_before & (acct.phase == FUNDED)
        failed = alive_before & (acct.phase == FAILED)
        outcome[passed] = "pass"
        outcome[failed] = "fail"
        days[passed | failed] = np.where(np.isnan(days[passed | failed]), k + 1, days[passed | failed])
        if not (acct.phase == EVAL).any():
            break
    # starts whose path ran off the end of the data before resolving are censored, not failures
    horizon = np.minimum(max_days, n - starts)
    censored = (outcome == "open") & (horizon < max_days)
    outcome[censored] = "censored"
    return pd.DataFrame({"start": dates, "outcome": outcome, "days": days})


def walk_forward_payout_probability(trades: pd.DataFrame, rules: FirmRules, funded_risk: float, max_days: int = 60, trading_days=None) -> pd.DataFrame:
    """A fresh funded account started on every trading day; first payout or breach.
    `payout_now` is asked every day; a path is retired after its first payout."""
    dates, rs = _daily_r(trades, trading_days)
    n = len(dates)
    if n == 0:
        return pd.DataFrame(columns=["start", "outcome", "days", "amount"])
    acct = PropAccount(rules, sims=n, risk_per_trade=funded_risk, start_phase=FUNDED, restart_failed=False)
    outcome = np.array(["open"] * n, dtype=object)
    days = np.full(n, np.nan)
    amount = np.zeros(n)
    starts = np.arange(n)
    for k in range(max_days):
        r, mask = _matrix(rs, starts + k)
        live = acct.phase == FUNDED
        acct.apply_day(r, mask)
        paid = acct.payout_now()
        got = live & (paid > 0) & (outcome == "open")
        bust = live & (acct.phase == FAILED) & (outcome == "open")
        outcome[got] = "payout"
        amount[got] = paid[got]
        outcome[bust] = "bust"
        days[got | bust] = k + 1
        acct.phase[got] = FAILED  # retire paid paths: we measure the first payout only
        if not (acct.phase == FUNDED).any():
            break
    horizon = np.minimum(max_days, n - starts)
    censored = (outcome == "open") & (horizon < max_days)
    outcome[censored] = "censored"
    return pd.DataFrame({"start": dates, "outcome": outcome, "days": days, "amount": amount})


def _newey_west_se(y: np.ndarray, bandwidth: int) -> float:
    """Standard error of the mean of a serially dependent 0/1 sequence: Bartlett-kernel long-run variance."""
    n = len(y)
    if n == 0:
        return float("nan")
    yc = y - y.mean()
    v = float(yc @ yc) / n
    for k in range(1, min(int(bandwidth), n - 1) + 1):
        v += 2.0 * (1.0 - k / (bandwidth + 1.0)) * float(yc[:-k] @ yc[k:]) / n
    return float(np.sqrt(max(v, 0.0) / n))


def _rate(df: pd.DataFrame, good: str, bad: str, horizon: int | None = None) -> dict:
    """P(good within the horizon) over the starts that had the full horizon of data (good, bad and open),
    with a dependence-aware standard error (starts overlap in time), the median days to `good`, and the counts.
    `rate_resolved` is the older good / (good + bad) conditional on resolving."""
    seen = df[df["outcome"].isin([good, bad, "open"])].sort_values("start")
    y = (seen["outcome"] == good).to_numpy(float)
    n = len(y)
    resolved = seen[seen["outcome"] != "open"]
    n_open = int((seen["outcome"] == "open").sum())
    p = float(y.mean()) if n else float("nan")
    d_all = resolved["days"].to_numpy(float)
    bw = int(np.nanmax(d_all)) if len(d_all) else 0
    if n_open and horizon is not None:
        bw = max(bw, int(horizon))
    se = _newey_west_se(y, bw) if n else float("nan")
    d = resolved.loc[resolved["outcome"] == good, "days"]
    n_res = len(resolved)
    return {"n_starts": int(len(df)), "n_seen": n, "n_resolved": n_res, "n_open": n_open, "rate": p,
            "rate_resolved": float((resolved["outcome"] == good).mean()) if n_res else float("nan"), "stderr": se,
            "days_median": float(d.median()) if len(d) else float("nan"), "n_censored": int((df["outcome"] == "censored").sum())}


def r_distribution_breakdown(trades: pd.DataFrame, regime: pd.Series | None = None, trading_days=None) -> pd.DataFrame:
    """Win rate, expectancy and profit factor by year, quarter, session, setup and regime.
    trades/day divides by the trading days of the bucket when a `trading_days` calendar is given
    (a day without trades is a day), otherwise by the days that carry a trade."""
    if trades.empty:
        return pd.DataFrame()
    t = trades.copy()
    et = _ny_naive(t["entry_time"])
    t["day"] = et.dt.normalize()
    t["year"] = et.dt.year.astype(str)
    t["quarter"] = et.dt.to_period("Q").astype(str)
    if regime is not None:
        t["regime"] = t["day"].map(regime).fillna("n/a")
    cal = _calendar(trading_days)
    cal_df = None
    if cal is not None and len(cal):
        cal_df = pd.DataFrame({"year": cal.year.astype(str), "quarter": cal.to_period("Q").astype(str)}, index=cal)
        if regime is not None:
            cal_df["regime"] = cal_df.index.map(regime).fillna("n/a")
    day_level = {"year", "quarter", "regime"}
    rows = []

    def stats(name, key, g):
        wins = g[g["r"] > 0]["r"].sum()
        losses = -g[g["r"] <= 0]["r"].sum()
        if cal_df is None:
            ndays = g["day"].nunique()
        elif name in day_level:
            ndays = int((cal_df[name] == str(key)).sum())
        else:
            ndays = len(cal_df)
        rows.append({"dimension": name, "bucket": str(key), "trades": int(len(g)), "win_rate": float((g["r"] > 0).mean()), "expectancy_r": float(g["r"].mean()),
                     "profit_factor": float(wins / losses) if losses > 0 else float("inf"), "net_r": float(g["r"].sum()), "trades_per_day": float(len(g) / max(1, ndays))})
    stats("all", "all", t)
    for dim in ["year", "quarter", "session", "setup", "grade", "direction"] + (["regime"] if regime is not None else []):
        for key, g in t.groupby(dim):
            stats(dim, key, g)
    return pd.DataFrame(rows)


def volatility_regime(bars: pd.DataFrame, period: int = 14, fit_through=None) -> pd.Series:
    """Per-day regime label (low / mid / high) from the mean 1-minute ATR between 09:30 and 11:00 New York time.
    The tercile thresholds are fitted on the days up to `fit_through` (the in-sample cut) and applied to every day,
    so an out-of-sample tail never moves the in-sample labels."""
    from .indicators import atr
    a = atr(bars, period).to_numpy(float)
    idx = _ny_naive_index(bars.index)
    m = idx.hour * 60 + idx.minute
    sel = (m >= 570) & (m < 660)
    daily = pd.Series(a[sel], index=idx[sel].normalize()).groupby(level=0).mean().dropna()
    if daily.empty:
        return pd.Series(dtype=object)
    fit = daily if fit_through is None else daily[daily.index <= pd.Timestamp(fit_through)]
    if fit.empty:
        fit = daily
    q1, q2 = fit.quantile([1 / 3, 2 / 3])
    return daily.apply(lambda v: "low" if v <= q1 else ("high" if v > q2 else "mid"))


@dataclass
class EvaluationReport:
    tables: dict
    text: str


def evaluate_trades(trades: pd.DataFrame, bars: pd.DataFrame | None = None, firms: tuple[str, ...] = ("topstep_50k", "fundednext_50k_flex", "topstep_100k", "tradeify_100k_growth"),
                    eval_risk_mode: str = "two_trade", eval_risk: float = 500.0, funded_risk: float = 500.0, oos_months: int = 3, max_eval_days: int = 30, max_funded_days: int = 60,
                    start_cash=(500.0, 1000.0, 2000.0, 5000.0)) -> EvaluationReport:
    """The pipeline: R distribution -> pass probability per firm rule -> funded payout probability -> bootstrap survival, in-sample and out-of-sample.

    The split is by New York trading day: the in-sample part ends on the day `oos_months` before the last trade's day
    (`cut`), the out-of-sample part is every later day. Nothing from the tail reaches the in-sample numbers: the
    walk-forward paths use only the part's own days (a path that reaches the cut unresolved is censored), the
    volatility-regime terciles are fitted on bars up to the cut, and the trading-day calendar is split at the cut."""
    tables: dict = {}
    lines = ["# Evaluation of the implemented rules on this data", ""]
    if trades.empty:
        return EvaluationReport(tables, "no trades")
    day = _ny_naive(trades["entry_time"]).dt.normalize()
    last = day.max()
    cut = (last - pd.DateOffset(months=oos_months)).normalize()
    ins, oos = trades[day <= cut], trades[day > cut]
    cal = trading_days_of(bars) if bars is not None else None
    regime = volatility_regime(bars, fit_through=cut) if bars is not None else None
    lines += [f"Trades: {len(trades)} from {day.min().date()} to {last.date()}; in-sample through {cut.date()} ({len(ins)} trades), out-of-sample after it ({len(oos)} trades, untouched by any tuning).",
              "Days are New York trading days (every day with bars, traded or not); rates are the share of starts that reached the outcome within the horizon, with open starts counted as not reached and starts cut off by the end of the data excluded; +/- is a Newey-West standard error that allows for the overlap of neighbouring starts.", ""]
    for label, part in (("in_sample", ins), ("out_of_sample", oos)):
        if part.empty:
            continue
        cal_part = None if cal is None else (cal[cal <= cut] if label == "in_sample" else cal[cal > cut])
        bd = r_distribution_breakdown(part, regime, trading_days=cal_part)
        tables[f"r_{label}"] = bd
        lines += [f"## R distribution, {label.replace('_', ' ')}", "", "| dimension | bucket | trades | win rate | expectancy R | profit factor | trades/day |", "|---|---|---|---|---|---|---|"]
        for _, r in bd.iterrows():
            pf = "inf" if np.isinf(r["profit_factor"]) else f"{r['profit_factor']:.2f}"
            lines.append(f"| {r['dimension']} | {r['bucket']} | {r['trades']} | {r['win_rate']:.1%} | {r['expectancy_r']:+.3f} | {pf} | {r['trades_per_day']:.2f} |")
        lines.append("")
        rows = []
        for key in firms:
            rules = FIRM_PRESETS[key]
            er = rules.profit_target / (2.0 * 1.5) if eval_risk_mode == "two_trade" else eval_risk
            pp = walk_forward_pass_probability(part, rules, er, max_eval_days, trading_days=cal_part)
            pr = walk_forward_payout_probability(part, rules, funded_risk, max_funded_days, trading_days=cal_part)
            a, b = _rate(pp, "pass", "fail", horizon=max_eval_days), _rate(pr, "payout", "bust", horizon=max_funded_days)
            rows.append({"firm": key, "eval_risk": er, "pass_rate": a["rate"], "pass_stderr": a["stderr"], "eval_days_median": a["days_median"], "n_eval_starts": a["n_seen"], "n_eval_open": a["n_open"], "n_eval_censored": a["n_censored"],
                         "payout_rate": b["rate"], "payout_stderr": b["stderr"], "payout_days_median": b["days_median"], "n_funded_starts": b["n_seen"], "n_funded_open": b["n_open"], "n_funded_censored": b["n_censored"],
                         "payout_median_amount": float(pr.loc[pr["outcome"] == "payout", "amount"].median()) if (pr["outcome"] == "payout").any() else float("nan")})
            tables[f"pass_{label}_{key}"] = pp
            tables[f"payout_{label}_{key}"] = pr
            # pass probability by year / quarter / regime of the start day
            pp2 = pp.copy()
            pp2["year"] = pd.to_datetime(pp2["start"]).dt.year
            pp2["quarter"] = pd.to_datetime(pp2["start"]).dt.to_period("Q").astype(str)
            if regime is not None:
                pp2["regime"] = pd.to_datetime(pp2["start"]).map(regime).fillna("n/a")
            sub = []
            for dim in ["year", "quarter"] + (["regime"] if regime is not None else []):
                for k, g in pp2.groupby(dim):
                    s = _rate(g, "pass", "fail", horizon=max_eval_days)
                    sub.append({"firm": key, "dimension": dim, "bucket": str(k), "n": s["n_seen"], "n_open": s["n_open"], "pass_rate": s["rate"], "stderr": s["stderr"]})
            tables[f"pass_breakdown_{label}_{key}"] = pd.DataFrame(sub)
        fr = pd.DataFrame(rows)
        tables[f"firms_{label}"] = fr
        lines += [f"## Pass and payout probability under exact firm rules, {label.replace('_', ' ')} (one evaluation / funded account started on every trading day)", "",
                  f"| firm | eval risk | P(pass) within {max_eval_days} days | +/- | days to pass (median) | starts (open) | P(payout before breach) within {max_funded_days} days | +/- | days to payout | starts (open) | payout (median $) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in fr.iterrows():
            lines.append(f"| {r['firm']} | {r['eval_risk']:,.0f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {r['eval_days_median']:.0f} | {r['n_eval_starts']} ({r['n_eval_open']}) | {r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_days_median']:.0f} | {r['n_funded_starts']} ({r['n_funded_open']}) | {r['payout_median_amount']:,.0f} |")
        lines.append("")
        for key in firms:
            bdp = tables[f"pass_breakdown_{label}_{key}"]
            if bdp.empty:
                continue
            lines += [f"Pass probability by start period, {key}: " + "; ".join(f"{r['dimension']} {r['bucket']}: {r['pass_rate']:.0%} (n={r['n']})" for _, r in bdp.iterrows()), ""]
        # bootstrap survival from MEASURED inputs (first firm with resolved starts)
        for _, r in fr.iterrows():
            if np.isnan(r["pass_rate"]) or np.isnan(r["payout_rate"]):
                continue
            rules = FIRM_PRESETS[r["firm"]]
            cost = rules.eval_cost
            size = r["payout_median_amount"] if not np.isnan(r["payout_median_amount"]) else rules.profit_target / 2
            calc = his_calculator(cost, r["pass_rate"], r["payout_rate"], size)
            lines += [f"## Bootstrap survival from the measured inputs ({label.replace('_', ' ')}, {r['firm']}: ${cost:,.0f} per evaluation, pass {r['pass_rate']:.0%}, payout {r['payout_rate']:.0%} of ${size:,.0f}, {r['eval_days_median']:.0f} days to pass, {r['payout_days_median']:.0f} days to payout)", "",
                      f"Calculator: gross ${calc['gross_return_per_eval']:,.0f} per evaluation, EV {calc['ev_per_eval']:+,.0f}, P(payout per evaluation) {calc['p_payout_per_eval']:.1%}.", "",
                      "| start cash | P(bust, 12 months) | P(zero payouts, first batch) | median first payout (days) | funded accounts month 12 (median) |", "|---|---|---|---|---|"]
            for c in start_cash:
                sim = simulate_his_stats(HisStatsConfig(start_cash=c, eval_cost=cost, pass_rate=r["pass_rate"], payout_rate=r["payout_rate"], payout_size=size,
                                                        eval_days=int(max(1, np.nan_to_num(r["eval_days_median"], nan=5))), qualifying_days=int(max(1, np.nan_to_num(r["payout_days_median"], nan=10))), sims=2000))
                n0 = int(c // cost)
                lines.append(f"| {c:,.0f} | {sim['p_bust']:.0%} | {(1 - calc['p_payout_per_eval']) ** n0:.0%} | {sim['first_payout']['median_trading_days']:.0f} | {sim['funded_last_month']['median']:.0f} |")
            lines.append("")
            break
    return EvaluationReport(tables, "\n".join(lines))
