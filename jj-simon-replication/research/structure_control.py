"""Structure versus edge: how much of B4's lifetime EV a stream would earn with no edge at all.

B4 (research/run1_b4_lifetime.md) finds a positive development lifetime EV per evaluation even for S0r, whose trades
lose on average. A funded account's loss is capped by the firm's drawdown while half of every upswing can be
withdrawn, so a trader with no edge can be paid. This control measures that part directly.

For each of B3's streams (S0r and S1 to S4, after the sequential pass), every trade's R is shifted by the stream's
development mean R per trade. The development expectancy becomes exactly zero; the entries, their timing, their number
and the spread of their outcomes are unchanged. Both the stream and its shifted copy go through B4's lifetime_rows at
every preset, size, payout policy and horizon B4 uses (the first-payout gate included). The shifted copy's EV is what
the structure pays this pattern of trades; the difference is what the stream's edge adds. The benchmark year is shifted
by the same development mean and shown beside; nothing here is chosen on it.

Descriptive: no test, nothing selected. Defined after B4's headline rows were seen (S0r positive in development),
before its full tables were read.

usage: python research/structure_control.py <B3's arguments> --out research/staging/run1_structure.md
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.candidates import add_gate_args, build_streams, gated_inputs, ny_day  # noqa: E402
from research.lifetime import POLICIES, RUNS, STREAMS, lifetime_rows  # noqa: E402


def shifted(stream: pd.DataFrame, cut: pd.Timestamp) -> tuple[pd.DataFrame, float]:
    """The stream with every R shifted by its development mean R per trade (development expectancy exactly zero), and
    that mean. pnl_dollars is left alone: the sequential pass has already run, and the frozen evaluator reads R."""
    dev = (ny_day(stream) <= cut).to_numpy()
    m = float(stream.loc[dev, "r"].astype(float).mean())
    out = stream.copy()
    out["r"] = out["r"].astype(float) - m
    return out, m


def rows_for(name: str, st: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp) -> list[dict]:
    zero, m = shifted(st, cut)
    out = []
    for firm, size in RUNS:
        real = lifetime_rows(st, cal, cut, firm, size, policies=tuple(POLICIES))
        null = lifetime_rows(zero, cal, cut, firm, size, policies=tuple(POLICIES))
        for a, b in zip(real, null):
            if (a["period"], a["policy"], a["horizon"]) != (b["period"], b["policy"], b["horizon"]):
                raise ValueError("the stream's and the shifted stream's rows do not line up")
            out.append({"stream": name, "shift": m, "firm": firm, "size": size, "period": a["period"], "policy": a["policy"], "horizon": a["horizon"],
                        "pass": a["pass_rate"], "pass0": b["pass_rate"], "paid": a["paid_mean"], "paid0": b["paid_mean"], "ev": a["ev"], "ev0": b["ev"]})
    return out


def _c(x: float, fmt: str) -> str:
    return "n/a" if not np.isfinite(x) else format(x, fmt)


def report(rows: list[dict], gate_note: str, cut: pd.Timestamp) -> str:
    s = ["# Structure versus edge: B4's lifetime EV with the edge removed\n", gate_note, "",
         f"Development: New York days through {cut.date()}; benchmark from {(cut + pd.Timedelta(days=1)).date()}, shifted by the development mean and shown beside. "
         "Each stream's R is shifted by its own development mean R per trade (the shift column), so its development expectancy is exactly zero while every entry, its timing and the spread of outcomes stay as they are. "
         "Both copies go through B4's lifetime_rows (research/lifetime.py; its first-payout gate passed on every row). "
         "EV with no edge is what the firm's structure pays this pattern of trades: a funded account's loss is capped by the drawdown, while half of every upswing can be withdrawn. "
         "The edge's part is the difference. Descriptive only; nothing is chosen here.\n"]
    df = pd.DataFrame(rows)
    for (firm, size), g in df.groupby(["firm", "size"], sort=False):
        s += [f"## {firm} at {size:.2f} of the budget\n",
              "| stream | shift (R per trade) | period | policy | H | P(pass) | P(pass), no edge | expected paid per funded account | the same, no edge | EV per evaluation | EV with no edge | the edge's part |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            s.append(f"| {r['stream']} | {r['shift']:+.3f} | {r['period']} | {r['policy']} | {r['horizon']} | {r['pass']:.1%} | {r['pass0']:.1%} | {_c(r['paid'], ',.0f')} | {_c(r['paid0'], ',.0f')} | "
                     f"{_c(r['ev'], '+,.0f')} | {_c(r['ev0'], '+,.0f')} | {_c(r['ev'] - r['ev0'], '+,.0f')} |")
        s.append("")
    return "\n".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    add_gate_args(ap)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    g = gated_inputs(a)
    try:
        _, streams, _, _ = build_streams(g["trades"], g["bars"], g["replay"], g["cut"])
        rows = []
        for name in STREAMS:
            rows += rows_for(name, streams[name], g["cal"], g["cut"])
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    text = report(rows, g["note"], g["cut"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
