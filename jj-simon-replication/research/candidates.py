"""B3: candidate trade streams under the frozen firm rules.

Each candidate is a stream of sealed entries with a per-trade outcome taken either from the ledger or from
research/bracket_replay.py's per-trade file, put through the sequential pass of research/ledger_filters.py (one
position at a time, the three-loss session stop, each trade's own exit time). Every stream is then scored with the
frozen evaluator's own walk-forward functions (fpt.evaluate.walk_forward_pass_probability,
walk_forward_payout_probability and _rate) under the four firm presets, as fpt.evaluate.evaluate_trades does, except
that the cut between development and benchmark is fixed at the sealed run's cut (the frozen function moves the cut
with each stream's last trade day). EV per evaluation and the bootstrap use the frozen calculator and simulator
(fpt.bootstrap.his_calculator, simulate_his_stats) with the frozen report's inputs, payout-size fallback included.

Gates before anything is reported: the trades, bars and sealed report given are the sealed run's (sha256 against the
manifest), the replay file holds every variant this tool reads, and the sealed ledger scored this way reproduces the
eight firm rows of the sealed report character for character. Otherwise the tool refuses.

Streams (provenance: docs/reviews/run1_b2_read.md):
  S0   sealed ledger (the gate stream)
  S0r  sealed brackets replayed, flat at 16:00: the control for S1-S4 (same entries, same flat); S0 differs from it
       by the entries the replay drops for lack of context and by the ledger's exits after 16:00
  S1   continuation only, sealed bracket. Exact: its entries are those of a frozen-engine run with reversion off
       (less the entries the replay drops for lack of context), because a reversion can never precede or block a
       continuation in a session
  S2   continuation, plus reversion A+ only (his funded entry trigger), sealed bracket
  S3   continuation only, with the bracket chosen year by year by the pooled walk-forward over earlier development
       years among the ATR-scaled brackets (the sealed bracket before the chain starts; benchmark trades take the
       choice made on all development years)
  S4   S3's continuation plus A+ reversion with the sealed bracket
Only development trades (New York day on or before the cut) enter any choice; the benchmark is never used to choose.
S2-S4 are built from the sealed entries, so they cannot contain an A+ reversion the sealed three-loss stop or open
position suppressed, nor a continuation re-entry an earlier ATR exit would have freed: research/engine.py re-simulates
whatever survives.

Sizing. The frozen account books every trade at R x its risk budget whatever the stop (fractional contracts). At
that sizing a sealed stop-out costs 1.02 R with slippage and commission, so two of them cost $2,040 against Topstep
50K's $2,000 drawdown and end the evaluation (on the frozen preset its $1,000 soft daily limit caps each at exactly
$1,000 and the balance lands on the threshold, which also fails). Sized 2% smaller the account fails on the third
stop-out instead, and two wins (2.96 R) no longer reach the target. Every Topstep 50K rate and Topstep 100K's payout
rates at the sealed sizing, the sealed report's included, sit on this edge (a Topstep 100K evaluation fails on two
stop-outs at any size), so B3 shows each stream at 1.00, 0.98 and 0.95 of the budget and in
whole micro NQ contracts (the largest count whose full stop-out, slippage and commission included, stays strictly
within the budget; entries that round to zero skipped; R scaled by the risk carried). Both tables use the TopstepX
preset, which has no daily limit: below the sealed sizing (and, at it, after a day that started with a win) the
frozen account's soft daily limit would credit a later trade on a day that has nearly reached the limit with a full
win but a loss cut to the room left, which no real account allows. That also slightly favours the streams that
trade more than once a day on the frozen preset at the sealed sizing, so streams are best compared in the TopstepX
1.00 column.

Plus a direction split (long / short) of continuation under the sealed bracket, S3's brackets and the hold-to-16:00
control, and a drift control for the hold: each trade held to 16:00 against the same-direction trade from the same
minute, averaged over every non-roll trading day of the same period label (a development calendar year, the
development part of 2025 for 2025, or the benchmark period) that has a bar at that minute. The two carry identical
costs, so their difference is d x (the trade's move - the mean move) / 25 points: what the direction call adds beyond
the market's drift; it is also given per daily ATR, so years at 2,000 and at 25,000 count alike. A continuation
edge that is only the 2020-2026 bull market shows up as long winners, short losers and no excess.

usage: python research/candidates.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv --source-tz UTC \
           --oos-start 2025-10-06 --manifest sealed/run1/manifest.json --report sealed/run1/report.md \
           --replay-csv research/private/run1_bracket_replay_b2.csv --out research/staging/run1_b3.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.bootstrap import HisStatsConfig, his_calculator, simulate_his_stats  # noqa: E402
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from fpt.evaluate import _daily_r, _rate, trading_days_of, walk_forward_pass_probability, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import FIRM_PRESETS  # noqa: E402
from research.anatomy import daily_context, exclude_roll_trades, load_trades  # noqa: E402
from research.bracket_replay import COMMISSION_RT, FIXED_STOP, POINT_VALUE, SLIPPAGE, grid  # noqa: E402
from research.ledger_filters import apply_filter, build_gates, check_alignment, sequential_pass  # noqa: E402

FIRMS = ("topstep_50k", "fundednext_50k_flex", "topstep_100k", "tradeify_100k_growth")
# the frozen presets plus one research variant (fpt/ is untouched): TopstepX accounts created or reset since 2024-08-25
# have no daily loss limit in the Combine or the Express Funded Account (Topstep help centre article 8284207, read
# through a search engine; three third-party guides agree), and new Combines are TopstepX only
PRESETS = {**FIRM_PRESETS, "topstep_50k_x": FIRM_PRESETS["topstep_50k"].with_(
    plan="50K Trading Combine -> Express Funded, TopstepX (no daily loss limit)", daily_loss_limit=None, verified=False,
    notes="research variant of topstep_50k without the daily loss limit, as TopstepX accounts since 2024-08-25; everything else as topstep_50k")}
# below the sealed sizing (and, at it, after a day that started with a win) the frozen account's soft daily limit
# credits a later trade on a day that has nearly reached the limit with a full win but a loss cut to the room left,
# which no real account allows; the sizing tables therefore use only the preset without a daily limit (the frozen
# topstep_50k appears at the sealed sizing only)
SIZING_FIRMS = ("topstep_50k_x",)
MAX_EVAL_DAYS, MAX_FUNDED_DAYS, FUNDED_RISK = 30, 60, 500.0
START_CASH = (500.0, 1000.0, 2000.0, 5000.0)  # the frozen report's bootstrap rows
ATR_NAMES = [v["name"] for v in grid() if v["family"] == "atr"]
NEEDED_VARIANTS = ["ledger_bracket", "hold_to_1600", *ATR_NAMES]
CHAIN_START = 3  # as research/bracket_replay.walk_forward: the chain starts at the fourth development year
MNQ_POINT_VALUE = 2.0  # micro E-mini Nasdaq-100, first traded 2019-05-06
MICROS_PER_MINI = 10  # the firms count ten micros as one mini against the contract limit
BILLING_DAYS = 30  # calendar days in a billing month
MICRO_COMMISSION_RT = COMMISSION_RT / MICROS_PER_MINI  # the replay's $5 per NQ round trip, per micro: $0.50 (real micro fees run higher)
SIZES = (1.00, 0.98, 0.95)  # fractional sizes around Topstep's daily-loss-limit edge


def firm_rows(part: pd.DataFrame, cal_part: pd.DatetimeIndex, firms=FIRMS, eval_risk_mode: str = "two_trade", eval_risk: float = 500.0,
              funded_part: pd.DataFrame | None = None) -> pd.DataFrame:
    """The firm table of fpt.evaluate.evaluate_trades for one part of the data, computed with its own functions.
    `funded_part` (default: `part`) is the stream the funded phase trades, when it differs from the evaluation's."""
    funded_part = part if funded_part is None else funded_part
    rows = []
    for key in firms:
        rules = PRESETS[key]
        er = rules.profit_target / (2.0 * 1.5) if eval_risk_mode == "two_trade" else eval_risk
        pp = walk_forward_pass_probability(part, rules, er, MAX_EVAL_DAYS, trading_days=cal_part)
        pr = walk_forward_payout_probability(funded_part, rules, FUNDED_RISK, MAX_FUNDED_DAYS, trading_days=cal_part)
        a, b = _rate(pp, "pass", "fail", horizon=MAX_EVAL_DAYS), _rate(pr, "payout", "bust", horizon=MAX_FUNDED_DAYS)
        run = pp[pp["outcome"] != "censored"]
        dates = pd.DatetimeIndex(_daily_r(part, cal_part)[0])  # the frozen walk-forward's own day index
        pos = dates.get_indexer(pd.DatetimeIndex(run["start"]))
        used = np.where(run["outcome"] == "open", MAX_EVAL_DAYS, run["days"].to_numpy(float)).astype(int)  # an open evaluation ran the full horizon
        last = np.minimum(pos + used - 1, len(dates) - 1)
        months = 1 + ((dates[last] - dates[pos]).days.to_numpy() // BILLING_DAYS)  # billed on the start date and every 30 calendar days after
        rows.append({"firm": key, "eval_risk": er, "pass_rate": a["rate"], "pass_stderr": a["stderr"], "eval_days_median": a["days_median"],
                     "eval_months_mean": float(months.mean()) if len(run) else float("nan"),
                     "n_eval_starts": a["n_seen"], "n_eval_open": a["n_open"], "payout_rate": b["rate"], "payout_stderr": b["stderr"],
                     "payout_days_median": b["days_median"], "n_funded_starts": b["n_seen"], "n_funded_open": b["n_open"],
                     "payout_median_amount": float(pr.loc[pr["outcome"] == "payout", "amount"].median()) if (pr["outcome"] == "payout").any() else float("nan")})
    return pd.DataFrame(rows)


def format_row(r: dict) -> str:
    """Exactly the frozen report's firm-row format."""
    return (f"| {r['firm']} | {r['eval_risk']:,.0f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {r['eval_days_median']:.0f} | {r['n_eval_starts']} ({r['n_eval_open']}) | "
            f"{r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_days_median']:.0f} | {r['n_funded_starts']} ({r['n_funded_open']}) | {r['payout_median_amount']:,.0f} |")


def payout_size(r: dict) -> float:
    """The frozen report's payout size: the median payout, or half the profit target when no payout happened."""
    size = r["payout_median_amount"]
    return float(size) if np.isfinite(size) else PRESETS[r["firm"]].profit_target / 2


def ev_per_eval(r: dict) -> float:
    if not np.isfinite(r["pass_rate"]) or not np.isfinite(r["payout_rate"]):
        return float("nan")
    return float(his_calculator(PRESETS[r["firm"]].eval_cost, r["pass_rate"], r["payout_rate"], payout_size(r))["ev_per_eval"])


def fees_per_eval(r: dict) -> float:
    """What one evaluation costs on average under the preset, which the frozen calculator leaves out: the fee for
    every billing month the evaluation runs when the fee is monthly (open evaluations counted at the full horizon),
    plus the activation fee on a pass."""
    rules = PRESETS[r["firm"]]
    months = r["eval_months_mean"] if rules.eval_cost_is_monthly else 1.0
    return float(rules.eval_cost * months + r["pass_rate"] * rules.activation_fee)


def ev_net(r: dict) -> float:
    """EV per evaluation net of every fee: pass x payout x median payout - fees_per_eval."""
    if not np.isfinite(r["pass_rate"]) or not np.isfinite(r["payout_rate"]) or not np.isfinite(r["eval_months_mean"]):
        return float("nan")
    return float(r["pass_rate"] * r["payout_rate"] * payout_size(r) - fees_per_eval(r))


def bootstrap(r: dict, start_cash: float) -> dict:
    """One row of the frozen report's bootstrap survival table (fpt.evaluate.evaluate_trades), with the same call."""
    rules = PRESETS[r["firm"]]
    calc = his_calculator(rules.eval_cost, r["pass_rate"], r["payout_rate"], payout_size(r))
    sim = simulate_his_stats(HisStatsConfig(start_cash=start_cash, eval_cost=rules.eval_cost, pass_rate=r["pass_rate"], payout_rate=r["payout_rate"], payout_size=payout_size(r),
                                            eval_days=int(max(1, np.nan_to_num(r["eval_days_median"], nan=5))),
                                            qualifying_days=int(max(1, np.nan_to_num(r["payout_days_median"], nan=10))), sims=2000))
    return {"p_bust": sim["p_bust"], "p_zero_first_batch": (1 - calc["p_payout_per_eval"]) ** int(start_cash // rules.eval_cost),
            "first_payout_days": sim["first_payout"]["median_trading_days"], "funded_month12": sim["funded_last_month"]["median"]}


def format_bootstrap(start_cash: float, b: dict) -> str:
    """Exactly the frozen report's bootstrap row format."""
    return f"| {start_cash:,.0f} | {b['p_bust']:.0%} | {b['p_zero_first_batch']:.0%} | {b['first_payout_days']:.0f} | {b['funded_month12']:.0f} |"


def ny_day(t: pd.DataFrame) -> pd.Series:
    return t["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)


def score(stream: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp) -> dict:
    day = ny_day(stream)
    out = {}
    for label, part, cal_part in (("development", stream[day <= cut], cal[cal <= cut]), ("benchmark", stream[day > cut], cal[cal > cut])):
        out[label] = {"trades": int(len(part)), "expectancy_r": float(part["r"].mean()) if len(part) else float("nan"),
                      "total_r": float(part["r"].sum()), "firms": firm_rows(part, cal_part) if len(part) else pd.DataFrame()}
    return out


def whole_contracts(pre: pd.DataFrame, budget: float, cap: int) -> pd.DataFrame:
    """The stream a whole-contract account takes from the candidate entries `pre` (before the sequential pass): each
    trade in micro NQ ($2 a point) at the largest count whose full stop-out (the stop plus the exit slippage, plus the
    round-trip commission) stays within `budget`, at most `cap`; a trade that rounds to zero contracts is not taken;
    then the sequential pass. `size` is the contracts' stop risk as a share of the budget, and R is scaled by it, so
    the frozen account's R x budget is the dollar result of those contracts."""
    stop = (pre["stop_pts"] if "stop_pts" in pre.columns else pre["stop_points"]).astype(float).to_numpy()
    if not np.isfinite(stop).all() or (stop <= 0).any():
        raise ValueError("a candidate trade has no positive stop to size from")
    per_micro = (stop + SLIPPAGE) * MNQ_POINT_VALUE + MICRO_COMMISSION_RT
    n = np.floor(budget / per_micro)
    n = np.minimum(np.where(n * per_micro >= budget, n - 1, n), cap)  # strictly within: two stop-outs never land exactly on a drawdown of twice the budget
    keep = n > 0
    t = pre[keep].copy()
    t["size"] = n[keep] * stop[keep] * MNQ_POINT_VALUE / budget
    t["r"] = t["r"].astype(float).to_numpy() * t["size"].to_numpy()
    return sequential_pass(t)


def score_whole(pre: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp, firm: str) -> dict:
    """One firm's row per period with whole micro contracts: the evaluation trades the stream sized to the two-trade
    evaluation risk, the funded phase the stream sized to the funded risk."""
    rules = PRESETS[firm]
    cap = MICROS_PER_MINI * rules.max_contracts
    ev = whole_contracts(pre, rules.profit_target / (2.0 * 1.5), cap)
    fu = whole_contracts(pre, FUNDED_RISK, cap)
    de, df_ = ny_day(ev), ny_day(fu)
    out = {}
    for label, me, mf, cal_part in (("development", de <= cut, df_ <= cut, cal[cal <= cut]), ("benchmark", de > cut, df_ > cut, cal[cal > cut])):
        pe, pf = ev[me], fu[mf]
        out[label] = {"eval_trades": int(len(pe)), "eval_size": float(pe["size"].mean()) if len(pe) else float("nan"),
                      "funded_trades": int(len(pf)), "funded_size": float(pf["size"].mean()) if len(pf) else float("nan"),
                      "firms": firm_rows(pe, cal_part, firms=(firm,), funded_part=pf) if len(pe) and len(pf) else pd.DataFrame()}
    return out


def score_sized(stream: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp, size: float, firm: str) -> dict:
    """One firm's row per period with every trade's R scaled by `size` (fractional), in both phases."""
    t = stream.copy()
    t["r"] = t["r"].astype(float) * size
    day = ny_day(t)
    return {label: (firm_rows(t[m], cal[mc], firms=(firm,)).iloc[0].to_dict() if m.any() else None)
            for label, m, mc in (("development", day <= cut, cal <= cut), ("benchmark", day > cut, cal > cut))}


def sealed_firm_rows(report_text: str) -> dict:
    """The firm rows of the sealed report, by part."""
    out, part = {"development": [], "benchmark": []}, None
    for line in report_text.splitlines():
        if line.startswith("## Pass and payout probability under exact firm rules, in sample"):
            part = "development"
        elif line.startswith("## Pass and payout probability under exact firm rules, out of sample"):
            part = "benchmark"
        elif line.startswith("## "):
            part = None
        elif part and any(line.startswith(f"| {f} |") for f in FIRMS):
            out[part].append(line.strip())
    return out


def check_grid(replay: pd.DataFrame) -> None:
    """Refuse a replay file without every variant this tool reads: a missing ATR variant would silently change the chain."""
    missing = [v for v in NEEDED_VARIANTS if v not in set(replay["variant"].astype(str))]
    if missing:
        raise ValueError(f"the replay file lacks {len(missing)} of the variants this tool reads ({', '.join(missing[:4])}{', ...' if len(missing) > 4 else ''})")


def variant_frame(trades: pd.DataFrame, replay: pd.DataFrame, choice: pd.Series) -> pd.DataFrame:
    """Trades with r, pnl sign, stop and exit time from the replay variant named per trade in `choice` (index: trade id)."""
    rows = replay[replay["variant"] != "_dropped"].set_index(["trade", "variant"])
    keys = pd.MultiIndex.from_arrays([choice.index.astype(int), choice.to_numpy()], names=["trade", "variant"])
    missing = keys.difference(rows.index)
    if len(missing):
        raise ValueError(f"{len(missing)} (trade, variant) pairs are not in the replay file")
    sel = rows.loc[keys]
    t = trades.loc[choice.index].copy()
    t["r"] = sel["r"].astype(float).to_numpy()
    t["pnl_dollars"] = t["r"].to_numpy()
    t["stop_pts"] = sel["stop_pts"].astype(float).to_numpy()
    t["exit_time"] = pd.to_datetime(sel["exit_time"], utc=True).dt.tz_convert(NY).array
    t["bracket"] = choice.to_numpy()
    return t


def period_label(day: pd.Series, cut: pd.Timestamp) -> pd.Series:
    """'2010' ... for development days (calendar year), 'benchmark' after the cut."""
    return pd.Series(np.where(day <= cut, day.dt.year.astype(str), "benchmark"), index=day.index)


def pooled_choices(replay: pd.DataFrame, trades: pd.DataFrame, setup: str, names: list[str], dev_years: list[int], cut: pd.Timestamp) -> dict:
    """Year -> bracket chosen on the pooled (trade-weighted) expectancy of all earlier development years for one setup,
    as research/bracket_replay.walk_forward; the key 'benchmark' holds the choice made on all development years (it is
    the chain's next link, so it too needs CHAIN_START earlier years). Only trades whose New York day is on or before
    the cut enter: the last development year also holds benchmark trades, and they must not steer any choice."""
    t = trades[trades["setup"].astype(str) == setup]
    ny = t["entry_time"].dt.tz_convert(NY)
    year = ny.dt.year[ny.dt.normalize().dt.tz_localize(None) <= cut]
    r = replay[replay["variant"].isin(names) & replay["trade"].isin(year.index)].copy()
    r["year"] = r["trade"].map(year)
    r = r[r["year"].isin(dev_years)]
    sums = r.groupby(["variant", "year"])["r"].sum().unstack("year").reindex(index=names, columns=dev_years)
    cnt = r.groupby(["variant", "year"])["r"].size().unstack("year").reindex(index=names, columns=dev_years)
    out = {}
    for j, y in enumerate(dev_years + ["benchmark"]):
        if j < CHAIN_START:
            continue
        upto = dev_years[:j] if y != "benchmark" else dev_years
        prior = sums[upto].sum(axis=1, min_count=1) / cnt[upto].sum(axis=1, min_count=1)
        if prior.isna().all():
            continue
        out[y] = prior.idxmax()
    return out


def s3_bracket(trades: pd.DataFrame, chain: dict, cut: pd.Timestamp) -> pd.Series:
    """S3's bracket per trade: a development continuation trade takes the chain's link for its calendar year (the
    sealed bracket before the chain starts), a benchmark continuation trade the link chosen on all development years
    (whatever its calendar year); reversion keeps the sealed bracket."""
    ny = trades["entry_time"].dt.tz_convert(NY)
    day = ny.dt.normalize().dt.tz_localize(None)
    cont = (trades["setup"].astype(str) == "continuation").to_numpy()
    out = ["ledger_bracket" if not c else (chain.get("benchmark", "ledger_bracket") if d > cut else chain.get(int(y), "ledger_bracket"))
           for c, d, y in zip(cont, day, ny.dt.year)]
    return pd.Series(out, index=trades.index, dtype=object)


def build_streams(trades: pd.DataFrame, bars: pd.DataFrame, replay: pd.DataFrame, cut: pd.Timestamp) -> tuple[dict, dict, dict, pd.Series]:
    """The candidate entries before the sequential pass, the streams after it, the continuation chain, and S3's
    bracket per replayed trade."""
    gates = build_gates(trades, bars)
    replayed = sorted(set(int(x) for x in replay.loc[replay["variant"] != "_dropped", "trade"]))
    t = trades.loc[replayed]
    is_cont = t["setup"].astype(str) == "continuation"
    day, year = ny_day(t), t["entry_time"].dt.tz_convert(NY).dt.year
    dev_years = sorted(int(y) for y in year[day <= cut].unique())
    ctrl = variant_frame(t, replay, pd.Series("ledger_bracket", index=t.index))
    chain = pooled_choices(replay, t, "continuation", ATR_NAMES, dev_years, cut)
    s3_choice = s3_bracket(t, chain, cut)
    mixed = variant_frame(t, replay, s3_choice)
    pre = {
        "S0 sealed ledger": trades,
        "S0r sealed brackets, flat 16:00": ctrl,
        "S1 continuation only, sealed bracket": ctrl[is_cont],
        "S2 continuation + A+ reversion, sealed bracket": apply_filter(ctrl, "B2a", gates),
        "S3 continuation only, walk-forward ATR bracket": mixed[is_cont],
        "S4 S3 + A+ reversion, sealed bracket": apply_filter(mixed, "B2a", gates),
    }
    return pre, {name: sequential_pass(p) for name, p in pre.items()}, chain, s3_choice


def drift_baseline(bars: pd.DataFrame, rolls, cut: pd.Timestamp) -> pd.Series:
    """Mean move in points from each regular-session minute's open to the close of that day's last bar before 16:00
    (the replay's flat exit), over every non-roll trading day with a bar at that minute, by period label and minute."""
    ny = bars.index.tz_convert(NY)
    mins = np.asarray(ny.hour * 60 + ny.minute, dtype=np.int64)
    rth = (mins >= 9 * 60 + 30) & (mins < 16 * 60)
    b = pd.DataFrame({"day": ny[rth].normalize().tz_localize(None), "min": mins[rth],
                      "open": bars["open"].to_numpy(float)[rth], "close": bars["close"].to_numpy(float)[rth]})
    b = b[~b["day"].dt.date.isin(set(rolls))]
    b["move"] = b["day"].map(b.groupby("day")["close"].last()) - b["open"]
    b["label"] = period_label(b["day"], cut).to_numpy()
    return b.groupby(["label", "min"])["move"].mean()


def hold_drift(trades: pd.DataFrame, bars: pd.DataFrame, replay: pd.DataFrame, ids, cut: pd.Timestamp, rolls) -> pd.DataFrame:
    """Per trade in `ids`: its replayed R held to 16:00 (hold_r), the R of the same-direction trade from the same
    minute averaged over every non-roll trading day with the same period label, at the same costs (drift_r), the
    difference (excess_r = d x (the trade's move - the mean move) / 25 points), and that difference in points over
    the previous session's daily ATR (excess_atr; NaN while the ATR has no history)."""
    t = trades.loc[ids]
    ny = t["entry_time"].dt.tz_convert(NY)
    day = ny.dt.normalize().dt.tz_localize(None)
    on_roll = day.dt.date.isin(set(rolls))
    if on_roll.any():
        raise ValueError(f"{int(on_roll.sum())} trades fall on roll dates, which have no drift baseline")
    label = period_label(day, cut)
    d = t["direction"].astype(int).to_numpy()
    key = pd.MultiIndex.from_arrays([label.to_numpy(), (ny.dt.hour * 60 + ny.dt.minute).to_numpy(np.int64)])
    avg = drift_baseline(bars, rolls, cut).reindex(key).to_numpy(float)
    if np.isnan(avg).any():
        raise ValueError(f"{int(np.isnan(avg).sum())} trades have no drift baseline (entry outside 09:30-16:00)")
    drift_r = ((d * avg - 2 * SLIPPAGE) * POINT_VALUE - COMMISSION_RT) / (FIXED_STOP * POINT_VALUE)
    hold_r = variant_frame(t, replay, pd.Series("hold_to_1600", index=t.index))["r"].to_numpy(float)
    atr = day.map(daily_context(bars)["daily_atr"]).to_numpy(float)
    excess = hold_r - drift_r
    return pd.DataFrame({"day": day.to_numpy(), "label": label.to_numpy(), "period": np.where(label == "benchmark", "benchmark", "development"),
                         "side": np.where(d > 0, "long", "short"), "hold_r": hold_r, "drift_r": drift_r, "excess_r": excess,
                         "excess_atr": excess * FIXED_STOP / np.where(atr > 0, atr, np.nan)}, index=t.index)


def mean_se(x: pd.Series, day: pd.Series) -> tuple[int, float, float]:
    """Trades, mean, and the standard error of the mean clustered by day (trades on one day share its close); NaNs are
    left out."""
    x = pd.Series(np.asarray(x, dtype=float))
    day = np.asarray(day)
    ok = x.notna().to_numpy()
    x, day = x[ok], day[ok]
    n = len(x)
    if n == 0:
        return 0, float("nan"), float("nan")
    m = float(x.mean())
    g = (x - m).groupby(day).sum()
    k = len(g)
    return n, m, float(np.sqrt(k / (k - 1) * (g ** 2).sum()) / n) if k > 1 else float("nan")


def direction_table(trades: pd.DataFrame, replay: pd.DataFrame, s3_choice: pd.Series, drift: pd.DataFrame, first_link: int | None) -> list[str]:
    """Continuation by direction and period under the sealed bracket, S3's own per-trade bracket and the hold, with
    the drift control; and the hold against the drift by year, in R per 25 points and per daily ATR."""
    ids = drift.index
    t = trades.loc[ids]
    s3_label = "S3 walk-forward bracket" + (f" (sealed before {first_link})" if first_link else " (sealed: no chain)")
    outcomes = {"sealed bracket": variant_frame(t, replay, pd.Series("ledger_bracket", index=ids))["r"],
                s3_label: variant_frame(t, replay, s3_choice.loc[ids])["r"],
                "held to 16:00 (R per 25 points)": drift["hold_r"],
                "held to 16:00, excess over the drift (R per 25 points)": drift["excess_r"],
                "held to 16:00, excess over the drift (per daily ATR)": drift["excess_atr"]}
    s = ["## Continuation by direction\n",
         "Replayed continuation entries before the sequential pass, flat at 16:00. Cells: trades, mean (standard error of the mean, clustered by day). "
         "The drift is the same-direction trade from the same minute, at the same costs, averaged over every non-roll trading day of the same period label that has a bar at that minute "
         "(a development calendar year; for 2025, 1 January to the cut; the benchmark period); the excess is the trade held to 16:00 minus that drift, zero on average if the direction call adds nothing to the market's drift at that time of day. "
         "R per 25 points weighs a 2025 trade about eleven times a 2010 one (NQ went from about 2,000 to 22,000); per daily ATR (the excess in points over the previous session's daily ATR) weighs every year alike.\n",
         "| outcome | period | long | short | both |", "|---|---|---|---|---|"]
    for name, x in outcomes.items():
        for per in ("development", "benchmark"):
            cells = []
            for side in ("long", "short", "both"):
                m = (drift["period"] == per) & ((drift["side"] == side) | (side == "both"))
                n, mu, se = mean_se(x[m], drift.loc[m, "day"])
                cells.append(f"{n}, {mu:+.3f} ({se:.3f})" if n else "0, n/a")
            s.append(f"| {name} | {per} | " + " | ".join(cells) + " |")
    s += ["", "### Held to 16:00 against the drift, by year\n",
          "| year | long: trades, held, drift, excess (R per 25 points) | short: trades, held, drift, excess (R per 25 points) | both: excess, R per 25 points (se) | both: excess per daily ATR (se) |", "|---|---|---|---|---|"]
    yearly_r, yearly_atr = {}, {}
    for lab in sorted(drift["label"].unique()):
        g = drift[drift["label"] == lab]
        cells = []
        for side in ("long", "short"):
            q = g[g["side"] == side]
            cells.append(f"{len(q)}, {q['hold_r'].mean():+.3f}, {q['drift_r'].mean():+.3f}, {q['excess_r'].mean():+.3f}" if len(q) else "0, n/a")
        _, mu, se = mean_se(g["excess_r"], g["day"])
        na, mua, sea = mean_se(g["excess_atr"], g["day"])
        yearly_r[lab], yearly_atr[lab] = mu, (mua if na else float("nan"))
        s.append(f"| {lab} | {cells[0]} | {cells[1]} | {mu:+.3f} ({se:.3f}) | " + (f"{mua:+.3f} ({sea:.3f})" if na else "n/a") + " |")
    dev = [lab for lab in yearly_r if lab != "benchmark"]
    ya = np.array([yearly_atr[lab] for lab in dev if np.isfinite(yearly_atr[lab])])
    pos_r = sum(1 for lab in dev if yearly_r[lab] > 0)
    s.append("")
    if len(ya) > 1:
        s.append(f"Development years with a positive mean excess: {pos_r} of {len(dev)} in R per 25 points, {int((ya > 0).sum())} of {len(ya)} per daily ATR. "
                 f"Mean of the yearly means per daily ATR {ya.mean():+.4f}, standard error across years {ya.std(ddof=1) / np.sqrt(len(ya)):.4f} (each year one observation).\n")
    return s


def report(streams: dict, pre: dict, chain: dict, cal: pd.DatetimeIndex, cut: pd.Timestamp, gate_note: str, direction_lines: list[str]) -> str:
    s = ["# B3: candidate streams under the frozen firm rules\n", gate_note, ""]
    s.append("Every stream goes through the sequential pass (one position at a time, three-loss session stop, each trade's own exit time) and is scored with the frozen evaluator's walk-forward pass and payout functions under each firm preset and the sealed cut. "
             "The benchmark year is reported beside and never used to choose. EV per evaluation is the frozen calculator: pass x payout x median payout - fee.\n")
    s.append("Read with: S0r, not S0, is the control for S1-S4 (same entries, same 16:00 flat); S0 differs from it by the entries the replay drops for lack of context and by the ledger's exits after 16:00. "
             "S1's entries are exactly those of a frozen-engine run with reversion off, less the entries the replay drops for lack of context. S2-S4 are built from the sealed entries: they cannot contain an A+ reversion that the sealed three-loss stop or open position suppressed, nor a continuation re-entry that an earlier ATR exit would have freed (research/engine.py re-simulates whatever survives). "
             "Sizing: these tables book every trade at R x its budget whatever the stop ($1,000 or $2,000 in the evaluation by firm, $500 funded), as the frozen evaluator does, which is fractional contracts; the whole-contract table below sizes in micro NQ.\n")
    links = sorted(k for k in chain if k != "benchmark")
    if chain:
        chain_txt = "; ".join(f"{k}: {v}" for k, v in chain.items()) + (f"; before {links[0]}, the sealed bracket" if links else "")
    else:
        chain_txt = f"none (the chain needs {CHAIN_START} earlier development years), so S3 and S4 keep the sealed bracket"
    s.append(f"Walk-forward bracket for continuation (S3, S4), chosen on earlier development years only: {chain_txt}.\n")
    s.append("## Summary, topstep_50k\n")
    s.append("EV per evaluation is the frozen calculator's (pass x payout x median payout - one evaluation fee), as in the sealed report. EV net of all fees also charges the evaluation fee for every billing month the evaluation runs (monthly at this firm; 22 trading days a month) and the activation fee on each pass, which the frozen calculator leaves out.\n")
    s.append("| stream | period | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
    scored = {name: score(st, cal, cut) for name, st in streams.items()}
    for name, sc in scored.items():
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            r = p["firms"].set_index("firm").loc["topstep_50k"].to_dict()
            r["firm"] = "topstep_50k"
            s.append(f"| {name} | {per} | {p['trades']} | {p['expectancy_r']:+.3f} | {p['total_r']:+.1f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_median_amount']:,.0f} | {ev_per_eval(r):+,.0f} | {ev_net(r):+,.0f} |")
    s.append("")
    s.append("## Position size at Topstep's drawdown, topstep_50k_x\n")
    s.append("At the sealed sizing a stop-out costs 1.02 R with slippage and commission ($1,020 in a Topstep 50K evaluation), so two stop-outs cost $2,040 and breach the $2,000 drawdown; on the frozen topstep_50k preset its $1,000 soft daily limit caps each at exactly $1,000 and the balance lands on the threshold, which fails too (the help centre: an account fails when its balance hits the limit). "
             "Sized 0.98 the account fails on the third stop-out instead of the second, and two wins (2 x 1.51 R x 0.98 = 2.96 R) no longer reach the $3,000 target; the funded phase has the same kind of edge at four stop-outs. 0.98 clears the edge only for stops of about 25 points or more (the edge is 1 / (1 + 0.5 / stop): 0.965 at 14 points). "
             "This table and the next use topstep_50k_x (TopstepX: no daily loss limit for accounts created or reset since 2024-08-25; everything else as topstep_50k), because below the sealed sizing (and, at it, after a day that started with a win) the frozen account's soft daily limit credits a later trade on a day that has nearly reached the limit with a full win but a loss cut to the room left, which no real account allows; the frozen topstep_50k preset is shown at the sealed sizing only, where this slightly favours the streams that trade more than once a day, so compare streams in this table's 1.00 column. Fractional sizes, both phases scaled alike.\n")
    s.append("| preset | stream | period | P(pass) at " + " / ".join(f"{z:.2f}" for z in SIZES) + " | P(payout) at " + " / ".join(f"{z:.2f}" for z in SIZES) + " | EV net of all fees at " + " / ".join(f"{z:.2f}" for z in SIZES) + " |")
    s.append("|---|---|---|---|---|---|")
    for firm in SIZING_FIRMS:
        for name, st in streams.items():
            sized = {z: score_sized(st, cal, cut, z, firm) for z in SIZES}
            for per in ("development", "benchmark"):
                rows_ = [sized[z][per] for z in SIZES]
                if any(x is None for x in rows_):
                    continue
                s.append(f"| {firm} | {name} | {per} | " + " / ".join(f"{x['pass_rate']:.1%}" for x in rows_) + " | " + " / ".join(f"{x['payout_rate']:.1%}" for x in rows_)
                         + " | " + " / ".join(f"{ev_net({**x, 'firm': firm}):+,.0f}" for x in rows_) + " |")
    s.append("")
    rules = PRESETS["topstep_50k"]
    cap = MICROS_PER_MINI * rules.max_contracts
    s.append("## Whole contracts\n")
    s.append(f"Each candidate's entries sized in whole micro NQ contracts ($2 a point): the largest count whose full stop-out (the stop plus {SLIPPAGE} point of exit slippage, plus ${MICRO_COMMISSION_RT:.2f} round-trip commission per micro, the replay's $5 per NQ scaled; real micro fees run higher, about 0.01 to 0.02 R per trade on a 25-point stop) stays within the budget (${rules.profit_target / 3:,.0f} in the evaluation, ${FUNDED_RISK:,.0f} funded), at most {cap} (the preset's {rules.max_contracts} NQ). "
             "An entry that rounds to zero contracts is not taken, the sequential pass runs on what is taken, and each R is scaled by the contracts' stop risk as a share of the budget (size). "
             "No stream sits on the drawdown edge here: the sealed 25-point stop takes 19 micros in the evaluation (size 0.95) and 9 funded (0.90), the 50-point stop 9 and 4 (0.90 and 0.80), so the sealed rows differ from the summary for that reason; the preset is topstep_50k_x, for the reason given above. "
             "Micro NQ began trading on 2019-05-06; this applies today's contract menu to every year, which is the question for an account opened now (before May 2019 only NQ existed, and a stop wider than 50 points could not be taken at $1,000 of risk, nor one wider than 25 at $500). The frozen bootstrap is run on these inputs.\n")
    s.append("| preset | stream | period | evaluation: trades, mean size | P(pass) | +/- | funded: trades, mean size | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees | P(bust) from $2,000 |")
    s.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for firm in SIZING_FIRMS:
        for name, p in pre.items():
            w = score_whole(p, cal, cut, firm)
            for per in ("development", "benchmark"):
                q = w[per]
                if q["firms"].empty:
                    continue
                r = q["firms"].iloc[0].to_dict()
                ok = np.isfinite(r["pass_rate"]) and np.isfinite(r["payout_rate"])
                bust = f"{bootstrap(r, 2000.0)['p_bust']:.0%}" if ok else "n/a"
                s.append(f"| {firm} | {name} | {per} | {q['eval_trades']}, {q['eval_size']:.2f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {q['funded_trades']}, {q['funded_size']:.2f} | {r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_median_amount']:,.0f} | {ev_per_eval(r):+,.0f} | {ev_net(r):+,.0f} | {bust} |")
    s.append("")
    for name, sc in scored.items():
        s.append(f"## {name}\n")
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            s.append(f"{per}: {p['trades']} trades, {p['expectancy_r']:+.3f} R per trade, {p['total_r']:+.1f} R.\n")
            s.append(f"| firm | eval risk | P(pass) within {MAX_EVAL_DAYS} days | +/- | days to pass (median) | starts (open) | P(payout before breach) within {MAX_FUNDED_DAYS} days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for r in p["firms"].to_dict("records"):
                s.append(format_row(r)[:-1] + f"| {ev_per_eval(r):+,.0f} | {ev_net(r):+,.0f} |")
            s.append("")
    s.append("## Bootstrap with the frozen simulator, topstep_50k\n")
    s.append("The frozen report's bootstrap (fpt.bootstrap.simulate_his_stats: 2,000 paths, seed 0, twelve months, everything reinvested, one payout per funded account, payouts gross) run on each stream's measured topstep_50k inputs from the summary (fractional sizing), exactly as the sealed report runs it on Baseline 0. "
             "P(bust) is the share of paths with no live account and too little cash for another evaluation within twelve months. "
             "Like the frozen calculator, the simulator charges one evaluation fee per evaluation and no activation fee, so these rates are optimistic wherever the net EV is below the frozen one.\n")
    s.append("| stream | period | P(bust) from " + " | ".join(f"${c:,.0f}" for c in START_CASH) + " | P(zero payouts, first batch, $2,000) | median days to first payout ($2,000) | funded accounts month 12, median ($2,000) |")
    s.append("|---|---|" + "---|" * (len(START_CASH) + 3))
    for name, sc in scored.items():
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            r = p["firms"].set_index("firm").loc["topstep_50k"].to_dict()
            r["firm"] = "topstep_50k"
            if not (np.isfinite(r["pass_rate"]) and np.isfinite(r["payout_rate"])):
                continue
            b = {c: bootstrap(r, c) for c in START_CASH}
            k = b[2000.0]
            s.append(f"| {name} | {per} | " + " | ".join(f"{b[c]['p_bust']:.0%}" for c in START_CASH) + f" | {k['p_zero_first_batch']:.0%} | {k['first_payout_days']:.0f} | {k['funded_month12']:.0f} |")
    s.append("")
    s += direction_lines
    return "\n".join(s)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--report", required=True, help="sealed/run1/report.md: its firm rows are the reproduction gate")
    ap.add_argument("--replay-csv", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.manifest) as fh:
        m = json.load(fh)
    try:
        wanted = (("trades", a.trades, m["outputs"]["trades_sha256"]), ("report", a.report, m["outputs"]["report_sha256"]), ("bar file", a.csv, m["data"]["sha256"]))
    except KeyError as e:
        raise SystemExit(f"refusing to report: the manifest has no {e} hash to check provenance against")
    for what, path, want in wanted:
        if sha256(path) != want:
            raise SystemExit(f"refusing to report: the {what} given ({path}) is not the sealed run's (sha256 differs from the manifest)")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = load_trades(a.trades)
    rolls = sorted(roll_days(bars))
    if sorted(pd.Timestamp(d).date() for d in m["data"]["roll_dates_excluded"]) != rolls:
        raise SystemExit("roll dates from bars differ from the manifest; refusing to report")
    trades, n_excl = exclude_roll_trades(trades, rolls)
    if len(trades) != int(m["outputs"]["n_trades"]) - int(m["hygiene"]["trades_excluded"]):
        raise SystemExit("analysed population differs from the sealed population; refusing to report")
    cut = pd.Timestamp(a.oos_start) - pd.Timedelta(days=1)
    cal = trading_days_of(bars)
    with open(a.report) as fh:
        sealed = sealed_firm_rows(fh.read())
    gate = score(sequential_pass(trades), cal, cut)
    for per in ("development", "benchmark"):
        mine = [format_row(r) for r in gate[per]["firms"].to_dict("records")]
        if mine != sealed[per] or len(mine) != len(FIRMS):
            raise SystemExit(f"refusing to report: the {per} firm rows do not reproduce the sealed report\nsealed: {sealed[per]}\nmine:   {mine}")
    replay = pd.read_csv(a.replay_csv)
    try:
        check_grid(replay)
        n_checked = check_alignment(trades, replay)
        pre, streams, chain, s3_choice = build_streams(trades, bars, replay, cut)
        cont = s3_choice.index[trades.loc[s3_choice.index, "setup"].astype(str) == "continuation"]
        drift = hold_drift(trades, bars, replay, cont, cut, rolls)
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    links = sorted(k for k in chain if k != "benchmark")
    gate_note = (f"Data hygiene: {n_excl} trades on {len(rolls)} contract-roll dates excluded, as in the sealed report. "
                 f"Provenance: the trades, the bar file and the report given ({a.report}) have the manifest's sha256. "
                 f"Reproduction gate: the sealed ledger scored here reproduces all {2 * len(FIRMS)} firm rows of {a.report} character for character. "
                 f"Replay join: checked on {n_checked} stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.")
    text = report(streams, pre, chain, cal, cut, gate_note, direction_table(trades, replay, s3_choice, drift, links[0] if links else None))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
