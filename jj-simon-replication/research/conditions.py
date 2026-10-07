"""Research step 4: conditional edge, exactly as pre-registered in docs/research/preregistration_conditional_edge.md
(registered in commit c0c7a15, before this tool existed and before any of these splits was computed).

Nine one-sided hypotheses on the sealed entries the B2 replay covers, outcome the sealed bracket replayed and flat at
16:00 (`ledger_bracket`): H1-H6 on continuation (every grade), H7-H9 on reversion A+. Context comes only from what is
known before the entry (session_context); continuous conditions split at walk-forward medians from earlier
development years; each test is the development difference in mean R, favoured minus other side, with day-clustered
standard errors, a one-sided normal p-value, Holm's step-down across all nine at 0.05, and year consistency. A
condition passes only if Holm-significant and positive in at least 60% of eligible development years. The benchmark
year is reported beside and never used. The report carries the sha256 of the registration file it implements.

Gates: the trades and bars are the sealed run's (sha256 against the manifest), roll dates and population as sealed,
and the replay file aligns with the ledger (research/ledger_filters.check_alignment).

usage: python research/conditions.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv --source-tz UTC \
           --oos-start 2025-10-06 --manifest sealed/run1/manifest.json --replay-csv research/private/run1_bracket_replay_b2.csv \
           --registration docs/research/preregistration_conditional_edge.md --out research/staging/run1_conditions.md \
           [--private-out research/private/run1_conditions.csv]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from research.anatomy import daily_context, exclude_roll_trades, load_trades  # noqa: E402
from research.candidates import hold_drift, mean_se, ny_day, sha256, variant_frame  # noqa: E402
from research.ledger_filters import check_alignment  # noqa: E402

ALPHA, MIN_YEAR_SIDE, CONSISTENCY = 0.05, 10, 0.60
HYPOTHESES = [  # id, population, condition, favoured side (as registered)
    ("H1", "continuation", "trend", "with the 20-session trend"),
    ("H2", "continuation", "overnight move", "continuing the overnight move"),
    ("H3", "continuation", "opening candle", "body / ATR at or above its walk-forward median"),
    ("H4", "continuation", "overnight compression", "overnight range / ATR at or below its walk-forward median"),
    ("H5", "continuation", "open outside the prior session", "open beyond the prior session's extreme in the trade's direction"),
    ("H6", "continuation", "extension at the signal", "distance from fair value / ATR at or below its walk-forward median"),
    ("H7", "reversion A+", "room to fair value", "distance from fair value / ATR at or above its walk-forward median"),
    ("H8", "reversion A+", "trend", "with the 20-session trend"),
    ("H9", "reversion A+", "gap fill", "trading back across the overnight move"),
]


def session_context(bars: pd.DataFrame) -> pd.DataFrame:
    """Per Globex session D (18:00 on D-1 to 17:00 on D, keyed by D as a naive date), only what is known before D's
    09:31: atr (daily ATR(14) through D-1), prev_close / prev_high / prev_low (the session ending on D-1), open and
    body of D's 09:30 bar, overnight_range (D's bars before 09:30) and trend20 (sign of prev_close minus the close
    of the session 20 sessions before D-1)."""
    idx = bars.index.tz_convert(NY)
    naive = idx.tz_localize(None)
    sess = (naive + pd.Timedelta(hours=6)).normalize()
    b = pd.DataFrame({"sess": sess, "naive": naive, "open": bars["open"].to_numpy(float), "high": bars["high"].to_numpy(float),
                      "low": bars["low"].to_numpy(float), "close": bars["close"].to_numpy(float)})
    d = b.groupby("sess").agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    out = pd.DataFrame(index=d.index)
    out["atr"] = daily_context(bars)["daily_atr"].reindex(d.index)
    out["prev_close"], out["prev_high"], out["prev_low"] = d["close"].shift(), d["high"].shift(), d["low"].shift()
    first = b[(b["naive"] - b["sess"]) == pd.Timedelta(hours=9, minutes=30)].set_index("sess")
    out["open"] = first["open"].reindex(d.index)
    out["body"] = (first["close"] - first["open"]).abs().reindex(d.index)
    pre = b[b["naive"] < b["sess"] + pd.Timedelta(hours=9, minutes=30)].groupby("sess")
    out["overnight_range"] = (pre["high"].max() - pre["low"].min()).reindex(d.index)
    out["trend20"] = np.sign(out["prev_close"] - out["prev_close"].shift(20))
    return out


def walk_forward_threshold(values: pd.Series, year: pd.Series, dev: pd.Series, labels: pd.Series) -> pd.Series:
    """The registered threshold for each element of `labels` ('2011', ..., 'benchmark'): the median of `values` over
    development elements of earlier years (all development years for the benchmark); NaN for the first year."""
    v = pd.DataFrame({"v": values.to_numpy(float), "year": year.to_numpy(int), "dev": dev.to_numpy(bool)}).dropna(subset=["v"])
    v = v[v["dev"]]
    cache = {}
    for lab in labels.unique():
        upto = v if lab == "benchmark" else v[v["year"] < int(lab)]
        cache[lab] = float(upto["v"].median()) if len(upto) else float("nan")
    return labels.map(cache).astype(float)


def trade_frame(trades: pd.DataFrame, bars: pd.DataFrame, replay: pd.DataFrame, cut: pd.Timestamp, rolls) -> pd.DataFrame:
    """One row per replayed entry: population, period, year, label, outcome R, the registered context and the
    favoured flag of each hypothesis (NaN where the registered quantity is undefined)."""
    replayed = sorted(set(int(x) for x in replay.loc[replay["variant"] != "_dropped", "trade"]))
    t = trades.loc[replayed]
    day = ny_day(t)
    ctx = session_context(bars)
    c = ctx.reindex(day.to_numpy())
    c.index = t.index
    f = pd.DataFrame(index=t.index)
    setup, grade = t["setup"].astype(str), t["grade"].astype(str)
    f["population"] = np.where(setup == "continuation", "continuation", np.where(grade == "A+", "reversion A+", "other"))
    f["day"] = day.to_numpy()
    f["period"] = np.where(day <= cut, "development", "benchmark")
    f["year"] = day.dt.year.to_numpy()
    f["label"] = np.where(f["period"] == "development", f["year"].astype(str), "benchmark")
    f["direction"] = t["direction"].astype(int).to_numpy()
    f["r"] = variant_frame(t, replay, pd.Series("ledger_bracket", index=t.index))["r"].to_numpy()
    for k in ("atr", "prev_close", "prev_high", "prev_low", "open", "body", "overnight_range", "trend20"):
        f[k] = c[k].to_numpy(float)
    atr = f["atr"].where(f["atr"] > 0)
    gap = f["open"] - f["prev_close"]
    f["gap"] = gap
    f["body_atr"] = f["body"] / atr
    f["overnight_atr"] = f["overnight_range"] / atr
    f["ext_atr"] = t["distance_from_fv"].astype(float).abs().to_numpy() / atr
    d = f["direction"]

    def flag(ok, fav):
        return pd.Series(np.where(ok, fav, np.nan), index=f.index)
    trend_ok = f["trend20"].isin([-1.0, 1.0])
    gap_ok = gap.notna() & (gap != 0)
    f["H1"] = flag(trend_ok, d == f["trend20"])
    f["H2"] = flag(gap_ok, d == np.sign(gap))
    # day-level walk-forward thresholds: every trading day with a 09:30 bar and an ATR, development days only
    days = ctx[ctx["open"].notna() & (ctx["atr"] > 0)]
    dev_day = pd.Series(days.index <= cut, index=days.index)
    lab = f["label"]
    thr_body = walk_forward_threshold((days["body"] / days["atr"]), pd.Series(days.index.year, index=days.index), dev_day, lab)
    thr_on = walk_forward_threshold((days["overnight_range"] / days["atr"]), pd.Series(days.index.year, index=days.index), dev_day, lab)
    f["H3"] = flag(f["body_atr"].notna() & thr_body.notna(), f["body_atr"] >= thr_body)
    f["H4"] = flag(f["overnight_atr"].notna() & thr_on.notna(), f["overnight_atr"] <= thr_on)
    out_ok = f[["open", "prev_high", "prev_low"]].notna().all(axis=1)
    f["H5"] = flag(out_ok, ((d > 0) & (f["open"] > f["prev_high"])) | ((d < 0) & (f["open"] < f["prev_low"])))
    for h, pop, fav_above in (("H6", "continuation", False), ("H7", "reversion A+", True)):
        m = f["population"] == pop
        sub = f.loc[m]
        thr = walk_forward_threshold(sub["ext_atr"], sub["year"], sub["period"] == "development", lab[m])
        ok = (sub["ext_atr"].notna() & thr.notna()).to_numpy()
        fav = ((sub["ext_atr"] >= thr) if fav_above else (sub["ext_atr"] <= thr)).to_numpy(float)
        f[h] = np.nan
        f[f"{h}_threshold"] = np.nan
        f.loc[m, h] = np.where(ok, fav, np.nan)
        f.loc[m, f"{h}_threshold"] = thr.to_numpy(float)
    f["H8"] = f["H1"]
    f["H9"] = flag(gap_ok, d == -np.sign(gap))
    f["thr_body"], f["thr_overnight"] = thr_body, thr_on
    # descriptive only: volatility terciles (ATR / previous close) fitted on every development trading day
    q = (days.loc[dev_day.to_numpy(), "atr"] / days.loc[dev_day.to_numpy(), "prev_close"]).quantile([1 / 3, 2 / 3]).to_numpy()
    pct = f["atr"] / f["prev_close"]
    f["vol_tier"] = np.select([pct <= q[0], pct <= q[1], pct > q[1]], ["low", "mid", "high"], default="n/a")
    return f


def one_sided_p(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2.0)) if np.isfinite(z) else float("nan")


def holm(p: list[float]) -> list[float]:
    """Holm's step-down adjusted p-values over the whole registered family: a test that could not be computed
    still counts toward the family size (ranked last, as p = 1) and is reported as NaN."""
    m = len(p)
    order = sorted(range(m), key=lambda i: p[i] if np.isfinite(p[i]) else 2.0)
    out, running = [float("nan")] * m, 0.0
    for rank, i in enumerate(order):
        if not np.isfinite(p[i]):
            continue
        running = max(running, min(1.0, (m - rank) * p[i]))
        out[i] = running
    return out


def evaluate_hypothesis(f: pd.DataFrame, h: str, pop: str) -> dict:
    """The registered statistic for one hypothesis: development difference in mean R, favoured minus other, with
    day-clustered standard errors per side, one-sided p, year consistency; the benchmark beside."""
    g = f[(f["population"] == pop) & f[h].notna()]
    res = {}
    for per in ("development", "benchmark"):
        p = g[g["period"] == per]
        fav, oth = p[p[h] == 1.0], p[p[h] == 0.0]
        nf, mf, sf = mean_se(fav["r"], fav["day"])
        no, mo, so = mean_se(oth["r"], oth["day"])
        delta = mf - mo
        se = math.sqrt(sf ** 2 + so ** 2) if np.isfinite(sf) and np.isfinite(so) else float("nan")
        res[per] = {"n_fav": nf, "r_fav": mf, "n_oth": no, "r_oth": mo, "delta": delta, "se": se}
    dev = res["development"]
    dev["p"] = one_sided_p(dev["delta"] / dev["se"]) if dev["se"] and np.isfinite(dev["se"]) and dev["se"] > 0 else float("nan")
    d = g[g["period"] == "development"]
    pos = n = 0
    for _, y in d.groupby("year"):
        a, b = y[y[h] == 1.0]["r"], y[y[h] == 0.0]["r"]
        if len(a) >= MIN_YEAR_SIDE and len(b) >= MIN_YEAR_SIDE:
            n += 1
            pos += int(a.mean() > b.mean())
    dev["years_pos"], dev["years_n"] = pos, n
    return res


def secondary(f: pd.DataFrame, h: str, excess_atr: pd.Series) -> dict:
    """Continuation only: the hold-minus-drift per daily ATR on each side, per period (reported, not tested)."""
    g = f[(f["population"] == "continuation") & f[h].notna()].join(excess_atr.rename("excess_atr"))
    out = {}
    for per in ("development", "benchmark"):
        p = g[g["period"] == per]
        out[per] = tuple(mean_se(p[p[h] == v]["excess_atr"], p[p[h] == v]["day"])[1] for v in (1.0, 0.0))
    return out


def report(f: pd.DataFrame, excess_atr: pd.Series, registration_sha: str, gate_note: str) -> tuple[str, list[dict]]:
    rows = []
    for h, pop, cond, fav in HYPOTHESES:
        res = evaluate_hypothesis(f, h, pop)
        rows.append({"id": h, "pop": pop, "cond": cond, "fav": fav, **{f"dev_{k}": v for k, v in res["development"].items()},
                     **{f"bm_{k}": v for k, v in res["benchmark"].items()}})
    adj = holm([r["dev_p"] for r in rows])
    for r, a in zip(rows, adj):
        r["holm"] = a
        cons = r["dev_years_pos"] / r["dev_years_n"] if r["dev_years_n"] else float("nan")
        r["passes"] = bool(np.isfinite(a) and a <= ALPHA and r["dev_delta"] > 0 and np.isfinite(cons) and cons >= CONSISTENCY)
    s = ["# Conditional edge: the pre-registered tests (research step 4)\n", gate_note, "",
         f"Implements docs/research/preregistration_conditional_edge.md as registered in commit c0c7a15 (sha256 of the registration file read: {registration_sha}). "
         "Outcome: R of the sealed bracket replayed, flat at 16:00. Each test is the development difference in mean R, favoured minus other side, with day-clustered standard errors, "
         f"a one-sided normal p-value and Holm's step-down across all nine at {ALPHA}; a condition passes only if Holm-significant and positive in at least {CONSISTENCY:.0%} of the development years "
         f"with at least {MIN_YEAR_SIDE} trades on each side. The benchmark year is reported beside and never used.\n",
         "## Tests\n",
         "| id | population | condition (favoured side) | development: favoured n, R | other n, R | difference (se) | p | Holm p | years positive | passes | benchmark: favoured n, R | other n, R | difference |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        s.append(f"| {r['id']} | {r['pop']} | {r['cond']} ({r['fav']}) | {r['dev_n_fav']}, {r['dev_r_fav']:+.3f} | {r['dev_n_oth']}, {r['dev_r_oth']:+.3f} | "
                 f"{r['dev_delta']:+.3f} ({r['dev_se']:.3f}) | {r['dev_p']:.4f} | {r['holm']:.4f} | {r['dev_years_pos']} of {r['dev_years_n']} | {'yes' if r['passes'] else 'no'} | "
                 f"{r['bm_n_fav']}, {r['bm_r_fav']:+.3f} | {r['bm_n_oth']}, {r['bm_r_oth']:+.3f} | {r['bm_delta']:+.3f} |")
    s.append("")
    passing = [r["id"] for r in rows if r["passes"]]
    s.append(f"Passing conditions: {', '.join(passing) if passing else 'none'}. Per the registration, a passing condition becomes a candidate filter (B3 firm scoring on its favoured side, then re-simulation); a failing one is dropped and not re-cut on these data.\n")
    s.append("## Secondary outcome, continuation: hold to 16:00 minus the drift, per daily ATR (reported, not tested)\n")
    s.append("| id | development: favoured | other | benchmark: favoured | other |\n|---|---|---|---|---|")
    for h, pop, cond, _ in HYPOTHESES:
        if pop != "continuation":
            continue
        sec = secondary(f, h, excess_atr)
        s.append(f"| {h} | {sec['development'][0]:+.4f} | {sec['development'][1]:+.4f} | {sec['benchmark'][0]:+.4f} | {sec['benchmark'][1]:+.4f} |")
    s.append("")
    s.append("## Thresholds used (walk-forward medians from earlier development years; the benchmark uses all development years)\n")
    s.append("| label | body / ATR (H3) | overnight range / ATR (H4) | extension / ATR, continuation (H6) | room / ATR, reversion A+ (H7) |\n|---|---|---|---|---|")
    for lab, g in f.groupby("label", sort=True):
        def first(col, pop=None):
            x = g if pop is None else g[g["population"] == pop]
            v = x[col].dropna()
            return f"{v.iloc[0]:.3f}" if len(v) else "n/a"
        s.append(f"| {lab} | {first('thr_body')} | {first('thr_overnight')} | {first('H6_threshold', 'continuation')} | {first('H7_threshold', 'reversion A+')} |")
    s.append("")
    s.append("## Volatility regime, descriptive only (seen in the anatomy, not tested)\n")
    s.append("Daily ATR as a share of the previous close, terciles fitted on all development trading days.\n")
    tier = f["vol_tier"]
    s.append("| population | period | low: n, R | mid: n, R | high: n, R |\n|---|---|---|---|---|")
    for pop in ("continuation", "reversion A+"):
        for per in ("development", "benchmark"):
            m = (f["population"] == pop) & (f["period"] == per)
            cells = []
            for tname in ("low", "mid", "high"):
                x = f.loc[m & (tier == tname), "r"]
                cells.append(f"{len(x)}, {x.mean():+.3f}" if len(x) else "0, n/a")
            s.append(f"| {pop} | {per} | " + " | ".join(cells) + " |")
    s.append("")
    return "\n".join(s), rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--replay-csv", required=True)
    ap.add_argument("--registration", required=True, help="docs/research/preregistration_conditional_edge.md")
    ap.add_argument("--out", required=True)
    ap.add_argument("--private-out", default=None, help="per-trade conditions (private: research/private/)")
    a = ap.parse_args()
    with open(a.manifest) as fh:
        m = json.load(fh)
    for what, path, want in (("trades", a.trades, m["outputs"]["trades_sha256"]), ("bar file", a.csv, m["data"]["sha256"])):
        if sha256(path) != want:
            raise SystemExit(f"refusing to report: the {what} given ({path}) is not the sealed run's (sha256 differs from the manifest)")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = load_trades(a.trades)
    rolls = sorted(roll_days(bars))
    if sorted(pd.Timestamp(d).date() for d in m["data"]["roll_dates_excluded"]) != rolls:
        raise SystemExit("roll dates from bars differ from the manifest; refusing to report")
    trades, n_excl = exclude_roll_trades(trades, rolls)
    if len(trades) != int(m["outputs"]["n_trades"]) - int(m["hygiene"]["trades_excluded"]):
        raise SystemExit("analysed population differs from the sealed population; refusing to report")
    cut = pd.Timestamp(a.oos_start) - pd.Timedelta(days=1)
    replay = pd.read_csv(a.replay_csv)
    try:
        missing = [v for v in ("ledger_bracket", "hold_to_1600") if v not in set(replay["variant"].astype(str))]
        if missing:
            raise ValueError(f"the replay file lacks {', '.join(missing)}")
        n_checked = check_alignment(trades, replay)
        f = trade_frame(trades, bars, replay, cut, rolls)
        cont = f.index[f["population"] == "continuation"]
        excess_atr = hold_drift(trades, bars, replay, cont, cut, rolls)["excess_atr"]
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    gate_note = (f"Data hygiene: {n_excl} trades on {len(rolls)} contract-roll dates excluded, as in the sealed report. Provenance: the trades and the bar file have the manifest's sha256. "
                 f"Replay join: checked on {n_checked} stop or target exits before 16:00 (R and exit time). Entries: {len(f)} replayed, of which {int((f['population'] == 'continuation').sum())} continuation and "
                 f"{int((f['population'] == 'reversion A+').sum())} reversion A+.")
    text, _ = report(f, excess_atr, sha256(a.registration), gate_note)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write(text)
    if a.private_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.private_out)), exist_ok=True)
        f.join(excess_atr.rename("excess_atr")).to_csv(a.private_out)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
