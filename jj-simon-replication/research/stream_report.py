"""Firm scoring for candidate streams, each on its own span: every table B3 and B4 print, for tools whose streams do
not start where the data does (research/trend_exit.py, research/h3_filter.py).

A stream that takes no trade before some day is scored on a calendar that starts that day. The frozen walk-forward
starts an evaluation and a funded account on every calendar day and counts a start still open at its horizon as not
passed (or not paid). On a calendar wider than the stream, the starts more than a horizon before its first entry see
no trade at all and count as failures, and the later early starts replay its first days on a shortened window; neither
is an evaluation the stream could have run, and together they bias every rate in either direction.

Sections, per stream and period:
  B3 summary            the frozen topstep_50k at the sealed sizing: trades, R per trade, total R, P(pass), P(payout),
                        their standard errors, the median payout, JJ's calculator's EV and the EV net of every fee
                        (research/candidates.score)
  size sensitivity      topstep_50k_x (TopstepX) at 1.00, 0.98 and 0.95 of the budget (candidates.score_sized)
  whole micro contracts topstep_50k_x, entries sized in whole micro NQ within the budget (candidates.score_whole),
                        with the evaluation and funded trade counts and mean sizes, and the frozen bootstrap's P(bust)
                        from $2,000 as B3 prints it; n/a when no funded trade fits
  lifetime              B4 (research/lifetime.lifetime_rows) at every preset and size B4 uses, both payout policies,
                        horizons 60, 120 and 250
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.candidates import SIZES, bootstrap, ev_net, ev_per_eval, ny_day, score, score_sized, score_whole
from research.ledger_filters import sequential_pass
from research.lifetime import HORIZONS, POLICIES, RUNS, lifetime_rows

TOPSTEPX = "topstep_50k_x"


def on_span(pre: pd.DataFrame, cal: pd.DatetimeIndex, start: pd.Timestamp | None) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """The entries and the calendar from `start` (a New York date) on; everything when start is None."""
    if start is None:
        return pre, cal
    return pre[(ny_day(pre) >= start).to_numpy()], cal[cal >= start]


def _cell(x: float, fmt: str) -> str:
    return "n/a" if x is None or not np.isfinite(x) else format(x, fmt)


def scoring_sections(streams: list[tuple[str, pd.DataFrame, pd.Timestamp | None]], cal: pd.DatetimeIndex, cut: pd.Timestamp) -> list[str]:
    """The four sections for (name, entries before the sequential pass, span start) triples."""
    names = [name for name, _, _ in streams]
    if len(set(names)) != len(names):
        raise ValueError(f"stream names must be distinct: {names}")
    spans = [(name, *on_span(pre, cal, start), start) for name, pre, start in streams]
    s = ["### B3 summary: the frozen topstep_50k at the sealed sizing\n",
         "| stream | period | span from | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    seqs = {}
    for name, pre, cal_s, start in spans:
        st = sequential_pass(pre)
        seqs[name] = (st, pre, cal_s)
        sc = score(st, cal_s, cut)
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            r = p["firms"].set_index("firm").loc["topstep_50k"].to_dict()
            r["firm"] = "topstep_50k"
            s.append(f"| {name} | {per} | {start.date() if start is not None else 'all'} | {p['trades']} | {p['expectancy_r']:+.3f} | {p['total_r']:+.1f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | "
                     f"{r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {_cell(r['payout_median_amount'], ',.0f')} | {_cell(ev_per_eval(r), '+,.0f')} | {_cell(ev_net(r), '+,.0f')} |")
    s += ["", f"### Size sensitivity, {TOPSTEPX}\n",
          "| stream | period | P(pass) at " + " / ".join(f"{z:.2f}" for z in SIZES) + " | P(payout) at " + " / ".join(f"{z:.2f}" for z in SIZES) + " | EV net of all fees at " + " / ".join(f"{z:.2f}" for z in SIZES) + " |",
          "|---|---|---|---|---|"]
    for name, (st, pre, cal_s) in seqs.items():
        sized = {z: score_sized(st, cal_s, cut, z, TOPSTEPX) for z in SIZES}
        for per in ("development", "benchmark"):
            rows = [sized[z][per] for z in SIZES]
            if any(x is None for x in rows):
                continue
            s.append(f"| {name} | {per} | " + " / ".join(f"{x['pass_rate']:.1%}" for x in rows) + " | " + " / ".join(f"{x['payout_rate']:.1%}" for x in rows)
                     + " | " + " / ".join(_cell(ev_net({**x, 'firm': TOPSTEPX}), '+,.0f') for x in rows) + " |")
    s += ["", f"### Whole micro contracts, {TOPSTEPX}\n",
          "| stream | period | evaluation: trades, mean size | P(pass) | +/- | funded: trades, mean size | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees | P(bust) from $2,000 (frozen bootstrap) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, (st, pre, cal_s) in seqs.items():
        w = score_whole(pre, cal_s, cut, TOPSTEPX)
        dpre = ny_day(pre)
        for per, has in (("development", (dpre <= cut).any()), ("benchmark", (dpre > cut).any())):
            if not has:  # no entry in the period at all, as the other sections skip it
                continue
            q = w[per]
            head = f"| {name} | {per} | {q['eval_trades']}, {_cell(q['eval_size'], '.2f')} |"
            if q["firms"].empty:
                why = "no trade fits the evaluation budget" if not q["eval_trades"] else "no funded trade fits"
                s.append(head + " n/a | n/a | " + f"{q['funded_trades']}, {_cell(q['funded_size'], '.2f')} | n/a ({why}) | n/a | n/a | n/a | n/a | n/a |")
                continue
            r = q["firms"].iloc[0].to_dict()
            ok = np.isfinite(r["pass_rate"]) and np.isfinite(r["payout_rate"])
            bust = f"{bootstrap(r, 2000.0)['p_bust']:.0%}" if ok else "n/a"
            s.append(head + f" {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {q['funded_trades']}, {_cell(q['funded_size'], '.2f')} | {r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | "
                     f"{_cell(r['payout_median_amount'], ',.0f')} | {_cell(ev_per_eval(r), '+,.0f')} | {_cell(ev_net(r), '+,.0f')} | {bust} |")
    s += ["", "### Lifetime (B4): EV per evaluation with every payout and every fee\n",
          "Payout policies: " + "; ".join(f"{k}, {v}" for k, v in POLICIES.items()) + ". The first-payout gate is checked on the first policy.\n"]
    for firm, size in RUNS:
        s += [f"{firm} at {size:.2f} of the budget:\n",
              "| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | " + " | ".join(f"EV, H {h}" for h in HORIZONS) + f" | P(any payout by {HORIZONS[-1]}) | P(breach by {HORIZONS[-1]}) |",
              "|---|---|---|---|---|---|" + "---|" * (len(HORIZONS) + 2)]
        for name, (st, pre, cal_s) in seqs.items():
            rows = lifetime_rows(st, cal_s, cut, firm, size, policies=tuple(POLICIES))
            for per in ("development", "benchmark"):
                for policy in POLICIES:
                    rr = {r["horizon"]: r for r in rows if r["period"] == per and r["policy"] == policy}
                    if not rr:
                        continue
                    r0, last = rr[HORIZONS[0]], rr[HORIZONS[-1]]
                    s.append(f"| {name} | {per} | {policy} | {r0['pass_rate']:.1%} | {r0['fees']:,.0f} | {r0['b3_payout_rate']:.1%} | "
                             + " | ".join(_cell(rr[h]["ev"], "+,.0f") for h in HORIZONS) + f" | {_cell(last['p_any'], '.1%')} | {_cell(last['p_breach'], '.1%')} |")
        s.append("")
    return s
