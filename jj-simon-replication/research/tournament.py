"""The forward tournament (docs/research/forward_tournament_v1.md): Baseline 0 and 27 one-dial variants of JJ's
rules, frozen on 2026-10-08 before any of them had a forward trade, run forward side by side every night, each at
one contract per trade.

Each variant is Baseline 0 with one dial the public record leaves open set to a documented alternative (JJ's own
statements, fxreplay's codification, or a structural choice already in the engine). Nothing here was chosen on
historical performance, and nothing reports any: the one-time `init` only proves that the nightly tail rerun gives
the same trades as a longer one, and pins the code and the variants.

It reuses research/forward.py's checks unchanged: the forward file's form, continuity, the gap rules and the holiday
calendar (gaps a person accepted for the v1 test are accepted here too), the session and roll rules, and the ledger
that never rewrites a scored date. Its state, ledger and summary are its own.

Promotion rule, fixed now: a variant is promotable when it has at least MIN_TRADES forward trades and the lower
bound of its forward mean R per trade, one-sided at 5% divided by the number of variants (day-clustered standard
error), is above zero. Promotable means a candidate for a new frozen version, which Chris decides and which is judged
only on forward data after it.

usage (on the GB10):
  python research/tournament.py init --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --out research/tournament_v1_init.json
  python research/tournament.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --init research/tournament_v1_init.json --state research/private/tournament_v1_state.json \\
      --v1-state research/private/forward_v1_state.json --summary research/private/tournament_v1_summary.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import os
import sys
from dataclasses import asdict, replace
from datetime import datetime, timezone
from statistics import NormalDist

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import load_minute_bars, roll_days  # noqa: E402
from research import forward as fw  # noqa: E402
from research.candidates import mean_se  # noqa: E402
from research.engine import ResearchConfig, generate_trades  # noqa: E402

B0 = ResearchConfig(one_contract=True)  # one contract per trade in every variant: R is unchanged, and a wide stop is not sized to zero
# contracts and skipped (the separate B0 stream, research/forward_b0.py, keeps JJ's risk sizing exactly)
# name: (the dial and where the alternative comes from, the configuration)
VARIANTS = {
    "T00": ("JJ's rules as frozen (one contract per trade)", B0),
    "T01": ("continuation window to 09:45 (fxreplay: 10-15 minutes)", replace(B0, continuation_end="09:45")),
    "T02": ("skip the first 3 minutes (fxreplay's filtered test)", replace(B0, skip_first_minutes=3)),
    "T03": ("trading window ends 10:30", replace(B0, window_end="10:30")),
    "T04": ("trading window ends 12:00", replace(B0, window_end="12:00")),
    "T05": ("reversions only until 10:00 (fxreplay's filtered test)", replace(B0, reversion_end="10:00")),
    "T06": ("adds the 14:00-15:00 afternoon session (JJ's earlier videos)", replace(B0, pm_session=True)),
    "T07": ("fair value fixed at the open (no rolling consolidation)", replace(B0, rolling_fair_value=False)),
    "T08": ("reversion only after touching the fair-value band", replace(B0, require_band_touch=True)),
    "T09": ("reversion only 20+ points from fair value", replace(B0, min_distance_from_fv=20.0)),
    "T10": ("continuation direction from the side of fair value", replace(B0, continuation_direction="side_of_fv")),
    "T11": ("fxreplay's wick displacement test", replace(B0, displacement_mode="wick")),
    "T12": ("3/3 swing pivots (fxreplay-style structure)", replace(B0, swing_left=3, swing_right=3)),
    "T13": ("no continuation stall cut-off", replace(B0, continuation_stall_candles=None)),
    "T14": ("grade A+ only, both setups", replace(B0, allow_grade_a=False)),
    "T15": ("continuation only", replace(B0, reversion_end="09:30")),
    "T16": ("reversion only", replace(B0, continuation_end="09:30")),
    "T17": ("reversion A+ only, continuation all grades (S4's entries)", replace(B0, allow_grade_a_reversion=False)),
    "T18": ("fxreplay's ATR stop ladder", replace(B0, stop_mode="atr_tier")),
    "T19": ("target 2.0 x stop", replace(B0, rr=2.0)),
    "T20": ("target 1.0 x stop", replace(B0, rr=1.0)),
    "T21": ("50-point stop (JJ's wide stop)", replace(B0, stop_points=50.0)),
    "T22": ("continuation bracket 0.4 x daily ATR, 2R (S3's)", replace(B0, continuation_atr_k=0.4, continuation_rr=2.0)),
    "T23": ("flat at 16:00", replace(B0, flat_time="16:00")),
    "T24": ("flat at the trading window's end (11:00)", replace(B0, flat_at_window_end=True)),
    "T25": ("no three-loss session stop", replace(B0, max_consecutive_losses=None)),
    "T26": ("two-loss session stop", replace(B0, max_consecutive_losses=2)),
    "T27": ("stop for the day after -2 R", replace(B0, daily_loss_stop_r=2.0)),
}
MIN_TRADES = 50
ALPHA = 0.05
CHECK_DAYS = 60  # init: the tail rerun must match a run started this many calendar days earlier


def z_bound(n_variants: int) -> float:
    return NormalDist().inv_cdf(1 - ALPHA / n_variants)


def code_hashes() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = {}
    for m in fw.TRADE_MODULES + ("research.tournament",):
        f = os.path.abspath(importlib.import_module(m).__file__)
        out[os.path.relpath(f, root)] = fw.sha256(f)
    return out


def configs() -> dict:
    return json.loads(json.dumps({k: asdict(cfg) for k, (_, cfg) in VARIANTS.items()}))


def variant_trades(bars: pd.DataFrame, rolls) -> dict:
    """Every variant's trades, roll dates excluded, with the date and the micro counts the ledger keeps."""
    excl = {pd.Timestamp(d) for d in rolls}
    out = {}
    for name, (_, cfg) in VARIANTS.items():
        t = generate_trades(bars, cfg)
        if t.empty:
            out[name] = t.assign(candidate=name, date=pd.Series(dtype="datetime64[ns]"), micros_eval=0, micros_funded=0)
            continue
        t = t.assign(candidate=name, date=fw.ny_date(t["entry_time"]))
        t = t[~t["date"].isin(excl)].reset_index(drop=True)
        t["micros_eval"] = fw.micros(t["stop_points"], fw.EVAL_BUDGET)
        t["micros_funded"] = fw.micros(t["stop_points"], fw.FUNDED_BUDGET)
        out[name] = t
    return out


def init(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    sealed = load_minute_bars(a.csv, source_tz=a.source_tz)
    rolls = roll_days(sealed)
    first = sealed.index.max().tz_convert(fw.NY).normalize().tz_localize(None) + pd.Timedelta(days=1)
    start = fw.tail_start(first)
    late = variant_trades(sealed[sealed.index >= start], rolls)
    early = variant_trades(sealed[sealed.index >= start - pd.Timedelta(days=CHECK_DAYS)], rolls)
    after = start.tz_localize(None) + pd.Timedelta(days=fw.TAIL_WARMUP)
    compared = {}
    for name in VARIANTS:
        x = fw.ledger_rows({name: late[name][late[name]["date"] >= after]}, sorted(late[name]["date"].unique()))
        y = fw.ledger_rows({name: early[name][early[name]["date"] >= after]}, sorted(early[name]["date"].unique()))
        if not fw.same_rows(x, y):
            raise SystemExit(f"refusing: {name}'s tail rerun does not match a run started {CHECK_DAYS} days earlier")
        compared[name] = int(len(x))
    if sum(compared.values()) == 0:
        raise SystemExit("refusing: the tail check compared no trade")
    pinned = {"version": 1, "frozen": "2026-10-08", "first_unseen": str(fw.FIRST_UNSEEN.date()), "code": code_hashes(), "variants": configs(),
              "descriptions": {k: d for k, (d, _) in VARIANTS.items()}, "tail_check_trades": compared, "min_trades": MIN_TRADES, "alpha": ALPHA,
              "sealed_sha256": man["data"]["sha256"]}
    with open(a.out, "w") as fh:
        json.dump(pinned, fh, indent=1, sort_keys=True)
    print(f"tail check: {sum(compared.values())} trades compared across {len(VARIANTS)} variants; pinned {a.out}")
    return 0


def summarize(led: pd.DataFrame, dates: list) -> dict:
    z = z_bound(len(VARIANTS))
    rows = {}
    for name, (desc, _) in VARIANTS.items():
        t = led[led["candidate"] == name] if len(led) else led
        n = int(len(t))
        if n:
            _, mu, se = mean_se(t["r"].astype(float), pd.to_datetime(t["date"]))
        else:
            mu, se = float("nan"), float("nan")
        lcb = mu - z * se if n > 1 and se == se else float("nan")
        rows[name] = {"description": desc, "trades": n, "r_per_trade": mu, "se": se, "lower_bound": lcb,
                      "total_r": float(t["r"].astype(float).sum()) if n else 0.0, "wins": int((t["r"].astype(float) > 0).sum()) if n else 0,
                      "promotable": bool(n >= MIN_TRADES and lcb == lcb and lcb > 0)}
    return {"sessions": len(dates), "first": dates[0] if dates else None, "last": dates[-1] if dates else None, "z": z, "min_trades": MIN_TRADES,
            "variants": rows}


def day(a) -> int:
    with open(a.manifest) as fh:
        man = json.load(fh)
    if fw.sha256(a.csv) != man["data"]["sha256"]:
        raise SystemExit("refusing: the bar file is not the sealed run's")
    with open(a.init) as fh:
        pinned = json.load(fh)
    code = code_hashes()
    if pinned["code"] != code or pinned["variants"] != configs():
        changed = sorted(k for k in set(code) | set(pinned["code"]) if pinned["code"].get(k) != code.get(k))
        raise SystemExit(f"refusing: the code or variants changed since init ({', '.join(changed) or 'variants'}): that is a new tournament version")
    prev = None
    if os.path.exists(a.state):
        with open(a.state, "rb") as fh:
            raw = fh.read()
        prev = hashlib.sha256(raw).hexdigest()
        state = json.loads(raw)
    else:
        state = {"init": fw.sha256(a.init), "dates": [], "trades": [], "runs": []}
    if state["init"] != fw.sha256(a.init):
        raise SystemExit("refusing: the state belongs to another tournament init")
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
        raise SystemExit(f"refusing: a gap stops the run ({blocking[0][0]} to {blocking[0][1]}); the v1 runner's recorded acceptance applies here too")
    bars = pd.concat([sealed[sealed.index >= fw.tail_start(fw.FIRST_UNSEEN)], fwd[sealed.columns.intersection(fwd.columns)]])
    rolls = roll_days(pd.concat([sealed.iloc[-1:], fwd]))
    dates, _ = fw.scorable_dates(fwd.index, fw.FIRST_UNSEEN, rolls)
    try:
        new = fw.ledger_rows(variant_trades(bars, rolls), dates)
        old = pd.DataFrame(state["trades"]) if state["trades"] else None
        led, scored = fw.merge_ledger(old, state["dates"], new, dates)
    except ValueError as e:
        raise SystemExit(f"refusing: {e}")
    added = sorted(set(scored) - set(state["dates"]))
    state["dates"], state["trades"] = scored, json.loads(led.to_json(orient="records"))
    state["runs"].append({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "forward_sha256": hashlib.sha256(data).hexdigest(),
                          "dates_added": added, "previous_state_sha256": prev})
    fw._write(a.state, json.dumps(state, sort_keys=True, indent=1))
    summary = summarize(led, scored)
    fw._write(a.summary, json.dumps(summary, indent=1, sort_keys=True))
    print(f"tournament: {len(scored)} sessions, {len(led)} trades across {len(VARIANTS)} variants; added {', '.join(added) or 'none'}")
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
    d.add_argument("--state", required=True)
    d.add_argument("--v1-state", help="the v1 runner's state, whose accepted gaps apply here too")
    d.add_argument("--summary", required=True)
    a = ap.parse_args()
    return init(a) if a.mode == "init" else day(a)


if __name__ == "__main__":
    raise SystemExit(main())
