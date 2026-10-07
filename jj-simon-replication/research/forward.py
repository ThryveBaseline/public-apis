"""Forward paper test, version 1, exactly as frozen in docs/research/forward_protocol_v1.md (commit 1a9da90).

S3 (the main candidate) and S4 (the challenger) are the frozen engine's rules run through research/engine.py with
fixed hooks; nothing here chooses anything. Two modes:

  baseline  once, on the sealed history only (the bar file's sha256 must be the sealed manifest's): both candidates'
            trades by period, and the checkpoint thresholds fixed from development trades (windows of consecutive
            sessions or trades, every start counted). Writes a public report with the thresholds as a JSON block, and
            the per-trade history privately.
  day       each trading day: the sealed bars plus the forward bars (prepared exactly as the sealed file, starting
            after it), both candidates rerun over a tail long enough for every indicator; the trades of each complete
            forward date (bars through the 15:59 ET bar, not a roll date) are appended to the private ledger. A trade
            already in the ledger that would come out differently stops the run: history is never rewritten. The
            public status report gives each candidate's forward record, the checkpoint flags against the baseline
            (pinned by sha256), and a paper Topstep 50K account from $2,000, one at a time, in whole micros, both
            payout policies (research/b5_paths mechanics; bookkeeping, not a test).

usage:
  python research/forward.py baseline --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/staging/forward_v1_baseline.md --private-out research/private/forward_v1_baseline_trades.csv
  python research/forward.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --baseline research/forward_v1_baseline.md \\
      --ledger research/private/forward_v1_ledger.csv --out research/staging/forward_v1_status.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from research.b5_paths import day_arrays, phase_days, phase_streams, simulate  # noqa: E402
from research.bracket_replay import SLIPPAGE  # noqa: E402
from research.candidates import MICRO_COMMISSION_RT, MNQ_POINT_VALUE, mean_se  # noqa: E402
from research.engine import ResearchConfig, generate_trades  # noqa: E402

PROTOCOL_SHA256 = "8fb5bc3f54994390e47f68c7941f4bfa78bcf53c04b59a4d69157ea18bb5670c"  # docs/research/forward_protocol_v1.md at 1a9da90
BASELINE_SHA256 = None  # pinned in the commit after the baseline run; until then the day mode refuses
CANDIDATES = {
    "S3": ResearchConfig(reversion_end="09:30", continuation_atr_k=0.4, continuation_rr=2.0, flat_time="16:00", one_contract=True),
    "S4": ResearchConfig(allow_grade_a_reversion=False, continuation_atr_k=0.4, continuation_rr=2.0, flat_time="16:00", one_contract=True),
}
DEV_END = pd.Timestamp("2025-10-05")
FIRST_UNSEEN = pd.Timestamp("2026-10-06")
SESSION_WINDOW = 10
SETUP_CHECKS = (20, 30)
EVAL_BUDGET, FUNDED_BUDGET, MICRO_CAP = 1000.0, 500.0, 50
TAIL_SESSIONS = 120  # the day mode reruns this many calendar days before the first unseen day, plus the forward days
TAIL_WARMUP = 60  # calendar days of that tail before which indicators may still differ from the full run
LEDGER_KEY = ["candidate", "date", "entry_time", "setup", "grade", "direction", "entry", "stop", "target", "exit_time", "exit", "exit_reason", "r"]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ny_date(ts: pd.Series) -> pd.Series:
    return ts.dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)


def micros(stop_pts: np.ndarray, budget: float) -> np.ndarray:
    """Whole micro NQ within the budget at a full stop-out, strictly inside it (research/candidates.whole_contracts)."""
    per = (np.asarray(stop_pts, dtype=float) + SLIPPAGE) * MNQ_POINT_VALUE + MICRO_COMMISSION_RT
    n = np.floor(budget / per)
    return np.minimum(np.where(n * per >= budget, n - 1, n), MICRO_CAP).astype(int)


def candidate_trades(bars: pd.DataFrame, rolls) -> dict:
    """Both frozen candidates' trades, roll dates excluded, with the date and the whole-micro counts beside them."""
    excl = {pd.Timestamp(d) for d in rolls}
    out = {}
    for name, cfg in CANDIDATES.items():
        t = generate_trades(bars, cfg)
        if t.empty:
            out[name] = t.assign(candidate=name, date=pd.Series(dtype="datetime64[ns]"))
            continue
        t = t.assign(candidate=name, date=ny_date(t["entry_time"]))
        t = t[~t["date"].isin(excl)].reset_index(drop=True)
        t["micros_eval"] = micros(t["stop_points"], EVAL_BUDGET)
        t["micros_funded"] = micros(t["stop_points"], FUNDED_BUDGET)
        out[name] = t
    return out


def _quantile(x, q: float) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.quantile(x, q)) if len(x) else float("nan")


def _max_drawdown(r: np.ndarray) -> float:
    c = np.cumsum(r)
    return float(np.max(np.maximum.accumulate(np.r_[0.0, c])[1:] - c)) if len(r) else 0.0


def session_shares(t: pd.DataFrame, sessions: pd.DatetimeIndex) -> dict:
    """Per session: the trade count and the counts of targets, stops, 16:00 exits and longs."""
    reason = t["exit_reason"].astype(str)
    longs = t["direction"].astype(str).str.lower().isin(["long", "1"])
    f = pd.DataFrame({"date": t["date"], "n": 1, "target": (reason == "target").astype(int), "stop": (reason == "stop").astype(int),
                      "flat": (reason == "flat").astype(int), "long": longs.astype(int)})
    return {k: v.to_numpy() for k, v in f.groupby("date")[["n", "target", "stop", "flat", "long"]].sum().reindex(sessions, fill_value=0).items()}


def thresholds(trades: pd.DataFrame, sessions: pd.DatetimeIndex) -> dict:
    """The protocol's checkpoint thresholds from one candidate's development trades and sessions: over every window
    of 10 consecutive sessions, the trade count and the shares of targets, stops, 16:00 exits and longs (windows with
    a trade); over every block of 20 and 30 consecutive trades, the mean R, the deepest cumulative-R drawdown and the
    target share."""
    t = trades.sort_values("entry_time", kind="stable")
    per = session_shares(t, sessions)
    win = np.ones(SESSION_WINDOW, dtype=int)
    roll = {k: np.convolve(v, win, mode="valid") for k, v in per.items()}
    has = roll["n"] > 0
    out = {"sessions_window": SESSION_WINDOW, "count_p01": _quantile(roll["n"], 0.01), "count_p99": _quantile(roll["n"], 0.99)}
    for k in ("target", "stop", "flat", "long"):
        share = roll[k][has] / roll["n"][has]
        out[f"{k}_share_p01"], out[f"{k}_share_p99"] = _quantile(share, 0.01), _quantile(share, 0.99)
    r = t["r"].astype(float).to_numpy()
    reason = t["exit_reason"].astype(str).to_numpy()
    for n in SETUP_CHECKS:
        starts = range(len(r) - n + 1)
        out[f"mean_r_{n}_p025"] = _quantile([r[i:i + n].mean() for i in starts], 0.025)
        out[f"drawdown_{n}_p99"] = _quantile([_max_drawdown(r[i:i + n]) for i in starts], 0.99)
        out[f"target_share_{n}_p01"] = _quantile([(reason[i:i + n] == "target").mean() for i in starts], 0.01)
    return out


def period_rows(name: str, t: pd.DataFrame, sessions: pd.DatetimeIndex) -> list[str]:
    rows = []
    for label, lo, hi in (("development", None, DEV_END), ("benchmark", DEV_END + pd.Timedelta(days=1), FIRST_UNSEEN - pd.Timedelta(days=1))):
        m = (t["date"] <= hi) & ((t["date"] >= lo) if lo is not None else True)
        p = t[m]
        ns = int(((sessions <= hi) & ((sessions >= lo) if lo is not None else True)).sum())
        n, mu, se = mean_se(p["r"].astype(float), p["date"])
        reason = p["exit_reason"].astype(str)
        longs = p["direction"].astype(str).str.lower().isin(["long", "1"])
        rows.append(f"| {name} | {label} | {n} | {ns} | {n / ns if ns else float('nan'):.2f} | {mu:+.3f} ({se:.3f}) | {(reason == 'target').mean():.1%} | "
                    f"{(reason == 'stop').mean():.1%} | {(reason == 'flat').mean():.1%} | {longs.mean():.1%} | {p['micros_eval'].mean():.1f} / {p['micros_funded'].mean():.1f} |")
    return rows


def baseline(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's (sha256 differs from the manifest)")
    if sha256(a.protocol) != PROTOCOL_SHA256:
        raise SystemExit("refusing: the protocol file is not the frozen one")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    rolls = roll_days(bars)
    trades = candidate_trades(bars, rolls)
    excl = {pd.Timestamp(d) for d in rolls}
    sessions = pd.DatetimeIndex(sorted(set(bars.index.tz_convert(NY).normalize().tz_localize(None)) - excl))
    dev_sessions = sessions[sessions <= DEV_END]
    thr = {name: thresholds(t[t["date"] <= DEV_END], dev_sessions) for name, t in trades.items()}
    tail_ok = tail_check(bars, rolls, trades)
    s = ["# Forward paper test v1: the baseline\n",
         f"Sealed bars (sha256 {man['data']['sha256']}, the manifest's), {len(rolls)} roll dates excluded. Protocol: docs/research/forward_protocol_v1.md (sha256 {PROTOCOL_SHA256}). "
         f"Both candidates rerun through research/engine.py exactly as frozen; development through {DEV_END.date()}, benchmark to {(FIRST_UNSEEN - pd.Timedelta(days=1)).date()}. "
         "R is per contract (one_contract); whole micros at a full stop-out within $1,000 (evaluation) and $500 (funded) beside it. "
         f"Tail check: rerunning only the last {TAIL_SESSIONS} calendar days of the sealed bars, as the day mode does, reproduces the full run's trades on the last "
         f"{TAIL_SESSIONS - TAIL_WARMUP} of them for both candidates ({tail_ok} trades compared).\n",
         "| candidate | period | trades | sessions | trades per session | R per trade (se, by day) | target | stop | flat 16:00 | long | micros: evaluation / funded |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, t in trades.items():
        s += period_rows(name, t, sessions)
    s += ["", "## Checkpoint thresholds, from development trades (fixed before any forward day is scored)\n", "```json", json.dumps(thr, indent=1, sort_keys=True), "```", ""]
    text = "\n".join(s)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    if a.private_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.private_out)), exist_ok=True)
        pd.concat(trades.values(), ignore_index=True).to_csv(a.private_out, index=False)
    print(text)
    return 0


def tail_check(bars: pd.DataFrame, rolls, full: dict) -> int:
    """The day mode reruns only a tail of the history. On the sealed bars, a run from TAIL_SESSIONS calendar days
    before the end must give the full run's trades on every date after the warm-up. Refuses otherwise; returns the
    number of trades compared."""
    end = bars.index.max().tz_convert(NY).normalize().tz_localize(None)
    start = end - pd.Timedelta(days=TAIL_SESSIONS)
    tail = candidate_trades(bars[bars.index >= start.tz_localize(NY)], rolls)
    after = start + pd.Timedelta(days=TAIL_WARMUP)
    n = 0
    for name in CANDIDATES:
        a = ledger_rows({name: full[name][full[name]["date"] >= after]}, sorted(full[name]["date"].unique()))
        b = ledger_rows({name: tail[name][tail[name]["date"] >= after]}, sorted(tail[name]["date"].unique()))
        if not same_rows(a, b):
            raise SystemExit(f"refusing: the tail rerun does not reproduce the full run for {name}")
        n += len(a)
    return n


def same_rows(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    """Equal ledgers: the same rows in the same order, text fields exactly, prices and R within 1e-6."""
    if len(a) != len(b):
        return False
    if len(a) == 0:
        return True
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    num = ["entry", "stop", "target", "exit", "r"]
    txt = [c for c in LEDGER_KEY if c not in num]
    if not a[txt].astype(str).equals(b[txt].astype(str)):
        return False
    return bool(np.allclose(a[num].astype(float).to_numpy(), b[num].astype(float).to_numpy(), atol=1e-6, rtol=0))


def read_thresholds(path: str) -> dict:
    text = open(path).read()
    return json.loads(text.split("```json", 1)[1].split("```", 1)[0])


def complete_dates(bars: pd.DataFrame, start: pd.Timestamp) -> list:
    """Forward New York dates whose bars reach the 15:59 ET bar."""
    ny = bars.index.tz_convert(NY)
    f = pd.DataFrame({"date": ny.normalize().tz_localize(None), "minute": ny.hour * 60 + ny.minute})
    f = f[f["date"] >= start]
    last = f.groupby("date")["minute"].max()
    return sorted(last[last >= 15 * 60 + 59].index)


def ledger_rows(trades: dict, dates: list) -> pd.DataFrame:
    keep = set(dates)
    rows = [t[t["date"].isin(keep)] for t in trades.values()]
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if out.empty:
        return pd.DataFrame(columns=LEDGER_KEY + ["micros_eval", "micros_funded"])
    out = out.assign(entry_time=out["entry_time"].astype(str), exit_time=out["exit_time"].astype(str), date=out["date"].dt.strftime("%Y-%m-%d"),
                     direction=out["direction"].astype(str))
    for c in ("entry", "stop", "target", "exit", "r"):
        out[c] = out[c].astype(float).round(6)
    return out[LEDGER_KEY + ["micros_eval", "micros_funded"]].sort_values(["candidate", "entry_time"], kind="stable").reset_index(drop=True)


def merge_ledger(old: pd.DataFrame | None, old_dates: list, new: pd.DataFrame, dates: list) -> tuple[pd.DataFrame, list]:
    """The ledger and the scored dates after today's run. Every date already scored (with or without a trade) must
    be scored again and come out identically, since history is never rewritten; dates not yet scored are appended."""
    today = {d.strftime("%Y-%m-%d") for d in dates}
    recorded = set(old_dates)
    if not recorded <= today:
        raise ValueError(f"dates already scored are missing from this run: {sorted(recorded - today)}")
    order = ["candidate", "entry_time"]
    if old is None or old.empty:
        old = new.iloc[:0]
    old = old.astype({c: str for c in ("date", "entry_time", "exit_time", "direction", "candidate", "setup", "grade", "exit_reason")})
    new = new.astype({"grade": str})
    before = old.sort_values(order, kind="stable").reset_index(drop=True)
    again = new[new["date"].isin(recorded)].sort_values(order, kind="stable").reset_index(drop=True)
    if not set(before["date"]) <= recorded or not same_rows(before[LEDGER_KEY], again[LEDGER_KEY]):
        raise ValueError("a recorded forward trade would change: history is never rewritten (record a new protocol version instead)")
    added = new[~new["date"].isin(recorded)]
    merged = pd.concat([before, added], ignore_index=True).sort_values(order, kind="stable").reset_index(drop=True)
    return merged, sorted(recorded | today)


def checkpoint_flags(led: pd.DataFrame, thr: dict, dates: list) -> list[str]:
    """The protocol's checkpoints that have been reached: the first 10 forward sessions, and the first 20 and 30
    setups of each candidate (S3 decides; S4 beside it)."""
    out = []
    first = [d.strftime("%Y-%m-%d") for d in sorted(dates)[:SESSION_WINDOW]]
    for name in CANDIDATES:
        t = led[led["candidate"] == name].sort_values("entry_time", kind="stable")
        th = thr[name]
        if len(dates) >= SESSION_WINDOW:
            w = t[t["date"].isin(first)]
            n = len(w)
            reason = w["exit_reason"].astype(str)
            vals = {"count": n}
            if n:
                vals |= {"target": (reason == "target").mean(), "stop": (reason == "stop").mean(), "flat": (reason == "flat").mean(),
                         "long": w["direction"].astype(str).str.lower().isin(["long", "1"]).mean()}
            parts, flags = [], []
            for k, v in vals.items():
                lo, hi = (th["count_p01"], th["count_p99"]) if k == "count" else (th[f"{k}_share_p01"], th[f"{k}_share_p99"])
                parts.append(f"{k} {v:.0f}" if k == "count" else f"{k} {v:.0%}")
                if not lo <= v <= hi:
                    flags.append(f"{k} outside {lo:.2f}-{hi:.2f}")
            out.append(f"{name}, first {SESSION_WINDOW} sessions: " + ", ".join(parts) + (f" **FLAG: {'; '.join(flags)}**" if flags else ": within the development 1st-99th percentiles"))
        r = t["r"].astype(float).to_numpy()
        reason = t["exit_reason"].astype(str).to_numpy()
        for n in SETUP_CHECKS:
            if len(r) < n:
                continue
            b, rr = r[:n], reason[:n]
            flags = []
            if b.mean() < th[f"mean_r_{n}_p025"]:
                flags.append("mean R below the 2.5th percentile")
            if _max_drawdown(b) > th[f"drawdown_{n}_p99"]:
                flags.append("drawdown beyond the 99th percentile")
            if (rr == "target").mean() < th[f"target_share_{n}_p01"]:
                flags.append("target share below the 1st percentile")
            out.append(f"{name}, first {n} setups: mean R {b.mean():+.3f} (2.5th pct {th[f'mean_r_{n}_p025']:+.3f}), drawdown {_max_drawdown(b):.2f} R "
                       f"(99th pct {th[f'drawdown_{n}_p99']:.2f}), targets {(rr == 'target').mean():.0%} (1st pct {th[f'target_share_{n}_p01']:.0%})"
                       + (f" **FLAG: {'; '.join(flags)}**" if flags else ": no flag"))
    return out


def paper_account(led: pd.DataFrame, dates: list, name: str, policy: str) -> dict:
    """One Topstep 50K path from $2,000, one account at a time, whole micros, on the candidate's forward trades."""
    t = led[led["candidate"] == name]
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(dates)))
    if not len(cal):
        return {}
    pre = pd.DataFrame({"entry_time": pd.to_datetime(t["entry_time"], utc=True), "exit_time": pd.to_datetime(t["exit_time"], utc=True),
                        "r": t["r"].astype(float), "setup": t["setup"], "stop_points": (t["entry"] - t["stop"]).abs().astype(float),
                        "pnl_dollars": t["r"].astype(float)})
    ev, fu = phase_streams(pre, "topstep_50k_x", "whole micros", 1.0)
    d, rs_e, rs_f = phase_days(ev, fu, cal)
    w = max([1] + [len(x) for x in rs_e + rs_f])
    res = simulate(d, day_arrays(rs_e, w), day_arrays(rs_f, w), np.array([0]), np.array([len(d)]), "topstep_50k_x", policy, 1)
    return {k: float(res[k][0]) for k in ("final_cash", "evals", "passes", "activations", "xfa_breaches", "payouts", "paid", "fees")} | {"ruined": bool(res["ruined"][0])}


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    if BASELINE_SHA256 is None or sha256(a.baseline) != BASELINE_SHA256:
        raise SystemExit("refusing: the baseline report is not the pinned one (run the baseline and pin its sha256 first)")
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    fwd = load_minute_bars(a.forward_csv, source_tz=a.source_tz)
    if fwd.index.min() <= sealed.index.max():
        raise SystemExit("refusing: the forward bars must start after the sealed bars")
    if not fwd.index.is_unique or not fwd.index.is_monotonic_increasing:
        raise SystemExit("refusing: the forward bars repeat or are out of order")
    tail_start = (FIRST_UNSEEN - pd.Timedelta(days=TAIL_SESSIONS)).tz_localize(NY)
    bars = pd.concat([sealed[sealed.index >= tail_start], fwd[sealed.columns.intersection(fwd.columns)]])
    rolls = roll_days(pd.concat([sealed.iloc[-1:], fwd]))
    roll_set = set(rolls)
    dates = [d for d in complete_dates(bars, FIRST_UNSEEN) if d.date() not in roll_set]
    try:
        trades = candidate_trades(bars, rolls)
        new = ledger_rows(trades, dates)
        old = pd.read_csv(a.ledger) if os.path.exists(a.ledger) else None
        dates_file = a.ledger + ".dates.json"
        old_dates = json.load(open(dates_file)) if os.path.exists(dates_file) else []
        if (old is not None and len(old)) and not old_dates:
            raise ValueError("the ledger has trades but no record of its scored dates")
        led, scored = merge_ledger(old, old_dates, new, dates)
    except ValueError as e:
        raise SystemExit(f"refusing: {e}")
    thr = read_thresholds(a.baseline)
    s = ["# Forward paper test v1: status\n",
         f"Protocol sha256 {PROTOCOL_SHA256}; baseline sha256 {BASELINE_SHA256}; forward bars sha256 {sha256(a.forward_csv)}. "
         f"Complete forward sessions scored: {len(dates)} ({dates[0].date() if dates else 'none'} to {dates[-1].date() if dates else 'none'}); roll dates excluded: {[str(d) for d in rolls] or 'none'}.\n",
         "| candidate | trades | R per trade | cumulative R | target | stop | flat 16:00 | long |", "|---|---|---|---|---|---|---|---|"]
    for name in CANDIDATES:
        t = led[led["candidate"] == name]
        r = t["r"].astype(float)
        reason = t["exit_reason"].astype(str)
        s.append(f"| {name} | {len(t)} | {r.mean() if len(t) else float('nan'):+.3f} | {r.sum():+.2f} | {(reason == 'target').mean() if len(t) else 0:.0%} | "
                 f"{(reason == 'stop').mean() if len(t) else 0:.0%} | {(reason == 'flat').mean() if len(t) else 0:.0%} | "
                 f"{t['direction'].astype(str).str.lower().isin(['long', '1']).mean() if len(t) else 0:.0%} |")
    flags = checkpoint_flags(led, thr, dates)
    s += ["", "## Checkpoints (protocol v1)\n"] + ([f"- {x}" for x in flags] or ["- none reached yet"])
    s += ["", "## Paper Topstep 50K account, one at a time, whole micros, from $2,000 (bookkeeping)\n",
          "| candidate | policy | cash | evaluations | passes | payouts | paid | fees | ruined |", "|---|---|---|---|---|---|---|---|---|"]
    for name in CANDIDATES:
        for policy in ("ask", "wait"):
            p = paper_account(led, dates, name, policy)
            if p:
                s.append(f"| {name} | {policy} | {p['final_cash']:,.0f} | {p['evals']:.0f} | {p['passes']:.0f} | {p['payouts']:.0f} | {p['paid']:,.0f} | {p['fees']:,.0f} | {p['ruined']} |")
    text = "\n".join(s) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(a.ledger)), exist_ok=True)
    led.to_csv(a.ledger, index=False)
    with open(a.ledger + ".dates.json", "w") as fh:
        json.dump(scored, fh)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("baseline")
    d = sub.add_parser("day")
    for p in (b, d):
        p.add_argument("--csv", required=True)
        p.add_argument("--source-tz", default="UTC")
        p.add_argument("--manifest", required=True)
        p.add_argument("--out", required=True)
    b.add_argument("--protocol", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research", "forward_protocol_v1.md"))
    b.add_argument("--private-out")
    d.add_argument("--forward-csv", required=True)
    d.add_argument("--baseline", required=True)
    d.add_argument("--ledger", required=True)
    a = ap.parse_args()
    return baseline(a) if a.mode == "baseline" else day(a)


if __name__ == "__main__":
    raise SystemExit(main())
