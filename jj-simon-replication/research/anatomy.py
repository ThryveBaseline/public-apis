"""Anatomy of a sealed trade ledger: where the edge lives and where it is taxed away.

Reads a frozen `trades.csv` and the bars it was produced from, and reports, by period
(development / benchmark), setup, direction, grade, entry-time bucket, year and volatility
regime: win rate, expectancy, profit factor, maximum favourable and adverse excursion while
held, follow-through beyond the target through the rest of the day, how often losers nearly
reached the target before the stop, how close winners came to the stop, and the bracket
geometry relative to daily ATR and the opening range. Aggregates only; the per-trade
excursion table is written next to the report for private use.

Trades entered on contract-roll dates are excluded exactly as the sealed report excludes them
(the sealed trades.csv is written before that exclusion), so the period rows reproduce the
sealed in-sample and out-of-sample "all" rows.

usage: python research/anatomy.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv \
           --source-tz UTC --oos-start 2025-10-06 --manifest sealed/run1/manifest.json --out research/run1_anatomy.md
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from fpt.evaluate import volatility_regime  # noqa: E402
from fpt.indicators import atr as atr_fn  # noqa: E402

ENTRY_BUCKETS = [(570, 575, "09:30-09:35"), (575, 585, "09:35-09:45"), (585, 600, "09:45-10:00"),
                 (600, 630, "10:00-10:30"), (630, 660, "10:30-11:00"), (660, 10 ** 6, "after 11:00")]


def _ts(s: pd.Series) -> pd.Series:
    t = pd.to_datetime(s, utc=True)
    return t.dt.tz_convert(NY)


def load_trades(path: str) -> pd.DataFrame:
    t = pd.read_csv(path)
    for c in ("signal_time", "entry_time", "exit_time"):
        t[c] = _ts(t[c])
    t["direction"] = t["direction"].map(lambda v: 1 if str(v).lower() in ("1", "long", "buy", "1.0") else -1).astype(int)
    return t


def daily_context(bars: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Per Globex trade date (18:00 ET the evening before through 17:00 ET): daily ATR(period) in points
    from the full session, the session's last close, and the 09:30-09:35 opening range. A regular-hours
    entry's New York date equals its Globex date, so the trade join uses the New York date."""
    idx = bars.index.tz_convert(NY)
    naive = idx.tz_localize(None)
    sess = (naive + pd.Timedelta(hours=6)).normalize()  # 18:00 D-1 .. 17:00 D -> D; DST switches fall when Globex is closed
    g = pd.DataFrame({"high": bars["high"].to_numpy(), "low": bars["low"].to_numpy(), "close": bars["close"].to_numpy()}, index=sess).groupby(level=0)
    d = g.agg({"high": "max", "low": "min", "close": "last"})
    prev_close = d["close"].shift()
    tr = pd.concat([d["high"] - d["low"], (d["high"] - prev_close).abs(), (d["low"] - prev_close).abs()], axis=1).max(axis=1)
    d["daily_atr"] = tr.rolling(period, min_periods=period).mean().shift()  # the previous session's ATR is known at today's open
    d["prev_close"] = prev_close
    d["atr_pct"] = d["daily_atr"] / d["prev_close"]  # price-relative volatility, comparable across eras
    m = idx.hour * 60 + idx.minute
    sel = (m >= 570) & (m < 575)
    orng = pd.DataFrame({"high": bars["high"].to_numpy()[sel], "low": bars["low"].to_numpy()[sel]}, index=naive[sel].normalize()).groupby(level=0)
    d["opening_range"] = orng["high"].max() - orng["low"].min()
    return d[["daily_atr", "opening_range", "prev_close", "atr_pct"]]


def excursions(trades: pd.DataFrame, bars: pd.DataFrame, day_end: str = "16:00") -> pd.DataFrame:
    """Per trade: MFE and MAE in points while held (entry bar through exit bar), MFE from entry through
    the bar before `day_end` New York time or the exit bar, whichever is later, and the bars in the slice.

    The ledger resolves a bar that contains both the stop and the target as a stop (stop checked first),
    so a stop bar's favourable extreme and a target bar's adverse extreme are not counted: the exit level
    is taken to print first in its bar. Entry bars and session-end exits count in full."""
    hi = bars["high"].to_numpy(float)
    lo = bars["low"].to_numpy(float)
    idx = bars.index
    eh, em = (int(x) for x in day_end.split(":"))
    out = np.full((len(trades), 4), np.nan)
    reasons = trades["exit_reason"].astype(str) if "exit_reason" in trades.columns else pd.Series([""] * len(trades), index=trades.index)
    for k, (et, xt, d, entry, reason) in enumerate(zip(trades["entry_time"], trades["exit_time"], trades["direction"], trades["entry"].astype(float), reasons)):
        i0 = idx.searchsorted(et)
        i1 = idx.searchsorted(xt, side="right")
        if i0 >= len(idx) or i1 <= i0:
            continue
        h, l = hi[i0:i1], lo[i0:i1]
        j = i1 - 1 if reason in ("stop", "target") else i1
        hf, lf = (hi[i0:j], lo[i0:j]) if j > i0 else (np.array([entry]), np.array([entry]))
        hm, lm = (hf, lf) if reason == "stop" else (h, l)      # favourable side: drop the stop bar
        ha, la = (hf, lf) if reason == "target" else (h, l)    # adverse side: drop the target bar
        mfe = (hm.max() - entry) if d > 0 else (entry - lm.min())
        mae = (entry - la.min()) if d > 0 else (ha.max() - entry)
        end = et.tz_convert(NY).replace(hour=eh, minute=em, second=0, microsecond=0)
        i2 = idx.searchsorted(end, side="left")  # [entry, day_end) in bar-open time, as fpt.data.rth_mask
        stop_at = max(i2, i1)
        h2, l2 = hi[i0:stop_at], lo[i0:stop_at]
        mfe_day = (h2.max() - entry) if d > 0 else (entry - l2.min())
        out[k] = (mfe, mae, mfe_day, i1 - i0)
    e = pd.DataFrame(out, columns=["mfe_held", "mae_held", "mfe_day", "bars_in_slice"], index=trades.index)
    return e


def _pf(r: pd.Series) -> float:
    w = r[r > 0].sum()
    l = -r[r <= 0].sum()
    return float(w / l) if l > 0 else float("inf")


def bucket_table(t: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in t.groupby(by, sort=True, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        win = g["r"] > 0
        loss = ~win
        tgt = g["target_points"].astype(float)
        stp = g["stop_points"].astype(float)
        rows.append({
            **dict(zip(by, key)),
            "trades": int(len(g)),
            "win_rate": float(win.mean()),
            "expectancy_r": float(g["r"].mean()),
            "profit_factor": _pf(g["r"]),
            "mfe_held_med": float(g["mfe_held"].median()),
            "mae_held_med": float(g["mae_held"].median()),
            "winners_room_beyond_target_12pt": float((g.loc[win, "mfe_day"] >= tgt[win] + 12).mean()) if win.any() else float("nan"),
            "winners_room_2x_target": float((g.loc[win, "mfe_day"] >= 2 * tgt[win]).mean()) if win.any() else float("nan"),
            "winners_mae_ge_60pct_stop": float((g.loc[win, "mae_held"] >= 0.6 * stp[win]).mean()) if win.any() else float("nan"),
            "losers_mfe_ge_50pct_target": float((g.loc[loss, "mfe_held"] >= 0.5 * tgt[loss]).mean()) if loss.any() else float("nan"),
            "losers_mfe_ge_75pct_target": float((g.loc[loss, "mfe_held"] >= 0.75 * tgt[loss]).mean()) if loss.any() else float("nan"),
            "losers_mfe_ge_90pct_target": float((g.loc[loss, "mfe_held"] >= 0.9 * tgt[loss]).mean()) if loss.any() else float("nan"),
            "stop_over_daily_atr_med": float((stp / g["daily_atr"]).median()),
            "target_over_opening_range_med": float((tgt / g["opening_range"]).median()),
        })
    return pd.DataFrame(rows)


def _md(df: pd.DataFrame, cols: list[str]) -> str:
    fmt = {"win_rate": "{:.1%}", "expectancy_r": "{:+.3f}", "profit_factor": "{:.2f}", "mfe_held_med": "{:.1f}", "mae_held_med": "{:.1f}",
           "stop_over_daily_atr_med": "{:.2f}", "target_over_opening_range_med": "{:.2f}"}
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.to_dict("records"):
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float) and np.isnan(v):
                cells.append("n/a")
            elif c in fmt:
                cells.append(fmt[c].format(v))
            elif isinstance(v, float) and c.startswith(("winners_", "losers_")):
                cells.append(f"{v:.0%}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def exclude_roll_trades(trades: pd.DataFrame, exclude_dates) -> tuple[pd.DataFrame, int]:
    """Drop trades entered on the given New York dates, exactly as fpt.evaluate.evaluate_trades does."""
    excl = {pd.Timestamp(d).date() for d in (exclude_dates or [])}
    if not excl or trades.empty:
        return trades.reset_index(drop=True), 0
    dkey = trades["entry_time"].dt.tz_convert(NY).dt.date
    kept = trades[~dkey.isin(excl)].reset_index(drop=True)
    return kept, int(len(trades) - len(kept))


def anatomy(trades: pd.DataFrame, bars: pd.DataFrame, oos_start: str, day_end: str = "16:00", exclude_dates=None) -> tuple[str, pd.DataFrame]:
    t, n_excl = exclude_roll_trades(trades.copy(), exclude_dates)
    n_roll_dates = len({pd.Timestamp(d).date() for d in (exclude_dates or [])})
    if "target_points" not in t.columns:
        t["target_points"] = (t["target"].astype(float) - t["entry"].astype(float)).abs()
    ex = excursions(t, bars, day_end)
    t = pd.concat([t, ex], axis=1)
    ny = t["entry_time"].dt.tz_convert(NY)
    t["day"] = ny.dt.normalize().dt.tz_localize(None)
    t["year"] = ny.dt.year
    minute = ny.dt.hour * 60 + ny.dt.minute
    t["entry_bucket"] = pd.cut(minute, [b[0] for b in ENTRY_BUCKETS] + [10 ** 7], right=False, labels=[b[2] for b in ENTRY_BUCKETS]).astype(str)
    t["period"] = np.where(t["day"] < pd.Timestamp(oos_start), "development", "benchmark")
    ctx = daily_context(bars)
    t = t.join(ctx, on="day")
    reg = volatility_regime(bars, fit_through=pd.Timestamp(oos_start) - pd.Timedelta(days=1))
    t["regime"] = t["day"].map(reg).fillna("n/a")
    # price-relative regime: terciles of daily ATR / previous close over DEVELOPMENT days, applied to every day
    dev_days = ctx.loc[ctx.index < pd.Timestamp(oos_start), "atr_pct"].dropna()
    if len(dev_days):
        q1, q2 = dev_days.quantile([1 / 3, 2 / 3])
        t["rel_regime"] = t["atr_pct"].map(lambda v: "n/a" if pd.isna(v) else ("low" if v <= q1 else ("high" if v > q2 else "mid")))
    else:
        t["rel_regime"] = "n/a"
    t["outcome"] = np.where(t["r"] > 0, "win", "loss")

    base = ["trades", "win_rate", "expectancy_r", "profit_factor", "mfe_held_med", "mae_held_med",
            "winners_room_beyond_target_12pt", "winners_room_2x_target", "winners_mae_ge_60pct_stop",
            "losers_mfe_ge_50pct_target", "losers_mfe_ge_75pct_target", "losers_mfe_ge_90pct_target",
            "stop_over_daily_atr_med", "target_over_opening_range_med"]
    sections = []
    sections.append("# Anatomy of the sealed ledger\n")
    sections.append(f"Data hygiene: {n_excl} trades on {n_roll_dates} contract-roll dates excluded, as in the sealed report. Trades: {len(t)}; development {int((t['period']=='development').sum())}, benchmark {int((t['period']=='benchmark').sum())} (benchmark = entries on or after {oos_start}: the same window the sealed report calls out of sample, renamed because it has now been inspected; never used for selection).")
    sections.append("Excursions are in points from the entry price: `mfe_held`/`mae_held` over the bars from entry to exit, with a stop bar's favourable extreme and a target bar's adverse extreme left out (the ledger takes the exit level to print first); `winners_room_*` use the MFE from entry through the bar before " + day_end + " New York or the exit bar, whichever is later; `losers_mfe_*` is how far a losing trade went toward the target before stopping out; `winners_mae_*` is how close a winner came to the stop. `stop_over_daily_atr` uses the previous Globex session's 14-session ATR; `target_over_opening_range` uses the 09:30-09:35 range.\n")
    for title, by in [("By period", ["period"]), ("By period and setup", ["period", "setup"]), ("By period and direction", ["period", "direction"]),
                      ("By period and grade", ["period", "grade"]), ("By period and entry time", ["period", "entry_bucket"]),
                      ("By period and volatility regime in points (terciles fitted on development days; confounded with price level)", ["period", "regime"]),
                      ("By period and price-relative regime (daily ATR / previous close, terciles fitted on development days)", ["period", "rel_regime"]),
                      ("By period, setup and grade", ["period", "setup", "grade"]),
                      ("By period, setup and entry time", ["period", "setup", "entry_bucket"]),
                      ("By period, setup and price-relative regime", ["period", "setup", "rel_regime"]),
                      ("By year", ["year"]), ("By year and setup", ["year", "setup"]), ("By period, setup and exit reason", ["period", "setup", "exit_reason"])]:
        bt = bucket_table(t, by)
        sections.append(f"## {title}\n\n" + _md(bt, by + base) + "\n")
    # geometry drift by year: what 25/38 points meant each year
    geo = t.groupby("year").agg(daily_atr_med=("daily_atr", "median"), opening_range_med=("opening_range", "median"), price_med=("prev_close", "median"),
                                stop_pts=("stop_points", "median"), target_pts=("target_points", "median"), trades=("r", "size"))
    geo["stop_over_atr"] = geo["stop_pts"] / geo["daily_atr_med"]
    geo["target_over_or"] = geo["target_pts"] / geo["opening_range_med"]
    geo["stop_pct_price"] = geo["stop_pts"] / geo["price_med"]
    sections.append("## Bracket geometry by year\n\n| year | trades | median price | median daily ATR (pts) | median 09:30-09:35 range (pts) | stop pts | target pts | stop / daily ATR | target / opening range | stop as % of price |\n|---|---|---|---|---|---|---|---|---|---|")
    for y, r in geo.iterrows():
        sections.append(f"| {y} | {int(r['trades'])} | {r['price_med']:,.0f} | {r['daily_atr_med']:.0f} | {r['opening_range_med']:.1f} | {r['stop_pts']:.0f} | {r['target_pts']:.0f} | {r['stop_over_atr']:.3f} | {r['target_over_or']:.2f} | {r['stop_pct_price']:.3%} |")
    sections.append("")
    # excursion quantiles by outcome and period
    q = t.groupby(["period", "outcome"])[["mfe_held", "mae_held", "mfe_day"]].quantile([0.25, 0.5, 0.75]).unstack()
    sections.append("## Excursion quantiles (points) by period and outcome\n")
    sections.append("| period | outcome | mfe_held p25 | p50 | p75 | mae_held p25 | p50 | p75 | mfe_day p25 | p50 | p75 |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for (p, o), r in q.iterrows():
        vals = [r[("mfe_held", 0.25)], r[("mfe_held", 0.5)], r[("mfe_held", 0.75)], r[("mae_held", 0.25)], r[("mae_held", 0.5)], r[("mae_held", 0.75)], r[("mfe_day", 0.25)], r[("mfe_day", 0.5)], r[("mfe_day", 0.75)]]
        sections.append(f"| {p} | {o} | " + " | ".join(f"{v:.1f}" for v in vals) + " |")
    sections.append("")
    return "\n".join(sections), t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--day-end", default="16:00")
    ap.add_argument("--out", required=True)
    ap.add_argument("--private-out", default=None, help="per-trade excursion CSV (derivative data; keep out of public repos)")
    ap.add_argument("--manifest", default=None, help="sealed manifest.json; its data.roll_dates_excluded must equal the roll days derived from the bars")
    a = ap.parse_args()
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = load_trades(a.trades)
    rolls = sorted(roll_days(bars))
    if a.manifest:
        import json
        with open(a.manifest) as fh:
            listed = sorted(pd.Timestamp(d).date() for d in json.load(fh)["data"]["roll_dates_excluded"])
        if listed != rolls:
            raise SystemExit(f"roll dates from bars ({len(rolls)}) differ from the manifest ({len(listed)}); refusing to report")
    text, per_trade = anatomy(trades, bars, a.oos_start, a.day_end, exclude_dates=rolls)
    if a.manifest:
        with open(a.manifest) as fh:
            m = json.load(fh)
        expected = int(m["outputs"]["n_trades"]) - int(m["hygiene"]["trades_excluded"])
        if len(per_trade) != expected:
            raise SystemExit(f"analysed population {len(per_trade)} != sealed population {expected} (n_trades - trades_excluded); refusing to report")
        text = text.replace("as in the sealed report.", f"as in the sealed report; analysed population {len(per_trade)} equals the manifest's n_trades minus trades_excluded.", 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    if a.private_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.private_out)), exist_ok=True)
        per_trade.to_csv(a.private_out, index=False)
    print(text[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
