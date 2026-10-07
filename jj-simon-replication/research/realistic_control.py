"""The zero-edge control for task 15: how much of S3's and S4's realistic result (research/realistic_economics.py,
TopstepX's $1.22 micro fee, dips counted) the same trades would earn with no edge at all.

A Topstep account caps a trader's loss at the loss limit while half of every upswing can be withdrawn, so a stream
with no edge can be paid (docs/reviews/topstep_economics_audit.md; research/run1_structure.md for B4's accounting).
Here the two nulls of research/structure_control.py are rebuilt from the trades themselves and run through the
identical realistic paths, so "net per evaluation" splits into what the structure pays and what the edge adds:

  shift     every trade's R per micro, net of the real fee, moves by the period's mean, so the period's mean is
            exactly zero (outcome sizes move with it)
  re-label  winners take, in a seeded random order, the lower-median loss of the period's own losers until the
            period's mean is as close to zero as one more trade can bring it (outcome sizes stay the stream's own);
            ten orders, averaged, with their range

Each period's own mean is removed (development, in-sample; development from 2021; the benchmark path). A trade's
worst excursion is never less than its new loss. Descriptive: nothing is chosen on it.

usage:
  python research/realistic_control.py --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/s3s4_zero_edge_control.md
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

FEE = FEES["TopstepX"]
SEEDS = tuple(range(10))
FAR = pd.Timestamp("2100-01-01")  # every trade passed in counts as the period whose mean is removed


def net_r(pre: pd.DataFrame, fee: float = FEE) -> np.ndarray:
    """R per micro, net of the round-trip fee, on the trade's own stop."""
    stop = pre["stop_points"].astype(float).to_numpy()
    return (pre["pnl_points"].astype(float).to_numpy() * MNQ_POINT_VALUE - fee) / (stop * MNQ_POINT_VALUE)


def with_net_r(pre: pd.DataFrame, r: np.ndarray, fee: float = FEE) -> pd.DataFrame:
    """The trades with new net R per micro: points moved to match, and the worst excursion at least the new loss."""
    out = pre.copy()
    stop = out["stop_points"].astype(float).to_numpy()
    pnl = (np.asarray(r, dtype=float) * stop * MNQ_POINT_VALUE + fee) / MNQ_POINT_VALUE
    out["pnl_points"] = pnl
    out["mae_points"] = np.maximum(out["mae_points"].astype(float).to_numpy(), -pnl)
    return out


def shift_null(pre: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    r = net_r(pre)
    m = float(r.mean())
    return with_net_r(pre, r - m), m


def relabel_null(pre: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, float]:
    st, share = relabelled(pre.assign(r=net_r(pre)), FAR, seed)
    return with_net_r(pre, st["r"].to_numpy()), share


def control_rows(name: str, pre: pd.DataFrame, cal: pd.DatetimeIndex, last: pd.Timestamp | None, period: str) -> list[dict]:
    day = pd.DatetimeIndex(pre["entry_time"]).tz_convert("America/New_York").tz_localize(None).normalize()
    part = pre[(day >= cal[0]) & (day <= cal[-1])]
    zero, m = shift_null(part)
    flips = [relabel_null(part, s) for s in SEEDS]
    rows = []
    for policy in POLICIES:
        for callup in (None, CALLUP):
            act = run_variant(part, cal, last, policy, callup, FEE, dips=True)
            sh = run_variant(zero, cal, last, policy, callup, FEE, dips=True)
            rl = [run_variant(f, cal, last, policy, callup, FEE, dips=True) for f, _ in flips]
            rows.append({"candidate": name, "period": period, "policy": policy, "callup": callup, "trades": int(len(part)), "mean_net_r": m,
                         "relabel_share": float(np.mean([s for _, s in flips])), "actual": act, "shift": sh,
                         "relabel": {k: float(np.mean([x[k] for x in rl])) for k in ("net_per_eval", "cash_p50", "cash_mean", "p_ruin", "p_above_2000")},
                         "relabel_range": (float(min(x["net_per_eval"] for x in rl)), float(max(x["net_per_eval"] for x in rl)))})
            print(name, period, policy, callup, f"actual {act['net_per_eval']:+.0f} shift {sh['net_per_eval']:+.0f} "
                  f"relabel {rows[-1]['relabel']['net_per_eval']:+.0f}", flush=True)
    return rows


def report(rows: list[dict], bars_sha: str) -> str:
    s = ["# S3 and S4, realistic: what the structure pays a zero-edge stream, and what the edge adds\n",
         f"Sealed bars sha256 {bars_sha}. The paths of research/realistic_economics.py (from ${START_CASH:,.0f}, one Topstep 50K TopstepX account at "
         f"a time, whole micros sized with the fee, 365 days) with TopstepX's ${FEE:.2f} micro fee and dips counted, for the forward protocol's frozen "
         "S3 and S4 and for two zero-edge copies of the same trades (same entries, timing, stops and sizes): shift (every trade's net R per micro moved "
         "by the period's mean) and re-label (winners given the period's lower-median loss until the mean is zero; ten seeded orders averaged, "
         "range shown). Each period's own mean is removed. The edge's part is the stream's net per evaluation less the null's.\n",
         "Which rows to read: 'development, in-sample' flatters the candidates (the bracket was chosen on those years); 'development from 2021' is out "
         "of sample for the bracket; the benchmark is a single path.\n",
         "| candidate | period | policy | call-up | trades | mean net R | actual: net per eval / median / ruin | shift null: net / median / ruin | "
         "re-label null: net (range) / median / ruin | edge's part (vs shift / vs re-label) |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        a, sh, rl, lo_hi = x["actual"], x["shift"], x["relabel"], x["relabel_range"]
        s.append(f"| {x['candidate']} | {x['period']} | {x['policy']} | {'3rd payout' if x['callup'] else 'none'} | {x['trades']} | {x['mean_net_r']:+.3f} | "
                 f"{a['net_per_eval']:+,.0f} / {a['cash_p50']:,.0f} / {a['p_ruin']:.1%} | {sh['net_per_eval']:+,.0f} / {sh['cash_p50']:,.0f} / {sh['p_ruin']:.1%} | "
                 f"{rl['net_per_eval']:+,.0f} ({lo_hi[0]:+,.0f} to {lo_hi[1]:+,.0f}) / {rl['cash_p50']:,.0f} / {rl['p_ruin']:.1%} | "
                 f"{a['net_per_eval'] - sh['net_per_eval']:+,.0f} / {a['net_per_eval'] - rl['net_per_eval']:+,.0f} |")
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
            rows += control_rows(name, pre, cal, last, period)
    text = report(rows, bars_sha)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
