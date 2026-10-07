"""A trend exit for continuation, exactly as pre-registered in docs/research/preregistration_trend_exit.md
(registered in commit 66a400a, before any no-target ATR bracket had been replayed on any data).

The registered family: stop k x the previous Globex session's daily ATR (tick-rounded, at least 2 points), k in
{0.2, 0.3, 0.4, 0.5, 0.7, 1.0}, no target, flat at the close of the last bar before 16:00, replayed with
research/bracket_replay.replay on the sealed entries (the same context drops as the B2 replay file, checked). k is
chosen year by year by the pooled walk-forward of B1 and B3 within the family (from the fourth development year;
no trend trade before; benchmark trades take the choice made on all development years).

The test: the paired difference per continuation entry, trend-exit R minus S3's R (each with its own chain's choice
for the entry's year), averaged over development entries from the chain's first year to the cut, with a standard
error clustered by day and a one-sided normal p-value; it passes if p < 0.05 and the mean difference is positive in
at least 60% of the chain's development years. Reported beside: the chain, R per trade by direction against S1 and
S3, the exit mix, and the streams S5 (continuation, walk-forward trend exit) and S6 (S5 plus reversion A+, sealed
bracket) with their comparators S3 and S4 from the chain's first year, through B3's firm scoring (TopstepX at 0.95,
whole micro contracts) and B4's lifetime EV. The benchmark year is reported beside and never used.

Gates: B3's (research/candidates.gated_inputs), the registration file pinned by sha256, and the trend replay covering
exactly the entries the B2 replay covers.

usage: python research/trend_exit.py <B3's arguments> --registration docs/research/preregistration_trend_exit.md \
           --out research/staging/run1_trend_exit.md
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY  # noqa: E402
from research.bracket_replay import dropped_rows, replay  # noqa: E402
from research.candidates import (add_gate_args, build_streams, ev_net, gated_inputs, mean_se, ny_day, pooled_choices, score_sized,  # noqa: E402
                                 score_whole, sha256, variant_frame)
from research.conditions import one_sided_p  # noqa: E402
from research.ledger_filters import apply_filter, build_gates, sequential_pass  # noqa: E402
from research.lifetime import HORIZONS, lifetime_rows  # noqa: E402

REGISTRATION_SHA256 = "77816edcad0a40a265f095eba02202ae20f89b1c969cebda9839db60f1963e12"  # the file as registered in 66a400a
TREND_K = (0.2, 0.3, 0.4, 0.5, 0.7, 1.0)
TREND_NAMES = [f"trend_{k:g}" for k in TREND_K]
ALPHA, CONSISTENCY = 0.05, 0.60
FIRM, SIZE = "topstep_50k_x", 0.95


def trend_variants() -> list[dict]:
    """The registered family in research/bracket_replay's variant format: ATR-scaled stop, no target."""
    return [{"name": n, "family": "atr", "k": k, "rr": np.inf} for n, k in zip(TREND_NAMES, TREND_K)]


def replay_trend(trades: pd.DataFrame, bars: pd.DataFrame, b2_replay: pd.DataFrame) -> pd.DataFrame:
    """Replay the family on every gated entry (trade ids are ledger positions, as in the B2 replay file) and refuse
    unless it covers exactly the entries the B2 replay covers."""
    rep = replay(trades, bars, trend_variants())
    rep = pd.concat([rep, dropped_rows(rep)], ignore_index=True)
    mine = set(int(x) for x in rep.loc[rep["variant"] != "_dropped", "trade"])
    theirs = set(int(x) for x in b2_replay.loc[b2_replay["variant"] != "_dropped", "trade"])
    if mine != theirs:
        raise ValueError(f"the trend replay covers {len(mine)} entries, the B2 replay {len(theirs)}: not the same population")
    return rep


def trend_choice(trades: pd.DataFrame, chain: dict, cut: pd.Timestamp) -> pd.Series:
    """Per continuation entry: the chain's link for its development year, the all-development link in the benchmark,
    None before the chain's first year (no trend trade is taken there)."""
    ny = trades["entry_time"].dt.tz_convert(NY)
    day = ny.dt.normalize().dt.tz_localize(None)
    out = [chain.get("benchmark") if d > cut else chain.get(int(y)) for d, y in zip(day, ny.dt.year)]
    return pd.Series(out, index=trades.index, dtype=object)


def paired_test(trades: pd.DataFrame, trend_rep: pd.DataFrame, b2_replay: pd.DataFrame, s3_choice: pd.Series, tchoice: pd.Series, cut: pd.Timestamp) -> dict:
    """The registered statistic on development continuation entries that have a trend choice."""
    ids = tchoice.index[tchoice.notna().to_numpy() & (ny_day(trades.loc[tchoice.index]) <= cut).to_numpy()]
    t = trades.loc[ids]
    rt = variant_frame(t, trend_rep, tchoice.loc[ids])["r"].astype(float)
    rs = variant_frame(t, b2_replay, s3_choice.loc[ids])["r"].astype(float)
    d = rt - rs
    day = ny_day(t)
    n, m, se = mean_se(d, day)
    p = one_sided_p(m / se) if se and np.isfinite(se) and se > 0 else float("nan")
    years = d.groupby(day.dt.year).mean()
    pos = int((years > 0).sum())
    passes = bool(np.isfinite(p) and p < ALPHA and len(years) and pos / len(years) >= CONSISTENCY)
    return {"n": n, "trend_r": float(rt.mean()), "s3_r": float(rs.mean()), "delta": m, "se": se, "p": p,
            "years_pos": pos, "years_n": int(len(years)), "by_year": years, "passes": passes}


def r_by_direction(trades: pd.DataFrame, frames: dict, cut: pd.Timestamp) -> list[str]:
    """R per trade by period and direction for each named per-entry frame (same entries)."""
    s = ["| outcome | period | long | short | both |", "|---|---|---|---|---|"]
    for name, f in frames.items():
        day = ny_day(f)
        side = np.where(f["direction"].astype(int) > 0, "long", "short")
        for per, m in (("development", day <= cut), ("benchmark", day > cut)):
            cells = []
            for sd in ("long", "short", None):
                mm = m & ((side == sd) if sd else True)
                n, mu, se = mean_se(f.loc[mm, "r"], day[mm])
                cells.append(f"{n}, {mu:+.3f} ({se:.3f})" if n else "0, n/a")
            s.append(f"| {name} | {per} | " + " | ".join(cells) + " |")
    return s


def stream_rows(name: str, stream: pd.DataFrame, pre: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp) -> list[str]:
    """One stream through B3's firm scoring at TopstepX 0.95 and in whole micros, and B4's lifetime EV."""
    sized = score_sized(stream, cal, cut, SIZE, FIRM)
    whole = score_whole(pre, cal, cut, FIRM)
    life = {(r["period"], r["horizon"]): r["ev"] for r in lifetime_rows(stream, cal, cut, FIRM, SIZE)}
    day = ny_day(stream)
    out = []
    for per, m in (("development", day <= cut), ("benchmark", day > cut)):
        x = sized[per]
        if x is None:
            continue
        w = whole[per]["firms"]
        ew = ev_net(w.iloc[0].to_dict()) if not w.empty else float("nan")
        out.append(f"| {name} | {per} | {int(m.sum())} | {stream.loc[m, 'r'].astype(float).mean():+.3f} | {x['pass_rate']:.1%} | {x['payout_rate']:.1%} | "
                   f"{ev_net({**x, 'firm': FIRM}):+,.0f} | {ew:+,.0f} | " + " | ".join(f"{life.get((per, h), float('nan')):+,.0f}" for h in HORIZONS) + " |")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    add_gate_args(ap)
    ap.add_argument("--registration", required=True, help="docs/research/preregistration_trend_exit.md")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    reg_sha = sha256(a.registration)
    if reg_sha != REGISTRATION_SHA256:
        raise SystemExit(f"refusing to report: the registration file ({a.registration}) is not the pinned one (sha256 {reg_sha})")
    g = gated_inputs(a)
    trades, bars, b2, cut, cal = g["trades"], g["bars"], g["replay"], g["cut"], g["cal"]
    try:
        trend_rep = replay_trend(trades, bars, b2)
        pre, streams, s3_chain, s3_choice = build_streams(trades, bars, b2, cut)
        t = trades.loc[s3_choice.index]
        cont = t["setup"].astype(str) == "continuation"
        day = ny_day(t)
        year = t["entry_time"].dt.tz_convert(NY).dt.year
        dev_years = sorted(int(y) for y in year[day <= cut].unique())
        chain = pooled_choices(trend_rep, t, "continuation", TREND_NAMES, dev_years, cut)
        if not any(k != "benchmark" for k in chain):
            raise ValueError("the trend chain has no year: the walk-forward needs four development years")
        tchoice = trend_choice(t[cont], chain, cut)
        test = paired_test(t, trend_rep, b2, s3_choice, tchoice, cut)
        first = min(k for k in chain if k != "benchmark")
        took = tchoice.dropna()
        trend_frame = variant_frame(t, trend_rep, took)
        s3_frame = variant_frame(t, b2, s3_choice.loc[took.index])
        s1_frame = variant_frame(t, b2, pd.Series("ledger_bracket", index=took.index))
        # streams from the chain's first year: S5 (trend), S6 (S5 + reversion A+); comparators S3 and S4 on the same span
        gates = build_gates(trades, bars)
        rev = t.index[~cont.to_numpy()]
        span = ((year >= first) | (day > cut)).to_numpy()
        rev_span = pd.Index([k for k in rev if span[t.index.get_loc(k)]])
        rev_frame = variant_frame(t, b2, pd.Series("ledger_bracket", index=rev_span))
        s5_pre = trend_frame
        s6_pre = apply_filter(pd.concat([trend_frame, rev_frame]).sort_values("entry_time", kind="stable"), "B2a", gates)
        s3_pre = s3_frame
        s4_pre = apply_filter(pd.concat([s3_frame, rev_frame]).sort_values("entry_time", kind="stable"), "B2a", gates)
        rows = []
        for name, p in (("S3 from the chain's first year", s3_pre), ("S5 continuation, walk-forward trend exit", s5_pre),
                        ("S4 from the chain's first year", s4_pre), ("S6 S5 + A+ reversion, sealed bracket", s6_pre)):
            rows += stream_rows(name, sequential_pass(p), p, cal, cut)
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    stops = (trend_rep.set_index(["trade", "variant"]).loc[pd.MultiIndex.from_arrays([took.index.astype(int), took.to_numpy()]), "exit_reason"] == "stop").mean()
    s = ["# Trend exit for continuation: the pre-registered test\n", g["note"], "",
         f"Implements docs/research/preregistration_trend_exit.md as registered in commit 66a400a (sha256 of the file read: {reg_sha}, the pinned value). "
         f"Development: New York days through {cut.date()}; benchmark from {(cut + pd.Timedelta(days=1)).date()}. "
         f"Family: stop k x the previous session's daily ATR, k in {{{', '.join(f'{k:g}' for k in TREND_K)}}}, no target, flat at 16:00; replayed on the {trend_rep.loc[trend_rep['variant'] != '_dropped', 'trade'].nunique()} entries the B2 replay covers.\n",
         "Walk-forward k, chosen on earlier development years only: " + "; ".join(f"{k}: {v}" for k, v in chain.items()) + f"; before {first}, no trend trade. S3's chain for comparison: "
         + "; ".join(f"{k}: {v}" for k, v in s3_chain.items()) + ".\n",
         "## The test\n",
         f"Paired difference per development continuation entry from {first}, trend-exit R minus S3's R: {test['delta']:+.4f} (standard error {test['se']:.4f}, clustered by day), "
         f"one-sided p {test['p']:.4f}; trend exit {test['trend_r']:+.4f} R against S3 {test['s3_r']:+.4f} R on {test['n']} entries; positive in {test['years_pos']} of {test['years_n']} chain years. "
         f"**{'Passes' if test['passes'] else 'Fails'}** (registered rule: p < {ALPHA} and positive in at least {CONSISTENCY:.0%} of chain years).\n",
         "| year | mean difference |\n|---|---|"]
    s += [f"| {y} | {v:+.4f} |" for y, v in test["by_year"].items()]
    s += ["", "## R per trade by direction, same entries (from the chain's first year)\n"]
    s += r_by_direction(t, {"trend exit (chain)": trend_frame, "S3 (chain)": s3_frame, "S1 (sealed bracket)": s1_frame}, cut)
    s += ["", f"Exit mix of the trend exit: {stops:.1%} stopped, {1 - stops:.1%} flat at 16:00.\n",
          f"## Streams under the firm rules ({FIRM} at {SIZE:.2f} of the budget, B3 and B4)\n",
          ("Per the registration these are the next step for a passing exit; " if test["passes"] else "The exit failed its test; per the registration these are reported once for the record and dropped. ")
          + "EV net is JJ's calculator with every fee (first payout only); whole micros as B3; lifetime EV as B4 (every payout, Topstep's Express Funded rule) at H walk-forward days.\n",
          "| stream | period | trades | R/trade | P(pass) | P(payout) | EV net, first payout | EV net, whole micros | " + " | ".join(f"lifetime EV, H {h}" for h in HORIZONS) + " |",
          "|---|---|---|---|---|---|---|---|" + "---|" * len(HORIZONS)]
    s += rows
    s.append("")
    text = "\n".join(s)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
