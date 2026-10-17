"""The background lab (docs/research/jj_lab.md): one-setting versions of the JJ system run every night beside it on
paper, each compared day by day with the live JJ system. Nothing here changes the JJ system. A version that beats it is
a proposal for Chris, never an automatic change.

Batches are files research/jj_lab/batch_NN.json, each written and committed before its first day:
  {"batch": 1, "frozen": "2026-10-17", "first_day": "2026-10-19", "engine": "research.jj_lab_engine_b1",
   "variants": {"L01": {"description": "...", "source": "...", "dials": {...}}, ...}}
The dials are fields of the engine's LabConfig; a version is the live system with those fields changed. A batch's
first run pins its file's and its engine's sha256 in its state, and a later change refuses. A new idea is a new
batch, judged only on the trading days from its own first day.

The lab uses the same bars, data checks, scoring rules and calendar as the JJ system (research/forward_jj.py), and
its ledgers never rewrite a scored day.

Comparison: on each trading day both have scored, the version's total R minus the JJ system's. The verdict is taken at
checkpoints, every MIN_DAYS such days (20, 40, ...), on the days up to that checkpoint: a version "beats" the JJ system
when the one-sided lower bound of the mean daily difference (Student t) is above zero, at 5% divided by the number of
versions tried in all batches so far and by 2^k at the k-th checkpoint (so repeated looks cannot add up past 5%); it
"trails" when the upper bound is below zero. A verdict once reached stands.

usage (on the GB10, nightly, after research/forward_jj.py day):
  python research/jj_lab.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --batches research/jj_lab --calendar-dir research/private/calendar \\
      --jj-state research/private/jj_system_v1_state.json --v1-state research/private/forward_v1_state.json \\
      --state-dir research/private/jj_lab --summary research/private/jj_lab_summary.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from statistics import NormalDist

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars  # noqa: E402
from research import forward as fw  # noqa: E402
from research import forward_jj as fj  # noqa: E402
from research.news_calendar import events_for  # noqa: E402

MIN_DAYS = 20  # trading days both have scored before a version can be called better or worse; the verdict is taken at
# every MIN_DAYS-day checkpoint (20, 40, 60, ...), the k-th at 5% / (tries x 2^k), so all the looks together stay within 5% / tries
SHOW_DAYS = 5  # below this no bound is shown
ALPHA = 0.05
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_batches(folder: str) -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(folder, "batch_*.json"))):
        with open(path, "rb") as fh:
            raw = fh.read()
        b = json.loads(raw)
        b["path"], b["sha256"] = path, hashlib.sha256(raw).hexdigest()
        out.append(b)
    return out


def engine_of(b: dict):
    mod = importlib.import_module(b["engine"])
    return mod, fw.sha256(os.path.abspath(mod.__file__))


def _tuples(v):
    return tuple(_tuples(x) for x in v) if isinstance(v, (list, tuple)) else v


def config(mod, dials: dict):
    return mod.LabConfig(**{k: _tuples(v) for k, v in dials.items()})


def t_quantile(p: float, df: int) -> float:
    """Student t quantile (Hill's expansion around the normal; accurate to about 1e-3 for df >= 5)."""
    z = NormalDist().inv_cdf(p)
    v = float(df)
    return (z + (z ** 3 + z) / (4 * v) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * v ** 2)
            + (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / (384 * v ** 3)
            + (79 * z ** 9 + 776 * z ** 7 + 1482 * z ** 5 - 1920 * z ** 3 - 945 * z) / (92160 * v ** 4))


def run_variant(mod, cfg, bars: pd.DataFrame, sealed: pd.DataFrame, days: list, events) -> pd.DataFrame:
    """As research/forward_jj.run, with the batch's engine and the version's configuration."""
    if not days:
        return pd.DataFrame()
    start = (min(days) - pd.Timedelta(days=fj.CONTEXT_DAYS)).tz_localize(NY)
    window = bars[bars.index >= start]
    hi = max(fj.prior_high(sealed, start), float(bars[bars.index < start]["high"].max()) if (bars.index < start).any() else float("-inf"))
    return mod.generate_trades(window, cfg, events=events, days=days, prior_high=hi)


def daily_r(trades: list, dates: list) -> pd.Series:
    """Total R per scored day (0 on a scored day without a trade)."""
    t = pd.DataFrame(trades) if trades else pd.DataFrame(columns=["date", "r"])
    s = t.groupby("date")["r"].sum() if len(t) else pd.Series(dtype=float)
    return pd.Series({d: float(s.get(d, 0.0)) for d in dates}, dtype=float)


def compare(version: pd.Series, jj: pd.Series, tries: int) -> dict:
    common = sorted(set(version.index) & set(jj.index))
    diff = (version[common] - jj[common]).to_numpy(float) if common else np.zeros(0)
    n = len(diff)
    mean = float(diff.mean()) if n else float("nan")
    se = float(diff.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    verdict, lo, hi, q = "too early", float("nan"), float("nan"), float("nan")
    for k in range(1, n // MIN_DAYS + 1):  # every checkpoint so far, on the days up to it
        x = diff[:k * MIN_DAYS]
        q = t_quantile(1 - ALPHA / (max(tries, 1) * 2 ** k), len(x) - 1)
        s = float(x.std(ddof=1) / np.sqrt(len(x)))
        lo, hi = float(x.mean()) - q * s, float(x.mean()) + q * s
        if verdict == "too early" and lo > 0:
            verdict = "beats JJ"
        elif verdict == "too early" and hi < 0:
            verdict = "trails JJ"
    return {"days": n, "per_day_vs_jj": mean, "se": se, "lower": lo, "upper": hi, "t": q, "verdict": verdict,
            "next_checkpoint": (n // MIN_DAYS + 1) * MIN_DAYS}


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    batches = load_batches(a.batches)
    if not batches:
        raise SystemExit(f"refusing: no batch in {a.batches}")
    with open(a.forward_csv, "rb") as fh:
        data = fh.read()
    fw.check_forward_file(data)
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    fwd = load_minute_bars(io.BytesIO(data), source_tz=a.source_tz)
    if fwd.index.min() <= sealed.index.max() or fwd.index.min() - sealed.index.max() - pd.Timedelta(minutes=1) > fw.MAX_GAP:
        raise SystemExit("refusing: the forward bars must continue the sealed ones")
    accepted = set()
    if a.v1_state and os.path.exists(a.v1_state):
        with open(a.v1_state) as fh:
            accepted = {(g["from"], g["to"]) for g in json.load(fh).get("accepted_gaps", [])}
    gaps = fw.classify_gaps(sealed.index[-1:].append(fwd.index))
    blocking = [(x, y) for kind in ("session", "roll") for x, y in gaps[kind] if (x, y) not in accepted]
    if blocking:
        raise SystemExit(f"refusing: a gap stops the run ({blocking[0][0]} to {blocking[0][1]})")
    if not glob.glob(os.path.join(a.calendar_dir, "ff_*.json")):
        raise SystemExit(f"refusing: no calendar snapshot in {a.calendar_dir}")
    cols = sealed.columns.intersection(fwd.columns)
    first_all = min(pd.Timestamp(b["first_day"]) for b in batches)
    bars = pd.concat([sealed[sealed.index >= (first_all - pd.Timedelta(days=fj.CONTEXT_DAYS + 1)).tz_localize(NY)][cols], fwd[cols]])
    both = pd.concat([sealed.iloc[-1:][cols], fwd[cols]])
    before = sealed[sealed.index < bars.index.min()]
    jj = {"dates": [], "trades": []}
    if a.jj_state and os.path.exists(a.jj_state):
        with open(a.jj_state) as fh:
            jj = json.load(fh)
    jj_daily = daily_r(jj["trades"], jj["dates"])
    valid = {}
    for b in batches:
        mod, _ = engine_of(b)
        for name, v in b["variants"].items():
            try:
                config(mod, v["dials"])
                valid[(b["batch"], name)] = None
            except (TypeError, ValueError) as e:
                valid[(b["batch"], name)] = f"{type(e).__name__}: {e}"
    tries = sum(1 for x in valid.values() if x is None)
    os.makedirs(a.state_dir, exist_ok=True)
    summary = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tries": tries, "min_days": MIN_DAYS, "show_days": SHOW_DAYS,
               "jj_days": len(jj["dates"]), "batches": []}
    for b in batches:
        mod, eng_sha = engine_of(b)
        path = os.path.join(a.state_dir, f"batch_{int(b['batch']):02d}_state.json")
        prev = None
        if os.path.exists(path):
            with open(path, "rb") as fh:
                raw = fh.read()
            prev = hashlib.sha256(raw).hexdigest()
            st = json.loads(raw)
            if st["batch_sha256"] != b["sha256"] or st["engine_sha256"] != eng_sha:
                raise SystemExit(f"refusing: batch {b['batch']}'s file or engine changed since its first run: a change is a new batch")
        else:
            st = {"batch_sha256": b["sha256"], "engine_sha256": eng_sha, "dates": [], "trades": {}, "runs": [], "unscored": []}
        first = max(pd.Timestamp(b["first_day"]), fj.FIRST_DAY)
        days, why = fj.scorable(both.index, both["symbol"] if "symbol" in both else None, first)
        cal, missing = events_for(days, a.calendar_dir)
        unscored = {d["day"]: d["why"] for d in st["unscored"]}
        for d, reason in why.items():
            unscored.setdefault(d.strftime("%Y-%m-%d"), reason)
        for d in missing:
            unscored.setdefault(d.strftime("%Y-%m-%d"), "no calendar snapshot fetched before the day began")
        scored = [d for d in days if d.strftime("%Y-%m-%d") not in unscored]
        names = [d.strftime("%Y-%m-%d") for d in scored]
        rows = []
        for name, v in b["variants"].items():
            if valid[(b["batch"], name)] is not None:  # a version whose settings do not build: reported, not run, not counted
                rows.append({"version": name, "kind": v.get("kind", "component"), "description": v["description"], "source": v.get("source", ""),
                             "trades": 0, "total_r": 0.0, "wins": 0, "days": 0, "per_day_vs_jj": float("nan"), "verdict": "invalid: " + valid[(b["batch"], name)]})
                continue
            try:
                t = run_variant(mod, config(mod, v["dials"]), bars, before, scored, cal)
                new = fj.ledger_rows(t)
                new["candidate"] = name
                led = fj.merge(st["trades"].get(name, []), st["dates"], new, names)
            except ValueError as e:
                raise SystemExit(f"refusing: batch {b['batch']} {name}: {e}")
            st["trades"][name] = json.loads(led.to_json(orient="records"))
            r = led["r"].astype(float) if len(led) else pd.Series(dtype=float)
            row = {"version": name, "kind": v.get("kind", "component"), "description": v["description"], "source": v.get("source", ""), "trades": int(len(led)),
                   "total_r": float(r.sum()), "wins": int((r > 0).sum())}
            row.update(compare(daily_r(st["trades"][name], names), jj_daily, tries))
            rows.append(row)
        added = sorted(set(names) - set(st["dates"]))
        st["dates"] = names
        st["unscored"] = [{"day": k, "why": w} for k, w in sorted(unscored.items())]
        st["runs"].append({"at": summary["at"], "forward_sha256": hashlib.sha256(data).hexdigest(), "days_added": added, "previous_state_sha256": prev})
        fw._write(path, json.dumps(st, sort_keys=True, indent=1))
        summary["batches"].append({"batch": b["batch"], "first_day": b["first_day"], "days": len(names), "versions": rows})
        print(f"lab batch {b['batch']}: {len(names)} days, {len(rows)} versions; added {', '.join(added) or 'none'}")
    fw._write(a.summary, json.dumps(summary, indent=1, sort_keys=True, default=str))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("day")
    for k in ("--csv", "--forward-csv", "--manifest", "--batches", "--calendar-dir", "--state-dir", "--summary"):
        d.add_argument(k, required=True)
    d.add_argument("--source-tz", default="UTC")
    d.add_argument("--jj-state", help="the JJ system's state, to compare with")
    d.add_argument("--v1-state", help="the v1 runner's state, whose accepted gaps apply here too")
    a = ap.parse_args()
    return day(a)


if __name__ == "__main__":
    raise SystemExit(main())
