"""Forward paper test, version 1, exactly as frozen in docs/research/forward_protocol_v1.md (commit 1a9da90,
with its clarifications before the first forward day).

S3 (the main candidate) and S4 (the challenger) are the frozen engine's rules run through research/engine.py with
fixed hooks; nothing here chooses anything. Two modes:

  baseline  once, on the sealed history only (the bar file's sha256 must be the sealed manifest's): both candidates'
            trades by period, and the checkpoint thresholds fixed from development trades (windows of consecutive
            sessions or trades, every start counted). Writes a public report with the thresholds as a JSON block, and
            the per-trade history privately.
  day       each trading day: the sealed bars plus the forward bars (prepared exactly as the sealed file, symbol equal to
            instrument_id on every bar, continuing it within 30 minutes), both candidates rerun over a tail long
            enough for every indicator. A stretch of over 30 minutes without a bar stops the run if it misses bars
            inside a 09:30-16:00 session or spans 00:00 UTC (the continuous series' roll instant), unless it runs
            from a scheduled halt (the 17:00 daily break, a 13:00 holiday halt, a 13:15 early close) to the 18:00
            reopen, or a person has recorded it as an exchange halt (--accept-gap, with a reason). A forward trading
            session (a New York date with a 09:30 bar) is scored once the file holds a bar on a later date, so its
            evening roll, if any, is visible; roll dates are excluded as in the sealed run. The scored dates and
            their trades are appended to a private state file written atomically, with a run log chained by the
            state file's sha256; a scored date that would come out differently stops the run, and so does any change
            to the code that produces the trades (this runner included) or to the configurations since the baseline
            (history is never rewritten; a change is protocol version 2). The baseline report must match the sha256
            committed in research/forward_v1_baseline.sha256. The public status gives counts, hashes, dates and the
            checkpoint results when reached; a private status adds the values, the forward record and a paper
            Topstep 50K account from $2,000, one at a time, whole micros, both payout policies (research/b5_paths
            mechanics; bookkeeping, not a test).

usage:
  python research/forward.py baseline --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/forward_v1_baseline.md --private-out research/private/forward_v1_baseline_trades.csv
  python research/forward.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --baseline research/forward_v1_baseline.md \\
      --state research/private/forward_v1_state.json --out research/forward_v1_status.md \\
      --private-out research/private/forward_v1_status_private.md
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import io
import json
import os
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from research.b5_paths import day_arrays, phase_days, phase_streams, simulate  # noqa: E402
from research.bracket_replay import SLIPPAGE  # noqa: E402
from research.candidates import MICRO_COMMISSION_RT, MNQ_POINT_VALUE, mean_se  # noqa: E402
from research.engine import ResearchConfig, generate_trades  # noqa: E402

PROTOCOL_SHA256 = "4b41f1bc82499f39f224a4bd342271c61f29eeb4ebfac83b16065c778852e0de"  # docs/research/forward_protocol_v1.md with its clarifications before the first forward day
BASELINE_PIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward_v1_baseline.sha256")  # the baseline report's sha256, committed
# after the baseline run (a file, so that this runner, whose own hash the baseline records, never changes); until then the day mode refuses
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
MAX_GAP = pd.Timedelta(minutes=30)  # longer without a bar is a gap
REOPEN_GRACE_MIN = 5  # the 18:00 ET Globex reopen: the first bar within this many minutes of it
HALT_GRACE = pd.Timedelta(minutes=10)  # a scheduled halt: the last bar within this long before it
SCHEDULED_HALTS = {"daily break": (17, 0), "holiday halt": (13, 0), "early close": (13, 15)}  # ET; the only session ends in the sealed bars
# 2023-10 to 2026-10 besides the daily break (12:59 and 13:14 ET last bars)
# The CME equity-index holiday schedule, benchmark and forward years (the benchmark's from the sealed bars; the forward year's from the
# exchange's rules as understood here). A holiday halt or early close is exempt only on its listed date, and a halt that runs past a
# weekday only when that weekday is a listed full closure. A date missing from these lists stops the run (fail safe: a person records
# it with --accept-gap); extending them past CALENDAR_END is protocol version 2.
HOLIDAY_HALTS = {"2025-11-27", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
                 "2026-11-26", "2027-01-18", "2027-02-15", "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06"}  # 13:00 ET halt
EARLY_CLOSES = {"2025-11-28", "2025-12-24", "2026-11-27", "2026-12-24"}  # 13:15 ET close
FULL_CLOSURES = {"2025-12-25", "2026-01-01", "2026-04-03", "2026-12-25", "2027-01-01", "2027-03-26"}
CALENDAR_END = pd.Timestamp("2027-10-05")
TRADE_MODULES = ("research.forward", "research.engine", "research.anatomy", "research.bracket_replay", "research.candidates", "fpt.strategy",
                 "fpt.fair_value", "fpt.indicators", "fpt.structure", "fpt.risk", "fpt.data", "fpt.evaluate")  # frozen from the baseline: a change stops the test
LEDGER_KEY = ["candidate", "date", "signal_time", "entry_time", "setup", "grade", "direction", "entry", "stop", "target", "exit_time", "exit", "exit_reason",
              "ambiguous_bar", "r"]


def _span(t: pd.Timedelta) -> str:
    m = int(t.total_seconds() // 60)
    return f"{m // 60} hours" if m % 60 == 0 and m >= 120 else f"{m} minutes"


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


def rth_sessions(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Trading sessions: New York dates with a 09:30 bar (Sunday evenings and closed holidays are not sessions)."""
    ny = index.tz_convert(NY)
    opening = (ny.hour == 9) & (ny.minute == 30)
    return pd.DatetimeIndex(sorted(set(ny[opening].normalize().tz_localize(None))))


def _halt(a: pd.Timestamp, b: pd.Timestamp) -> str | None:
    """The scheduled halt a gap from bar a to bar b runs from, if any: a is within HALT_GRACE before the halt (a
    holiday halt or early close only on its listed date), b is the 18:00 reopen, and every weekday the gap covers
    after a's date is a listed full closure."""
    if not (b.hour == 18 and b.minute <= REOPEN_GRACE_MIN):
        return None
    covered = pd.date_range(a.normalize() + pd.Timedelta(days=1), b.normalize(), freq="D")
    if any(d.weekday() < 5 and d.strftime("%Y-%m-%d") not in FULL_CLOSURES for d in covered):
        return None
    day = a.strftime("%Y-%m-%d")
    listed = {"daily break": True, "holiday halt": day in HOLIDAY_HALTS, "early close": day in EARLY_CLOSES}
    for name, (h, m) in SCHEDULED_HALTS.items():
        at = a.normalize() + pd.Timedelta(hours=h, minutes=m)
        if at - HALT_GRACE <= a < at and listed[name]:
            return name
    return None


def classify_gaps(index: pd.DatetimeIndex) -> dict:
    """Every stretch of more than MAX_GAP without a bar, between consecutive bars a and b (bars missing over
    [a + 1 min, b)), by kind:
      halts      a scheduled halt: a is within HALT_GRACE before the 17:00 daily break, a listed 13:00 holiday halt or
                 a listed 13:15 early close, b is the 18:00 reopen, and any weekday in between is a listed closure;
      session    anything else missing bars inside a weekday's 09:30-16:00 session: missing data, stops the run;
      roll       anything else spanning 00:00 UTC, the instant the continuous series rolls: the roll date would be
                 misplaced, stops the run;
      overnight  the rest: can be genuine (a bar exists only when a trade did), reported.
    Each as (a, b) strings, halts with their kind."""
    out = {"halts": [], "session": [], "roll": [], "overnight": []}
    ny = index.tz_convert(NY)
    if len(ny) < 2:
        return out
    long = np.asarray((ny[1:] - ny[:-1]) - pd.Timedelta(minutes=1) > MAX_GAP)
    for a, b in zip(ny[:-1][long], ny[1:][long]):
        halt = _halt(a, b)
        if halt:
            out["halts"].append((str(a), str(b), halt))
            continue
        first = a + pd.Timedelta(minutes=1)
        days = pd.date_range(first.normalize(), b.normalize(), freq="D")
        opens = [d + pd.Timedelta(hours=9, minutes=30) for d in days if d.weekday() < 5]
        if any(first < o + pd.Timedelta(hours=6, minutes=30) and b > o for o in opens):
            out["session"].append((str(a), str(b)))
        elif first.tz_convert("UTC").normalize() != b.tz_convert("UTC").normalize():
            out["roll"].append((str(a), str(b)))
        else:
            out["overnight"].append((str(a), str(b)))
    return out


def code_hashes() -> dict:
    """The sha256 of each module that produces the trades, as imported (not as found on some other path)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = {}
    for m in TRADE_MODULES:
        f = os.path.abspath(importlib.import_module(m).__file__)
        out[os.path.relpath(f, root)] = sha256(f)
    return out


def candidate_configs() -> dict:
    return {name: asdict(cfg) for name, cfg in CANDIDATES.items()}


def tail_start(first_unseen: pd.Timestamp) -> pd.Timestamp:
    """Where the day mode's rerun starts: TAIL_SESSIONS calendar days before the first unseen day, at New York midnight."""
    return (first_unseen - pd.Timedelta(days=TAIL_SESSIONS)).tz_localize(NY)


def baseline(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's (sha256 differs from the manifest)")
    if sha256(a.protocol) != PROTOCOL_SHA256:
        raise SystemExit("refusing: the protocol file is not the frozen one")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    rolls = roll_days(bars)
    recorded = man["data"].get("roll_dates_excluded")
    if recorded is not None:
        recorded = ast.literal_eval(recorded) if isinstance(recorded, str) else recorded
        if sorted(str(d) for d in rolls) != sorted(str(d) for d in recorded):
            raise SystemExit("refusing: the roll dates differ from the manifest's")
    trades = candidate_trades(bars, rolls)
    excl = {pd.Timestamp(d) for d in rolls}
    sessions = pd.DatetimeIndex([d for d in rth_sessions(bars.index) if d not in excl])
    dev_sessions = sessions[sessions <= DEV_END]
    thr = {name: thresholds(t[t["date"] <= DEV_END], dev_sessions) for name, t in trades.items()}
    tail_ok = tail_check(bars, rolls, trades)
    bench = bars.index[bars.index >= (DEV_END + pd.Timedelta(days=1)).tz_localize(NY)]
    g = classify_gaps(bench)
    code = code_hashes()
    early = sorted({(x[0][:10], x[0][11:16], x[2]) for x in g["halts"] if x[2] != "daily break"})
    s = ["# Forward paper test v1: the baseline\n",
         f"Sealed bars (sha256 {man['data']['sha256']}, the manifest's), {len(rolls)} roll dates excluded (the manifest's). Protocol: docs/research/forward_protocol_v1.md (sha256 {PROTOCOL_SHA256}). "
         f"Both candidates rerun through research/engine.py exactly as frozen; development through {DEV_END.date()}, benchmark to {(FIRST_UNSEEN - pd.Timedelta(days=1)).date()}. "
         "A session is a trading day: a New York date with a 09:30 bar. R is per contract (one_contract); whole micros at a full stop-out within $1,000 (evaluation) and $500 (funded) beside it. "
         f"Tail check: rerunning from {TAIL_SESSIONS} calendar days before the day after the sealed bars, as the day mode does, reproduces the full run's "
         f"trades after the first {TAIL_WARMUP} days of that tail for both candidates ({tail_ok} trades compared). "
         "The code that produces the trades, this runner included, is frozen from here (its sha256 and both configurations are in the JSON block below).\n",
         f"The day mode's gap rule applied to the benchmark year's bars: {len(g['halts'])} scheduled halts, of which {len(early)} early ends "
         + (f"({', '.join(f'{d} {t} {k}' for d, t, k in early)})" if early else "") + f"; {len(g['session'])} gaps inside a 09:30-16:00 session and "
         f"{len(g['roll'])} across 00:00 UTC (each would stop a daily run)"
         + (f": {'; '.join(f'{x} to {y}' for x, y in (g['session'] + g['roll'])[:10])}" if g["session"] or g["roll"] else "")
         + f"; {len(g['overnight'])} overnight (reported only).\n",
         "| candidate | period | trades | sessions | trades per session | R per trade (se, by day) | target | stop | flat 16:00 | long | micros: evaluation / funded |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, t in trades.items():
        s += period_rows(name, t, sessions)
    s += ["", "## Checkpoint thresholds, from development trades (fixed before any forward day is scored)\n",
          "S3's 20- and 30-setup checks decide; S4's are computed at S4's own 20th and 30th setups and reported beside.\n",
          "```json", json.dumps({"thresholds": thr, "code": code, "candidates": candidate_configs()}, indent=1, sort_keys=True), "```", ""]
    text = "\n".join(s)
    _write(a.out, text)
    if a.private_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.private_out)), exist_ok=True)
        pd.concat(trades.values(), ignore_index=True).to_csv(a.private_out, index=False)
    print(text)
    return 0


def tail_check(bars: pd.DataFrame, rolls, full: dict) -> int:
    """The day mode reruns only a tail of the history, from tail_start(the first unseen day). On the sealed bars, a
    run from tail_start(the day after them) must give the full run's trades on every date after the warm-up, and
    there must be trades to compare. Refuses otherwise; returns the number of trades compared."""
    start = tail_start(bars.index.max().tz_convert(NY).normalize().tz_localize(None) + pd.Timedelta(days=1))
    tail = candidate_trades(bars[bars.index >= start], rolls)
    after = start.tz_localize(None) + pd.Timedelta(days=TAIL_WARMUP)
    n = 0
    for name in CANDIDATES:
        a = ledger_rows({name: full[name][full[name]["date"] >= after]}, sorted(full[name]["date"].unique()))
        b = ledger_rows({name: tail[name][tail[name]["date"] >= after]}, sorted(tail[name]["date"].unique()))
        if not same_rows(a, b):
            raise SystemExit(f"refusing: the tail rerun does not reproduce the full run for {name}")
        n += len(a)
    if n == 0:
        raise SystemExit("refusing: the tail check compared no trade")
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


def read_baseline(text: str) -> dict:
    return json.loads(text.split("```json", 1)[1].split("```", 1)[0])


def read_pin(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        words = fh.read().split()
    return words[0].lower() if words else None


def scorable_dates(index: pd.DatetimeIndex, start: pd.Timestamp, rolls) -> tuple[list, list]:
    """Forward sessions that can be scored (a 09:30 bar, a bar on a later New York date in the file, not a roll
    date), and the forward weekdays that are not scored with the reason."""
    ny_dates = index.tz_convert(NY).normalize().tz_localize(None)
    last = ny_dates.max()
    sessions = [d for d in rth_sessions(index) if d >= start]
    roll_set = {pd.Timestamp(d) for d in rolls}
    scored = [d for d in sessions if d < last and d not in roll_set]
    skipped = [(d, "roll date") for d in sessions if d in roll_set and d < last]
    seen = set(sessions)
    for d in pd.date_range(start, last - pd.Timedelta(days=1), freq="B"):
        if d not in seen:
            skipped.append((d, "no 09:30 bar (market closed or data missing)"))
    return scored, sorted(skipped)


def ledger_rows(trades: dict, dates: list) -> pd.DataFrame:
    keep = set(dates)
    rows = [t[t["date"].isin(keep)] for t in trades.values()]
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if out.empty:
        return pd.DataFrame(columns=LEDGER_KEY + ["micros_eval", "micros_funded"])
    out = out.assign(signal_time=out["signal_time"].astype(str), entry_time=out["entry_time"].astype(str), exit_time=out["exit_time"].astype(str),
                     date=out["date"].dt.strftime("%Y-%m-%d"), direction=out["direction"].astype(str), ambiguous_bar=out["ambiguous_bar"].astype(bool))
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
    old = old.astype({c: str for c in ("date", "signal_time", "entry_time", "exit_time", "direction", "candidate", "setup", "grade", "exit_reason")})
    new = new.astype({"grade": str})
    before = old.sort_values(order, kind="stable").reset_index(drop=True)
    again = new[new["date"].isin(recorded)].sort_values(order, kind="stable").reset_index(drop=True)
    if not set(before["date"]) <= recorded or not same_rows(before[LEDGER_KEY], again[LEDGER_KEY]):
        raise ValueError("a recorded forward trade would change: history is never rewritten (record a new protocol version instead)")
    added = new[~new["date"].isin(recorded)]
    merged = pd.concat([before, added], ignore_index=True).sort_values(order, kind="stable").reset_index(drop=True)
    return merged, sorted(recorded | today)


def _fmt_check(v: float, lo: float, hi: float, pct: bool) -> tuple[str, bool]:
    shown = f"{v:.0%}" if pct else f"{v:.0f}"
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return shown + " (no threshold)", False
    return shown, not lo <= v <= hi


def checkpoint_flags(led: pd.DataFrame, thr: dict, dates: list) -> list[tuple[str, str]]:
    """The protocol's checkpoints that have been reached: the first 10 forward sessions, and the first 20 and 30
    setups of each candidate (S3 decides; S4 is reported beside at its own 20th and 30th setups). Each as a public
    line (which checks were flagged) and a private line (with the values)."""
    out = []
    first = [d.strftime("%Y-%m-%d") for d in sorted(dates)[:SESSION_WINDOW]]
    for name in CANDIDATES:
        t = led[led["candidate"] == name].sort_values("entry_time", kind="stable")
        th = thr[name]
        if len(dates) >= SESSION_WINDOW:
            w = t[t["date"].isin(first)]
            shown, flag = _fmt_check(len(w), th["count_p01"], th["count_p99"], False)
            parts, flags = [f"count {shown}"], (["count"] if flag else [])
            if len(w):
                reason = w["exit_reason"].astype(str)
                vals = {"target": (reason == "target").mean(), "stop": (reason == "stop").mean(), "flat": (reason == "flat").mean(),
                        "long": w["direction"].astype(str).str.lower().isin(["long", "1"]).mean()}
                for k, v in vals.items():
                    shown, flag = _fmt_check(v, th[f"{k}_share_p01"], th[f"{k}_share_p99"], True)
                    parts.append(f"{k} {shown}")
                    flags += [k] if flag else []
            else:
                parts.append("no trade, so the shares are not evaluated")
            verdict = (f"**FLAG: outside the development 1st-99th percentile for {', '.join(flags)}**" if flags
                       else "within the development 1st-99th percentiles")
            head = f"{name}, first {SESSION_WINDOW} sessions"
            out.append((f"{head}: {verdict}" + ("" if len(w) else " (no trade, so the shares are not evaluated)"), f"{head}: {', '.join(parts)}: {verdict}"))
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
            head = f"{name} ({'decides' if name == 'S3' else 'beside'}), its first {n} setups"
            verdict = f"**FLAG: {'; '.join(flags)}**" if flags else "no flag"
            out.append((f"{head}: {verdict}",
                        f"{head}: mean R {b.mean():+.3f} (2.5th pct {th[f'mean_r_{n}_p025']:+.3f}), drawdown {_max_drawdown(b):.2f} R "
                        f"(99th pct {th[f'drawdown_{n}_p99']:.2f}), targets {(rr == 'target').mean():.0%} (1st pct {th[f'target_share_{n}_p01']:.0%}): {verdict}"))
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


def _write(path: str, text: str) -> None:
    """Write a file atomically: a temporary file in the same folder, then a rename."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-")
    with os.fdopen(fd, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def check_forward_file(data: bytes) -> None:
    """The raw forward file, before loading (the loader silently sorts and keeps the last duplicate): ts_event
    strictly increasing, and a symbol on every bar equal to its instrument_id (the preparation symbol :=
    instrument_id, without which rolls cannot be seen)."""
    raw = pd.read_csv(io.BytesIO(data), usecols=lambda c: c.strip().lower() in ("ts_event", "symbol", "instrument_id"), dtype=str)
    cols = {c.strip().lower(): c for c in raw.columns}
    if "ts_event" not in cols:
        raise SystemExit("refusing: the forward file has no ts_event column")
    if "symbol" not in cols or "instrument_id" not in cols:
        raise SystemExit("refusing: the forward file needs symbol and instrument_id columns")
    sym, iid = raw[cols["symbol"]].fillna("").str.strip(), raw[cols["instrument_id"]].fillna("").str.strip()
    if (sym == "").any() or not sym.equals(iid):
        raise SystemExit("refusing: the forward file needs a symbol on every bar equal to its instrument_id (prepare it as the sealed file)")
    ts = pd.to_datetime(raw[cols["ts_event"]], utc=True)
    if not ts.is_monotonic_increasing or ts.duplicated().any():
        raise SystemExit("refusing: the forward bars repeat or are out of order")


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    if sha256(a.protocol) != PROTOCOL_SHA256:
        raise SystemExit("refusing: the protocol file is not the frozen one")
    pin = read_pin(BASELINE_PIN)
    with open(a.baseline) as fh:
        base_text = fh.read()
    if pin is None or hashlib.sha256(base_text.encode()).hexdigest() != pin:
        raise SystemExit(f"refusing: the baseline report is not the pinned one ({BASELINE_PIN}; run the baseline and commit its sha256 there first)")
    base = read_baseline(base_text)
    code = code_hashes()
    if base["code"] != code or base["candidates"] != json.loads(json.dumps(candidate_configs())):
        changed = sorted(k for k in set(code) | set(base["code"]) if base["code"].get(k) != code.get(k))
        raise SystemExit(f"refusing: the code or configurations that produce the trades changed since the baseline ({', '.join(changed) or 'configurations'}): "
                         "that is protocol version 2")
    prev = None
    if os.path.exists(a.state):
        with open(a.state, "rb") as fh:
            raw_state = fh.read()
        prev = hashlib.sha256(raw_state).hexdigest()
        state = json.loads(raw_state)
    else:
        state = {"protocol": PROTOCOL_SHA256, "baseline": pin, "code": code, "dates": [], "trades": [], "runs": [], "accepted_gaps": []}
    if state["protocol"] != PROTOCOL_SHA256 or state["baseline"] != pin or state["code"] != code:
        raise SystemExit("refusing: the state file belongs to another protocol, baseline or code")
    with open(a.forward_csv, "rb") as fh:
        data = fh.read()
    fwd_sha = hashlib.sha256(data).hexdigest()
    check_forward_file(data)
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    fwd = load_minute_bars(io.BytesIO(data), source_tz=a.source_tz)
    if fwd.index.min() <= sealed.index.max():
        raise SystemExit("refusing: the forward bars must start after the sealed bars")
    if fwd.index.max().tz_convert(NY).tz_localize(None) > CALENDAR_END + pd.Timedelta(days=1):
        raise SystemExit(f"refusing: the holiday calendar ends {CALENDAR_END.date()}; extending it is protocol version 2")
    if fwd.index.min() - sealed.index.max() - pd.Timedelta(minutes=1) > MAX_GAP:
        raise SystemExit(f"refusing: the forward bars must continue the sealed ones (last sealed bar {sealed.index.max()}, first forward bar {fwd.index.min()})")
    gaps = classify_gaps(sealed.index[-1:].append(fwd.index))
    accepted = {(g["from"], g["to"]) for g in state["accepted_gaps"]}
    blocking = [(x, y, kind) for kind in ("session", "roll") for x, y in gaps[kind]]
    for when in a.accept_gap or []:
        hit = [g for g in blocking if g[0][:16] == when[:16]]
        if not hit or not a.accept_reason:
            raise SystemExit(f"refusing: --accept-gap {when} needs --accept-reason and must name the first bar time of a gap that stops this run")
        if (hit[0][0], hit[0][1]) not in accepted:
            state["accepted_gaps"].append({"from": hit[0][0], "to": hit[0][1], "kind": hit[0][2], "reason": a.accept_reason,
                                           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            accepted.add((hit[0][0], hit[0][1]))
    open_ = [g for g in blocking if (g[0], g[1]) not in accepted]
    if open_:
        x, y, kind = open_[0]
        what = "inside a 09:30-16:00 session" if kind == "session" else "across 00:00 UTC, where the continuous series rolls"
        raise SystemExit(f"refusing: no bar for more than {_span(MAX_GAP)} {what}, from {x} to {y} ({len(open_)} such gaps). If the exchange itself halted "
                         f"(not missing data), rerun with --accept-gap '{x[:16]}' --accept-reason '<what happened, with a source>'; it is recorded")
    bars = pd.concat([sealed[sealed.index >= tail_start(FIRST_UNSEEN)], fwd[sealed.columns.intersection(fwd.columns)]])
    rolls = roll_days(pd.concat([sealed.iloc[-1:], fwd]))
    dates, skipped = scorable_dates(fwd.index, FIRST_UNSEEN, rolls)
    try:
        trades = candidate_trades(bars, rolls)
        new = ledger_rows(trades, dates)
        old = pd.DataFrame(state["trades"]) if state["trades"] else None
        led, scored = merge_ledger(old, state["dates"], new, dates)
    except ValueError as e:
        raise SystemExit(f"refusing: {e}")
    added = sorted(set(scored) - set(state["dates"]))
    since = pd.Timestamp(state["runs"][-1]["last_bar"]) if state["runs"] else None
    state["dates"], state["trades"] = scored, json.loads(led.to_json(orient="records"))
    state["runs"].append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "forward_sha256": fwd_sha, "forward_rows": int(len(fwd)),
                          "last_bar": str(fwd.index.max()), "dates_added": added, "skipped": [[d.strftime("%Y-%m-%d"), why] for d, why in skipped],
                          "new_overnight_gaps": [g for g in gaps["overnight"] if since is None or pd.Timestamp(g[0]) >= since],
                          "new_halts": [g for g in gaps["halts"] if since is None or pd.Timestamp(g[0]) >= since], "previous_state_sha256": prev})
    body = json.dumps(state, sort_keys=True, indent=1)
    _write(a.state, body)
    state_sha = hashlib.sha256(body.encode()).hexdigest()
    thr = base["thresholds"]
    early = [(x, k) for x, _, k in gaps["halts"] if k != "daily break" and x[:10] >= FIRST_UNSEEN.strftime("%Y-%m-%d")]
    flags = checkpoint_flags(led, thr, [pd.Timestamp(d) for d in scored])
    pub = ["# Forward paper test v1: status\n",
           f"Run {len(state['runs'])} at {state['runs'][-1]['at']}. Protocol sha256 {PROTOCOL_SHA256}; baseline sha256 {pin}; forward bars sha256 {fwd_sha}; "
           f"state sha256 {state_sha} (its run log chains each run to the previous state). Sessions scored: {len(scored)}"
           + (f", {scored[0]} to {scored[-1]}" if scored else "") + f"; added in this run: {', '.join(added) or 'none'}.",
           "Unscored forward weekdays: " + ("; ".join(f"{d.date()} ({why})" for d, why in skipped) or "none") + ". "
           "Scheduled early ends: " + ("; ".join(f"{x[:16]} ({k})" for x, k in early) or "none") + ". "
           f"Overnight stretches of over {_span(MAX_GAP)} without a bar: {len(gaps['overnight'])}"
           + (f" (the last: {gaps['overnight'][-1][0]} to {gaps['overnight'][-1][1]})" if gaps["overnight"] else "") + ". "
           "Gaps accepted as exchange halts: " + ("; ".join(f"{g['from'][:16]} to {g['to'][:16]} ({g['reason']})" for g in state["accepted_gaps"]) or "none")
           + ".\n",
           "| candidate | trades so far |", "|---|---|"]
    pub += [f"| {name} | {int((led['candidate'] == name).sum())} |" for name in CANDIDATES]
    pub += ["", "## Checkpoints (protocol v1)\n"] + ([f"- {x}" for x, _ in flags] or ["- none reached yet"])
    _write(a.out, "\n".join(pub) + "\n")
    if a.private_out:
        prv = pub[:pub.index("## Checkpoints (protocol v1)\n")] + ["## Checkpoints (protocol v1)\n"] + ([f"- {x}" for _, x in flags] or ["- none reached yet"])
        prv += ["", "## Forward record (private)\n", "| candidate | trades | R per trade | cumulative R | target | stop | flat 16:00 | long |", "|---|---|---|---|---|---|---|---|"]
        for name in CANDIDATES:
            t = led[led["candidate"] == name]
            r, reason = t["r"].astype(float), t["exit_reason"].astype(str)
            n = len(t)
            prv.append(f"| {name} | {n} | {r.mean() if n else float('nan'):+.3f} | {r.sum():+.2f} | {(reason == 'target').mean() if n else 0:.0%} | "
                       f"{(reason == 'stop').mean() if n else 0:.0%} | {(reason == 'flat').mean() if n else 0:.0%} | "
                       f"{t['direction'].astype(str).str.lower().isin(['long', '1']).mean() if n else 0:.0%} |")
        prv += ["", "## Paper Topstep 50K account, one at a time, whole micros, from $2,000 (bookkeeping; cash includes payouts not yet credited)\n",
                "| candidate | policy | cash | evaluations | passes | payouts | paid | fees | ruined |", "|---|---|---|---|---|---|---|---|---|"]
        for name in CANDIDATES:
            for policy in ("ask", "wait"):
                p = paper_account(led, [pd.Timestamp(d) for d in scored], name, policy)
                if p:
                    prv.append(f"| {name} | {policy} | {p['final_cash']:,.0f} | {p['evals']:.0f} | {p['passes']:.0f} | {p['payouts']:.0f} | {p['paid']:,.0f} | {p['fees']:,.0f} | {p['ruined']} |")
        _write(a.private_out, "\n".join(prv) + "\n")
    if a.ledger_csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.ledger_csv)), exist_ok=True)
        led.to_csv(a.ledger_csv, index=False)
    print("\n".join(pub))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("baseline")
    d = sub.add_parser("day")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in (b, d):
        p.add_argument("--csv", required=True)
        p.add_argument("--source-tz", default="UTC")
        p.add_argument("--manifest", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--protocol", default=os.path.join(root, "docs", "research", "forward_protocol_v1.md"))
        p.add_argument("--private-out")
    d.add_argument("--forward-csv", required=True)
    d.add_argument("--baseline", required=True)
    d.add_argument("--state", required=True)
    d.add_argument("--ledger-csv", help="optional: also write the ledger as CSV (private)")
    d.add_argument("--accept-gap", action="append", help="the first bar time (New York, 'YYYY-MM-DD HH:MM') of a gap checked to be an exchange halt")
    d.add_argument("--accept-reason", help="what happened, with a source; recorded with the gap")
    a = ap.parse_args()
    return baseline(a) if a.mode == "baseline" else day(a)


if __name__ == "__main__":
    raise SystemExit(main())
