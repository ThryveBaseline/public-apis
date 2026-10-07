"""S3 and S4 on a Topstep 50K account with what B4/B5 left out (docs/reviews/topstep_economics_audit.md): TopstepX's
micro fee ($1.22 a round trip, not $0.50), the loss limit enforced on each trade's worst excursion rather than only
on closed trades, and the call-up to Live at the 3rd payout. Sizing includes the real fee, as a live account must
(the forward ledger's micro counts are sized at $0.50 and are bookkeeping only). Before any money is spent (task 15); it does not touch
the forward test.

The candidates are the forward protocol's frozen S3 and S4 (research/forward.CANDIDATES, research/engine.py) on the
sealed bars. The paths are B5's (research/b5_paths.simulate): from $2,000, one account at a time, whole micros,
TopstepX, 365 days, both payout policies, with and without the call-up. Each candidate runs four ways, so each
correction's cost shows: the B5 fee or the real one, and dips ignored or counted.

A dip is counted with the frozen account: each trade becomes two steps on its day, the worst excursion (see
mae_points; the round-trip fee charged up front), then the rest of the trade. The frozen account fails on any step that takes the balance to the loss
limit, and TopstepX has no daily loss limit and trails at the day's end, so nothing else changes.

usage:
  python research/realistic_economics.py --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/s3s4_realistic_economics.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import load_minute_bars, roll_days  # noqa: E402
from fpt.evaluate import _daily_r  # noqa: E402
from research.b5_paths import (CALLUP, PATH_DAYS, START_CASH, TOPSTEPX, day_arrays, eval_risk, path_bounds, phase_days, simulate,  # noqa: E402
                               summarize)
from research.bracket_replay import SLIPPAGE  # noqa: E402
from research.candidates import FUNDED_RISK, MICROS_PER_MINI, MNQ_POINT_VALUE, PRESETS  # noqa: E402
from research.forward import CANDIDATES, DEV_END, FIRST_UNSEEN, candidate_trades, rth_sessions, sha256  # noqa: E402
from research.ledger_filters import sequential_pass  # noqa: E402

FEES = {"B5": 0.50, "TopstepX": 1.22}  # per micro round trip
CHAIN_FROM = pd.Timestamp("2021-01-01")  # S3's walk-forward chain chose this bracket, on earlier years only, every year from 2021 (research/run1_b3.md)
POLICIES = ("ask", "wait")


def mae_points(trades: pd.DataFrame, bars: pd.DataFrame) -> np.ndarray:
    """Each trade's most adverse excursion from its entry, in points. A stop exit's is exactly its fill (no earlier
    bar reached the stop, or the trade would have stopped there). Otherwise the bars from the entry bar to the exit
    bar, the exit bar's whole range included (conservative for a target exit: the target may have printed before
    the bar's low; exact for a 16:00 exit, open through its bar)."""
    idx = bars.index
    lo, hi = bars["low"].to_numpy(float), bars["high"].to_numpy(float)
    a = idx.searchsorted(pd.DatetimeIndex(trades["entry_time"]).tz_convert(idx.tz), side="left")
    b = idx.searchsorted(pd.DatetimeIndex(trades["exit_time"]).tz_convert(idx.tz), side="right")
    long = trades["direction"].astype(str).str.lower().isin(["long", "1"]).to_numpy()
    entry = trades["entry"].astype(float).to_numpy()
    out = np.zeros(len(trades))
    for i in range(len(trades)):
        if b[i] <= a[i]:
            raise ValueError(f"trade {i} has no bar between its entry and exit")
        out[i] = entry[i] - lo[a[i]:b[i]].min() if long[i] else hi[a[i]:b[i]].max() - entry[i]
    stop = (trades["exit_reason"].astype(str) == "stop").to_numpy()
    out = np.where(stop, -trades["pnl_points"].astype(float).to_numpy(), out)
    return np.maximum(out, 0.0)


def micro_stream(pre: pd.DataFrame, budget: float, cap: int, fee: float) -> pd.DataFrame:
    """research/candidates.whole_contracts with the fee as a parameter: the largest count of micros whose full
    stop-out (stop plus exit slippage, plus the fee) stays strictly within the budget, at most `cap`; zero-count
    trades dropped; then the sequential pass on the micros' dollars. `r` and `w` (the worst excursion, fee
    included) are in units of the budget, as the account multiplies them by its risk."""
    stop = pre["stop_points"].astype(float).to_numpy()
    per = (stop + SLIPPAGE) * MNQ_POINT_VALUE + fee
    n = np.floor(budget / per)
    n = np.minimum(np.where(n * per >= budget, n - 1, n), cap)
    keep = n > 0
    t = pre[keep].copy()
    n = n[keep]
    dollars = n * (t["pnl_points"].astype(float).to_numpy() * MNQ_POINT_VALUE - fee)
    worst = -n * (t["mae_points"].astype(float).to_numpy() * MNQ_POINT_VALUE + fee)
    t["micros"], t["pnl_dollars"] = n, dollars
    t["r"], t["w"] = dollars / budget, np.minimum(worst, dollars) / budget
    return sequential_pass(t)


def split_rows(st: pd.DataFrame, dates: pd.DatetimeIndex, dips: bool) -> list[np.ndarray]:
    """The stream's day rows on `dates`: each trade as one step (r), or as two (w, then r - w) when dips count."""
    if st.empty:
        return [np.zeros(0) for _ in dates]
    _, rs = _daily_r(st, dates)
    if not dips:
        return rs
    _, ws = _daily_r(st.assign(r=st["w"]), dates)
    out = []
    for r, w in zip(rs, ws):
        x = np.empty(2 * len(r))
        x[0::2], x[1::2] = w, r - w
        out.append(x)
    return out


def run_variant(pre: pd.DataFrame, cal: pd.DatetimeIndex, last: pd.Timestamp | None, policy: str, callup: int | None, fee: float, dips: bool) -> dict:
    rules = PRESETS[TOPSTEPX]
    if rules.daily_loss_limit is not None or rules.drawdown_type != "trailing_eod":
        raise ValueError("the dip split is exact only without a daily loss limit and with end-of-day trailing")
    cap = MICROS_PER_MINI * rules.max_contracts
    streams = []
    for budget in (eval_risk(TOPSTEPX), FUNDED_RISK):
        st = micro_stream(pre, budget, cap, fee)
        day = pd.DatetimeIndex(st["entry_time"]).tz_convert("America/New_York").tz_localize(None).normalize()
        streams.append(st[((day >= cal[0]) & (day <= cal[-1]))])
    ev, fu = streams
    dates, _, _ = phase_days(ev.drop(columns="w"), fu.drop(columns="w"), cal)
    rs_e, rs_f = split_rows(ev, dates, dips), split_rows(fu, dates, dips)
    width = max([1] + [len(x) for x in rs_e + rs_f])
    starts, ends = path_bounds(dates, last)
    res = simulate(dates, day_arrays(rs_e, width), day_arrays(rs_f, width), starts, ends, TOPSTEPX, policy, 1, callup)
    out = summarize(res, dates, starts, 0, 0)
    evals = out["evals_mean"]
    out["net_per_eval"] = (out["cash_mean"] - START_CASH) / evals if evals else float("nan")
    out.update({"eval_trades": int(len(ev)), "funded_trades": int(len(fu)), "micros_eval": float(ev["micros"].mean()) if len(ev) else float("nan")})
    return out


def report(rows: list[dict], meta: dict) -> str:
    s = ["# S3 and S4 with TopstepX's fees, intraday dips and the call-up (task 15)\n",
         f"Sealed bars sha256 {meta['bars_sha256']}; the forward protocol's frozen S3 and S4 through research/engine.py; roll dates excluded. "
         f"B5's paths (research/b5_paths.simulate): from ${START_CASH:,.0f}, one Topstep 50K account at a time on TopstepX, whole micros "
         f"(evaluation budget ${eval_risk(TOPSTEPX):,.0f}, funded ${FUNDED_RISK:,.0f}), {PATH_DAYS} days; development paths start every trading day "
         f"and end by {DEV_END.date()}, the benchmark is one path from 2025-10-06. Fees per micro round trip: B5 $0.50, TopstepX $1.22. "
         "Dips: the loss limit is checked at each trade's worst excursion (the exit bar's whole range included, the fee charged up front). "
         f"Call-up: every account closes at the path's {CALLUP}rd payout request and the Live account counts for nothing. "
         "Sizing includes the fee in each variant's budget (a live account must size with the real $1.22).\n",
         "Which rows to read: the bracket was chosen on all development years, so 'development, in-sample' flatters both candidates. "
         "'Development from 2021' is out of sample for the bracket (S3's walk-forward chain chose it each year from 2021 on earlier years only), "
         "and the benchmark is one path the choice never saw.\n",
         "Net per evaluation is (mean final cash - $2,000) / mean evaluations bought; it includes the activations and the payouts.\n",
         "| candidate | period | policy | call-up | fee | dips | paths | ruin | cash p10 | median cash | mean cash | > $2,000 | evaluations | payouts | net per evaluation |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        s.append(f"| {x['candidate']} | {x['period']} | {x['policy']} | {'3rd payout' if x['callup'] else 'none'} | {x['fee']} | {'counted' if x['dips'] else 'ignored'} | "
                 f"{x['paths']} | {x['p_ruin']:.1%} | {x['cash_p10']:,.0f} | {x['cash_p50']:,.0f} | {x['cash_mean']:,.0f} | {x['p_above_2000']:.0%} | "
                 f"{x['evals_mean']:.1f} | {x['payouts_mean']:.1f} | {x['net_per_eval']:+,.0f} |")
    return "\n".join(s) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.manifest) as fh:
        man = json.load(fh)
    bars_sha = sha256(a.csv)
    if bars_sha != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    rolls = roll_days(bars)
    excl = {pd.Timestamp(d) for d in rolls}
    sessions = pd.DatetimeIndex([d for d in rth_sessions(bars.index) if d not in excl])
    trades = candidate_trades(bars, rolls)
    rows = []
    for name in CANDIDATES:
        pre = trades[name].copy()
        pre["mae_points"] = mae_points(pre, bars)
        for period, cal, last in (("development, in-sample", sessions[sessions <= DEV_END], DEV_END),
                                  ("development from 2021", sessions[(sessions >= CHAIN_FROM) & (sessions <= DEV_END)], DEV_END),
                                  ("benchmark", sessions[(sessions > DEV_END) & (sessions < FIRST_UNSEEN)], None)):
            for policy in POLICIES:
                for callup in (None, CALLUP):
                    for fee_name, fee in FEES.items():
                        for dips in (False, True):
                            out = run_variant(pre, cal, last, policy, callup, fee, dips)
                            rows.append({"candidate": name, "period": period, "policy": policy, "callup": callup, "fee": fee_name, "dips": dips, **out})
                            print(name, period, policy, callup, fee_name, dips, f"median {out['cash_p50']:.0f} ruin {out['p_ruin']:.3f}", flush=True)
    text = report(rows, {"bars_sha256": bars_sha})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
