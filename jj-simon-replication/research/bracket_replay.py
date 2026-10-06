"""B1: bracket replay on frozen entries.

Every entry in a sealed ledger (time, fill price, direction, setup, grade) is kept exactly as sealed, and
the bars from the entry bar through the last bar before 16:00 New York are replayed under a pre-registered
grid of stop/target brackets. This isolates bracket geometry from signal quality. The frozen fill and cost
model is reproduced: the ledger's `entry` already contains entry slippage; a stop fills at the stop level
less slippage, a target fills exactly, a flat at 16:00 fills at the 15:59 bar's close less slippage; the
stop is checked before the target within a bar, and a bar containing both is a stop, flagged ambiguous;
commission is a flat round trip; R = (points x point value - commission) / (stop points x point value),
which does not depend on the contract count.

Caveat, stated in the report: replaying entries one at a time ignores sequencing (a longer hold would have
blocked later entries, and the three-consecutive-loss stop would fire differently). Shortlisted brackets go
to full re-simulation on the research branch.

Grid (pre-registered, see docs/RESEARCH_PLAN.md):
  ledger bracket (control: each trade's own sealed stop and target, so the replay can be checked against the ledger);
  fixed 25/38 (the evaluation bracket applied to every entry, including the sealed 50/75 wide-open trades);
  ATR family: stop = k x previous Globex session's 14-session daily ATR, k in {0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30},
              reward-to-risk in {1.0, 1.52, 2.0};
  opening-range family: stop = k x the PREVIOUS session's 09:30-09:35 range (known at entry), k in {0.25, 0.5, 0.75, 1.0, 1.5, 2.0}, RR 1.52;
  price family: stop = y x entry price, y in {0.05%, 0.10%, 0.15%, 0.20%, 0.30%}, RR 1.52.
Stops are rounded to the 0.25 tick and floored at 2 points.

usage: python research/bracket_replay.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv \
           --source-tz UTC --oos-start 2025-10-06 --manifest sealed/run1/manifest.json \
           --out research/run1_bracket_replay.md --private-out research/private/run1_bracket_replay.csv
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
from research.anatomy import daily_context, exclude_roll_trades, load_trades  # noqa: E402

POINT_VALUE = 20.0
COMMISSION_RT = 2.0 * 2.50
SLIPPAGE = 0.25
TICK = 0.25
MIN_STOP = 2.0
FIXED_STOP, FIXED_TARGET = 25.0, 38.0
RR_FIXED = FIXED_TARGET / FIXED_STOP

ATR_K = (0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)
OR_K = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
PRICE_Y = (0.0005, 0.0010, 0.0015, 0.0020, 0.0030)


def grid() -> list[dict]:
    g = [{"name": "ledger_bracket", "family": "ledger", "k": None, "rr": None},  # control: each trade's own sealed stop and target
         {"name": "fixed_25_38", "family": "fixed", "k": None, "rr": RR_FIXED}]
    for rr in (1.0, RR_FIXED, 2.0):
        for k in ATR_K:
            g.append({"name": f"atr_{k:g}_rr{rr:.2f}", "family": "atr", "k": k, "rr": rr})
    for k in OR_K:
        g.append({"name": f"or_{k:g}_rr{RR_FIXED:.2f}", "family": "or_prev", "k": k, "rr": RR_FIXED})
    for y in PRICE_Y:
        g.append({"name": f"px_{y * 100:.2f}pct_rr{RR_FIXED:.2f}", "family": "price", "k": y, "rr": RR_FIXED})
    return g


def _round_tick(x: float) -> float:
    return max(MIN_STOP, float(np.round(x / TICK) * TICK))


def stop_points_for(variant: dict, daily_atr: float, or_prev: float, entry: float) -> float:
    f = variant["family"]
    if f == "fixed":
        return FIXED_STOP
    if f == "ledger":
        raise ValueError("ledger bracket is resolved per trade in replay()")
    if f == "atr":
        base = daily_atr
    elif f == "or_prev":
        base = or_prev
    elif f == "price":
        base = entry
    else:
        raise ValueError(f)
    if base is None or not np.isfinite(base) or base <= 0:
        return float("nan")
    return _round_tick(variant["k"] * base)


def replay_one(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, d: int, entry: float, stop_pts: float, target_pts: float) -> tuple:
    """First-touch replay over the slice (entry bar first). Returns (exit_price, reason, bars_held, ambiguous)."""
    if d > 0:
        stop, target = entry - stop_pts, entry + target_pts
        hit_stop = l <= stop
        hit_tgt = h >= target
    else:
        stop, target = entry + stop_pts, entry - target_pts
        hit_stop = h >= stop
        hit_tgt = l <= target
    i_s = int(np.argmax(hit_stop)) if hit_stop.any() else -1
    i_t = int(np.argmax(hit_tgt)) if hit_tgt.any() else -1
    if i_s >= 0 and (i_t < 0 or i_s <= i_t):
        return stop - d * SLIPPAGE, "stop", i_s + 1, bool(i_t == i_s)
    if i_t >= 0:
        return target, "target", i_t + 1, False
    n = len(c)
    return c[n - 1] - d * SLIPPAGE, "flat_1600", n, False


def r_of(exit_price: float, entry: float, d: int, stop_pts: float) -> float:
    pnl_points = (exit_price - entry) * d
    return (pnl_points * POINT_VALUE - COMMISSION_RT) / (stop_pts * POINT_VALUE)


def replay(trades: pd.DataFrame, bars: pd.DataFrame, variants: list[dict], day_end: str = "16:00") -> pd.DataFrame:
    o = bars["open"].to_numpy(float)
    h = bars["high"].to_numpy(float)
    l = bars["low"].to_numpy(float)
    c = bars["close"].to_numpy(float)
    idx = bars.index
    eh, em = (int(x) for x in day_end.split(":"))
    ctx = daily_context(bars)
    ctx["or_prev"] = ctx["opening_range"].shift()
    ny = trades["entry_time"].dt.tz_convert(NY)
    day = ny.dt.normalize().dt.tz_localize(None)
    atr = day.map(ctx["daily_atr"]).to_numpy(float)
    orp = day.map(ctx["or_prev"]).to_numpy(float)
    ok = np.isfinite(atr) & np.isfinite(orp)
    led_stop = trades["stop_points"].astype(float).to_numpy() if "stop_points" in trades.columns else np.full(len(trades), FIXED_STOP)
    led_tgt = (trades["target"].astype(float) - trades["entry"].astype(float)).abs().to_numpy() if "target" in trades.columns else led_stop * RR_FIXED
    n_no_context = 0
    rows = []
    for k, (et, d, entry) in enumerate(zip(trades["entry_time"], trades["direction"].astype(int), trades["entry"].astype(float))):
        i0 = idx.searchsorted(et)
        if i0 >= len(idx) or idx[i0] != et:
            continue  # entry bar missing from the bars: the ledger and the bars disagree; skipped and counted by main()
        if not ok[k]:
            n_no_context += 1
            continue  # no previous-session ATR (first 14 sessions) or opening range: dropped for EVERY variant so all tables score the same trades
        end = et.tz_convert(NY).replace(hour=eh, minute=em, second=0, microsecond=0)
        i2 = idx.searchsorted(end, side="left")
        if i2 <= i0:
            i2 = i0 + 1  # entered at or after day_end: the entry bar alone
        so, sh, sl, sc = o[i0:i2], h[i0:i2], l[i0:i2], c[i0:i2]
        for v in variants:
            if v["family"] == "ledger":
                sp, tp = float(led_stop[k]), float(led_tgt[k])
            else:
                sp = stop_points_for(v, atr[k], orp[k], entry)
                tp = _round_tick(sp * v["rr"])
            xp, reason, held, amb = replay_one(so, sh, sl, sc, d, entry, sp, tp)
            rows.append((k, v["name"], v["family"], sp, tp, xp, reason, held, amb, r_of(xp, entry, d, sp)))
    out = pd.DataFrame(rows, columns=["trade", "variant", "family", "stop_pts", "target_pts", "exit", "exit_reason", "bars_held", "ambiguous", "r"])
    out.attrs["n_no_context"] = n_no_context
    return out


def _pf(r: pd.Series) -> float:
    w = r[r > 0].sum()
    lo = -r[r <= 0].sum()
    return float(w / lo) if lo > 0 else float("inf")


def summarize(rep: pd.DataFrame, meta: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    df = rep.join(meta, on="trade")
    rows = []
    for key, g in df.groupby(["variant"] + by, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        rows.append({"variant": key[0], **dict(zip(by, key[1:])), "trades": int(len(g)), "win_rate": float((g["r"] > 0).mean()),
                     "expectancy_r": float(g["r"].mean()), "profit_factor": _pf(g["r"]), "ambiguous": int(g["ambiguous"].sum()),
                     "mean_bars": float(g["bars_held"].mean()), "stop_pts_med": float(g["stop_pts"].median())})
    out = pd.DataFrame(rows)
    if len(out):
        order = {v["name"]: i for i, v in enumerate(grid())}
        out = out.sort_values(by=["variant"] + by, key=lambda col: col.map(order) if col.name == "variant" else col, kind="stable").reset_index(drop=True)
    return out


def walk_forward(rep: pd.DataFrame, meta: pd.DataFrame, years: list[int], families: dict[str, list[str]]) -> tuple[pd.DataFrame, list[str]]:
    """Expectancy by development year per variant, and the sequential chain: for each year Y (from the fourth
    development year on), the variant with the best mean expectancy over years < Y is chosen and its year-Y
    expectancy is recorded. Reported per family and over the whole grid, against the fixed bracket."""
    df = rep.join(meta, on="trade")
    df = df[df["period"] == "development"]
    piv = df.groupby(["variant", "year"])["r"].mean().unstack("year").reindex(columns=years)
    cnt = df.groupby(["variant", "year"])["r"].size().unstack("year").reindex(columns=years)
    lines = []
    fixed = piv.loc["ledger_bracket"] if "ledger_bracket" in piv.index else None
    for fam, names in families.items():
        sub = piv.loc[[n for n in names if n in piv.index]]
        chain = []
        for j, y in enumerate(years):
            if j < 3:
                continue
            prior = sub.iloc[:, :j].mean(axis=1)
            if sub.empty or prior.isna().all():
                continue
            best = prior.idxmax()
            chain.append((y, best, float(sub.loc[best, y]) if pd.notna(sub.loc[best, y]) else float("nan"), float(fixed[y]) if fixed is not None and pd.notna(fixed[y]) else float("nan"), int(cnt.loc[best, y]) if pd.notna(cnt.loc[best, y]) else 0))
        if not chain:
            continue
        ch = pd.DataFrame(chain, columns=["year", "chosen_on_prior_years", "expectancy_r_in_year", "ledger_bracket_in_year", "trades"])
        w = ch["trades"].to_numpy(float)
        tot = float(np.nansum(ch["expectancy_r_in_year"] * w) / w.sum()) if w.sum() else float("nan")
        tot_f = float(np.nansum(ch["ledger_bracket_in_year"] * w) / w.sum()) if w.sum() else float("nan")
        lines.append(f"### Sequential walk-forward, family `{fam}`\n")
        lines.append("| year | chosen on prior years | expectancy R in year | sealed bracket in year | trades |\n|---|---|---|---|---|")
        for _, r in ch.iterrows():
            lines.append(f"| {int(r['year'])} | {r['chosen_on_prior_years']} | {r['expectancy_r_in_year']:+.3f} | {r['fixed_25_38_in_year']:+.3f} | {int(r['trades'])} |")
        lines.append(f"\nTrade-weighted out-of-year expectancy of the chain: {tot:+.3f} R against {tot_f:+.3f} R for the sealed bracket (each trade's own stop and target, flat at 16:00) over the same years.\n")
    return piv, lines


def _fmt_table(df: pd.DataFrame, cols: list[str]) -> str:
    fmt = {"win_rate": "{:.1%}", "expectancy_r": "{:+.3f}", "profit_factor": "{:.2f}", "mean_bars": "{:.1f}", "stop_pts_med": "{:.2f}"}
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.to_dict("records"):
        out.append("| " + " | ".join(fmt.get(c, "{}").format(r[c]) if not (isinstance(r[c], float) and np.isnan(r[c])) else "n/a" for c in cols) + " |")
    return "\n".join(out)


def report(trades: pd.DataFrame, rep: pd.DataFrame, oos_start: str, n_excl: int, n_roll: int, n_skipped: int, n_no_context: int = 0) -> str:
    ny = trades["entry_time"].dt.tz_convert(NY)
    xt = trades["exit_time"].dt.tz_convert(NY)
    meta = pd.DataFrame({"period": np.where(ny.dt.normalize().dt.tz_localize(None) < pd.Timestamp(oos_start), "development", "benchmark"),
                         "year": ny.dt.year.to_numpy(), "setup": trades["setup"].astype(str).to_numpy(),
                         "ledger_r": trades["r"].astype(float).to_numpy(), "ledger_reason": trades["exit_reason"].astype(str).to_numpy(),
                         "ledger_stop": trades["stop_points"].astype(float).to_numpy() if "stop_points" in trades.columns else np.full(len(trades), FIXED_STOP),
                         "exit_before_end": ((xt.dt.hour * 60 + xt.dt.minute) < 16 * 60).to_numpy()}, index=trades.index)
    s = ["# B1: bracket replay on frozen entries\n"]
    s.append(f"Data hygiene: {n_excl} trades on {n_roll} contract-roll dates excluded, as in the sealed report; {n_skipped} entries skipped because their entry bar is not in the bars; {n_no_context} entries dropped for every variant because the previous session's 14-session ATR or opening range is undefined (the first sessions of the data), so every variant including the controls is scored on the same {trades.index.size - n_skipped - n_no_context} entries. Period split at {oos_start} (development / benchmark; the benchmark is the sealed out-of-sample year, now inspected, reported beside and never selected on).")
    s.append("Replay ignores sequencing between trades (documented caveat); brackets are per the pre-registered grid in the module docstring; costs as sealed; same-bar stop and target resolved as a stop and counted as ambiguous; positions flat at the last bar before 16:00 New York.\n")
    # reproduction check: the ledger-bracket control must reproduce every ledger stop/target fill that printed before 16:00
    fx = rep[rep["variant"] == "ledger_bracket"].join(meta, on="trade")
    st = fx["ledger_reason"].isin(["stop", "target"])
    late = st & ~fx["exit_before_end"]
    same = fx[st & fx["exit_before_end"]]
    agree = float((same["exit_reason"] == same["ledger_reason"]).mean()) if len(same) else float("nan")
    rdiff = float((same["r"] - same["ledger_r"]).abs().max()) if len(same) else float("nan")
    se = fx["ledger_reason"] == "session_end"
    se_led = float(fx.loc[se, "ledger_r"].mean()) if se.any() else float("nan")
    se_rep = float(fx.loc[se, "r"].mean()) if se.any() else float("nan")
    n_wide = int((meta["ledger_stop"] != FIXED_STOP).sum())
    s.append("## Reproduction check, ledger bracket\n\n"
             f"On the {len(same)} ledger trades that exited at the stop or the target before 16:00 New York, replaying each trade's own stop and target reaches the same exit reason on {agree:.2%} and the largest absolute R difference is {rdiff:.4f} (both must be 100% and 0 for the replay to be trusted). "
             f"Left out of the check: {int(late.sum())} stop or target fills printed at or after 16:00 (flat at 16:00 in the replay by design) and {int(se.sum())} ledger `session_end` trades (ledger mean R {se_led:+.3f}, replay mean R {se_rep:+.3f}). "
             f"The fixed 25/38 variant applies the evaluation bracket to every entry, including the {n_wide} sealed wide-open trades that carried 50/75.\n")
    cols = ["variant", "trades", "win_rate", "expectancy_r", "profit_factor", "ambiguous", "mean_bars", "stop_pts_med"]
    for per in ("development", "benchmark"):
        t = summarize(rep[rep["trade"].isin(meta.index[meta["period"] == per])], meta, [])
        s.append(f"## All entries, {per}\n\n" + _fmt_table(t, cols) + "\n")
        for setup in sorted(meta["setup"].unique()):
            sel = meta.index[(meta["period"] == per) & (meta["setup"] == setup)]
            t = summarize(rep[rep["trade"].isin(sel)], meta, [])
            s.append(f"## {setup}, {per}\n\n" + _fmt_table(t, cols) + "\n")
    years = sorted(int(y) for y in meta.loc[meta["period"] == "development", "year"].unique())
    fams = {"all": [v["name"] for v in grid()], "atr": [v["name"] for v in grid() if v["family"] == "atr"],
            "or_prev": [v["name"] for v in grid() if v["family"] == "or_prev"], "price": [v["name"] for v in grid() if v["family"] == "price"]}
    for setup_label, sel in [("all setups", meta.index), ("continuation", meta.index[meta["setup"] == "continuation"]), ("reversion", meta.index[meta["setup"] == "reversion"])]:
        piv, lines = walk_forward(rep[rep["trade"].isin(sel)], meta, years, fams)
        s.append(f"## Development years, {setup_label}: expectancy R by year and variant\n")
        head = "| variant | " + " | ".join(str(y) for y in years) + " | mean | years > 0 |\n|---|" + "---|" * (len(years) + 2)
        body = []
        for name, row in piv.iterrows():
            vals = row.reindex(years)
            body.append(f"| {name} | " + " | ".join("n/a" if pd.isna(v) else f"{v:+.3f}" for v in vals) + f" | {np.nanmean(vals):+.3f} | {int((vals > 0).sum())}/{int(vals.notna().sum())} |")
        s.append(head + "\n" + "\n".join(body) + "\n")
        s.extend(lines)
    return "\n".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--private-out", default=None)
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
    rep = replay(trades, bars, grid())
    n_no_context = int(rep.attrs.get("n_no_context", 0))
    n_skipped = int(trades.index.size - rep["trade"].nunique()) - n_no_context
    text = report(trades, rep, a.oos_start, n_excl, len(rolls), n_skipped, n_no_context)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    if a.private_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.private_out)), exist_ok=True)
        rep.to_csv(a.private_out, index=False)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
