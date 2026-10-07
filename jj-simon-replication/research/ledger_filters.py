"""B2: reversion rules as he states them, screened on the sealed ledger.

Two layers.
1. Filters on the sealed ledger. The sealed entries stay as sealed; a filter decides which reversion entries
   would not have been taken. Continuation is never filtered. The surviving entries then go through one
   sequential pass per session, in entry order, as the frozen engine takes trades: one position at a time (an
   entry is taken only if the previously taken trade exited before it), the three-consecutive-loss stop (every
   taken trade counts; reset at the session start), and, for B2c, the cap on reversion attempts actually taken.
   Before anything is reported, that pass on the unfiltered ledger must keep every trade; otherwise the
   semantics differ from the engine and the tool refuses.
2. Composites: the same filters applied to the trades replayed by research/bracket_replay.py under a bracket
   variant (flat at 16:00), using each replayed trade's own exit time in the sequential pass, so a longer hold
   blocks the entries it would have blocked and no decision uses an outcome that had not printed yet. The join
   is checked twice: the replay must cover every ledger entry (replayed or marked as dropped), and the replayed
   `ledger_bracket` control must equal the ledger R on every stop or target exit before 16:00.

Screening on a fixed ledger ignores that a dropped trade would have freed the position for a later signal, and
that trades the sealed loss stop suppressed would now be taken. It is a first screen; shortlisted rule sets go to
full re-simulation on the research branch.

Filters (provenance: docs/research/synthesis/reversion_rules.md section 7):
  base             the sealed ledger
  B2a              reversion grade A+ only (his funded entry trigger: break of structure)
  B2b2             the engine's own require_band_touch gate, for contrast: through the signal bar, the session extreme since
                   09:30 reached at least the trade's target away from its recorded fair value, on the side the reversion
                   fades (measured against the fair value in force at the signal, as the engine does)
  B2b1             the same gate restarted after the last close through fair value (a return to fair resets it)
  B2c4 / B2c3      at most 4 / 3 reversion attempts per session, in entry order
  B2h              April room rule: room at the signal >= the whole target (instead of 80% of it)
  cut0945/cut1000  reversion entries before 09:45 / 10:00 (a ledger hypothesis from the anatomy, not a stated rule)
  eval_as_stated   B2b1 with the band equal to the active target (76 on wide-open days, else 38) and, on
                   wide-open days, room >= 0.8 x 76; its bracket part (B2d, 50/76) is in the composites
  funded_as_stated B2a + B2b1 with the band equal to the funded target (the B2f1 menu target from the room) + B2c4;
                   its bracket part (B2f1) is in the composites

usage: python research/ledger_filters.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv \
           --source-tz UTC --oos-start 2025-10-06 --manifest sealed/run1/manifest.json \
           --replay-csv research/private/run1_bracket_replay_b2.csv --out research/run1_b2.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from research.anatomy import exclude_roll_trades, load_trades  # noqa: E402
from research.bracket_replay import WIDE_BODY, WIDE_TARGET, opening_bodies, room_target  # noqa: E402

MAX_CONSEC_LOSSES = 3
ROOM_SHARE = 0.8

FILTERS = ["base", "B2a", "B2b2", "B2b1", "B2c4", "B2c3", "B2h", "cut0945", "cut1000", "eval_as_stated", "funded_as_stated"]
FILTER_PARTS = {"base": [], "B2a": ["a"], "B2b2": ["b2"], "B2b1": ["b1"], "B2c4": ["c4"], "B2c3": ["c3"], "B2h": ["room_ge_target"],
                "cut0945": ["cut0945"], "cut1000": ["cut1000"], "eval_as_stated": ["b1w", "room_w"], "funded_as_stated": ["a", "b1f", "c4"]}
COMPOSITES = [  # (label, filter, replay variant)
    ("sealed bracket, flat 16:00 (control)", "base", "ledger_bracket"),
    ("B2d wide-open switch", "base", "wide_open_switch"),
    ("B2f1 target from room, menu", "base", "room_menu"),
    ("B2f2 target from room, exact", "base", "room_exact"),
    ("B2f3 target from room, half", "base", "room_half"),
    ("B2f1 + B2e wide stop over 100 room", "base", "room_menu_e"),
    ("B2a + B2f1", "B2a", "room_menu"),
    ("evaluation as stated (B2b1 band = target, B2d)", "eval_as_stated", "wide_open_switch"),
    ("funded filters with the sealed bracket", "funded_as_stated", "ledger_bracket"),
    ("funded as stated (B2a, B2b1, B2c4, B2f1)", "funded_as_stated", "room_menu"),
    ("funded as stated + B2e", "funded_as_stated", "room_menu_e"),
]


def _ny(s: pd.Series) -> pd.Series:
    return s.dt.tz_convert(NY)


def session_key(trades: pd.DataFrame) -> pd.Series:
    return _ny(trades["entry_time"]).dt.normalize().dt.tz_localize(None)


def sealed_target(trades: pd.DataFrame) -> np.ndarray:
    return (trades["target"].astype(float) - trades["entry"].astype(float)).abs().to_numpy()


def move_away_gate(trades: pd.DataFrame, bars: pd.DataFrame, since_last_cross: bool, threshold=None, session_start: str = "09:30",
                   inclusive: bool = False) -> pd.Series:
    """True for reversion trades whose decision was preceded, within the session and through the signal bar (known
    at the decision; entry is at the next bar's open), by a move of more than `threshold` points (default: the
    trade's sealed target) away from the trade's recorded fair value on the side it fades. Continuation rows: True.
    `inclusive=True` passes at equality, as the frozen engine's require_band_touch does (fpt/strategy.py: it skips only
    when the session extreme is short of fair value plus the band); his own "more than" gates are strict."""
    hi = bars["high"].to_numpy(float)
    lo = bars["low"].to_numpy(float)
    cl = bars["close"].to_numpy(float)
    idx = bars.index
    sh, sm = (int(x) for x in session_start.split(":"))
    out = np.ones(len(trades), dtype=bool)
    is_rev = (trades["setup"].astype(str) == "reversion").to_numpy()
    fv = trades["fair_value"].astype(float).to_numpy()
    thr = sealed_target(trades) if threshold is None else np.asarray(threshold, dtype=float)
    d = trades["direction"].astype(int).to_numpy()
    for k, st in enumerate(trades["signal_time"]):
        if not is_rev[k]:
            continue
        s0 = st.tz_convert(NY).replace(hour=sh, minute=sm, second=0, microsecond=0)
        i0 = idx.searchsorted(s0)
        i1 = idx.searchsorted(st, side="right")  # through the signal bar
        if since_last_cross and i1 > i0:
            c = cl[i0:i1]
            # a short reversion fades price above fair value: the move restarts after the last close at or below it
            opp = (c <= fv[k]) if d[k] < 0 else (c >= fv[k])
            if opp.any():
                i0 = i0 + int(np.flatnonzero(opp)[-1]) + 1
        if i1 <= i0:
            out[k] = False
            continue
        excursion = (hi[i0:i1].max() - fv[k]) if d[k] < 0 else (fv[k] - lo[i0:i1].min())
        out[k] = bool(excursion >= thr[k]) if inclusive else bool(excursion > thr[k])
    return pd.Series(out, index=trades.index)


def wide_open_days(trades: pd.DataFrame, bars: pd.DataFrame) -> np.ndarray:
    body = session_key(trades).map(opening_bodies(bars)).to_numpy(float)
    return np.isfinite(body) & (body > WIDE_BODY)


def build_gates(trades: pd.DataFrame, bars: pd.DataFrame) -> dict:
    wide = wide_open_days(trades, bars)
    tgt = sealed_target(trades)
    room = trades["distance_from_fv"].astype(float).abs().to_numpy()
    return {
        "b2": move_away_gate(trades, bars, since_last_cross=False, inclusive=True),  # the engine's require_band_touch, for contrast
        "b1": move_away_gate(trades, bars, since_last_cross=True),
        "b1w": move_away_gate(trades, bars, since_last_cross=True, threshold=np.where(wide, WIDE_TARGET, tgt)),
        "b1f": move_away_gate(trades, bars, since_last_cross=True, threshold=np.array([room_target("menu", float(x)) for x in room])),
        "room_ge_target": pd.Series(room >= tgt, index=trades.index),
        "room_w": pd.Series(~wide | (room >= ROOM_SHARE * WIDE_TARGET), index=trades.index),
        "wide": pd.Series(wide, index=trades.index),
    }


def apply_filter(trades: pd.DataFrame, name: str, gates: dict) -> pd.DataFrame:
    t = trades
    parts = FILTER_PARTS[name]
    rev = t["setup"].astype(str) == "reversion"
    keep = pd.Series(True, index=t.index)
    minute = _ny(t["entry_time"]).dt.hour * 60 + _ny(t["entry_time"]).dt.minute
    if "a" in parts:
        keep &= ~rev | (t["grade"].astype(str) == "A+")
    if "cut0945" in parts:
        keep &= ~rev | (minute < 9 * 60 + 45)
    if "cut1000" in parts:
        keep &= ~rev | (minute < 10 * 60)
    for g in ("b2", "b1", "b1w", "b1f", "room_ge_target", "room_w"):
        if g in parts:
            gv = gates[g].reindex(t.index)
            if gv.isna().any():
                raise ValueError(f"gate {g} has no value for {int(gv.isna().sum())} trades: the subset's labels are not ledger positions")
            keep &= ~rev | gv.astype(bool)
    return t[keep]


def sequential_pass(t: pd.DataFrame, cap: int | None = None, limit: int = MAX_CONSEC_LOSSES) -> pd.DataFrame:
    """Take trades per session (New York date) in entry order as the frozen engine would: an entry is taken only if
    the previously taken trade exited before it (exit_time < entry_time: one position at a time), the session's
    consecutive-loss streak is below `limit`, and, for a reversion under a cap, fewer than `cap` reversions have
    been taken. Every taken trade updates the streak (a loss is pnl_dollars < 0; anything else resets it)."""
    t = t.sort_values("entry_time", kind="stable")
    keep = np.zeros(len(t), dtype=bool)
    sess = session_key(t).to_numpy()
    et = list(t["entry_time"])
    xt = list(t["exit_time"])
    pnl = t["pnl_dollars"].astype(float).to_numpy()
    rev = (t["setup"].astype(str) == "reversion").to_numpy()
    last, streak, prev_exit, n_rev = None, 0, None, 0
    for i in range(len(t)):
        if sess[i] != last:
            last, streak, prev_exit, n_rev = sess[i], 0, None, 0
        if prev_exit is not None and prev_exit >= et[i]:
            continue  # a position is still open
        if streak >= limit:
            continue
        if cap is not None and rev[i] and n_rev >= cap:
            continue
        keep[i] = True
        prev_exit = xt[i]
        streak = streak + 1 if pnl[i] < 0 else 0
        n_rev += int(rev[i])
    return t[keep]


def select(trades: pd.DataFrame, name: str, gates: dict) -> pd.DataFrame:
    """Entry-time filters, then the sequential pass with the filter's reversion cap, if any."""
    parts = FILTER_PARTS[name]
    cap = 4 if "c4" in parts else (3 if "c3" in parts else None)
    return sequential_pass(apply_filter(trades, name, gates), cap=cap)


def consecutive_loss_stop(t: pd.DataFrame, limit: int = MAX_CONSEC_LOSSES) -> pd.DataFrame:
    """The sequential pass without a cap (kept for callers that only want the engine's stop and one position)."""
    return sequential_pass(t, cap=None, limit=limit)


def _pf(r: pd.Series) -> float:
    w = r[r > 0].sum()
    lo = -r[r <= 0].sum()
    return float(w / lo) if lo > 0 else float("inf")


def _stats(g: pd.DataFrame) -> dict:
    n = len(g)
    return {"trades": int(n), "win_rate": float((g["r"] > 0).mean()) if n else float("nan"),
            "expectancy_r": float(g["r"].mean()) if n else float("nan"), "profit_factor": _pf(g["r"]) if n else float("nan"),
            "total_r": float(g["r"].sum())}


def _f(v, spec):
    return "n/a" if (isinstance(v, float) and np.isnan(v)) else format(v, spec)


def check_alignment(trades: pd.DataFrame, replay: pd.DataFrame) -> int:
    """The replayed `ledger_bracket` control must equal the ledger R on every stop or target exit before 16:00;
    otherwise the replay rows are not keyed to these trades and nothing is reported."""
    if "exit_time" not in replay.columns:
        raise ValueError("the replay file has no exit_time column; rerun research/bracket_replay.py at this version")
    ids = set(int(x) for x in replay["trade"].unique())
    ledger_ids = set(int(x) for x in trades.index)
    if not ids <= ledger_ids:
        raise ValueError("replay trade ids are not a subset of the ledger positions")
    if ids != ledger_ids:
        raise ValueError(f"replay does not cover the ledger: {len(ledger_ids - ids)} ledger entries are neither replayed nor marked as dropped")
    rv = replay[replay["variant"] == "ledger_bracket"].set_index("trade")["r"].astype(float)
    t = trades.loc[trades.index.intersection(rv.index)]
    xt = _ny(t["exit_time"])
    sel = t["exit_reason"].astype(str).isin(["stop", "target"]) & ((xt.dt.hour * 60 + xt.dt.minute) < 16 * 60)
    if not sel.any():
        raise ValueError("no ledger stop/target exits before 16:00 to check the replay join against")
    diff = (rv.loc[t.index[sel]].to_numpy() - t.loc[sel, "r"].astype(float).to_numpy())
    if np.abs(diff).max() > 1e-9:
        raise ValueError(f"replay join misaligned: max |R replay - R ledger| = {np.abs(diff).max():.6f} on {int(sel.sum())} checked trades")
    return int(sel.sum())


def composite_frame(trades: pd.DataFrame, replay: pd.DataFrame, variant: str) -> pd.DataFrame:
    rv = replay[replay["variant"] == variant].set_index("trade")
    if rv.empty:
        raise ValueError(f"variant {variant} is not in the replay file")
    if "exit_time" not in rv.columns:
        raise ValueError("the replay file has no exit_time column; rerun research/bracket_replay.py at this version")
    t = trades.loc[trades.index.intersection(rv.index)].copy()
    t["r"] = rv.loc[t.index, "r"].astype(float).to_numpy()
    t["pnl_dollars"] = t["r"]  # the loss stop uses only the sign
    t["exit_time"] = pd.to_datetime(rv.loc[t.index, "exit_time"], utc=True).dt.tz_convert(NY)
    return t


def _period_tables(frames: list[tuple[str, pd.DataFrame]], years: list[int], key: str, control_label: str) -> list[str]:
    s = []
    rows = []
    for label, f in frames:
        for per in ("development", "benchmark"):
            p = f[f["period"] == per]
            for scope, g in (("all", p), ("reversion", p[p["setup"].astype(str) == "reversion"]), ("continuation", p[p["setup"].astype(str) == "continuation"])):
                rows.append({key: label, "period": per, "scope": scope, **_stats(g)})
    res = pd.DataFrame(rows)
    for scope in ("all", "reversion", "continuation"):
        s.append(f"### Scope = {scope}\n\n| {key} | period | trades | win rate | expectancy R | profit factor | total R |\n|---|---|---|---|---|---|---|")
        for label, _ in frames:
            for per in ("development", "benchmark"):
                r = res[(res[key] == label) & (res["period"] == per) & (res["scope"] == scope)].iloc[0]
                s.append(f"| {label} | {per} | {r['trades']} | {_f(r['win_rate'], '.1%')} | {_f(r['expectancy_r'], '+.3f')} | {_f(r['profit_factor'], '.2f')} | {r['total_r']:+.1f} |")
        s.append("")
    for scope in ("all", "reversion"):
        s.append(f"### Development years, scope = {scope}: expectancy R by year\n\n| {key} | " + " | ".join(str(y) for y in years) + f" | mean | years > 0 | years better than {control_label} |\n|---|" + "---|" * (len(years) + 3))
        per_year = {}
        for label, f in frames:
            dev = f[f["period"] == "development"]
            if scope == "reversion":
                dev = dev[dev["setup"].astype(str) == "reversion"]
            per_year[label] = [float(dev.loc[dev["year"] == y, "r"].mean()) if (dev["year"] == y).any() else float("nan") for y in years]
        ctrl = per_year[frames[0][0]]
        for label, _ in frames:
            vals = per_year[label]
            finite = [v for v in vals if not np.isnan(v)]
            better = sum(1 for v, c in zip(vals, ctrl) if not np.isnan(v) and not np.isnan(c) and v > c)
            mean_txt = f"{np.mean(finite):+.3f}" if finite else "n/a"
            s.append(f"| {label} | " + " | ".join(_f(v, '+.3f') for v in vals) + f" | {mean_txt} | {sum(1 for v in finite if v > 0)}/{len(finite)} | {better}/{len(years)} |")
        s.append("")
    return s


def evaluate(trades: pd.DataFrame, bars: pd.DataFrame, oos_start: str, replay: pd.DataFrame | None = None) -> tuple[str, dict]:
    gates = build_gates(trades, bars)
    trades = trades.assign(period=np.where(session_key(trades) < pd.Timestamp(oos_start), "development", "benchmark"),
                           year=_ny(trades["entry_time"]).dt.year)
    base = select(trades, "base", gates)
    if len(base) != len(trades):
        raise ValueError(f"the sequential pass (one position, three-loss stop) on the unfiltered ledger removed {len(trades) - len(base)} trades; the stop semantics differ from the engine")
    years = sorted(int(y) for y in trades.loc[trades["period"] == "development", "year"].unique())
    rev = trades["setup"].astype(str) == "reversion"
    n_rev = int(rev.sum())
    s = ["# B2: reversion rules as stated, screened on the sealed ledger\n"]
    s.append(f"Base reproduction: the sequential pass (one position at a time, three-loss session stop) on the unfiltered ledger keeps all {len(trades)} trades. That is a necessary condition only; that the pass reproduces the engine's stop is shown in the test suite by running the frozen engine with and without its loss stop.")
    s.append(f"Reversion entries: {n_rev}. Pass the move-away gate from the open (B2b2): {int(gates['b2'][rev].sum())}; since the last return to fair (B2b1): {int(gates['b1'][rev].sum())}; "
             f"B2b1 with the band at 76 on wide-open days: {int(gates['b1w'][rev].sum())}; B2b1 with the band at the funded menu target: {int(gates['b1f'][rev].sum())}. Room at the signal >= the whole target (B2h): {int(gates['room_ge_target'][rev].sum())}. "
             f"Trades on wide-open days (09:30 body > {WIDE_BODY:g} points): {int(gates['wide'].sum())}.")
    s.append("Screening on a fixed ledger ignores freed positions and trades the sealed stop suppressed (documented caveat). The benchmark year is reported beside and never selected on.\n")
    s.append("## Filters with the sealed brackets (ledger R, including positions held past 11:00 and the sealed `session_end` exits at the end of the New York calendar day)\n")
    frames = [(name, select(trades, name, gates)) for name in FILTERS]
    s += _period_tables(frames, years, "filter", "base")
    out = {"filters": frames}
    if replay is not None:
        n_checked = check_alignment(trades, replay)
        s.append(f"## Composites: filters x brackets (replayed, flat at 16:00)\n\nJoin check: the replayed sealed bracket equals the ledger R on all {n_checked} stop or target exits before 16:00. "
                 "Every composite is scored on the replayed entries (the replay drops entries without prior-session context for every variant), through the sequential pass with each replayed trade's own exit time: a longer hold blocks the entries it would have blocked, and the three-loss stop counts only outcomes that had printed.\n")
        comp = []
        for label, filt, variant in COMPOSITES:
            t = composite_frame(trades, replay, variant)
            comp.append((label, select(t, filt, gates)))
        s += _period_tables(comp, years, "composite", "the control")
        out["composites"] = comp
    return "\n".join(s), out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--replay-csv", default=None, help="private per-trade output of research/bracket_replay.py run on the same ledger and bars")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = load_trades(a.trades)
    rolls = sorted(roll_days(bars))
    if a.manifest:
        with open(a.manifest) as fh:
            m = json.load(fh)
        listed = sorted(pd.Timestamp(d).date() for d in m["data"]["roll_dates_excluded"])
        if listed != rolls:
            raise SystemExit(f"roll dates from bars ({len(rolls)}) differ from the manifest ({len(listed)}); refusing to report")
    trades, n_excl = exclude_roll_trades(trades, rolls)
    if a.manifest:
        expected = int(m["outputs"]["n_trades"]) - int(m["hygiene"]["trades_excluded"])
        if len(trades) != expected:
            raise SystemExit(f"analysed population {len(trades)} != sealed population {expected}; refusing to report")
    replay = pd.read_csv(a.replay_csv) if a.replay_csv else None
    try:
        text, _ = evaluate(trades, bars, a.oos_start, replay)
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    text = text.replace("# B2: reversion rules as stated, screened on the sealed ledger\n",
                        f"# B2: reversion rules as stated, screened on the sealed ledger\n\nData hygiene: {n_excl} trades on {len(rolls)} contract-roll dates excluded, as in the sealed report; population {len(trades)}.\n", 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
