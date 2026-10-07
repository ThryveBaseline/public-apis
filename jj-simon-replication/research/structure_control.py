"""Structure versus edge: how much of B4's lifetime EV the same trades would earn with no development edge.

B4 (research/run1_b4_lifetime.md) finds a positive development lifetime EV per evaluation even for S0r, whose trades
lose on average. A funded account's loss is capped by the firm's drawdown while half of every upswing can be
withdrawn, so a trader with no edge can be paid. This control estimates that part with two nulls, each keeping every
entry and its timing, and each removing the stream's development mean:

  shift       every trade's R moves by the stream's development mean R per trade (outcome sizes move with it)
  re-label    trades on the side that gives the stream its mean (its losers when the mean is negative, its winners
              when it is positive) take, in a seeded random order, a middle development outcome of the other side,
              until the development mean is as close to zero as one more trade can bring it; the benchmark re-labels
              the same share of its trades on that side (outcome sizes stay the stream's own); averaged over ten
              orders, with the spread across them shown

Both copies go through B4's lifetime_rows at TopstepX's sizes and both payout policies and horizons (B4's first-payout
gate included). TopstepX only: at the sealed sizing a stop-out sits 0.02 R from the frozen preset's soft daily limit
and the drawdown edges, so a shift of a few hundredths of an R crosses them and the frozen preset's rows would measure
that artifact (docs/ASSUMPTIONS.md row 39). The edge's part is the stream's EV less the null's; how far the two nulls
disagree shows how much that split depends on the null. The benchmark year is moved the same way and shown beside;
nothing here is chosen on it.

Descriptive: no test, nothing selected. Defined after B4's headline rows were seen (S0r positive in development),
before its full tables were read; the re-label null and the TopstepX restriction were added after its review, before
it ran on real data.

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

RUNS_X = tuple((firm, size) for firm, size in RUNS if firm == "topstep_50k_x")  # TopstepX only (see the module note)
SEEDS = tuple(range(10))  # the re-label null is averaged over these orders (one order's spread is about $12-21)


def shifted(stream: pd.DataFrame, cut: pd.Timestamp) -> tuple[pd.DataFrame, float]:
    """The stream with every R shifted by its development mean R per trade (development expectancy exactly zero), and
    that mean. pnl_dollars is left alone: the sequential pass has already run, and the frozen evaluator reads R."""
    dev = (ny_day(stream) <= cut).to_numpy()
    m = float(stream.loc[dev, "r"].astype(float).mean())
    out = stream.copy()
    out["r"] = out["r"].astype(float) - m
    return out, m


def relabelled(stream: pd.DataFrame, cut: pd.Timestamp, seed: int = 0) -> tuple[pd.DataFrame, float]:
    """The re-label null and the share of the moving side's development trades re-labelled (see the module note); the
    share is NaN, and the stream returned unchanged, when the other side has no development trade."""
    r = stream["r"].astype(float).to_numpy().copy()
    dev = (ny_day(stream) <= cut).to_numpy()
    m = float(r[dev].mean()) if dev.any() else 0.0
    if m == 0.0:
        return stream.copy(), 0.0
    side = r < 0 if m < 0 else r > 0
    other = (r > 0 if m < 0 else r < 0) & dev
    if not other.any():  # nothing to re-label towards: the null is not defined for this stream
        return stream.copy(), float("nan")
    target = float(np.quantile(r[other], 0.5, method="lower"))  # a middle outcome of the stream's own, never an average of two
    rng = np.random.default_rng(seed)
    order = rng.permutation(np.flatnonzero(dev & side))
    total, best_k, best = float(r[dev].sum()), 0, abs(float(r[dev].sum()))
    for k, i in enumerate(order, 1):
        total += target - r[i]
        if abs(total) < best:
            best_k, best = k, abs(total)
        if (m < 0 and total >= 0) or (m > 0 and total <= 0):
            break
    share = best_k / len(order) if len(order) else 0.0
    r[order[:best_k]] = target
    bm = rng.permutation(np.flatnonzero(~dev & side))
    r[bm[:int(round(share * len(bm)))]] = target
    out = stream.copy()
    out["r"] = r
    return out, share


def rows_for(name: str, st: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp) -> list[dict]:
    """Per TopstepX size, period, policy and horizon: the stream, the shift null, and the re-label null averaged over
    SEEDS with its standard deviation across them."""
    zero, m = shifted(st, cut)
    flips = [relabelled(st, cut, seed) for seed in SEEDS]
    flips = [(f, sh) for f, sh in flips if np.isfinite(sh)]
    share = float(np.mean([sh for _, sh in flips])) if flips else float("nan")
    out = []
    key = ("period", "policy", "horizon")
    for firm, size in RUNS_X:
        real = lifetime_rows(st, cal, cut, firm, size, policies=tuple(POLICIES))
        null = lifetime_rows(zero, cal, cut, firm, size, policies=tuple(POLICIES))
        nulls2 = [lifetime_rows(f, cal, cut, firm, size, policies=tuple(POLICIES)) for f, _ in flips]
        for i, (a, b) in enumerate(zip(real, null)):
            if tuple(a[k] for k in key) != tuple(b[k] for k in key) or any(tuple(n2[i][k] for k in key) != tuple(a[k] for k in key) for n2 in nulls2):
                raise ValueError("the stream's and the nulls' rows do not line up")
            evs = np.array([n2[i]["ev"] for n2 in nulls2], dtype=float)
            ps = np.array([n2[i]["pass_rate"] for n2 in nulls2], dtype=float)
            out.append({"stream": name, "shift": m, "share": share, "firm": firm, "size": size, "period": a["period"], "policy": a["policy"], "horizon": a["horizon"],
                        "pass": a["pass_rate"], "pass0": b["pass_rate"], "pass1": float(ps.mean()) if len(ps) else float("nan"), "ev": a["ev"], "ev0": b["ev"],
                        "ev1": float(evs.mean()) if len(evs) else float("nan"), "ev1_sd": float(evs.std(ddof=1)) if len(evs) > 1 else float("nan")})
    return out


def _c(x: float, fmt: str) -> str:
    return "n/a" if not np.isfinite(x) else format(x, fmt)


def report(rows: list[dict], gate_note: str, cut: pd.Timestamp) -> str:
    s = ["# Structure versus edge: B4's lifetime EV with the development edge removed\n", gate_note, "",
         f"Development: New York days through {cut.date()}; benchmark from {(cut + pd.Timedelta(days=1)).date()}, moved the same way and shown beside. "
         "Two nulls remove each stream's development mean while keeping every entry and its timing. Shift: every R moves by the development mean (the shift column). "
         f"Re-label: trades on the side that gives the stream its mean take a middle development outcome of the other side (its lower median), in a seeded random order, until the development mean is as close to zero as one more trade can bring it (the share column, averaged over orders), so outcome sizes stay the stream's own; "
         f"it is averaged over {len(SEEDS)} orders, with the standard deviation across them beside it, because one order moves its EV by about $12-21. "
         "All copies go through B4's lifetime_rows (research/lifetime.py; its first-payout gate passed on every row), on TopstepX only: at the sealed sizing a stop-out sits 0.02 R from the frozen preset's soft daily limit, so shifting R by a few hundredths would cross it and measure that artifact. "
         "EV with no edge is what the same pattern of trades earns with a zero development mean: a funded account's loss is capped by the drawdown while half of every upswing can be withdrawn. "
         "The edge's part is the difference, under each null; where the two nulls disagree by more than the re-label null's spread, the split depends on the null. Descriptive only; nothing is chosen here.\n"]
    df = pd.DataFrame(rows)
    for (firm, size), g in df.groupby(["firm", "size"], sort=False):
        s += [f"## {firm} at {size:.2f} of the budget\n",
              "| stream | shift (R per trade) | re-labelled share | period | policy | H | P(pass): stream / shift / re-label | EV per evaluation | EV with no edge: shift / re-label (sd across orders) | the edge's part: shift / re-label |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            s.append(f"| {r['stream']} | {r['shift']:+.3f} | {r['share']:.1%} | {r['period']} | {r['policy']} | {r['horizon']} | {r['pass']:.1%} / {r['pass0']:.1%} / {r['pass1']:.1%} | "
                     f"{_c(r['ev'], '+,.0f')} | {_c(r['ev0'], '+,.0f')} / {_c(r['ev1'], '+,.0f')} ({_c(r['ev1_sd'], ',.0f')}) | {_c(r['ev'] - r['ev0'], '+,.0f')} / {_c(r['ev'] - r['ev1'], '+,.0f')} |")
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
