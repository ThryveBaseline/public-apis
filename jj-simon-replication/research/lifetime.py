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
from fpt.evaluate import _daily_r, _matrix, _rate, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import FAILED, FUNDED, PropAccount  # noqa: E402
from research.candidates import (FUNDED_RISK, MAX_FUNDED_DAYS, PRESETS, add_gate_args, build_streams, ev_net, fees_per_eval, firm_rows,  # noqa: E402
                                 gated_inputs, ny_day)

HORIZONS = (60, 120, 250)
RUNS = (("topstep_50k_x", 1.00), ("topstep_50k_x", 0.95), ("topstep_50k", 1.00))
STREAMS = ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket", "S2 continuation + A+ reversion, sealed bracket",
           "S3 continuation only, walk-forward ATR bracket", "S4 S3 + A+ reversion, sealed bracket")
MLL_TO_START_ON_PAYOUT = {"topstep_50k", "topstep_50k_x", "topstep_100k", "topstep_150k"}  # Topstep's Express Funded rule


class LifetimeAccount(PropAccount):
    """The frozen account, with Topstep's Express Funded rule as an option: with a payout the threshold moves up to
    the starting balance. It never moves back down: the frozen trailing only raises the threshold, and the Topstep
    presets' lock caps it at the starting balance."""

    def __init__(self, *args, mll_to_start_on_payout: bool = False, **kw):
        super().__init__(*args, **kw)
        self.mll_to_start_on_payout = mll_to_start_on_payout

    def payout_now(self) -> np.ndarray:
        paid = super().payout_now()
        if self.mll_to_start_on_payout:
            self.threshold = np.where(paid > 0, np.maximum(self.threshold, self.rules.account_size), self.threshold)
        return paid


def walk_forward_lifetime(trades: pd.DataFrame, rules, funded_risk: float, horizons=HORIZONS, trading_days=None, mll_to_start_on_payout: bool = False) -> pd.DataFrame:
    """A funded account started on every trading day, as fpt.evaluate.walk_forward_payout_probability, but kept
    after its payouts. Per start and horizon H: paid_H (net of the split), payouts_H, breached_H, censored_H (the data
    ended before H days without a breach); plus the first payout's day and amount and the breach day."""
    dates, rs = _daily_r(trades, trading_days)
    n = len(dates)
    if n == 0:
        return pd.DataFrame()
    acct = LifetimeAccount(rules, sims=n, risk_per_trade=funded_risk, start_phase=FUNDED, restart_failed=False, mll_to_start_on_payout=mll_to_start_on_payout)
    paid, count = np.zeros(n), np.zeros(n, dtype=int)
    first_day, first_amount, bust_day = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    starts = np.arange(n)
    out = {"start": dates}
    for k in range(max(horizons)):
        r, mask = _matrix(rs, starts + k)
        live = acct.phase == FUNDED
        acct.apply_day(r, mask)
        got = acct.payout_now()
        paid += got
        count += (got > 0).astype(int)
        new = np.isnan(first_day) & (got > 0)
        first_day[new], first_amount[new] = k + 1, got[new]
        bust_day = np.where(live & (acct.phase == FAILED), k + 1, bust_day)
        if k + 1 in horizons:
            out[f"paid_{k + 1}"], out[f"payouts_{k + 1}"] = paid.copy(), count.copy()
        if not (acct.phase == FUNDED).any():
            for h in horizons:
                out.setdefault(f"paid_{h}", paid.copy())
                out.setdefault(f"payouts_{h}", count.copy())
            break
    avail = n - starts
    for h in horizons:
        out[f"breached_{h}"] = bust_day <= h
        out[f"censored_{h}"] = (avail < h) & ~(bust_day <= avail)
    out["first_payout_day"], out["first_payout_amount"], out["bust_day"] = first_day, first_amount, bust_day
    return pd.DataFrame(out)


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


def lifetime_rows(stream: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp, firm: str, size: float) -> list[dict]:
    """Per period and horizon: P(pass), the fees, the funded lifetime and the EV per evaluation, for one stream at one
    preset and size; the first-payout gate checked on the way."""
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
        lt = walk_forward_lifetime(part, rules, FUNDED_RISK, HORIZONS, cal_part, firm in MLL_TO_START_ON_PAYOUT)
        check_first_payout(part, rules, FUNDED_RISK, cal_part, lt)
        fees = fees_per_eval(ev_row)
        first = _rate(first_payout_outcomes(lt), "payout", "bust", horizon=MAX_FUNDED_DAYS)
        for h in HORIZONS:
            kept = lt[~lt[f"censored_{h}"]]
            mean_paid = float(kept[f"paid_{h}"].mean()) if len(kept) else float("nan")
            rows.append({"firm": firm, "size": size, "period": label, "horizon": h, "pass_rate": ev_row["pass_rate"], "fees": fees,
                         "funded_starts": int(len(kept)), "p_any": float((kept[f"payouts_{h}"] > 0).mean()) if len(kept) else float("nan"),
                         "payouts_mean": float(kept[f"payouts_{h}"].mean()) if len(kept) else float("nan"), "paid_mean": mean_paid,
                         "p_breach": float(kept[f"breached_{h}"].mean()) if len(kept) else float("nan"),
                         "ev": ev_row["pass_rate"] * mean_paid - fees, "ev_first_only": ev_net(ev_row), "first_payout_rate": first["rate"]})
    return rows


def report(rows: list[dict], gate_note: str) -> str:
    s = ["# B4: the lifetime value of a funded account, and EV with every payout and every fee\n", gate_note, "",
         "A funded account is started on every trading day and kept for up to H walk-forward days (New York dates with bars, about six a week), asking for a payout every day as the preset allows, until it breaches. "
         "On the Topstep presets the maximum loss limit moves to the starting balance with a payout (Topstep's Express Funded rule), so what is left after a payout is the whole cushion. "
         "Gate, passed on every row: each start's first payout within 60 days (outcome, day and amount) equals the frozen payout walk-forward's, so B3's payout rates are reproduced and only what comes after a first payout is new. "
         "EV per evaluation = P(pass) x mean lifetime payout per funded account (net of the split; starts with H days of data or a breach within them) - fees per evaluation (monthly billing and the activation fee). "
         "EV first payout only is B3's net EV (JJ's calculator with every fee). Fractional sizing; the risk per trade stays at the budget after a payout. The benchmark year is reported beside and never used to choose.\n"]
    df = pd.DataFrame(rows)
    for (firm, size), g in df.groupby(["firm", "size"], sort=False):
        s.append(f"## {firm} at {size:.2f} of the budget\n")
        s.append("| stream | period | H | P(pass) | fees per evaluation | funded starts | P(any payout) | payouts per account | mean paid per account | P(breach within H) | EV per evaluation | EV first payout only |")
        s.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for _, r in g.iterrows():
            s.append(f"| {r['stream']} | {r['period']} | {r['horizon']} | {r['pass_rate']:.1%} | {r['fees']:,.0f} | {r['funded_starts']} | {r['p_any']:.1%} | {r['payouts_mean']:.2f} | "
                     f"{r['paid_mean']:,.0f} | {r['p_breach']:.1%} | {r['ev']:+,.0f} | {r['ev_first_only']:+,.0f} |")
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
                for r in lifetime_rows(streams[name], g["cal"], g["cut"], firm, size):
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
