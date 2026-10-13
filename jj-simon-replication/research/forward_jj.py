"""The JJ system forward paper stream (docs/research/jj_system_v1.md): JJ's whole trading day, run every night on the
same finalized forward bars and data checks as the other streams, with its own state, ledger and paper account.

It reuses research/forward.py's checks unchanged: the forward file's form, its continuity with the sealed bars, the gap
rules and the holiday calendar (gaps a person accepted for the v1 test are accepted here too), and the ledger that never
rewrites a scored day. What differs is the day: the exchange's trading day, 18:00 ET the evening before to 17:00 ET,
because his evening sessions and overnight orders belong to the next morning's day.

A trading day is scored once the forward file holds a bar of a later trading day, the day has a 09:30 bar, no contract
roll falls inside it, and a calendar snapshot fetched before it began covers it (research/news_calendar.py). A day
without such a snapshot can never get one, so it is recorded as unscored, with the reason.

`init` (once, on the GB10) checks the engine on the sealed bars: a run started 30 days earlier gives the same trades
on the last days as a run with only the few days of bars the nightly run loads. It reports trade counts only, and
pins the code, the configuration and the spec. Nothing about performance is computed on history.

usage (on the GB10):
  python research/forward_jj.py init --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/jj_system_v1_init.json
  python research/forward_jj.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --init research/jj_system_v1_init.json --calendar-dir research/private/calendar \\
      --state research/private/jj_system_v1_state.json --v1-state research/private/forward_v1_state.json \\
      --summary research/private/jj_system_v1_summary.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars  # noqa: E402
from research import forward as fw  # noqa: E402
from research.b5_paths import day_arrays, eval_risk, phase_days, simulate  # noqa: E402
from research.candidates import FUNDED_RISK, MICROS_PER_MINI, whole_contracts  # noqa: E402
from research.jj_system import VERSION, JJConfig, generate_trades, trading_days  # noqa: E402
from research.news_calendar import events_for  # noqa: E402

SPEC = "docs/research/jj_system_v1.md"
SPEC_SHA256 = None  # set at the freeze: the spec's sha256
FIRST_DAY = pd.Timestamp("2026-10-15")  # the first trading day that began after this stream was frozen
CONTEXT_DAYS = 5  # calendar days of bars loaded before the first day wanted: its previous 09:30 open, the 12-hour bias, a weekend
CHECK_DAYS = 30  # the init check's earlier start
CHECK_LAST = 5  # trading days compared at the end of the sealed bars
FIRM = "topstep_50k_x"
EVAL_DAY_TARGET_R = 1.5  # "I'm just going to go for 1500": the evaluation's day stops at +$1,500, 1.5 x its $1,000 risk
TRADE_MODULES = ("research.jj_system", "research.news_calendar", "research.forward_jj", "research.forward", "fpt.data")
NAME = "JJ"
LEDGER_KEY = ["candidate", "date", "session", "signal_time", "entry_time", "setup", "grade", "direction", "entry", "stop", "target", "exit_time",
              "exit", "exit_reason", "ambiguous_bar", "r"]
NUM = ["entry", "stop", "target", "exit", "r"]


def code_hashes() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {os.path.relpath(os.path.abspath(importlib.import_module(m).__file__), root): fw.sha256(os.path.abspath(importlib.import_module(m).__file__))
            for m in TRADE_MODULES}


def config() -> dict:
    return json.loads(json.dumps(asdict(JJConfig())))


def prior_high(sealed: pd.DataFrame, start: pd.Timestamp) -> float:
    """The all-time high of the bars before `start` (the raw front-month series, as his chart shows it)."""
    before = sealed[sealed.index < start]
    return float(before["high"].max()) if len(before) else float("-inf")


def run(bars: pd.DataFrame, sealed: pd.DataFrame, days: list, events: pd.DataFrame | None) -> pd.DataFrame:
    """The engine on the given trading days, from CONTEXT_DAYS of bars before the first, with the all-time high before them."""
    if not days:
        return pd.DataFrame()
    start = (min(days) - pd.Timedelta(days=CONTEXT_DAYS)).tz_localize(NY)
    window = bars[bars.index >= start]
    hi = max(prior_high(sealed, start), float(bars[bars.index < start]["high"].max()) if (bars.index < start).any() else float("-inf"))
    return generate_trades(window, JJConfig(), events=events, days=days, prior_high=hi)


def ledger_rows(t: pd.DataFrame) -> pd.DataFrame:
    if t.empty:
        return pd.DataFrame(columns=LEDGER_KEY)
    out = t.assign(candidate=NAME, date=pd.to_datetime(t["trading_day"]).dt.strftime("%Y-%m-%d"))
    for k in ("signal_time", "entry_time", "exit_time"):
        out[k] = out[k].astype(str)
    out["ambiguous_bar"] = out["ambiguous_bar"].astype(bool)
    for k in NUM:
        out[k] = out[k].astype(float).round(6)
    keep = LEDGER_KEY + ["stop_points", "target_points", "contracts", "pnl_dollars", "attempt", "layer", "entry_kind", "anchor"]
    return out[keep].sort_values(["entry_time", "session", "attempt"], kind="stable").reset_index(drop=True)


def same(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    if len(a) != len(b):
        return False
    if not len(a):
        return True
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    txt = [k for k in LEDGER_KEY if k not in NUM]
    return a[txt].astype(str).equals(b[txt].astype(str)) and bool(np.allclose(a[NUM].astype(float), b[NUM].astype(float), atol=1e-6, rtol=0))


def merge(old: list, old_days: list, new: pd.DataFrame, days: list) -> pd.DataFrame:
    """The ledger after this run: every day already scored comes out identically (history is never rewritten)."""
    recorded = set(old_days)
    if not recorded <= set(days):
        raise ValueError(f"days already scored are missing from this run: {sorted(recorded - set(days))}")
    before = pd.DataFrame(old) if old else new.iloc[:0]
    again = new[new["date"].isin(recorded)]
    if not same(before[LEDGER_KEY] if len(before) else before, again[LEDGER_KEY] if len(again) else again):
        raise ValueError("a recorded forward trade would change: history is never rewritten (record a new version instead)")
    return pd.concat([before, new[~new["date"].isin(recorded)]], ignore_index=True).sort_values(["entry_time", "session", "attempt"], kind="stable").reset_index(drop=True)


def scorable(index: pd.DatetimeIndex, symbols: pd.Series | None, first: pd.Timestamp) -> tuple[list, list]:
    """Trading days from `first` with a 09:30 bar and a bar of a later trading day in the file, and the roll days among them."""
    td = pd.DatetimeIndex(trading_days(index))
    last = td.max()
    ny = index.tz_convert(NY)
    has930 = set(td[(ny.hour == 9) & (ny.minute == 30)])
    rolls = set()
    if symbols is not None:
        sym = symbols.astype(str).to_numpy()
        changed = np.flatnonzero(sym[1:] != sym[:-1]) + 1
        rolls = set(td[changed])
    days = sorted(d for d in has930 if first <= d < last)
    return [d for d in days if d not in rolls], [d for d in days if d in rolls]


def route(t: pd.DataFrame, funded: bool) -> pd.DataFrame:
    """The trades one account takes from the stream, one at a time, in entry order. An evaluation takes every kind of
    entry and stops for the day at +1.5 R ($1,500 on its $1,000 risk), and after a loss takes the next ("profit target
    or gone"); a funded account takes breaks of structure only, never a continuation ("continuations are only for
    evaluations") and never an overnight order ("I have an eval short at every single piece of structure")."""
    t = t.sort_values("entry_time", kind="stable")
    if funded:
        t = t[(t["grade"] == "A+") & ~t["setup"].isin(["continuation", "overnight"])]
    keep, busy_until, day_r = [], None, {}
    for i, x in t.iterrows():
        et, xt = pd.Timestamp(x["entry_time"]), pd.Timestamp(x["exit_time"])
        if busy_until is not None and et < busy_until:
            continue
        if not funded and day_r.get(x["date"], 0.0) >= EVAL_DAY_TARGET_R:
            continue
        keep.append(i)
        busy_until = xt
        day_r[x["date"]] = day_r.get(x["date"], 0.0) + float(x["r"])
    return t.loc[keep]


def paper_account(led: pd.DataFrame, days: list, policy: str = "wait") -> dict:
    """One Topstep 50K (TopstepX) path from $2,000, one account at a time, whole micro contracts within each phase's
    budget, on the trades that account takes (route); the firm rules, fees and payouts are the frozen bookkeeping's
    (research/b5_paths.simulate). Days are trading days: times move 6 hours forward so the firm's day key is the
    trading day."""
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(days)))
    if not len(cal) or led.empty:
        return {}

    def pre(t: pd.DataFrame) -> pd.DataFrame:
        if t.empty:
            return pd.DataFrame(columns=["entry_time", "exit_time", "r", "setup", "stop_points", "pnl_dollars"])
        shift = pd.Timedelta(hours=6)
        return pd.DataFrame({"entry_time": pd.to_datetime(t["entry_time"], utc=True) + shift, "exit_time": pd.to_datetime(t["exit_time"], utc=True) + shift,
                             "r": t["r"].astype(float), "setup": t["setup"], "stop_points": t["stop_points"].astype(float),
                             "pnl_dollars": t["r"].astype(float)}).reset_index(drop=True)

    cap = MICROS_PER_MINI * 5
    pe, pf = pre(route(led, False)), pre(route(led, True))
    ev = whole_contracts(pe, eval_risk(FIRM), cap) if len(pe) else pe
    fu = whole_contracts(pf, FUNDED_RISK, cap) if len(pf) else pf
    d, rs_e, rs_f = phase_days(ev, fu, cal)
    w = max([1] + [len(x) for x in rs_e + rs_f])
    res = simulate(d, day_arrays(rs_e, w), day_arrays(rs_f, w), np.array([0]), np.array([len(d)]), FIRM, policy, 1)
    return {k: float(res[k][0]) for k in ("final_cash", "evals", "passes", "activations", "xfa_breaches", "payouts", "paid", "fees")} | {"ruined": bool(res["ruined"][0])}


def summarize(led: pd.DataFrame, days: list, skipped: list) -> dict:
    r = led["r"].astype(float) if len(led) else pd.Series(dtype=float)
    out = {"version": VERSION, "first_day": str(FIRST_DAY.date()), "days": len(days), "first": days[0] if days else None, "last": days[-1] if days else None,
           "trades": int(len(led)), "total_r": float(r.sum()), "r_per_trade": float(r.mean()) if len(r) else float("nan"),
           "wins": int((r > 0).sum()), "losses": int((r <= 0).sum()), "skipped": skipped}
    if len(led):
        out["by_session"] = {k: {"trades": int(len(g)), "total_r": float(g["r"].astype(float).sum())} for k, g in led.groupby("session")}
        out["by_exit"] = {k: int(len(g)) for k, g in led.groupby("exit_reason")}
        out["account"] = paper_account(led, days)
    return out


def init(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    if SPEC_SHA256 is None or fw.sha256(SPEC) != SPEC_SHA256:
        raise SystemExit("refusing: the spec is not the frozen one")
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    idx = sealed.index
    days, _ = scorable(idx, sealed["symbol"] if "symbol" in sealed else None, pd.Timestamp("1900-01-01"))
    last = days[-CHECK_LAST:]
    short = run(sealed, sealed, last, None)
    longer_start = (min(last) - pd.Timedelta(days=CHECK_DAYS)).tz_localize(NY)
    longer = generate_trades(sealed[sealed.index >= longer_start], JJConfig(), days=last, prior_high=prior_high(sealed, longer_start))
    x, y = ledger_rows(short), ledger_rows(longer)
    if not same(x, y):
        raise SystemExit("refusing: the engine's trades depend on how much history is loaded")
    if len(x) == 0:
        raise SystemExit("refusing: the check compared no trade")
    per_day = x.groupby("date").size().to_dict()
    pinned = {"version": VERSION, "first_day": str(FIRST_DAY.date()), "spec_sha256": SPEC_SHA256, "code": code_hashes(), "config": config(),
              "check_trades": int(len(x)), "check_trades_per_day": per_day, "sealed_sha256": man["data"]["sha256"]}
    with open(a.out, "w") as fh:
        json.dump(pinned, fh, indent=1, sort_keys=True)
    print(f"check: {len(x)} trades on the sealed bars' last {len(last)} trading days compared ({per_day}); pinned {a.out}")
    return 0


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    with open(a.init) as fh:
        pinned = json.load(fh)
    code = code_hashes()
    if pinned["code"] != code or pinned["config"] != config() or pinned["spec_sha256"] != SPEC_SHA256 or fw.sha256(SPEC) != SPEC_SHA256:
        changed = sorted(k for k in set(code) | set(pinned["code"]) if pinned["code"].get(k) != code.get(k))
        raise SystemExit(f"refusing: the code, configuration or spec changed since init ({', '.join(changed) or 'configuration or spec'}): that is a new version")
    prev = None
    if os.path.exists(a.state):
        with open(a.state, "rb") as fh:
            raw = fh.read()
        prev = hashlib.sha256(raw).hexdigest()
        state = json.loads(raw)
    else:
        state = {"init": fw.sha256(a.init), "dates": [], "trades": [], "runs": [], "unscored": []}
    if state["init"] != fw.sha256(a.init):
        raise SystemExit("refusing: the state belongs to another init")
    with open(a.forward_csv, "rb") as fh:
        data = fh.read()
    fw.check_forward_file(data)
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    fwd = load_minute_bars(io.BytesIO(data), source_tz=a.source_tz)
    if fwd.index.min() <= sealed.index.max() or fwd.index.min() - sealed.index.max() - pd.Timedelta(minutes=1) > fw.MAX_GAP:
        raise SystemExit("refusing: the forward bars must continue the sealed ones")
    if fwd.index.max().tz_convert(NY).tz_localize(None) > fw.CALENDAR_END + pd.Timedelta(days=1):
        raise SystemExit(f"refusing: the holiday calendar ends {fw.CALENDAR_END.date()}; extending it is a new version")
    accepted = set()
    if a.v1_state and os.path.exists(a.v1_state):
        with open(a.v1_state) as fh:
            accepted = {(g["from"], g["to"]) for g in json.load(fh).get("accepted_gaps", [])}
    gaps = fw.classify_gaps(sealed.index[-1:].append(fwd.index))
    blocking = [(x, y) for kind in ("session", "roll") for x, y in gaps[kind] if (x, y) not in accepted]
    if blocking:
        raise SystemExit(f"refusing: a gap stops the run ({blocking[0][0]} to {blocking[0][1]}); the v1 runner's recorded acceptance applies here too")
    cols = sealed.columns.intersection(fwd.columns)
    bars = pd.concat([sealed[sealed.index >= (FIRST_DAY - pd.Timedelta(days=CONTEXT_DAYS + 1)).tz_localize(NY)][cols], fwd[cols]])
    both = pd.concat([sealed.iloc[-1:][cols], fwd[cols]])
    days, rolls = scorable(both.index, both["symbol"] if "symbol" in both else None, FIRST_DAY)
    cal, missing = events_for(days, a.calendar_dir)
    unscored = {d["day"]: d["why"] for d in state["unscored"]}
    for d in rolls:
        unscored.setdefault(d.strftime("%Y-%m-%d"), "a contract roll inside the day")
    for d in missing:
        unscored.setdefault(d.strftime("%Y-%m-%d"), "no calendar snapshot fetched before the day began")
    scored = [d for d in days if d.strftime("%Y-%m-%d") not in unscored]
    try:
        t = run(bars, sealed[sealed.index < bars.index.min()], scored, cal)
        new = ledger_rows(t)
        led = merge(state["trades"], state["dates"], new, [d.strftime("%Y-%m-%d") for d in scored])
    except ValueError as e:
        raise SystemExit(f"refusing: {e}")
    names = [d.strftime("%Y-%m-%d") for d in scored]
    added = sorted(set(names) - set(state["dates"]))
    state["dates"], state["trades"] = names, json.loads(led.to_json(orient="records"))
    state["unscored"] = [{"day": k, "why": v} for k, v in sorted(unscored.items())]
    state["runs"].append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "forward_sha256": hashlib.sha256(data).hexdigest(),
                          "last_bar": str(fwd.index.max()), "days_added": added, "previous_state_sha256": prev})
    fw._write(a.state, json.dumps(state, sort_keys=True, indent=1))
    summary = summarize(led, names, state["unscored"])
    fw._write(a.summary, json.dumps(summary, indent=1, sort_keys=True, default=str))
    print(f"JJ system: {len(names)} trading days, {len(led)} trades; added {', '.join(added) or 'none'}; unscored {len(state['unscored'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    i = sub.add_parser("init")
    d = sub.add_parser("day")
    for p in (i, d):
        p.add_argument("--csv", required=True)
        p.add_argument("--source-tz", default="UTC")
        p.add_argument("--manifest", required=True)
    i.add_argument("--out", required=True)
    d.add_argument("--forward-csv", required=True)
    d.add_argument("--init", required=True)
    d.add_argument("--calendar-dir", required=True)
    d.add_argument("--state", required=True)
    d.add_argument("--v1-state", help="the v1 runner's state, whose accepted gaps apply here too")
    d.add_argument("--summary", required=True)
    a = ap.parse_args()
    return init(a) if a.mode == "init" else day(a)


if __name__ == "__main__":
    raise SystemExit(main())
