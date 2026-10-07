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
(fractional) on its preset; for every stream and policy with a selected configuration, whole micro contracts run on
TopstepX (the frozen preset's soft daily limit is not usable below the sealed sizing; registration clarification 5).
All at caps 1 and 5, on development paths and on the benchmark path. Both phases share one calendar, so a period in
which no trade fits one phase's budget still runs: that phase's account never trades. Every run is repeated with
Topstep's call-up to a Live account at the path's 3rd payout request (amendment 10): every account closes, nothing more
is bought, and the Live account counts for nothing, a lower bound. The reading needs both versions to qualify.

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
from fpt.evaluate import _calendar, _daily_r, walk_forward_pass_probability, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import EVAL, FAILED, FUNDED, INACTIVE  # noqa: E402
from research import conditions, h3_filter, trend_exit  # noqa: E402
from research.candidates import (BILLING_DAYS, FUNDED_RISK, MAX_EVAL_DAYS, MAX_FUNDED_DAYS, MICROS_PER_MINI, PRESETS, add_gate_args, bootstrap,  # noqa: E402
                                 build_streams, gated_inputs, ny_day, score_sized, score_whole, sha256, whole_contracts)
from research.ledger_filters import sequential_pass  # noqa: E402
from research.lifetime import POLICIES, RUNS, STREAMS, TOPSTEP_XFA, LifetimeAccount, lifetime_rows, walk_forward_lifetime  # noqa: E402
from research.stream_report import on_span  # noqa: E402

REGISTRATION_SHA256 = "bdd8635616b27c07902ec3060a2990ee21004091a9e47430f400b4eacac5ac18"  # registered df2bc28, clarified 1995b2c 7465eed, amended eb01d37
START_CASH = 2000.0
H_SELECT = 250
PATH_DAYS = 365
PAYOUT_DELAY = 5
CAPS = (1, 5)
SIZINGS = ("fractional", "whole micros")
TOPSTEPX = "topstep_50k_x"  # whole micros run on this preset only (clarification 5)
CALLUP = 3  # the call-up to a Live account at the path's 3rd payout request, the lower bound (amendment 10)
CALLUPS = (None, CALLUP)


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
             firm: str, policy: str, cap: int, callup: int | None = None) -> dict:
    """Every path in one vectorised pass (a path is a sim of each of its `cap` slot accounts). Returns per-path
    arrays and the logs the gates compare. With `callup`, a path is called up to a Live account at the end of the day
    its payout requests (across all its accounts) reach that number: every account closes and the path stops
    (amendment 10); it is not a ruin, and the Live account counts for nothing."""
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
    called = np.zeros(p, dtype=bool)
    callup_day = np.full(p, np.nan)
    n_pay = np.zeros(p, dtype=int)
    eval_log, xfa_log = [], []
    rows = np.arange(p)
    for k in range(steps + 1):
        d = starts + k
        on = d < ends
        run_ = on & ~called  # a path called up has stopped
        for a in slots:  # a path that has ended or been called up stops: whatever is live is cut off
            a.phase[~run_ & (a.phase != INACTIVE)] = INACTIVE
        cash += due[:, k]
        if k == steps:
            break
        di = np.where(run_, d, n)
        for j, a in enumerate(slots):  # the monthly fee of every live evaluation
            live_eval = run_ & (a.phase == EVAL)
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
        can = run_ & (cash >= rules.eval_cost) & (live < cap)
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
            a.apply_day(np.where(use, ev_r[di], fu_r[di]), np.where(use, ev_m[di], fu_m[di]) & run_[:, None])
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
            n_pay += got
            first_payout = np.where(np.isnan(first_payout) & got, k + 1, first_payout)
            for i in rows[got & tracking[j]]:
                xfa_log.append((int(i), int(xfa_start[j, i]), "payout", int(d[i] - xfa_start[j, i] + 1), float(paid[i])))
            tracking[j] &= ~got
            aged = tracking[j] & (a.phase == FUNDED) & (d - xfa_start[j] + 1 >= MAX_FUNDED_DAYS)
            for i in rows[aged]:
                xfa_log.append((int(i), int(xfa_start[j, i]), "open", -1, 0.0))
            tracking[j] &= ~aged
        if callup is not None:
            hit = run_ & (n_pay >= callup)
            callup_day[hit] = k + 1
            called |= hit
        live = sum(((a.phase == EVAL) | (a.phase == FUNDED)).astype(int) for a in slots)
        pending = due[:, k + 1:].sum(axis=1) > 0
        newly = run_ & ~called & ~ruined & (cash < rules.eval_cost) & (live == 0) & ~pending
        ruin_day[newly] = k + 1
        ruined |= newly
        low = np.where(on, np.minimum(low, cash), low)
    out.update({"final_cash": cash + due[:, steps + 1:].sum(axis=1), "low": low, "ruined": ruined, "ruin_day": ruin_day,
                "first_payout": first_payout, "called": called, "callup_day": callup_day, "eval_log": eval_log, "xfa_log": xfa_log})
    return out


def phase_days(ev_stream: pd.DataFrame, fu_stream: pd.DataFrame, cal: pd.DatetimeIndex) -> tuple[pd.DatetimeIndex, list, list]:
    """Both phases' day rows on one calendar: the period's trading days and every day either phase trades, each row as
    fpt.evaluate._daily_r gives it on that calendar (empty arrays throughout for a stream with no trade)."""
    days = set(_calendar(cal))
    for st in (ev_stream, fu_stream):
        days |= set(ny_day(st)) if len(st) else set()
    dates = pd.DatetimeIndex(sorted(days))
    rows = []
    for st in (ev_stream, fu_stream):
        if st.empty:
            rows.append([np.zeros(0) for _ in range(len(dates))])
            continue
        got, rs = _daily_r(st, dates)
        if len(got) != len(dates) or (pd.DatetimeIndex(got) != dates).any():
            raise ValueError("a phase's day rows do not match the shared calendar")
        rows.append(rs)
    return dates, rows[0], rows[1]


def _empty_reference(n: int, horizon: int) -> pd.DataFrame:
    """The walk-forward of a stream with no trade: every start that has the horizon's days is open, the rest censored."""
    avail = n - np.arange(n)
    return pd.DataFrame({"outcome": np.where(avail >= horizon, "open", "censored"), "days": np.nan, "amount": 0.0})


def first_payout_reference(fu_stream: pd.DataFrame, dates: pd.DatetimeIndex, firm: str, policy: str) -> pd.DataFrame:
    """Per start day: the first payout within 60 days (outcome, day, amount) as the gate's reference."""
    rules = PRESETS[firm]
    if fu_stream.empty:
        return _empty_reference(len(dates), MAX_FUNDED_DAYS)
    if policy == "ask":
        return walk_forward_payout_probability(fu_stream, rules, FUNDED_RISK, MAX_FUNDED_DAYS, trading_days=dates)
    lt, _ = walk_forward_lifetime(fu_stream, rules, FUNDED_RISK, (MAX_FUNDED_DAYS,), dates, firm in TOPSTEP_XFA, wait_for_lock=True)
    fd, bd = lt["first_payout_day"].to_numpy(float), lt["bust_day"].to_numpy(float)
    pay = fd <= MAX_FUNDED_DAYS
    bust = ~pay & (bd <= MAX_FUNDED_DAYS)
    outcome = np.where(pay, "payout", np.where(bust, "bust", "open"))
    return pd.DataFrame({"start": lt["start"], "outcome": outcome, "days": np.where(pay, fd, np.where(bust, bd, np.nan)),
                         "amount": np.where(pay, lt["first_payout_amount"].to_numpy(float), 0.0)})


def check_gates(res: dict, ev_stream: pd.DataFrame, fu_stream: pd.DataFrame, dates: pd.DatetimeIndex, firm: str, policy: str) -> tuple[int, int]:
    """Refuse unless every logged evaluation and every logged first payout equals its reference on the shared
    calendar `dates`. Returns the counts compared."""
    rules = PRESETS[firm]
    ref_e = (walk_forward_pass_probability(ev_stream, rules, eval_risk(firm), MAX_EVAL_DAYS, trading_days=dates) if len(ev_stream)
             else _empty_reference(len(dates), MAX_EVAL_DAYS))
    ref_f = first_payout_reference(fu_stream, dates, firm, policy)
    for ref in (ref_e, ref_f):
        if len(ref) != len(dates):
            raise ValueError("a gate reference does not cover the shared calendar")
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


def run(pre: pd.DataFrame, cal: pd.DatetimeIndex, last: pd.Timestamp | None, firm: str, policy: str, sizing: str, size: float, cap: int,
        callup: int | None = None) -> dict:
    """One configuration on one period's calendar `cal` (`last` = the cut for development paths, None for the benchmark
    path): the streams on that calendar, the paths, the simulation, the gates, and the summary."""
    if not len(cal):
        return {"paths": 0}
    streams = []
    for st in phase_streams(pre, firm, sizing, size):
        day = ny_day(st)
        streams.append(st[((day >= cal[0]) & (day <= cal[-1])).to_numpy()])
    ev_stream, fu_stream = streams
    dates, rs_e, rs_f = phase_days(ev_stream, fu_stream, cal)
    width = max([1] + [len(x) for x in rs_e + rs_f])
    starts, ends = path_bounds(dates, last)
    if not len(starts):
        return {"paths": 0}
    res = simulate(dates, day_arrays(rs_e, width), day_arrays(rs_f, width), starts, ends, firm, policy, cap, callup)
    n_e, n_f = check_gates(res, ev_stream, fu_stream, dates, firm, policy)
    out = summarize(res, dates, starts, n_e, n_f)
    out.update({"eval_trades": int(len(ev_stream)), "funded_trades": int(len(fu_stream)),
                "span_days": int(np.median((dates[ends - 1] - dates[starts]).days + 1))})
    return out


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
            "p_callup": float(res["called"].mean()), "callup_day_median": float(np.nanmedian(res["callup_day"])) if res["called"].any() else float("nan"),
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


def frozen_row(pre_s: pd.DataFrame, cal_s: pd.DatetimeIndex, cut: pd.Timestamp, firm: str, sizing: str, size: float, period: str) -> dict:
    """That period's B3 firm row for the same stream, preset and sizing, and the frozen bootstrap from $2,000 on it,
    as B3 calls it (research/candidates.bootstrap): P(bust), the median days to the first payout, the funded accounts
    at month 12."""
    if sizing == "fractional":
        r = score_sized(sequential_pass(pre_s), cal_s, cut, size, firm)[period]
    else:
        w = score_whole(pre_s, cal_s, cut, firm)[period]["firms"]
        r = w.iloc[0].to_dict() if not w.empty else None
    if r is None or not (np.isfinite(r["pass_rate"]) and np.isfinite(r["payout_rate"])):
        return {"p_bust": float("nan"), "first_payout_days": float("nan"), "funded_month12": float("nan")}
    return bootstrap(r, START_CASH)


def plan_runs(sel: list[dict]) -> list[dict]:
    """The runs the selection asks for, without repeats: every selected configuration at its B4 size on its own
    preset, and for every stream and policy with a selected configuration on any preset, whole micros on TopstepX
    (clarification 5: the frozen preset's soft daily limit is not usable below the sealed sizing)."""
    plan, seen = [], set()
    for r in (x for x in sel if x["runs"]):
        for firm, sizing, size in ((r["firm"], "fractional", r["size"]), (TOPSTEPX, "whole micros", 1.0)):
            key = (r["stream"], firm, r["policy"], sizing, size if sizing == "fractional" else None)
            if key not in seen:
                seen.add(key)
                plan.append({"stream": r["stream"], "firm": firm, "policy": r["policy"], "sizing": sizing, "size": size})
    return plan


def qualifies(x: dict) -> bool:
    """The registered reading rule, on one development run."""
    return bool(x.get("paths") and x["p_ruin"] <= 0.10 and x["cash_p50"] > START_CASH and x["cash_p25"] >= 1000.0)


def verdict(ok: dict) -> str:
    """The amended reading for one stream and policy, from {(cap, call-up): qualifies} on development whole micros:
    both versions must qualify at one cap."""
    if any(ok.get((cap, None), False) and ok.get((cap, CALLUP), False) for cap in CAPS):
        return "**yes**"
    if any(ok.get((cap, None), False) for cap in CAPS):
        return "no: only without the call-up (depends on the Live account)"
    return "no"


def _f(x, fmt: str) -> str:
    return "n/a" if x is None or not np.isfinite(x) else format(x, fmt)


def report(sel: list[dict], results: list[dict], notes: list[str], gate_note: str, reg_sha: str, cut: pd.Timestamp) -> str:
    s = ["# B5: the $2,000 bootstrap on replayed market paths\n", gate_note, "",
         f"Implements docs/research/preregistration_b5_bootstrap.md as registered in df2bc28, clarified in 1995b2c and 7465eed and amended in eb01d37, all before any B5 number (sha256 of the file read: {reg_sha}, the pinned value). "
         f"Development: New York days through {cut.date()}; benchmark from {(cut + pd.Timedelta(days=1)).date()}, one path over the benchmark year, reported beside and never used. "
         f"From ${START_CASH:,.0f} of cash, each path runs Topstep 50K evaluations and Express Funded accounts for {PATH_DAYS} calendar days on the stream's own trading days, every live account taking the same trades on the same day: "
         "$49 an evaluation at purchase and every 30 calendar days it stays live, $149 to activate a pass, payouts net of the split credited five trading days after they are requested, at most one purchase a day, "
         f"evaluations closed after {MAX_EVAL_DAYS} trading days; ruin is cash below $49 with nothing live and nothing pending. "
         "Gates, passed on every run: each evaluation compared (those cancelled for fees or cut off by the path's end are not) equals the frozen pass walk-forward for its start day in outcome and day, and each Express Funded account's first payout within 60 days "
         "equals the frozen payout walk-forward's (B4's walk-forward of the same policy under \"wait\") in outcome, day and amount; B4's own gate passed on every stream in the selection. "
         "Whole micros run on TopstepX only (clarification 5); a selected configuration on the frozen topstep_50k preset is shown at its B4 size for the record and decides nothing. "
         f"Every run is shown twice (amendment 10): without a call-up, and with Topstep's call-up to a Live account at the path's {CALLUP}rd payout request, where every account closes, nothing more is bought and the Live account counts for nothing (a lower bound). "
         "Not modelled: Topstep's limit of 20 account purchases a month, which binds on part of the paths at cap 5 (in the review's synthetic probe enforcing it moved P(ruin) by under a point).\n",
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
          "Cash at the end counts payouts requested and not yet credited; accounts live at the end count for nothing. Development paths cover 365 calendar days; the benchmark path's span is shown. "
          "Ruin day and first payout: trading days into the path (about 310 a year), the payout on the day it is requested. Deepest fall: how far cash went below $2,000 at its lowest (the money actually at risk). "
          "Years: the non-overlapping years of data behind the development paths (the paths overlap, so this, not the number of paths, is the sample). "
          "Frozen bootstrap: the frozen simulator from $2,000 on that period's B3 firm row at the same stream, preset and sizing, as B3 calls it (independent accounts, one payout each, no activation fee): P(bust), median days to the first payout, funded accounts at month 12.\n"]
    for c in results:
        role = " (for the record: decides nothing)" if c["firm"] != TOPSTEPX else ""
        s += [f"### {c['stream']}: {c['firm']}, {c['policy']}{role}\n",
              "| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in c["runs"]:
            o, fz = x["out"], x["frozen"]
            frozen = f"{_f(fz['p_bust'], '.0%')}, {_f(fz['first_payout_days'], '.0f')}, {_f(fz['funded_month12'], '.0f')}"
            cu = "none" if x["callup"] is None else f"at payout {x['callup']}"
            if not o.get("paths"):
                s.append(f"| {x['sizing_label']} | {x['cap']} | {cu} | {x['period']} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | {frozen} |")
                continue
            q = " / ".join(f"{o[k]:,.0f}" for k in ("cash_p10", "cash_p25", "cash_p50", "cash_p75", "cash_p90"))
            called = "n/a" if x["callup"] is None else f"{o['p_callup']:.1%} ({_f(o['callup_day_median'], '.0f')})"
            s.append(f"| {x['sizing_label']} | {x['cap']} | {cu} | {x['period']} | {o['paths']} ({o['years']:.1f}; {o['span_days']} days) | {o['p_ruin']:.1%} | {_f(o['ruin_day_median'], '.0f')} | {q} | {o['cash_mean']:,.0f} | "
                     f"{o['p_above_2000']:.1%} | {o['p_above_4000']:.1%} | {o['fall_p50']:,.0f} / {o['fall_p90']:,.0f} | {called} | {frozen} |")
        s += ["", "| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in c["runs"]:
            o = x["out"]
            if not o.get("paths"):
                continue
            cu = "none" if x["callup"] is None else f"at payout {x['callup']}"
            s.append(f"| {x['sizing_label']} | {x['cap']} | {cu} | {x['period']} | {o['eval_trades']}, {o['funded_trades']} | {o['evals_mean']:.1f} | {o['passes_mean']:.2f} | {o['lost_passes_mean']:.2f} | {o['cancelled_mean']:.2f} | "
                     f"{o['xfa_breaches_mean']:.2f} | {o['payouts_mean']:.2f} | {o['fees_mean']:,.0f} | {o['paid_mean']:,.0f} | {_f(o['first_payout_median'], '.0f')} | {o['p_no_payout']:.1%} | {o['gate_evaluations']}, {o['gate_funded']} |")
        s.append("")
    s += ["## Reading (the registered rule, as amended)\n",
          "A configuration goes on to a forward test only if, on development paths in whole micros on TopstepX, at one cap, the thresholds hold both without a call-up and with the call-up at the "
          f"{CALLUP}rd payout: P(ruin within 12 months) at most 10%, median final cash above $2,000, its 25th percentile at least $1,000. One that qualifies only without the call-up depends on the Live account's value and is not carried forward on this evidence. "
          "The benchmark path decides nothing; clean proof comes only from data after 2026-10-05.\n",
          "| stream | policy | cap 1: no call-up / call-up | cap 5: no call-up / call-up | goes on to a forward test |", "|---|---|---|---|---|"]
    for c in (x for x in results if x["firm"] == TOPSTEPX):
        dev = {(x["cap"], x["callup"]): x["out"] for x in c["runs"] if x["sizing"] == "whole micros" and x["period"] == "development"}
        if not dev:
            continue
        ok = {key: qualifies(o) for key, o in dev.items()}
        cells = [" / ".join("yes" if ok.get((cap, cu), False) else "no" for cu in CALLUPS) for cap in CAPS]
        s.append(f"| {c['stream']} | {c['policy']} | " + " | ".join(cells) + f" | {verdict(ok)} |")
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
        results = []
        for item in plan_runs(sel):
            pre, start = by_name[item["stream"]]
            pre_s, cal_s = on_span(pre, cal, start)
            key = (item["stream"], item["firm"], item["policy"])
            c = next((x for x in results if (x["stream"], x["firm"], x["policy"]) == key), None)
            if c is None:
                c = {"stream": item["stream"], "firm": item["firm"], "policy": item["policy"], "runs": []}
                results.append(c)
            label = f"{item['size']:.2f} of the budget" if item["sizing"] == "fractional" else "whole micros"
            frozen = {period: frozen_row(pre_s, cal_s, cut, item["firm"], item["sizing"], item["size"], period) for period in ("development", "benchmark")}
            for cap in CAPS:
                for callup in CALLUPS:
                    for period, part, last in (("development", cal_s[cal_s <= cut], cut), ("benchmark", cal_s[cal_s > cut], None)):
                        out = run(pre_s, part, last, item["firm"], item["policy"], item["sizing"], item["size"], cap, callup)
                        c["runs"].append({"sizing": item["sizing"], "sizing_label": label, "cap": cap, "callup": callup, "period": period, "out": out,
                                          "frozen": frozen[period]})
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
