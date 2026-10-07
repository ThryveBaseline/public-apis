"""H3 through firm scoring: the one conditional-edge test that passed (research step 4), followed as its registration
requires (docs/research/preregistration_conditional_edge.md: a passing condition becomes a candidate filter and goes,
with provenance, through the B3 firm scoring on its favoured side, then re-simulation).

H3 favours continuation entries whose opening candle's body over the daily ATR is at or above its walk-forward median.
The flag is taken exactly as research/conditions.trade_frame computes it, with that registration pinned and at its
registered cut. For S1, S3 and S4 the comparator keeps every continuation entry where H3 is defined (it is not in the
first development year), the candidate only its favoured side; S4's reversion A+ entries are the same in both, and the
filter is applied before the sequential pass. H3 has no threshold before its second year, so both sides of every pair
are scored on a calendar from the first year in which H3 is defined (a wider calendar would add evaluations the
streams could not have run; research/stream_report). Scoring: every table of B3 and B4
(research/stream_report.scoring_sections). The benchmark year is reported beside and never used. Re-simulation on the
research engine follows for a filter that improves the streams here.

usage: python research/h3_filter.py <B3's arguments> --registration docs/research/preregistration_conditional_edge.md \
           --out research/staging/run1_h3.md
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY  # noqa: E402
from research import conditions  # noqa: E402
from research.candidates import add_gate_args, build_streams, gated_inputs, sha256  # noqa: E402
from research.stream_report import scoring_sections  # noqa: E402

STREAMS = (("S1", "S1 continuation only, sealed bracket"), ("S3", "S3 continuation only, walk-forward ATR bracket"),
           ("S4", "S4 S3 + A+ reversion, sealed bracket"))


def h3_frames(pre: dict, h3: pd.Series) -> list[tuple[str, pd.DataFrame]]:
    """Per stream, the comparator (continuation entries where H3 is defined) and the candidate (its favoured side);
    every other entry of the stream (S4's reversion A+) kept in both."""
    out = []
    for short, name in STREAMS:
        p = pre[name]
        cont = p["setup"].astype(str) == "continuation"
        flag = h3.reindex(p.index)
        out.append((f"{short} where H3 is defined", p[~cont | flag.notna()]))
        out.append((f"{short} on H3's favoured side", p[~cont | (flag == 1.0)]))
    return out


def h3_result(f: pd.DataFrame) -> dict:
    """H3's registered test on these inputs, exactly as research/conditions computes it: all nine hypotheses, Holm
    across the family, the pass rule."""
    rows = []
    for h, pop, _, _ in conditions.HYPOTHESES:
        res = conditions.evaluate_hypothesis(f, h, pop)
        rows.append({"id": h, **{f"dev_{k}": v for k, v in res["development"].items()}})
    conditions.decide(rows)
    return next(r for r in rows if r["id"] == "H3")


def main() -> int:
    ap = argparse.ArgumentParser()
    add_gate_args(ap)
    ap.add_argument("--registration", required=True, help="docs/research/preregistration_conditional_edge.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-other-cut", action="store_true", help="tests only: run at another cut; the report says it is not the registered run")
    a = ap.parse_args()
    reg_sha = sha256(a.registration)
    if reg_sha != conditions.REGISTRATION_SHA256:
        raise SystemExit(f"refusing to report: the registration file ({a.registration}) is not the pinned one (sha256 {reg_sha})")
    registered_cut = a.oos_start == conditions.REGISTERED_OOS_START
    if not registered_cut and not a.allow_other_cut:
        raise SystemExit(f"refusing to report: H3 is registered at --oos-start {conditions.REGISTERED_OOS_START}")
    g = gated_inputs(a)
    cut = g["cut"]
    try:
        f = conditions.trade_frame(g["trades"], g["bars"], g["replay"], cut)
        pre, _, _, _ = build_streams(g["trades"], g["bars"], g["replay"], cut)
        defined = f["H3"].dropna().index
        if not len(defined):
            raise ValueError("H3 is defined on no entry")
        first = int(g["trades"].loc[defined, "entry_time"].dt.tz_convert(NY).dt.year.min())
        frames = h3_frames(pre, f["H3"])
        res = h3_result(f)
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    start = pd.Timestamp(first, 1, 1)
    s = ["# H3 through firm scoring: continuation after a large opening candle\n"]
    if not registered_cut:
        s.append("**NOT THE REGISTERED RUN: the cut differs from the registered one (a test-only flag).**\n")
    s += [g["note"], "",
          f"H3 as registered in commit c0c7a15 and clarified in 26cb07a (sha256 of the file read: {reg_sha}, the pinned value), at the registered cut: development through {cut.date()}, benchmark from {(cut + pd.Timedelta(days=1)).date()}. "
          f"On these inputs its registered test gives a development difference of {res['dev_delta']:+.3f} R (standard error {res['dev_se']:.3f}), Holm p {res['holm']:.4f} across the nine, "
          f"positive in {res['dev_years_pos']} of {res['dev_years_n']} years: it **{'passes' if res['passes'] else 'does not pass'}**"
          + ("" if res["passes"] else ", so by its registration it is no candidate filter and these tables are for the record only") + ". "
          "Each stream is shown on the continuation entries where H3 is defined (the comparator) and on H3's favoured side only; S4's reversion A+ entries are the same in both, and the filter is applied before the sequential pass. "
          f"H3 is first defined in {first}, so both sides of every pair are scored on a calendar from {start.date()}.\n"]
    try:
        s += scoring_sections([(name, p, start) for name, p in frames], g["cal"], cut)
    except ValueError as e:
        s.append(f"The firm scoring stopped: {e}.\n")
    text = "\n".join(s)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
