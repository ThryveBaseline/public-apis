"""The JJ system's nightly learning report (docs/research/jj_lab.md): from the forward record only, what went well, what
went badly, and what the system could have done, written for the weekly review that builds the next challenger.

It reruns the JJ system's rules on every scored trading day with the learning engine (research/jj_lab_engine_b2.py),
whose defaults are the live system's rules, so that every decision is in its journal. It first checks that this rerun
gives exactly the live ledger's trades (else the report says the learning engine is out of step and stops there).
Then every signal, taken or passed, is replayed with other exits (research/jj_whatif.py), and the report gives:

  sessions   the live trades by session, setup, grade, direction, hour, bias, news day, weekday and layer
  rules      for each rule that passed on signals, what those signals would have made: a rule that kept the system out
             of losers earns its place, one that kept it out of winners costs
  exits      what the live trades would have made with each other stop and target, or held to the day's end
  excursion  how far trades went for and against them: stops first in profit, targets with more to give
  missed     sessions where price moved well away from fair value and came back without a reversion trade
  findings   the largest of these, in plain sentences, each with its number of trading days ("early" under 10)

The live system is never changed by any of this. A day's trades move together, so the sample is the number of days.

usage (on the GB10, nightly, after research/forward_jj.py day):
  python research/jj_learn.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --calendar-dir research/private/calendar --jj-state research/private/jj_system_v1_state.json \\
      --out research/private/jj_learn_report.json --md research/private/jj_learn_report.md
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars  # noqa: E402
from research import forward as fw  # noqa: E402
from research import forward_jj as fj  # noqa: E402
from research import jj_lab_engine_b2 as B  # noqa: E402
from research.jj_whatif import STOPS, TARGETS, replay_signals  # noqa: E402
from research.news_calendar import events_for  # noqa: E402

EARLY_DAYS = 10
GRID = [f"{s:g}/{t:g}" for s in STOPS for t in TARGETS]
HOLDS = [f"hold_{s:g}" for s in STOPS]


def _stats(t: pd.DataFrame, col: str = "r") -> dict:
    r = t[col].astype(float) if len(t) else pd.Series(dtype=float)
    return {"n": int(len(t)), "days": int(t["day"].nunique()) if len(t) else 0, "total_r": round(float(r.sum()), 3),
            "mean_r": round(float(r.mean()), 3) if len(r) else None, "win": round(float((r > 0).mean()), 3) if len(r) else None}


def _by(t: pd.DataFrame, key) -> dict:
    return {str(k): _stats(g) for k, g in t.groupby(key)} if len(t) else {}


def learn(bars: pd.DataFrame, days: list, events: pd.DataFrame | None, prior_high: float, live: pd.DataFrame | None) -> dict:
    """The report for these trading days. `bars` is the window the engine runs on; `live` the live ledger to check
    against (None: no check)."""
    journal: list = []
    trades = B.generate_trades(bars, B.LabConfig(), events=events, days=days, prior_high=prior_high, journal=journal)
    rep = {"days": [d.strftime("%Y-%m-%d") for d in days], "n_days": len(days), "trades": int(len(trades))}
    if live is not None:
        mine = fj.ledger_rows(trades)
        theirs = live[live["date"].isin(rep["days"])] if len(live) else live
        rep["in_step"] = bool(fj.same(mine[fj.LEDGER_KEY].reset_index(drop=True), theirs[fj.LEDGER_KEY].reset_index(drop=True))) if len(theirs) or len(mine) else True
        if not rep["in_step"]:
            rep["findings"] = ["The learning engine's trades differ from the live ledger: the report stops here until that is fixed."]
            return rep
    J = pd.DataFrame(journal)
    if trades.empty or J.empty:
        rep["findings"] = ["No trades yet."]
        return rep
    td = fj.trading_days(bars.index)
    trades = trades.assign(day=pd.to_datetime(trades["trading_day"]).dt.strftime("%Y-%m-%d"))
    sig = J[J["event"] == "signal"].copy()
    sig["day"] = pd.to_datetime(sig["day"]).dt.strftime("%Y-%m-%d")
    sig["taken"] = sig["taken"].astype(bool)
    grid = replay_signals(bars, sig, td)
    sig = sig.join(grid)
    taken = sig[sig["taken"]]
    # the live trades with their journal: the signal that made each (not the overnight orders, which have no signal)
    tr = trades.copy()
    tr["key"] = tr["session"] + "|" + tr["setup"] + "|" + tr["signal_time"].astype(str)
    taken = taken.assign(key=taken["session"] + "|" + taken["setup"] + "|" + taken["time"].astype(str))
    m = tr.merge(taken.drop(columns=["day", "session", "setup", "grade"]), on="key", how="left", suffixes=("", "_sig"))
    ny = pd.to_datetime(m["signal_time"]).dt.tz_convert(NY)
    m["hour"] = ny.dt.hour
    m["weekday"] = pd.to_datetime(m["day"]).dt.day_name()
    m["bias"] = np.where(m["htf"].isna(), "book", np.where(m["htf"] == 0, "neutral",
                                                          np.where(m["htf"] * np.where(m["direction"] == "long", 1, -1) > 0, "with", "against")))
    news_days = set(J[(J["event"] == "session") & (J["news"] == True)]["day"].astype(str).str[:10])  # noqa: E712
    m["news_day"] = m["day"].isin(news_days)
    rep["sessions"] = {k: _by(m, k) for k in ("session", "setup", "grade", "direction", "hour", "bias", "news_day", "weekday", "layer", "exit_reason")}
    rep["sessions"]["session_setup"] = _by(m.assign(ss=m["session"] + " " + m["setup"]), "ss")
    rep["overall"] = _stats(m)
    # rules: what the passed signals would have made at the bracket they would have had (25/38 when none was set)
    passed = sig[~sig["taken"]].copy()
    if len(passed):
        cell = passed.apply(lambda x: f"{(x['stop'] if x['stop'] == x['stop'] and x['stop'] is not None else 25.0):g}/"
                                      f"{(x['target'] if x['target'] == x['target'] and x['target'] is not None else 38.0):g}", axis=1)
        passed["whatif_r"] = [row.get(k, np.nan) for (_, row), k in zip(passed.iterrows(), cell)]
        rep["rules"] = {k: _stats(g.dropna(subset=["whatif_r"]), "whatif_r") for k, g in passed.groupby("reason")}
    # exits: the live trades from signals (not the overnight orders) under every other exit
    ex = m.dropna(subset=["entry_sig"]) if "entry_sig" in m else m.iloc[:0]
    if len(ex):
        rep["exits"] = {"actual": round(float(ex["r"].astype(float).sum()), 3),
                        **{k: round(float(ex[k].astype(float).sum()), 3) for k in GRID + HOLDS if k in ex}}
        rep["exits_by_session"] = {s: {"actual": round(float(g["r"].astype(float).sum()), 3),
                                       **{k: round(float(g[k].astype(float).sum()), 3) for k in GRID + HOLDS if k in g}} for s, g in ex.groupby("session")}
        ex = ex.assign(mfe_to_exit=to_exit(bars, ex))
        stops = ex[ex["exit_reason"] == "stop"]
        tgts = ex[ex["exit_reason"] == "target"]
        rep["excursion"] = {
            "stops": int(len(stops)),
            "stops_first_halfway": int((stops["mfe_to_exit"] >= 0.5 * stops["target_points"]).sum()) if len(stops) else 0,
            "stops_first_19": int((stops["mfe_to_exit"] >= 19).sum()) if len(stops) else 0,
            "targets": int(len(tgts)),
            "targets_with_twice_more": int((tgts["mfe"] >= 2 * tgts["target_points"]).sum()) if len(tgts) else 0,
            "median_mfe": round(float(ex["mfe"].median()), 2), "median_mae": round(float(ex["mae"].median()), 2)}
    # missed: sessions with a move of more than 38 points away from their opening fair value that came back to it,
    # with no reversion trade taken in the session
    rep["missed"] = missed(bars, J, trades)
    rep["by_day"] = {d: round(float(g["r"].astype(float).sum()), 3) for d, g in m.groupby("day")}
    rep["findings"] = findings(rep)
    return rep


def to_exit(bars: pd.DataFrame, t: pd.DataFrame) -> np.ndarray:
    """The most each trade went in its favour (points) from its entry bar up to, not including, its exit bar (the
    order of the extremes inside the exit bar is unknown)."""
    idx = bars.index
    h, lo = bars["high"].to_numpy(float), bars["low"].to_numpy(float)
    out = []
    for _, x in t.iterrows():
        i = idx.searchsorted(pd.Timestamp(x["entry_time"]))
        j = idx.searchsorted(pd.Timestamp(x["exit_time"]))
        d = 1 if x["direction"] == "long" else -1
        k = j if j > i else i + 1
        seg_h, seg_l = h[i:k], lo[i:k]
        out.append(float(((seg_h - x["entry"]) if d > 0 else (x["entry"] - seg_l)).max()) if len(seg_h) else 0.0)
    return np.asarray(out)


def missed(bars: pd.DataFrame, J: pd.DataFrame, trades: pd.DataFrame) -> list:
    out = []
    ses = J[J["event"] == "session"]
    if ses.empty:
        return out
    idx = bars.index
    for _, s in ses.iterrows():
        if s["session"] == "book":
            continue
        w = bars[(idx >= s["time"]) & (idx <= s["end"])]
        if w.empty:
            continue
        a = float(s["anchor"])
        up, dn = float(w["high"].max() - a), float(a - w["low"].min())
        far = max(up, dn)
        if far <= 38:
            continue
        side_hi = up >= dn
        ext_t = w["high"].idxmax() if side_hi else w["low"].idxmin()
        after = w[w.index > ext_t]
        came_back = bool(len(after) and ((after["low"] <= a).any() if side_hi else (after["high"] >= a).any()))
        if not came_back:
            continue
        day = str(s["day"])[:10]
        rev = trades[(pd.to_datetime(trades["trading_day"]).dt.strftime("%Y-%m-%d") == day) & (trades["session"] == s["session"])
                     & (trades["setup"] == "reversion")]
        if len(rev):
            continue
        passed = J[(J["event"] == "signal") & (J["session"] == s["session"]) & (J["day"].astype(str).str[:10] == day) & (J["setup"] == "reversion")]
        out.append({"day": day, "session": s["session"], "move": round(far, 2), "why_not": passed["reason"].value_counts().to_dict() if len(passed) else
                    {"no trigger": 1}})
    return out


def findings(rep: dict) -> list:
    """The largest effects, in plain sentences, each with its trading days."""
    out = []
    n = rep.get("n_days", 0)
    early = " (early: fewer than 10 trading days)" if n < EARLY_DAYS else ""
    sess = rep.get("sessions", {}).get("session", {})
    for k, v in sorted(sess.items(), key=lambda kv: kv[1]["total_r"]):
        out.append((abs(v["total_r"]), f"{k} session: {v['n']} trades on {v['days']} days, {v['total_r']:+.2f} R ({(v['win'] or 0):.0%} won){early}."))
    for k, v in rep.get("rules", {}).items():
        if v["n"]:
            verb = "kept the system out of" if v["total_r"] < 0 else "cost the system"
            out.append((abs(v["total_r"]), f"Rule '{k}' passed on {v['n']} signals on {v['days']} days: {verb} {abs(v['total_r']):.2f} R{early}."))
    ex = rep.get("exits")
    if ex:
        best = max((k for k in ex if k != "actual"), key=lambda k: ex[k])
        out.append((abs(ex[best] - ex["actual"]), f"Exits: the trades made {ex['actual']:+.2f} R; the best other exit, {best}, would have made "
                                                  f"{ex[best]:+.2f} R{early}."))
    x = rep.get("excursion")
    if x and x["stops"]:
        out.append((x["stops_first_halfway"], f"{x['stops_first_halfway']} of {x['stops']} stopped trades were first halfway to their target."))
    if rep.get("missed"):
        out.append((len(rep["missed"]) * 1.0, f"{len(rep['missed'])} sessions moved over 38 points from fair value and came back with no reversion taken."))
    return [s for _, s in sorted(out, key=lambda x: -x[0])]


def markdown(rep: dict) -> str:
    s = [f"# The JJ system: what it is learning", "", f"{rep.get('n_days', 0)} trading days, {rep.get('trades', 0)} trades. Written {rep.get('at', '')}.", ""]
    if rep.get("in_step") is False:
        return "\n".join(s + rep["findings"]) + "\n"
    s += ["## Findings, largest first", ""] + [f"- {f}" for f in rep.get("findings", [])]
    for title, key in (("By session", "session"), ("By setup and session", "session_setup"), ("By grade", "grade"), ("By hour", "hour"),
                       ("With or against the bias", "bias"), ("News days", "news_day"), ("Exit reasons", "exit_reason")):
        d = rep.get("sessions", {}).get(key)
        if d:
            s += ["", f"## {title}", "", "| | trades | days | total R | R per trade | won |", "|---|---|---|---|---|---|"]
            s += [f"| {k} | {v['n']} | {v['days']} | {v['total_r']:+.2f} | {v['mean_r']:+.3f} | {(v['win'] or 0):.0%} |" for k, v in d.items()]
    if rep.get("rules"):
        s += ["", "## What the rules passed on (and what those signals would have made)", "", "| rule | signals | days | would have made R |", "|---|---|---|---|"]
        s += [f"| {k} | {v['n']} | {v['days']} | {v['total_r']:+.2f} |" for k, v in sorted(rep["rules"].items(), key=lambda kv: kv[1]["total_r"])]
    if rep.get("exits"):
        s += ["", "## Other exits for the same trades (total R)", "", "| exit | total R |", "|---|---|"]
        s += [f"| {k} | {v:+.2f} |" for k, v in rep["exits"].items()]
    if rep.get("missed"):
        s += ["", "## Moves back to fair value with no reversion taken", ""]
        s += [f"- {x['day']} {x['session']}: {x['move']:.0f} points away; why not: {x['why_not']}" for x in rep["missed"]]
    return "\n".join(s) + "\n"


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    with open(a.jj_state) as fh:
        st = json.load(fh)
    days = [pd.Timestamp(d) for d in st["dates"]]
    with open(a.forward_csv, "rb") as fh:
        data = fh.read()
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    fwd = load_minute_bars(io.BytesIO(data), source_tz=a.source_tz)
    cols = sealed.columns.intersection(fwd.columns)
    rep = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "n_days": 0, "findings": ["No scored trading day yet."]}
    if days:
        start = (min(days) - pd.Timedelta(days=fj.CONTEXT_DAYS)).tz_localize(NY)
        bars = pd.concat([sealed[sealed.index >= start][cols], fwd[cols]])
        before = sealed[sealed.index < start]
        hi = float(before["high"].max()) if len(before) else float("-inf")
        cal, _ = events_for(days, a.calendar_dir)
        live = pd.DataFrame(st["trades"]) if st["trades"] else None
        rep = {"at": rep["at"], **learn(bars, days, cal, hi, live)}
    fw._write(a.out, json.dumps(rep, indent=1, sort_keys=True, default=str))
    if a.md:
        fw._write(a.md, markdown(rep))
    print(f"learning report: {rep.get('n_days', 0)} days, {rep.get('trades', 0)} trades, in step: {rep.get('in_step', 'n/a')}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("day")
    for k in ("--csv", "--forward-csv", "--manifest", "--calendar-dir", "--jj-state", "--out"):
        d.add_argument(k, required=True)
    d.add_argument("--source-tz", default="UTC")
    d.add_argument("--md")
    return day(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
