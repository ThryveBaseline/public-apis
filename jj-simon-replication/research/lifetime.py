"""B4: what a funded account is worth over its life, and the EV per evaluation with every payout and every fee.

B3 scored each candidate stream with JJ's calculator, which counts one payout per funded account (the first) and
retires it. Here a funded account is started on every trading day, as in the frozen payout walk-forward, and kept
trading for up to H walk-forward days (60, 120 and 250, recorded in one pass), asking for a payout every day as the
frozen walk-forward does, until it breaches. Topstep's Express Funded rule is applied to the Topstep presets: with a
payout the maximum loss limit moves to the starting balance (Topstep help centre, read through a search engine;
the frozen account leaves it trailing), so after a payout what is left is the whole cushion.

Nothing before the first payout changes, so each start's first-payout outcome within 60 days must equal the frozen
walk-forward's (fpt.evaluate.walk_forward_payout_probability) exactly: that is the gate, checked on every stream,
preset, size and period before anything is reported.

EV per evaluation over H = P(pass) x the mean lifetime payout per funded account (net of the split, over the starts
with H days of data or a breach within them) - the fees per evaluation (monthly billing and the activation fee, as
research/candidates.fees_per_eval). Fixed before any number was computed: B3's streams S0r and S1-S4; the presets
and sizes topstep_50k_x (TopstepX, no daily loss limit) at 1.00 and 0.95 of the budget and the frozen topstep_50k at
1.00 (its daily limit is not usable below 1.00); horizons 60, 120 and 250 walk-forward days (New York dates with
bars, about six a week on Globex data). Fractional sizing; the risk per trade stays at the budget after a payout.

usage: python research/lifetime.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv --source-tz UTC \
           --oos-start 2025-10-06 --manifest sealed/run1/manifest.json --report sealed/run1/report.md \
           --replay-csv research/private/run1_bracket_replay_b2.csv --out research/staging/run1_b4_lifetime.md
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.evaluate import _daily_r, _matrix, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import FAILED, FUNDED, PropAccount  # noqa: E402
from research.candidates import (FUNDED_RISK, MAX_FUNDED_DAYS, PRESETS, add_gate_args, build_streams, ev_net, fees_per_eval, firm_rows,  # noqa: E402
                                 gated_inputs, ny_day)

HORIZONS = (60, 120, 250)
RUNS = (("topstep_50k_x", 1.00), ("topstep_50k_x", 0.95), ("topstep_50k", 1.00))
STREAMS = ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket", "S2 continuation + A+ reversion, sealed bracket",
           "S3 continuation only, walk-forward ATR bracket", "S4 S3 + A+ reversion, sealed bracket")
TOPSTEP_XFA = {"topstep_50k", "topstep_50k_x", "topstep_100k", "topstep_150k"}  # Topstep's Express Funded payout rules apply
POLICIES = {"ask": "ask whenever eligible (the frozen walk-forward's policy; gated)",
            "wait": "wait until the loss limit has reached the starting balance (Topstep's advice)"}


class LifetimeAccount(PropAccount):
    """The frozen account with Topstep's Express Funded payout rules as an option (topstep_xfa): with a payout the
    threshold moves to the starting balance and stays there (the frozen trailing only raises it and the presets' lock
    caps it at the start), and a payout after the first needs a positive net profit since the previous one (the first
    is exempt). wait_for_lock is a payout policy: no payout until the threshold has reached the starting balance."""

    def __init__(self, *args, topstep_xfa: bool = False, wait_for_lock: bool = False, **kw):
        super().__init__(*args, **kw)
        self.topstep_xfa, self.wait_for_lock = topstep_xfa, wait_for_lock

    def payout_now(self) -> np.ndarray:
        blocked = np.zeros(self.sims, dtype=bool)
        if self.topstep_xfa:
            blocked |= (self.payout_count > 0) & (self.profit_since_reset <= 0.0)
        if self.wait_for_lock:
            blocked |= self.threshold < self.rules.account_size - 1e-9
        saved = self.days_since_payout[blocked].copy()
        self.days_since_payout[blocked] = -10 ** 9  # ineligible today; the frozen payout_now leaves ineligible sims untouched
        paid = super().payout_now()
        self.days_since_payout[blocked] = saved
        if self.topstep_xfa:
            self.threshold = np.where(paid > 0, np.maximum(self.threshold, self.rules.account_size), self.threshold)
        return paid


def walk_forward_lifetime(trades: pd.DataFrame, rules, funded_risk: float, horizons=HORIZONS, trading_days=None, topstep_xfa: bool = False,
                          wait_for_lock: bool = False) -> tuple[pd.DataFrame, dict]:
    """A funded account started on every trading day, as fpt.evaluate.walk_forward_payout_probability, but kept after
    its payouts. Returns the per-start table (cumulative paid_H and payouts_H, the first payout's day and amount, the
    breach day) and, per horizon, life-table estimates that use every start for every day it has data: the expected
    payout and number of payouts by H (each day's mean over the starts that have that day, summed), P(breach by H)
    (one minus the product of the daily breach hazards among the accounts still live), P(any payout by H) and the
    expected first payout by H (cumulative incidence, a breach before any payout competing), and the number of starts
    with H days of data."""
    dates, rs = _daily_r(trades, trading_days)
    n = len(dates)
    if n == 0:
        return pd.DataFrame(), {}
    acct = LifetimeAccount(rules, sims=n, risk_per_trade=funded_risk, start_phase=FUNDED, restart_failed=False, topstep_xfa=topstep_xfa, wait_for_lock=wait_for_lock)
    top = max(horizons)
    starts = np.arange(n)
    avail = n - starts
    paid, count = np.zeros(n), np.zeros(n, dtype=int)
    first_day, first_amount, bust_day = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    day_paid, day_count, h_breach, h_first, h_compete, first_amt = (np.full(top, np.nan) for _ in range(6))
    out = {"start": dates}
    for k in range(top):
        obs = avail >= k + 1
        if not obs.any():
            break
        r, mask = _matrix(rs, starts + k)
        live = acct.phase == FUNDED
        unpaid = np.isnan(first_day)
        acct.apply_day(r, mask)
        got = acct.payout_now()
        breached = live & (acct.phase == FAILED)
        first_now = unpaid & (got > 0)
        day_paid[k], day_count[k] = got[obs].mean(), (got[obs] > 0).mean()
        at_risk = obs & live
        h_breach[k] = breached[at_risk].mean() if at_risk.any() else 0.0
        at_risk1 = at_risk & unpaid
        if at_risk1.any():
            h_first[k], h_compete[k] = first_now[at_risk1].mean(), (breached & unpaid)[at_risk1].mean()
            first_amt[k] = np.where(first_now, got, 0.0)[at_risk1].mean()
        else:
            h_first[k] = h_compete[k] = first_amt[k] = 0.0
        paid += got
        count += (got > 0).astype(int)
        first_day[first_now], first_amount[first_now] = k + 1, got[first_now]
        bust_day[breached] = k + 1
        if k + 1 in horizons:
            out[f"paid_{k + 1}"], out[f"payouts_{k + 1}"] = paid.copy(), count.copy()
    for h in horizons:
        out.setdefault(f"paid_{h}", paid.copy())
        out.setdefault(f"payouts_{h}", count.copy())
    out["first_payout_day"], out["first_payout_amount"], out["bust_day"] = first_day, first_amount, bust_day
    s_before = np.r_[1.0, np.cumprod(1.0 - np.nan_to_num(h_first) - np.nan_to_num(h_compete))[:-1]]
    summary = {}
    for h in horizons:
        if h > n:
            summary[h] = {k: float("nan") for k in ("paid", "payouts", "p_breach", "p_any", "first_amount")} | {"n_full": 0}
            continue
        summary[h] = {"paid": float(day_paid[:h].sum()), "payouts": float(day_count[:h].sum()),
                      "p_breach": float(1.0 - np.prod(1.0 - h_breach[:h])), "p_any": float((s_before[:h] * h_first[:h]).sum()),
                      "first_amount": float((s_before[:h] * first_amt[:h]).sum()), "n_full": int((avail >= h).sum())}
    return pd.DataFrame(out), summary


def first_payout_outcomes(lt: pd.DataFrame, horizon: int = MAX_FUNDED_DAYS) -> pd.DataFrame:
    """The frozen payout walk-forward's per-start outcome table, read off a lifetime run: payout if the first payout
    came within the horizon, bust if the account breached first, open otherwise, censored if open and the data ended
    before the horizon."""
    first, bust = lt["first_payout_day"], lt["bust_day"]
    outcome = np.where(first <= horizon, "payout", np.where((bust <= horizon) & ~(first < bust), "bust", "open")).astype(object)
    days = np.where(outcome == "payout", first, np.where(outcome == "bust", bust, np.nan))
    n = len(lt)
    avail = n - np.arange(n)
    outcome[(outcome == "open") & (avail < horizon)] = "censored"
    amount = np.where(outcome == "payout", lt["first_payout_amount"], 0.0)
    return pd.DataFrame({"start": lt["start"], "outcome": outcome, "days": days, "amount": amount})


def check_first_payout(trades: pd.DataFrame, rules, funded_risk: float, cal_part, lt: pd.DataFrame) -> None:
    """The gate: the lifetime run's first-payout outcomes, days and amounts equal the frozen walk-forward's."""
    frozen = walk_forward_payout_probability(trades, rules, funded_risk, MAX_FUNDED_DAYS, trading_days=cal_part)
    mine = first_payout_outcomes(lt)
    same = (list(frozen["outcome"]) == list(mine["outcome"])
            and np.allclose(frozen["days"].to_numpy(float), mine["days"].to_numpy(float), equal_nan=True)
            and np.allclose(frozen["amount"].to_numpy(float), mine["amount"].to_numpy(float)))
    if not same:
        raise ValueError("the lifetime run's first payouts differ from the frozen payout walk-forward")


def lifetime_rows(stream: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp, firm: str, size: float, policies=("ask",)) -> list[dict]:
    """Per period, payout policy and horizon: P(pass), the fees, the funded lifetime (life-table estimates) and the EV
    per evaluation, for one stream at one preset and size; the first-payout gate checked on the gated policy."""
    rules = PRESETS[firm]
    t = stream.copy()
    t["r"] = t["r"].astype(float) * size
    day = ny_day(t)
    rows = []
    for label, m, mc in (("development", day <= cut, cal <= cut), ("benchmark", day > cut, cal > cut)):
        part, cal_part = t[m], cal[mc]
        if part.empty:
            continue
        ev_row = firm_rows(part, cal_part, firms=(firm,)).iloc[0].to_dict()
        fees = fees_per_eval(ev_row)
        for policy in policies:
            lt, summary = walk_forward_lifetime(part, rules, FUNDED_RISK, HORIZONS, cal_part, firm in TOPSTEP_XFA, wait_for_lock=(policy == "wait"))
            if policy == "ask":
                check_first_payout(part, rules, FUNDED_RISK, cal_part, lt)
            first = summary[MAX_FUNDED_DAYS]["first_amount"] if MAX_FUNDED_DAYS in summary else float("nan")
            for h in HORIZONS:
                x = summary[h]
                rows.append({"firm": firm, "size": size, "period": label, "policy": policy, "horizon": h, "pass_rate": ev_row["pass_rate"], "fees": fees,
                             "n_starts": int(len(lt)), "n_full": x["n_full"], "b3_payout_rate": ev_row["payout_rate"], "p_any": x["p_any"],
                             "payouts_mean": x["payouts"], "paid_mean": x["paid"], "p_breach": x["p_breach"], "ev": ev_row["pass_rate"] * x["paid"] - fees,
                             "ev_first_only": ev_net(ev_row), "ev_first_mean": ev_row["pass_rate"] * first - fees})
    return rows


def report(rows: list[dict], gate_note: str) -> str:
    s = ["# B4: the lifetime value of a funded account, and EV with every payout and every fee\n", gate_note, "",
         "A funded account is started on every trading day and kept for up to H walk-forward days (New York dates with bars, about six a week: 250 is about 42 weeks), until it breaches. "
         "On the Topstep presets Topstep's Express Funded payout rules apply: with a payout the maximum loss limit moves to the starting balance and stays there, and a payout after the first needs a positive net profit since the previous one. "
         "Two payout policies: " + "; ".join(f"{k}, {v}" for k, v in POLICIES.items()) + ". "
         "Gate, passed on every row of the first policy: each start's first payout within 60 days (outcome, day and amount) equals the frozen payout walk-forward's, so the first payouts are B3's; B3's P(payout) is printed beside. "
         "Lifetime figures are life-table estimates over every start, each day averaged over the starts that have that day of data, so late starts are used as far as their data goes and none is dropped for surviving (starts with H days counts the starts that have all H). "
         "EV per evaluation = P(pass) x expected lifetime payout by H (net of the split) - fees per evaluation (monthly billing and the activation fee). "
         "EV first payout only: B3's net EV (median-priced), and the same priced at the mean first payout within 60 days. "
         "Fractional sizing; the risk per trade stays at the budget after a payout. The benchmark year is reported beside and never used to choose.\n",
         "Not modelled, and worth more once later payouts count: Topstep typically moves an Express Funded trader to a live account after about 30 winning days, so the longest horizons overstate what one Express Funded account pays; "
         "after a payout under the first policy the cushion is often less than one stop-out, where an account that books realised R only (a winning trade's dip toward the limit is not modelled) is most optimistic.\n"]
    df = pd.DataFrame(rows)
    for (firm, size), g in df.groupby(["firm", "size"], sort=False):
        s.append(f"## {firm} at {size:.2f} of the budget\n")
        s.append("| stream | period | policy | H | P(pass) | fees per evaluation | starts (with H days) | B3 P(payout) | P(any payout by H) | payouts per account | expected paid per account | P(breach by H) | EV per evaluation | EV first payout only (B3, median) | EV first payout only (mean) |")
        s.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in g.iterrows():
            s.append(f"| {r['stream']} | {r['period']} | {r['policy']} | {r['horizon']} | {r['pass_rate']:.1%} | {r['fees']:,.0f} | {r['n_starts']} ({r['n_full']}) | {r['b3_payout_rate']:.1%} | {r['p_any']:.1%} | {r['payouts_mean']:.2f} | "
                     f"{r['paid_mean']:,.0f} | {r['p_breach']:.1%} | {r['ev']:+,.0f} | {r['ev_first_only']:+,.0f} | {r['ev_first_mean']:+,.0f} |")
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
        for firm, size in RUNS:
            for name in STREAMS:
                for r in lifetime_rows(streams[name], g["cal"], g["cut"], firm, size, policies=tuple(POLICIES)):
                    rows.append({"stream": name, **r})
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    text = report(rows, g["note"])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
