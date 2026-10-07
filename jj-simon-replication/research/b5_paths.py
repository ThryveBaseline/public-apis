"""B5: the $2,000 bootstrap on replayed market paths, as pre-registered in docs/research/preregistration_b5_bootstrap.md.

From $2,000 of cash, each path runs Topstep 50K evaluations and Express Funded accounts on 365 calendar days of one
stream's real trading days, with every fee and every payout; every live account of a path takes the stream's trades of
the same day. Development paths start on every development day whose path ends on or before the cut (they overlap, as
the walk-forward); the benchmark is one path from its first day, reported beside.

Per path, before each trading day: payouts due are credited; each live evaluation is billed $49 every 30 calendar days
after its purchase (cancelled if cash is short); at most one evaluation is bought, if cash covers $49 and fewer than
`cap` accounts (evaluations plus Express Funded) are live. Then every slot trades the day: an evaluation the stream
sized for the evaluation budget (two-trade posture), an Express Funded account the stream sized for the funded budget
(fractional R x size in both, or whole micro contracts within each budget). After the day: a pass pays the $149
activation and the account trades as Express Funded from the next day (research/lifetime.LifetimeAccount with Topstep's
rules and the policy; a pass that cash cannot activate is lost); a failed evaluation or one still open after 30 trading
days is closed; a breached Express Funded account is closed; payouts (net of the split) are credited five trading days
later. A path is ruined when cash is below $49 with no live account and no payout pending.

Gates, on every run: each evaluation's outcome and day equal the frozen pass walk-forward's for its start day
(fpt.evaluate.walk_forward_pass_probability, the same rules, risk, sizing and calendar), and each Express Funded
account's first payout within 60 days (outcome, day and amount) equals the frozen payout walk-forward's for the day after
its pass (walk_forward_payout_probability) under the "ask" policy; under "wait", which the frozen walk-forward does not
have, it equals B4's walk-forward of the same policy (research/lifetime.walk_forward_lifetime, itself checked against a
scalar reference). Evaluations cancelled for fees and accounts cut off by the path's end are not compared.

Which configurations run: every stream B4 scores (B3's S0r and S1-S4; S5 and S6 if the trend exit passes its
registered test; H3's favoured-side streams if H3 passes its registered test on these inputs), at every preset, size
and payout policy B4 uses, whose development lifetime EV per evaluation at H 250 is positive. Each runs at its B4 size
(fractional) and in whole micro contracts, at caps 1 and 5, on development paths and on the benchmark path.

usage: python research/b5_paths.py <B3's arguments> --registration docs/research/preregistration_b5_bootstrap.md \
           --trend-registration docs/research/preregistration_trend_exit.md \
           --conditions-registration docs/research/preregistration_conditional_edge.md --out research/staging/run1_b5.md
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpt.data import NY  # noqa: E402
from fpt.evaluate import _daily_r, walk_forward_pass_probability, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import EVAL, FAILED, FUNDED, INACTIVE  # noqa: E402
from research import conditions, h3_filter, trend_exit  # noqa: E402
from research.candidates import (BILLING_DAYS, FUNDED_RISK, MAX_EVAL_DAYS, MAX_FUNDED_DAYS, MICROS_PER_MINI, PRESETS, add_gate_args, bootstrap,  # noqa: E402
                                 build_streams, gated_inputs, ny_day, score_sized, score_whole, sha256, whole_contracts)
from research.ledger_filters import sequential_pass  # noqa: E402
from research.lifetime import POLICIES, RUNS, STREAMS, TOPSTEP_XFA, LifetimeAccount, lifetime_rows, walk_forward_lifetime  # noqa: E402
from research.stream_report import on_span  # noqa: E402

REGISTRATION_SHA256 = "2693fb360b3e68ed70580a643bc2f3437cbcbf360e2579929349fb5baa405a2a"  # registered in df2bc28, clarified in 1995b2c
START_CASH = 2000.0
H_SELECT = 250
PATH_DAYS = 365
PAYOUT_DELAY = 5
CAPS = (1, 5)
SIZINGS = ("fractional", "whole micros")


class SlotAccount(LifetimeAccount):
    """An account slot of B5: B4's account, whose payout count (Topstep's first-payout exemption is per account)
    restarts with every purchase; the frozen reset keeps it per slot."""

    def purchase(self, mask: np.ndarray):
        super().purchase(mask)
        self.payout_count[mask] = 0


def eval_risk(firm: str) -> float:
    """The evaluation's risk per trade, B3's two-trade posture (research/candidates.firm_rows)."""
    return PRESETS[firm].profit_target / (2.0 * 1.5)


def phase_streams(pre: pd.DataFrame, firm: str, sizing: str, size: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The evaluation's and the funded account's streams from the candidate entries before the sequential pass:
    fractional (the sequential pass, R x size, the same stream in both phases; research/candidates.score_sized) or
    whole micro contracts within each phase's budget (research/candidates.score_whole)."""
    if sizing == "fractional":
        st = sequential_pass(pre).copy()
        st["r"] = st["r"].astype(float) * size
        return st, st
    if sizing != "whole micros":
        raise ValueError(f"unknown sizing {sizing!r}")
    cap = MICROS_PER_MINI * PRESETS[firm].max_contracts
    return whole_contracts(pre, eval_risk(firm), cap), whole_contracts(pre, FUNDED_RISK, cap)


def day_arrays(rs: list[np.ndarray], width: int) -> tuple[np.ndarray, np.ndarray]:
    """The frozen walk-forward's day rows (fpt.evaluate._daily_r) as padded arrays, plus one empty row at the end for
    days off a path."""
    r = np.zeros((len(rs) + 1, width))
    m = np.zeros((len(rs) + 1, width), dtype=bool)
    for i, x in enumerate(rs):
        r[i, :len(x)], m[i, :len(x)] = x, True
    return r, m


def path_bounds(dates: pd.DatetimeIndex, last: pd.Timestamp | None) -> tuple[np.ndarray, np.ndarray]:
    """Starts and ends (exclusive day indices) of the paths: each covers the days in [start, start + 365 calendar
    days). With `last`, every start whose path ends on or before it (development); without, one path from the first
    day (the benchmark)."""
    span = pd.Timedelta(days=PATH_DAYS)
    if last is None:
        starts = np.array([0]) if len(dates) else np.array([], dtype=int)
    else:
        starts = np.flatnonzero(dates + span - pd.Timedelta(days=1) <= last)
    ends = np.searchsorted(dates.values, (dates[starts] + span).values, side="left") if len(starts) else np.array([], dtype=int)
    return starts.astype(int), np.asarray(ends, dtype=int)


def simulate(dates: pd.DatetimeIndex, ev: tuple[np.ndarray, np.ndarray], fu: tuple[np.ndarray, np.ndarray], starts: np.ndarray, ends: np.ndarray,
             firm: str, policy: str, cap: int) -> dict:
    """Every path in one vectorised pass (a path is a sim of each of its `cap` slot accounts). Returns per-path
    arrays and the logs the gates compare."""
    rules = PRESETS[firm]
    er, fr = eval_risk(firm), FUNDED_RISK
    ev_r, ev_m = ev
    fu_r, fu_m = fu
    if ev_r.shape != fu_r.shape:
        raise ValueError("the evaluation and funded day arrays must share a shape")
    n = len(dates)
    p = len(starts)
    steps = int((ends - starts).max()) if p else 0
    day_no = dates.values.astype("datetime64[D]").astype(np.int64)
    slots = [SlotAccount(rules, p, fr, start_phase=INACTIVE, restart_failed=False, eval_risk=er, topstep_xfa=firm in TOPSTEP_XFA,
                         wait_for_lock=policy == "wait") for _ in range(cap)]
    cash = np.full(p, START_CASH)
    low = cash.copy()
    due = np.zeros((p, steps + PAYOUT_DELAY + 1))
    bought = np.zeros((cap, p), dtype=int)
    billed = np.zeros((cap, p), dtype=int)
    age = np.zeros((cap, p), dtype=int)
    xfa_start = np.zeros((cap, p), dtype=int)
    tracking = np.zeros((cap, p), dtype=bool)  # an Express Funded account whose first payout the gate still waits for
    out = {k: np.zeros(p) for k in ("evals", "passes", "activations", "lost_passes", "cancelled", "xfa_breaches", "payouts", "paid", "fees")}
    first_payout = np.full(p, np.nan)
    ruin_day = np.full(p, np.nan)
    ruined = np.zeros(p, dtype=bool)
    eval_log, xfa_log = [], []
    rows = np.arange(p)
    for k in range(steps + 1):
        d = starts + k
        on = d < ends
        for a in slots:  # a path that has just ended stops: whatever is live is cut off
            a.phase[~on & (a.phase != INACTIVE)] = INACTIVE
        cash += due[:, k]
        if k == steps:
            break
        di = np.where(on, d, n)
        for j, a in enumerate(slots):  # the monthly fee of every live evaluation
            live_eval = on & (a.phase == EVAL)
            period = (day_no[np.minimum(d, n - 1)] - day_no[np.minimum(bought[j], n - 1)]) // BILLING_DAYS + 1
            owe = live_eval & (period > billed[j])
            pay = owe & (cash >= rules.eval_cost)
            cash -= np.where(pay, rules.eval_cost, 0.0)
            out["fees"] += np.where(pay, rules.eval_cost, 0.0)
            billed[j] = np.where(pay, period, billed[j])
            cancel = owe & ~pay
            out["cancelled"] += cancel
            a.phase[cancel] = INACTIVE
        live = sum(((a.phase == EVAL) | (a.phase == FUNDED)).astype(int) for a in slots)
        can = on & (cash >= rules.eval_cost) & (live < cap)
        for j, a in enumerate(slots):  # at most one purchase a day, in the first free slot
            buy = can & ((a.phase == INACTIVE) | (a.phase == FAILED))
            if buy.any():
                a.purchase(buy)
                cash -= np.where(buy, rules.eval_cost, 0.0)
                out["fees"] += np.where(buy, rules.eval_cost, 0.0)
                out["evals"] += buy
                bought[j] = np.where(buy, d, bought[j])
                billed[j] = np.where(buy, 1, billed[j])
                age[j] = np.where(buy, 0, age[j])
                can &= ~buy
        for j, a in enumerate(slots):
            was_eval, was_funded = a.phase == EVAL, a.phase == FUNDED
            use = was_eval[:, None]
            a.apply_day(np.where(use, ev_r[di], fu_r[di]), np.where(use, ev_m[di], fu_m[di]) & on[:, None])
            age[j] += was_eval
            passed = was_eval & (a.phase == FUNDED)
            failed = was_eval & (a.phase == FAILED)
            still = was_eval & (a.phase == EVAL) & (age[j] >= MAX_EVAL_DAYS)
            for mask, outcome in ((passed, "pass"), (failed, "fail"), (still, "open")):
                for i in rows[mask]:
                    eval_log.append((int(i), int(bought[j, i]), outcome, int(age[j, i]) if outcome != "open" else -1))
            out["passes"] += passed
            act = passed & (cash >= rules.activation_fee)
            cash -= np.where(act, rules.activation_fee, 0.0)
            out["fees"] += np.where(act, rules.activation_fee, 0.0)
            out["activations"] += act
            out["lost_passes"] += passed & ~act
            xfa_start[j] = np.where(act, d + 1, xfa_start[j])
            tracking[j] |= act
            a.phase[(passed & ~act) | failed | still] = INACTIVE
            busted = was_funded & (a.phase == FAILED)
            out["xfa_breaches"] += busted
            for i in rows[busted & tracking[j]]:
                xfa_log.append((int(i), int(xfa_start[j, i]), "bust", int(d[i] - xfa_start[j, i] + 1), 0.0))
            tracking[j] &= ~busted
            a.phase[busted] = INACTIVE
            paid = a.payout_now()
            got = paid > 0
            due[got, k + PAYOUT_DELAY] += paid[got]
            out["payouts"] += got
            out["paid"] += paid
            first_payout = np.where(np.isnan(first_payout) & got, k + 1, first_payout)
            for i in rows[got & tracking[j]]:
                xfa_log.append((int(i), int(xfa_start[j, i]), "payout", int(d[i] - xfa_start[j, i] + 1), float(paid[i])))
            tracking[j] &= ~got
            aged = tracking[j] & (a.phase == FUNDED) & (d - xfa_start[j] + 1 >= MAX_FUNDED_DAYS)
            for i in rows[aged]:
                xfa_log.append((int(i), int(xfa_start[j, i]), "open", -1, 0.0))
            tracking[j] &= ~aged
        live = sum(((a.phase == EVAL) | (a.phase == FUNDED)).astype(int) for a in slots)
        pending = due[:, k + 1:].sum(axis=1) > 0
        newly = on & ~ruined & (cash < rules.eval_cost) & (live == 0) & ~pending
        ruin_day[newly] = k + 1
        ruined |= newly
        low = np.where(on, np.minimum(low, cash), low)
    out.update({"final_cash": cash + due[:, steps + 1:].sum(axis=1), "low": low, "ruined": ruined, "ruin_day": ruin_day,
                "first_payout": first_payout, "eval_log": eval_log, "xfa_log": xfa_log})
    return out


def first_payout_reference(fu_stream: pd.DataFrame, cal: pd.DatetimeIndex, firm: str, policy: str) -> pd.DataFrame:
    """Per start day: the first payout within 60 days (outcome, day, amount) as the gate's reference."""
    rules = PRESETS[firm]
    if policy == "ask":
        return walk_forward_payout_probability(fu_stream, rules, FUNDED_RISK, MAX_FUNDED_DAYS, trading_days=cal)
    lt, _ = walk_forward_lifetime(fu_stream, rules, FUNDED_RISK, (MAX_FUNDED_DAYS,), cal, firm in TOPSTEP_XFA, wait_for_lock=True)
    fd, bd = lt["first_payout_day"].to_numpy(float), lt["bust_day"].to_numpy(float)
    pay = fd <= MAX_FUNDED_DAYS
    bust = ~pay & (bd <= MAX_FUNDED_DAYS)
    outcome = np.where(pay, "payout", np.where(bust, "bust", "open"))
    return pd.DataFrame({"start": lt["start"], "outcome": outcome, "days": np.where(pay, fd, np.where(bust, bd, np.nan)),
                         "amount": np.where(pay, lt["first_payout_amount"].to_numpy(float), 0.0)})


def check_gates(res: dict, ev_stream: pd.DataFrame, fu_stream: pd.DataFrame, cal: pd.DatetimeIndex, firm: str, policy: str) -> tuple[int, int]:
    """Refuse unless every logged evaluation and every logged first payout equals its reference. Returns the counts
    compared."""
    rules = PRESETS[firm]
    ref_e = walk_forward_pass_probability(ev_stream, rules, eval_risk(firm), MAX_EVAL_DAYS, trading_days=cal)
    ref_f = first_payout_reference(fu_stream, cal, firm, policy)
    e = pd.DataFrame(res["eval_log"], columns=["path", "start", "outcome", "days"])
    f = pd.DataFrame(res["xfa_log"], columns=["path", "start", "outcome", "days", "amount"])
    for what, log, ref in (("evaluation", e, ref_e), ("Express Funded account", f, ref_f)):
        if log.empty:
            continue
        want = ref.iloc[log["start"].to_numpy()].reset_index(drop=True)
        timed = log["outcome"] != "open"
        bad = (want["outcome"].to_numpy() != log["outcome"].to_numpy()) | (timed & (want["days"].to_numpy(float) != log["days"].to_numpy(float))).to_numpy()
        if "amount" in log:
            bad |= ~np.isclose(np.where(log["outcome"] == "payout", want["amount"].to_numpy(float), 0.0), log["amount"].to_numpy(float))
        if bad.any():
            i = int(np.flatnonzero(bad)[0])
            raise ValueError(f"{int(bad.sum())} of {len(log)} {what}s differ from the walk-forward reference; the first: path {log['path'][i]}, start day "
                             f"{log['start'][i]}, {log['outcome'][i]} on day {log['days'][i]} against {want['outcome'][i]} on day {want['days'][i]}")
    return len(e), len(f)


def run(pre: pd.DataFrame, cal: pd.DatetimeIndex, last: pd.Timestamp | None, firm: str, policy: str, sizing: str, size: float, cap: int) -> dict:
    """One configuration on one period's calendar `cal` (`last` = the cut for development paths, None for the benchmark
    path): the streams on that calendar, the paths, the simulation, the gates, and the summary."""
    if not len(cal):
        return {"paths": 0}
    streams = []
    for st in phase_streams(pre, firm, sizing, size):
        day = ny_day(st)
        streams.append(st[((day >= cal[0]) & (day <= cal[-1])).to_numpy()])
    ev_stream, fu_stream = streams
    (dates, rs_e), (dates_f, rs_f) = _daily_r(ev_stream, cal), _daily_r(fu_stream, cal)
    dates = pd.DatetimeIndex(dates)
    if len(dates_f) != len(dates) or (pd.DatetimeIndex(dates_f) != dates).any():
        raise ValueError("the evaluation and funded streams do not share a calendar")
    width = max([1] + [len(x) for x in rs_e + rs_f])
    starts, ends = path_bounds(dates, last)
    if not len(starts):
        return {"paths": 0}
    res = simulate(dates, day_arrays(rs_e, width), day_arrays(rs_f, width), starts, ends, firm, policy, cap)
    n_e, n_f = check_gates(res, ev_stream, fu_stream, cal, firm, policy)
    return summarize(res, dates, starts, n_e, n_f)


def summarize(res: dict, dates: pd.DatetimeIndex, starts: np.ndarray, n_e: int, n_f: int) -> dict:
    final = res["final_cash"]
    q = np.percentile(final, [10, 25, 50, 75, 90])
    fall = np.maximum(START_CASH - res["low"], 0.0)
    years = ((dates[starts[-1]] - dates[starts[0]]).days + PATH_DAYS) / 365.25
    fp = res["first_payout"]
    return {"paths": int(len(final)), "years": float(years), "p_ruin": float(res["ruined"].mean()),
            "ruin_day_median": float(np.nanmedian(res["ruin_day"])) if res["ruined"].any() else float("nan"),
            "cash_p10": q[0], "cash_p25": q[1], "cash_p50": q[2], "cash_p75": q[3], "cash_p90": q[4], "cash_mean": float(final.mean()),
            "p_above_2000": float((final > START_CASH).mean()), "p_above_4000": float((final > 2 * START_CASH).mean()),
            "fall_p50": float(np.median(fall)), "fall_p90": float(np.percentile(fall, 90)),
            **{f"{k}_mean": float(res[k].mean()) for k in ("evals", "passes", "activations", "lost_passes", "cancelled", "xfa_breaches", "payouts", "paid", "fees")},
            "first_payout_median": float(np.nanmedian(fp)) if np.isfinite(fp).any() else float("nan"), "p_no_payout": float(np.isnan(fp).mean()),
            "gate_evaluations": n_e, "gate_funded": n_f}


def candidate_streams(trades: pd.DataFrame, bars: pd.DataFrame, b2: pd.DataFrame, cut: pd.Timestamp) -> tuple[list[tuple], list[str]]:
    """Every stream B4 scores, as (name, entries before the sequential pass, span start), and a note on each family."""
    pre, _, _, _ = build_streams(trades, bars, b2, cut)
    out = [(name, pre[name], None) for name in STREAMS]
    notes = ["B3's S0r and S1 to S4 on all the data"]
    x = trend_exit.build_trend(trades, bars, b2, cut)
    test = x["test"]
    verdict = f"one-sided p {test['p']:.4f}, positive in {test['years_pos']} of {test['years_n']} chain years"
    if test["passes"]:
        _, s6 = trend_exit.with_reversion(trades, bars, b2, x)
        start = pd.Timestamp(x["first"], 1, 1)
        out += [("S5 continuation, walk-forward trend exit", x["trend_frame"], start), (f"S6 S5 + A+ reversion, from {x['first']}", s6, start)]
        notes.append(f"the trend exit passed its registered test ({verdict}): S5 and S6 from {start.date()}")
    else:
        notes.append(f"the trend exit failed its registered test ({verdict}): S5 and S6 do not run")
    f = conditions.trade_frame(trades, bars, b2, cut)
    res = h3_filter.h3_result(f)
    verdict = f"Holm p {res['holm']:.4f}, positive in {res['dev_years_pos']} of {res['dev_years_n']} years"
    if res["passes"]:
        defined = f["H3"].dropna().index
        start = pd.Timestamp(int(trades.loc[defined, "entry_time"].dt.tz_convert(NY).dt.year.min()), 1, 1)
        out += [(name, p, start) for name, p in h3_filter.h3_frames(pre, f["H3"]) if "favoured" in name]
        notes.append(f"H3 passed its registered test on these inputs ({verdict}): its favoured-side streams from {start.date()}")
    else:
        notes.append(f"H3 did not pass its registered test on these inputs ({verdict}): its streams do not run")
    return out, notes


def select(streams: list[tuple], cal: pd.DatetimeIndex, cut: pd.Timestamp) -> list[dict]:
    """B4's development lifetime EV at H 250 for every stream, preset, size and policy, each stream on its span; a
    configuration runs when it is positive. B4's own gate runs inside lifetime_rows."""
    rows = []
    for name, pre, start in streams:
        pre_s, cal_s = on_span(pre, cal, start)
        st = sequential_pass(pre_s)
        for firm, size in RUNS:
            for r in lifetime_rows(st, cal_s, cut, firm, size, policies=tuple(POLICIES)):
                if r["period"] == "development" and r["horizon"] == H_SELECT:
                    rows.append({"stream": name, "start": start, **r, "runs": bool(np.isfinite(r["ev"]) and r["ev"] > 0)})
    return rows


def frozen_row(pre_s: pd.DataFrame, cal_s: pd.DatetimeIndex, cut: pd.Timestamp, firm: str, sizing: str, size: float) -> dict:
    """B3's development firm row for the same stream, preset and sizing, and the frozen bootstrap from $2,000 on it."""
    if sizing == "fractional":
        r = score_sized(sequential_pass(pre_s), cal_s, cut, size, firm)["development"]
    else:
        w = score_whole(pre_s, cal_s, cut, firm)["development"]["firms"]
        r = w.iloc[0].to_dict() if not w.empty else None
    if r is None or not (np.isfinite(r["pass_rate"]) and np.isfinite(r["payout_rate"])):
        return {"p_bust": float("nan"), "first_payout_days": float("nan"), "funded_month12": float("nan")}
    return bootstrap(r, START_CASH)


def qualifies(x: dict) -> bool:
    """The registered reading rule, on one development run."""
    return bool(x.get("paths") and x["p_ruin"] <= 0.10 and x["cash_p50"] > START_CASH and x["cash_p25"] >= 1000.0)


def _f(x, fmt: str) -> str:
    return "n/a" if x is None or not np.isfinite(x) else format(x, fmt)


def report(sel: list[dict], results: list[dict], notes: list[str], gate_note: str, reg_sha: str, cut: pd.Timestamp) -> str:
    s = ["# B5: the $2,000 bootstrap on replayed market paths\n", gate_note, "",
         f"Implements docs/research/preregistration_b5_bootstrap.md as registered in df2bc28 and clarified in 1995b2c, before any B5 number (sha256 of the file read: {reg_sha}, the pinned value). "
         f"Development: New York days through {cut.date()}; benchmark from {(cut + pd.Timedelta(days=1)).date()}, one path, reported beside and never used. "
         f"From ${START_CASH:,.0f} of cash, each path runs Topstep 50K evaluations and Express Funded accounts for {PATH_DAYS} calendar days on the stream's own trading days, every live account taking the same trades on the same day: "
         "$49 an evaluation at purchase and every 30 calendar days it stays live, $149 to activate a pass, payouts net of the split credited five trading days later, at most one purchase a day, "
         f"evaluations closed after {MAX_EVAL_DAYS} trading days; ruin is cash below $49 with nothing live and nothing pending. "
         "Gates, passed on every run: each evaluation's outcome and day equal the frozen pass walk-forward's for its start day, and each Express Funded account's first payout within 60 days equals the frozen payout walk-forward's "
         "(B4's walk-forward of the same policy under \"wait\"); B4's own gate holds on every configuration.\n",
         "Streams: " + "; ".join(notes) + ".\n",
         f"## Which configurations run (B4's development lifetime EV per evaluation at H {H_SELECT})\n",
         "| stream | preset | size | policy | P(pass) | fees per evaluation | expected paid per funded account | EV per evaluation | runs |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in sel:
        s.append(f"| {r['stream']} | {r['firm']} | {r['size']:.2f} | {r['policy']} | {r['pass_rate']:.1%} | {r['fees']:,.0f} | {_f(r['paid_mean'], ',.0f')} | {_f(r['ev'], '+,.0f')} | {'yes' if r['runs'] else 'no'} |")
    s.append("")
    if not results:
        s.append(f"No configuration has a positive development lifetime EV at H {H_SELECT}. By the registration, B5 stops here.\n")
        return "\n".join(s)
    s += ["## Results\n",
          "Cash at 12 months counts payouts earned and not yet credited; accounts live at the end count for nothing. Deepest fall: how far cash went below $2,000 at its lowest (the money actually at risk). "
          "Years: the non-overlapping years of data behind the development paths (the paths overlap, so this, not the number of paths, is the sample). "
          "Frozen bootstrap: B3's P(bust) from $2,000 at the same stream, preset and sizing (independent accounts, one payout each, no activation fee), for comparison.\n"]
    for c in results:
        s += [f"### {c['stream']}: {c['firm']}, {c['policy']}\n",
              "| sizing | cap | period | paths (years) | P(ruin in 12 months) | median ruin day | cash at 12 months: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | frozen bootstrap P(bust) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in c["runs"]:
            o = x["out"]
            if not o.get("paths"):
                s.append(f"| {x['sizing_label']} | {x['cap']} | {x['period']} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
                continue
            q = " / ".join(f"{o[k]:,.0f}" for k in ("cash_p10", "cash_p25", "cash_p50", "cash_p75", "cash_p90"))
            s.append(f"| {x['sizing_label']} | {x['cap']} | {x['period']} | {o['paths']} ({o['years']:.1f}) | {o['p_ruin']:.1%} | {_f(o['ruin_day_median'], '.0f')} | {q} | {o['cash_mean']:,.0f} | "
                     f"{o['p_above_2000']:.1%} | {o['p_above_4000']:.1%} | {o['fall_p50']:,.0f} / {o['fall_p90']:,.0f} | {_f(x['frozen']['p_bust'], '.0%')} |")
        s += ["", "| sizing | cap | period | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout day (median) | no payout | gate: evaluations, funded compared |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in c["runs"]:
            o = x["out"]
            if not o.get("paths"):
                continue
            s.append(f"| {x['sizing_label']} | {x['cap']} | {x['period']} | {o['evals_mean']:.1f} | {o['passes_mean']:.2f} | {o['lost_passes_mean']:.2f} | {o['cancelled_mean']:.2f} | {o['xfa_breaches_mean']:.2f} | "
                     f"{o['payouts_mean']:.2f} | {o['fees_mean']:,.0f} | {o['paid_mean']:,.0f} | {_f(o['first_payout_median'], '.0f')} | {o['p_no_payout']:.1%} | {o['gate_evaluations']}, {o['gate_funded']} |")
        s.append("")
    s += ["## Reading (the registered rule)\n",
          "A configuration goes on to a forward test only if, on development paths in whole micros at either cap, P(ruin within 12 months) is at most 10%, the median cash at 12 months is above $2,000 and its 25th percentile is at least $1,000. "
          "The benchmark path decides nothing; clean proof comes only from data after 2026-10-05.\n",
          "| stream | preset | policy | cap 1 | cap 5 | goes on to a forward test |", "|---|---|---|---|---|---|"]
    for c in results:
        dev = {x["cap"]: x["out"] for x in c["runs"] if x["sizing"] == "whole micros" and x["period"] == "development"}
        cells = ["yes" if qualifies(dev.get(cap, {})) else "no" for cap in CAPS]
        s.append(f"| {c['stream']} | {c['firm']} | {c['policy']} | " + " | ".join(cells) + f" | {'**yes**' if 'yes' in cells else 'no'} |")
    s.append("")
    return "\n".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    add_gate_args(ap)
    ap.add_argument("--registration", required=True, help="docs/research/preregistration_b5_bootstrap.md")
    ap.add_argument("--trend-registration", required=True, help="docs/research/preregistration_trend_exit.md")
    ap.add_argument("--conditions-registration", required=True, help="docs/research/preregistration_conditional_edge.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--allow-other-cut", action="store_true", help="tests only: run at another cut; the report says it is not the registered run")
    a = ap.parse_args()
    reg_sha = sha256(a.registration)
    for path, want, what in ((a.registration, REGISTRATION_SHA256, "B5"), (a.trend_registration, trend_exit.REGISTRATION_SHA256, "trend-exit"),
                             (a.conditions_registration, conditions.REGISTRATION_SHA256, "conditional-edge")):
        got = sha256(path)
        if got != want:
            raise SystemExit(f"refusing to report: the {what} registration file ({path}) is not the pinned one (sha256 {got})")
    registered_cut = a.oos_start == conditions.REGISTERED_OOS_START
    if not registered_cut and not a.allow_other_cut:
        raise SystemExit(f"refusing to report: the registered cut is --oos-start {conditions.REGISTERED_OOS_START}")
    g = gated_inputs(a)
    trades, bars, b2, cut, cal = g["trades"], g["bars"], g["replay"], g["cut"], g["cal"]
    try:
        streams, notes = candidate_streams(trades, bars, b2, cut)
        sel = select(streams, cal, cut)
        by_name = {name: (pre, start) for name, pre, start in streams}
        results, done = [], set()
        for r in (x for x in sel if x["runs"]):
            pre, start = by_name[r["stream"]]
            pre_s, cal_s = on_span(pre, cal, start)
            key = (r["stream"], r["firm"], r["policy"])
            c = next((x for x in results if (x["stream"], x["firm"], x["policy"]) == key), None)
            if c is None:
                c = {"stream": r["stream"], "firm": r["firm"], "policy": r["policy"], "runs": []}
                results.append(c)
            for sizing in SIZINGS:
                label = f"{r['size']:.2f} of the budget" if sizing == "fractional" else "whole micros"
                if (key, label) in done:
                    continue
                done.add((key, label))
                frozen = frozen_row(pre_s, cal_s, cut, r["firm"], sizing, r["size"])
                for cap in CAPS:
                    for period, part, last in (("development", cal_s[cal_s <= cut], cut), ("benchmark", cal_s[cal_s > cut], None)):
                        out = run(pre_s, part, last, r["firm"], r["policy"], sizing, r["size"], cap)
                        c["runs"].append({"sizing": sizing, "sizing_label": label, "cap": cap, "period": period, "out": out, "frozen": frozen})
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    text = report(sel, results, notes, g["note"], reg_sha, cut)
    if not registered_cut:
        text = text.replace("\n", "\n**NOT THE REGISTERED RUN: the cut differs from the registered one (a test-only flag).**\n\n", 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
