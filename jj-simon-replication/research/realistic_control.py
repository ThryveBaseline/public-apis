"""The zero-edge control for task 15: how much of S3's and S4's realistic result (research/realistic_economics.py)
the same trades would earn with no edge at all.

A Topstep account caps a trader's loss at the loss limit while half of every upswing can be withdrawn, so a stream
with no edge can be paid (docs/reviews/topstep_economics_audit.md; research/run1_structure.md for B4's accounting).
Two nulls, modelled on research/structure_control.py, are applied inside the identical paths to each phase's stream
as the account trades it: after whole-micro sizing at the variant's own fee and the sequential pass, on the
period's calendar. So each null keeps exactly the actual stream's trades, entries, timing and sizes, and its mean
dollar result per trade is zero in each phase:

  shift     every trade is charged the same amount per dollar of stop risk (micros x stop x $2), so the phase's
            dollars sum to zero. The charge is taken at exit: the worst excursion is the trade's own, or the new
            result if lower. Charging at entry would deepen every winner's dip and make the null look worse, so
            the edge's part bigger; at exit errs the other way. Outcome sizes move, so a stop-out can lose more
            than its stop.
  re-label  winners take, in a seeded random order, the lower-median loss of the phase's own losers until the
            phase's mean is as close to zero as one more trade can bring it (feasible outcomes; read it first);
            ten orders, averaged, with their range.

Each variant (TopstepX fee with dips counted; B5's $0.50 with dips ignored) zeroes its own stream, net of its own
fee. The spread between the two nulls is part of the uncertainty. Descriptive: nothing is chosen on it.

usage:
  python research/realistic_control.py --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/staging/s3s4_zero_edge_control.md
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
from research.b5_paths import CALLUP, START_CASH  # noqa: E402
from research.candidates import MNQ_POINT_VALUE  # noqa: E402
from research.forward import CANDIDATES, DEV_END, FIRST_UNSEEN, candidate_trades, rth_sessions, sha256  # noqa: E402
from research.realistic_economics import CHAIN_FROM, FEES, POLICIES, mae_points, run_variant  # noqa: E402
from research.structure_control import relabelled  # noqa: E402

SEEDS = tuple(range(10))
VARIANTS = (("TopstepX fee, dips counted", FEES["TopstepX"], True), ("B5: $0.50 fee, dips ignored", FEES["B5"], False))
FAR = pd.Timestamp("2100-01-01")  # every trade passed in counts as the stream whose mean is removed


def shift_null(st: pd.DataFrame, budget: float) -> pd.DataFrame:
    """The phase's dollars brought to exactly zero by one charge per dollar of stop risk, taken at exit."""
    risk = st["micros"].astype(float).to_numpy() * st["stop_points"].astype(float).to_numpy() * MNQ_POINT_VALUE
    dollars = st["r"].astype(float).to_numpy() * budget
    charge = dollars.sum() / risk.sum() * risk / budget
    out = st.copy()
    out["r"] = st["r"].astype(float).to_numpy() - charge
    out["w"] = np.minimum(st["w"].astype(float).to_numpy(), out["r"].to_numpy())
    return out


def relabel_null(seed: int):
    def null(st: pd.DataFrame, budget: float) -> pd.DataFrame:
        flipped, share = relabelled(st, FAR, seed)
        if not np.isfinite(share):
            raise ValueError("the re-label null is not defined for this stream (no trade on the other side)")
        out = st.copy()
        r0, w0 = st["r"].astype(float).to_numpy(), st["w"].astype(float).to_numpy()
        r = flipped["r"].astype(float).to_numpy()
        moved = r != r0
        w = w0.copy()
        if moved.any():  # a re-labelled trade takes the outcome, and so the worst excursion, of the trade it borrows from
            target = r[moved][0]
            donor = np.flatnonzero(~moved & (r0 == target))[0]
            w[moved] = min(w0[donor], target)
        out["r"], out["w"] = r, w
        return out
    return null


def control_rows(name: str, pre: pd.DataFrame, cal: pd.DatetimeIndex, last: pd.Timestamp | None, period: str,
                 variant: tuple = VARIANTS[0]) -> list[dict]:
    """The stream and its two nulls through the same paths, under one variant (label, fee, dips)."""
    label, fee, dips = variant
    rows = []
    for policy in POLICIES:
        for callup in (None, CALLUP):
            act = run_variant(pre, cal, last, policy, callup, fee, dips)
            sh = run_variant(pre, cal, last, policy, callup, fee, dips, null=shift_null)
            rl = [run_variant(pre, cal, last, policy, callup, fee, dips, null=relabel_null(s)) for s in SEEDS]
            keys = ("net_per_eval", "cash_p50", "cash_mean", "p_ruin", "p_above_2000", "eval_dollars_per_trade", "funded_dollars_per_trade")
            rows.append({"candidate": name, "period": period, "variant": label, "policy": policy, "callup": callup, "actual": act, "shift": sh,
                         "relabel": {k: float(np.mean([x[k] for x in rl])) for k in keys},
                         "relabel_range": (float(min(x["net_per_eval"] for x in rl)), float(max(x["net_per_eval"] for x in rl)))})
            print(name, period, label, policy, callup, f"actual {act['net_per_eval']:+.0f} shift {sh['net_per_eval']:+.0f} "
                  f"relabel {rows[-1]['relabel']['net_per_eval']:+.0f}", flush=True)
    return rows


def report(rows: list[dict], bars_sha: str) -> str:
    s = ["# S3 and S4, realistic: what the structure pays a zero-edge stream, and what the edge adds\n",
         f"Sealed bars sha256 {bars_sha}. The paths of research/realistic_economics.py (from ${START_CASH:,.0f}, one Topstep 50K TopstepX account at "
         "a time, whole micros sized with the fee, 365 days), with TopstepX's $1.22 micro fee and dips counted and with B5's conventions ($0.50, dips "
         "ignored), for the forward protocol's frozen S3 and S4 and for two zero-edge copies of exactly the trades each phase's account takes (same "
         "entries, timing, stops and sizes): shift (one charge per dollar of stop risk, taken at exit, the convention that errs against the edge) and re-label (winners given the phase's "
         "lower-median loss until its mean is zero; ten seeded orders averaged, range shown). Each null's dollars per trade, shown for each phase, "
         "are zero (re-label: within one trade). The edge's part is the stream's net per evaluation less the null's; read re-label first (its "
         "outcomes are feasible trades) and the gap between the nulls as uncertainty.\n",
         "Which rows to read: 'development, in-sample' flatters the candidates (the bracket was chosen on those years); 'development from 2021' is out "
         "of sample for the bracket; the benchmark is a single path.\n",
         "| candidate | period | fee and dips | policy | call-up | trades: eval / funded | $ per trade, actual: eval / funded | actual: net per eval / median / ruin | "
         "shift null: $ per trade / net / median / ruin | re-label null: $ per trade / net (range) / median / ruin | edge's part (vs re-label / vs shift) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        a, sh, rl, lo_hi = x["actual"], x["shift"], x["relabel"], x["relabel_range"]
        s.append(f"| {x['candidate']} | {x['period']} | {x['variant']} | {x['policy']} | {'3rd payout' if x['callup'] else 'none'} | "
                 f"{a['eval_trades']} / {a['funded_trades']} | {a['eval_dollars_per_trade']:+.1f} / {a['funded_dollars_per_trade']:+.1f} | "
                 f"{a['net_per_eval']:+,.0f} / {a['cash_p50']:,.0f} / {a['p_ruin']:.1%} | "
                 f"{sh['eval_dollars_per_trade']:+.1f}, {sh['funded_dollars_per_trade']:+.1f} / {sh['net_per_eval']:+,.0f} / {sh['cash_p50']:,.0f} / {sh['p_ruin']:.1%} | "
                 f"{rl['eval_dollars_per_trade']:+.1f}, {rl['funded_dollars_per_trade']:+.1f} / {rl['net_per_eval']:+,.0f} ({lo_hi[0]:+,.0f} to {lo_hi[1]:+,.0f}) / "
                 f"{rl['cash_p50']:,.0f} / {rl['p_ruin']:.1%} | {a['net_per_eval'] - rl['net_per_eval']:+,.0f} / {a['net_per_eval'] - sh['net_per_eval']:+,.0f} |")
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
            for variant in VARIANTS:
                rows += control_rows(name, pre, cal, last, period, variant)
    text = report(rows, bars_sha)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
