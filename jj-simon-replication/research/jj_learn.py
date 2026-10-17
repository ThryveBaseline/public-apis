"""The JJ system's nightly learning report (docs/research/jj_lab.md): from the forward record only, what went well, what
went badly, and what the system could have done, written for the weekly review that builds the next challenger.

It reruns the JJ system's rules on every scored trading day with the learning engine (research/jj_lab_engine_b2.py),
whose defaults are the live system's rules, so that every decision is in its journal. It first checks that this rerun
gives exactly the live ledger's trades (else the report says the learning engine is out of step and stops there).
Then every signal, taken or passed, is replayed with other exits (research/jj_whatif.py), and the report gives:

  sessions   the live trades by session, setup, grade, direction, hour, bias, news day, weekday and layer
  rules      for each rule, the setups it alone stopped (no other rule failed them), once per episode, replayed at the
             bracket they would have had: a rule that kept the system out of losers earns its place, one that kept it
             out of winners costs
  exits      what the live trades would have made with each other stop and target, or held to the day's end
  excursion  how far trades went for and against them: stops first in profit, targets with more to give
  missed     sessions where price moved well away from fair value and came back without a reversion trade
  findings   the largest of these, in plain sentences, each with its number of trading days ("early" under 10)

A rule's effect counts only the setups it alone stopped, once per episode. The live system is never changed by any of this.
A day's trades move together, so the sample is the number of days.

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
from research.jj_whatif import STOPS, TARGETS, day_end_index, replay_exit, replay_signals  # noqa: E402
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
        theirs = live[live["date"].isin(rep["days"])] if len(live) else pd.DataFrame(columns=fj.LEDGER_KEY)
        rep["in_step"] = bool(fj.same(mine[fj.LEDGER_KEY].reset_index(drop=True), theirs[fj.LEDGER_KEY].reset_index(drop=True)))
        if not rep["in_step"]:
            rep["findings"] = ["The learning engine is out of step: its trades differ from the live ledger. The report stops here until that is fixed."]
            return rep
    J = pd.DataFrame(journal)
    if trades.empty:
        rep["findings"] = ["No trades yet."]
        return rep
    td = fj.trading_days(bars.index)
    trades = trades.assign(day=pd.to_datetime(trades["trading_day"]).dt.strftime("%Y-%m-%d"))
    has_sig = len(J) and "taken" in J and (J["event"] == "signal").any()
    sig = J[J["event"] == "signal"].copy() if has_sig else pd.DataFrame(columns=["day", "session", "setup", "time", "taken", "reason", "fails", "index", "d"])
    if len(sig):
        sig["day"] = pd.to_datetime(sig["day"]).dt.strftime("%Y-%m-%d")
        sig["taken"] = sig["taken"].astype(bool)
        sig = sig.join(replay_signals(bars, sig, td))
    taken = sig[sig["taken"]] if len(sig) else sig
    # the live trades with their journal: the signal that made each (not the overnight orders, which have no signal)
    tr = trades.copy()
    tr["key"] = tr["session"] + "|" + tr["setup"] + "|" + tr["signal_time"].astype(str)
    taken = taken.assign(key=taken["session"] + "|" + taken["setup"] + "|" + taken["time"].astype(str)) if len(taken) else taken.assign(key=[])
    m = tr.merge(taken.drop(columns=[c for c in ("day", "session", "setup", "grade") if c in taken]), on="key", how="left", suffixes=("", "_sig"))
    ny = pd.to_datetime(m["signal_time"]).dt.tz_convert(NY)
    m["hour"] = ny.dt.hour
    m["weekday"] = pd.to_datetime(m["day"]).dt.day_name()
    htf = m["htf"] if "htf" in m else pd.Series(np.nan, index=m.index)
    m["bias"] = np.where(htf.isna(), "overnight order", np.where(htf == 0, "neutral",
                                                                 np.where(htf * np.where(m["direction"] == "long", 1, -1) > 0, "with", "against")))
    ses = J[J["event"] == "session"] if len(J) else pd.DataFrame()
    rel = set(ses[ses.get("release_day", pd.Series(False, index=ses.index)) == True]["day"].astype(str).str[:10]) if len(ses) else set()  # noqa: E712
    m["release_day"] = m["day"].isin(rel)
    rep["sessions"] = {k: _by(m, k) for k in ("session", "setup", "grade", "direction", "hour", "bias", "release_day", "weekday", "layer", "exit_reason")}
    rep["sessions"]["session_setup"] = _by(m.assign(ss=m["session"] + " " + m["setup"]), "ss")
    rep["overall"] = _stats(m)
    rep["rules"] = rule_effects(bars, sig, td) if len(sig) else {}
    # exits: the live trades from signals (not the overnight orders) under every other exit
    ex = m.dropna(subset=["entry_sig"]) if "entry_sig" in m else m.iloc[:0]
    if len(ex):
        rep["exits"] = {"actual": round(float(ex["r"].astype(float).sum()), 3),
                        **{k: round(float(ex[k].astype(float).sum()), 3) for k in GRID + HOLDS if k in ex}}
        rep["exits_days"] = int(ex["day"].nunique())
        rep["exits_by_session"] = {s: {"actual": round(float(g["r"].astype(float).sum()), 3),
                                       **{k: round(float(g[k].astype(float).sum()), 3) for k in GRID + HOLDS if k in g}} for s, g in ex.groupby("session")}
        ex = ex.assign(mfe_to_exit=to_exit(bars, ex))
        stops = ex[ex["exit_reason"] == "stop"]
        tgts = ex[ex["exit_reason"] == "target"]
        rep["excursion"] = {
            "stops": int(len(stops)), "days": int(ex["day"].nunique()),
            "stops_first_halfway": int((stops["mfe_to_exit"] >= 0.5 * stops["target_points"]).sum()) if len(stops) else 0,
            "stops_first_19": int((stops["mfe_to_exit"] >= 19).sum()) if len(stops) else 0,
            "targets": int(len(tgts)),
            "targets_with_twice_more": int((tgts["mfe"] >= 2 * tgts["target_points"]).sum()) if len(tgts) else 0,
            "median_mfe": round(float(ex["mfe"].median()), 2), "median_mae": round(float(ex["mae"].median()), 2)}
    rep["missed"] = missed(bars, J, trades) if len(J) else []
    rep["by_day"] = {d: round(float(g["r"].astype(float).sum()), 3) for d, g in m.groupby("day")}
    rep["findings"] = findings(rep)
    return rep


NOT_RULES = ("no next bar",)  # not a trading rule: the next bar was missing or the firm had closed


def rule_effects(bars: pd.DataFrame, sig: pd.DataFrame, td: np.ndarray) -> dict:
    """What each rule did: the signals it alone stopped (no other rule failed them, so removing that rule alone would
    have taken them), counted once per episode (a signal is counted only after the previous counted one in the same
    day, session and direction would have closed), each replayed at the bracket it would have had (25/38 when its
    room gave none). Negative: the rule kept the system out of losers."""
    passed = sig[~sig["taken"]]
    if passed.empty:
        return {}
    o, h, l, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ny = bars.index.tz_convert(NY)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    fails = passed["fails"].apply(lambda f: list(f) if isinstance(f, (list, tuple)) else [])
    rules = sorted({x for f in fails for x in f if x not in NOT_RULES})
    out = {}
    for rule in rules:
        alone = passed[fails.apply(lambda f: f == [rule])].sort_values("index")
        rows, open_until = [], {}
        for _, x in alone.iterrows():
            key = (x["day"], x["session"], int(x["d"]))
            t = int(x["index"])
            if open_until.get(key, -1) >= t:
                continue
            stop = float(x["stop"]) if x["stop"] == x["stop"] and x["stop"] is not None else 25.0
            target = float(x["target"]) if x["target"] == x["target"] and x["target"] is not None else 38.0
            r, k = replay_exit(o, h, l, c, t, int(x["d"]), day_end_index(mod, td, t), stop, target)
            open_until[key] = k
            rows.append({"day": x["day"], "r": r})
        st = _stats(pd.DataFrame(rows, columns=["day", "r"]).dropna())
        out[rule] = {**st, "signals_alone": int(len(alone)), "signals_any": int(fails.apply(lambda f: rule in f).sum())}
    return out


def to_exit(bars: pd.DataFrame, t: pd.DataFrame) -> np.ndarray:
    """The most each trade went in its favour (points) from its entry bar up to, not including, its exit bar (the
    order of the extremes inside the exit bar is unknown); NaN for a trade closed in its entry bar."""
    idx = bars.index
    h, lo = bars["high"].to_numpy(float), bars["low"].to_numpy(float)
    out = []
    for _, x in t.iterrows():
        i = idx.searchsorted(pd.Timestamp(x["entry_time"]))
        j = idx.searchsorted(pd.Timestamp(x["exit_time"]))
        if j <= i:
            out.append(np.nan)
            continue
        d = 1 if x["direction"] == "long" else -1
        out.append(float(((h[i:j] - x["entry"]) if d > 0 else (x["entry"] - lo[i:j])).max()))
    return np.asarray(out, dtype=float)


def missed(bars: pd.DataFrame, J: pd.DataFrame, trades: pd.DataFrame) -> list:
    """Moves back to fair value with no reversion taken: in each session, following its fair value as it changed, a move of
    more than 38 points away from it that came back to it, with no reversion trade entered between the farthest point
    and the return."""
    out = []
    ses = J[J["event"] == "session"]
    anc = J[J["event"] == "anchor"] if (J["event"] == "anchor").any() else pd.DataFrame(columns=["day", "session", "time", "new"])
    sigs = J[J["event"] == "signal"] if (J["event"] == "signal").any() else pd.DataFrame(columns=["day", "session", "setup", "time", "reason"])
    rev = trades[trades["setup"] == "reversion"]
    for _, s in ses.iterrows():
        day = str(s["day"])[:10]
        w = bars[(bars.index >= s["time"]) & (bars.index <= s["end"])]
        if w.empty:
            continue
        changes = anc[(anc["day"].astype(str).str[:10] == day) & (anc["session"] == s["session"])].sort_values("time")
        ch_t, ch_v = list(changes["time"]), list(changes["new"])
        a, k = float(s["anchor"]), 0
        far, far_t, far_side = 0.0, None, 0
        for ts, row in w.iterrows():
            while k < len(ch_t) and ch_t[k] < ts:  # a change at a bar's close applies from the next bar
                a, k = float(ch_v[k]), k + 1
                far, far_t, far_side = 0.0, None, 0
            up, dn = row["high"] - a, a - row["low"]
            if far > 38 and ((far_side > 0 and row["low"] <= a) or (far_side < 0 and row["high"] >= a)):
                took = rev[(rev["session"] == s["session"]) & (pd.to_datetime(rev["entry_time"]) >= far_t) & (pd.to_datetime(rev["entry_time"]) <= ts)]
                if took.empty:
                    why = sigs[(sigs["session"] == s["session"]) & (sigs["setup"] == "reversion") & (pd.to_datetime(sigs["time"]) >= far_t)
                               & (pd.to_datetime(sigs["time"]) <= ts)]
                    out.append({"day": day, "session": s["session"], "move": round(far, 2), "from": str(far_t), "back": str(ts),
                                "why_not": why["reason"].value_counts().to_dict() if len(why) else {"no trigger": 1}})
                far, far_t, far_side = 0.0, None, 0
                continue
            if max(up, dn) > far:
                far, far_t, far_side = float(max(up, dn)), ts, (1 if up >= dn else -1)
    return out


def findings(rep: dict) -> list:
    """The largest effects in R first, then the counts, each with its own number of trading days ("early" under 10)."""
    def early(days: int) -> str:
        return " (early: under 10 trading days)" if days < EARLY_DAYS else ""
    r_items, counts = [], []
    for k, v in rep.get("sessions", {}).get("session", {}).items():
        r_items.append((abs(v["total_r"]), f"{k} session: {v['n']} trades on {v['days']} days, {v['total_r']:+.2f} R ({(v['win'] or 0):.0%} won){early(v['days'])}."))
    for k, v in rep.get("rules", {}).items():
        if not v["n"]:
            continue
        if abs(v["total_r"]) < 0.005:
            effect = "made no difference"
        elif v["total_r"] < 0:
            effect = f"kept the system out of {abs(v['total_r']):.2f} R of losses"
        else:
            effect = f"kept the system out of {v['total_r']:.2f} R of gains"
        r_items.append((abs(v["total_r"]), f"Rule '{k}' alone stopped {v['n']} separate setups on {v['days']} days: it {effect}{early(v['days'])}."))
    ex = rep.get("exits")
    if ex:
        others = [k for k in ex if k != "actual"]
        best = max(others, key=lambda k: ex[k])
        dd = rep.get("exits_days", 0)
        r_items.append((abs(ex[best] - ex["actual"]), f"Exits: the trades from signals (not the overnight orders) made {ex['actual']:+.2f} R on {dd} days; "
                                                      f"the best of {len(others)} other exits in hindsight, {best}, would have made {ex[best]:+.2f} R "
                                                      f"(picked after the fact, so it flatters){early(dd)}."))
    x = rep.get("excursion")
    if x and x["stops"]:
        counts.append(f"{x['stops_first_halfway']} of {x['stops']} stopped trades were first halfway to their target ({x['days']} days){early(x['days'])}.")
    if rep.get("missed"):
        md = len({(y['day']) for y in rep["missed"]})
        counts.append(f"{len(rep['missed'])} moves of over 38 points from fair value came back with no reversion taken ({md} days){early(md)}.")
    return [s for _, s in sorted(r_items, key=lambda z: -z[0])] + counts


def markdown(rep: dict) -> str:
    s = [f"# The JJ system: what it is learning", "", f"{rep.get('n_days', 0)} trading days, {rep.get('trades', 0)} trades. Written {rep.get('at', '')}.", ""]
    if rep.get("in_step") is False:
        return "\n".join(s + rep["findings"]) + "\n"
    s += ["## Findings, largest first", ""] + [f"- {f}" for f in rep.get("findings", [])]
    for title, key in (("By session", "session"), ("By setup and session", "session_setup"), ("By grade", "grade"), ("By hour", "hour"),
                       ("With or against the bias", "bias"), ("Release days", "release_day"), ("Exit reasons", "exit_reason")):
        d = rep.get("sessions", {}).get(key)
        if d:
            s += ["", f"## {title}", "", "| | trades | days | total R | R per trade | won |", "|---|---|---|---|---|---|"]
            s += [f"| {k} | {v['n']} | {v['days']} | {v['total_r']:+.2f} | {v['mean_r']:+.3f} | {(v['win'] or 0):.0%} |" for k, v in d.items()]
    if rep.get("rules"):
        s += ["", "## What each rule did", "", "The setups a rule alone stopped (no other rule failed them), once per episode, replayed at the bracket they "
              "would have had. Negative: the rule kept the system out of losers.", "",
              "| rule | setups it alone stopped (episodes) | days | they would have made R | setups it failed (any) |", "|---|---|---|---|---|"]
        s += [f"| {k} | {v['n']} | {v['days']} | {v['total_r']:+.2f} | {v['signals_any']} |" for k, v in sorted(rep["rules"].items(), key=lambda kv: kv[1]["total_r"])]
    if rep.get("exits"):
        s += ["", "## Other exits for the same trades (total R)", "", "| exit | total R |", "|---|---|"]
        s += [f"| {k} | {v:+.2f} |" for k, v in rep["exits"].items()]
    if rep.get("missed"):
        s += ["", "## Moves back to fair value with no reversion taken", ""]
        s += [f"- {x['day']} {x['session']}: {x['move']:.0f} points away, back by {x['back'][11:16]}; why not: {x['why_not']}" for x in rep["missed"]]
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
        live = pd.DataFrame(st["trades"]) if st["trades"] else pd.DataFrame(columns=fj.KEEP)
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
