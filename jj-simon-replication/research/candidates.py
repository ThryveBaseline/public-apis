"""B3: candidate trade streams under the frozen firm rules.

Each candidate is a stream of sealed entries with a per-trade outcome taken either from the ledger or from
research/bracket_replay.py's per-trade file, put through the sequential pass of research/ledger_filters.py (one
position at a time, the three-loss session stop, each trade's own exit time). Every stream is then scored with the
frozen evaluator's own walk-forward functions (fpt.evaluate.walk_forward_pass_probability,
walk_forward_payout_probability and _rate) under the four firm presets, exactly as fpt.evaluate.evaluate_trades does,
except that the cut between development and benchmark is fixed at the sealed run's cut (the frozen function moves the
cut with each stream's last trade day). The EV per evaluation uses the frozen calculator (fpt.bootstrap.his_calculator).

Gate before anything is reported: the sealed ledger, scored this way, must reproduce the eight firm rows of
sealed/run1/report.md character for character. Otherwise the tool refuses.

Streams (provenance: docs/reviews/run1_b2_read.md):
  S0   sealed ledger (the gate stream)
  S0r  sealed brackets replayed, flat at 16:00 (control for everything replayed)
  S1   continuation only, sealed bracket
  S2   continuation, plus reversion A+ only (his funded entry trigger), sealed bracket
  S3   continuation only, with the bracket chosen year by year by the pooled walk-forward over earlier development
       years among the ATR-scaled brackets (sealed bracket before the chain starts; the benchmark year uses the choice
       made on all development years)
  S4   S3's continuation plus A+ reversion with the sealed bracket
Only development trades (New York day on or before the cut) enter any choice; the benchmark is never used to choose.

Plus a direction split (long / short) of continuation under the sealed bracket, S3's brackets and the hold-to-16:00
control, and a drift control for the hold: each trade held to 16:00 against the same-direction trade from the same
minute on every non-roll trading day of its year. The two carry identical costs, so their difference is
d x (the trade's move - the mean move) / 25 points: what the direction call adds beyond the market's drift. A
continuation edge that is only the 2020-2026 bull market shows up as long winners, short losers and no excess.

usage: python research/candidates.py --trades sealed/run1/trades.csv --csv data/nq_1min_databento.csv --source-tz UTC \
           --oos-start 2025-10-06 --manifest sealed/run1/manifest.json --report sealed/run1/report.md \
           --replay-csv research/private/run1_bracket_replay_b2.csv --out research/staging/run1_b3.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.bootstrap import his_calculator  # noqa: E402
from fpt.data import NY, load_minute_bars, roll_days  # noqa: E402
from fpt.evaluate import _rate, trading_days_of, walk_forward_pass_probability, walk_forward_payout_probability  # noqa: E402
from fpt.propfirm import FIRM_PRESETS  # noqa: E402
from research.anatomy import exclude_roll_trades, load_trades  # noqa: E402
from research.bracket_replay import COMMISSION_RT, FIXED_STOP, POINT_VALUE, SLIPPAGE, grid  # noqa: E402
from research.ledger_filters import apply_filter, build_gates, check_alignment, sequential_pass  # noqa: E402

FIRMS = ("topstep_50k", "fundednext_50k_flex", "topstep_100k", "tradeify_100k_growth")
MAX_EVAL_DAYS, MAX_FUNDED_DAYS, FUNDED_RISK = 30, 60, 500.0
ATR_NAMES = [v["name"] for v in grid() if v["family"] == "atr"]
CHAIN_START = 3  # as research/bracket_replay.walk_forward: the chain starts at the fourth development year


def firm_rows(part: pd.DataFrame, cal_part: pd.DatetimeIndex, firms=FIRMS, eval_risk_mode: str = "two_trade", eval_risk: float = 500.0) -> pd.DataFrame:
    """The firm table of fpt.evaluate.evaluate_trades for one part of the data, computed with its own functions."""
    rows = []
    for key in firms:
        rules = FIRM_PRESETS[key]
        er = rules.profit_target / (2.0 * 1.5) if eval_risk_mode == "two_trade" else eval_risk
        pp = walk_forward_pass_probability(part, rules, er, MAX_EVAL_DAYS, trading_days=cal_part)
        pr = walk_forward_payout_probability(part, rules, FUNDED_RISK, MAX_FUNDED_DAYS, trading_days=cal_part)
        a, b = _rate(pp, "pass", "fail", horizon=MAX_EVAL_DAYS), _rate(pr, "payout", "bust", horizon=MAX_FUNDED_DAYS)
        rows.append({"firm": key, "eval_risk": er, "pass_rate": a["rate"], "pass_stderr": a["stderr"], "eval_days_median": a["days_median"],
                     "n_eval_starts": a["n_seen"], "n_eval_open": a["n_open"], "payout_rate": b["rate"], "payout_stderr": b["stderr"],
                     "payout_days_median": b["days_median"], "n_funded_starts": b["n_seen"], "n_funded_open": b["n_open"],
                     "payout_median_amount": float(pr.loc[pr["outcome"] == "payout", "amount"].median()) if (pr["outcome"] == "payout").any() else float("nan")})
    return pd.DataFrame(rows)


def format_row(r: dict) -> str:
    """Exactly the frozen report's firm-row format."""
    return (f"| {r['firm']} | {r['eval_risk']:,.0f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {r['eval_days_median']:.0f} | {r['n_eval_starts']} ({r['n_eval_open']}) | "
            f"{r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_days_median']:.0f} | {r['n_funded_starts']} ({r['n_funded_open']}) | {r['payout_median_amount']:,.0f} |")


def ev_per_eval(r: dict) -> float:
    rules = FIRM_PRESETS[r["firm"]]
    size = r["payout_median_amount"]
    if not np.isfinite(r["pass_rate"]) or not np.isfinite(r["payout_rate"]) or not np.isfinite(size):
        return float("nan")
    return float(his_calculator(rules.eval_cost, r["pass_rate"], r["payout_rate"], size)["ev_per_eval"])


def score(stream: pd.DataFrame, cal: pd.DatetimeIndex, cut: pd.Timestamp) -> dict:
    day = stream["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    out = {}
    for label, part, cal_part in (("development", stream[day <= cut], cal[cal <= cut]), ("benchmark", stream[day > cut], cal[cal > cut])):
        out[label] = {"trades": int(len(part)), "expectancy_r": float(part["r"].mean()) if len(part) else float("nan"),
                      "total_r": float(part["r"].sum()), "firms": firm_rows(part, cal_part) if len(part) else pd.DataFrame()}
    return out


def sealed_firm_rows(report_text: str) -> dict:
    """The firm rows of the sealed report, by part."""
    out, part = {"development": [], "benchmark": []}, None
    for line in report_text.splitlines():
        if line.startswith("## Pass and payout probability under exact firm rules, in sample"):
            part = "development"
        elif line.startswith("## Pass and payout probability under exact firm rules, out of sample"):
            part = "benchmark"
        elif line.startswith("## "):
            part = None
        elif part and any(line.startswith(f"| {f} |") for f in FIRMS):
            out[part].append(line.strip())
    return out


def variant_frame(trades: pd.DataFrame, replay: pd.DataFrame, choice: pd.Series) -> pd.DataFrame:
    """Trades with r, pnl sign and exit time from the replay variant named per trade in `choice` (index: trade id)."""
    rows = replay[replay["variant"] != "_dropped"].set_index(["trade", "variant"])
    keys = pd.MultiIndex.from_arrays([choice.index.astype(int), choice.to_numpy()], names=["trade", "variant"])
    missing = keys.difference(rows.index)
    if len(missing):
        raise ValueError(f"{len(missing)} (trade, variant) pairs are not in the replay file")
    sel = rows.loc[keys]
    t = trades.loc[choice.index].copy()
    t["r"] = sel["r"].astype(float).to_numpy()
    t["pnl_dollars"] = t["r"].to_numpy()
    t["exit_time"] = pd.to_datetime(sel["exit_time"], utc=True).dt.tz_convert(NY).array
    t["bracket"] = choice.to_numpy()
    return t


def period_label(day: pd.Series, cut: pd.Timestamp) -> pd.Series:
    """'2010' ... for development days (calendar year), 'benchmark' after the cut."""
    return pd.Series(np.where(day <= cut, day.dt.year.astype(str), "benchmark"), index=day.index)


def pooled_choices(replay: pd.DataFrame, trades: pd.DataFrame, setup: str, names: list[str], dev_years: list[int], cut: pd.Timestamp) -> dict:
    """Year -> bracket chosen on the pooled (trade-weighted) expectancy of all earlier development years for one setup,
    as research/bracket_replay.walk_forward; the key 'benchmark' holds the choice made on all development years (it is
    the chain's next link, so it too needs CHAIN_START earlier years). Only trades whose New York day is on or before
    the cut enter: the last development year also holds benchmark trades, and they must not steer any choice."""
    t = trades[trades["setup"].astype(str) == setup]
    ny = t["entry_time"].dt.tz_convert(NY)
    year = ny.dt.year[ny.dt.normalize().dt.tz_localize(None) <= cut]
    r = replay[replay["variant"].isin(names) & replay["trade"].isin(year.index)].copy()
    r["year"] = r["trade"].map(year)
    r = r[r["year"].isin(dev_years)]
    sums = r.groupby(["variant", "year"])["r"].sum().unstack("year").reindex(index=names, columns=dev_years)
    cnt = r.groupby(["variant", "year"])["r"].size().unstack("year").reindex(index=names, columns=dev_years)
    out = {}
    for j, y in enumerate(dev_years + ["benchmark"]):
        if j < CHAIN_START:
            continue
        upto = dev_years[:j] if y != "benchmark" else dev_years
        prior = sums[upto].sum(axis=1, min_count=1) / cnt[upto].sum(axis=1, min_count=1)
        if prior.isna().all():
            continue
        out[y] = prior.idxmax()
    return out


def build_streams(trades: pd.DataFrame, bars: pd.DataFrame, replay: pd.DataFrame, cut: pd.Timestamp) -> tuple[dict, dict, pd.Series]:
    """The candidate streams, the continuation chain, and S3's bracket per replayed trade."""
    gates = build_gates(trades, bars)
    replayed = sorted(set(int(x) for x in replay.loc[replay["variant"] != "_dropped", "trade"]))
    t = trades.loc[replayed]
    is_cont = t["setup"].astype(str) == "continuation"
    day = t["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    year = t["entry_time"].dt.tz_convert(NY).dt.year
    dev_years = sorted(int(y) for y in year[day <= cut].unique())
    ctrl = variant_frame(t, replay, pd.Series("ledger_bracket", index=t.index))
    chain = pooled_choices(replay, t, "continuation", ATR_NAMES, dev_years, cut)

    def cont_bracket(k):
        if day[k] > cut:
            return chain.get("benchmark", "ledger_bracket")
        return chain.get(int(year[k]), "ledger_bracket")
    s3_choice = pd.Series([cont_bracket(k) if is_cont[k] else "ledger_bracket" for k in t.index], index=t.index)
    mixed = variant_frame(t, replay, s3_choice)
    streams = {
        "S0 sealed ledger": sequential_pass(trades),
        "S0r sealed brackets, flat 16:00": sequential_pass(ctrl),
        "S1 continuation only, sealed bracket": sequential_pass(ctrl[is_cont]),
        "S2 continuation + A+ reversion, sealed bracket": sequential_pass(apply_filter(ctrl, "B2a", gates)),
        "S3 continuation only, walk-forward ATR bracket": sequential_pass(mixed[is_cont]),
        "S4 S3 + A+ reversion, sealed bracket": sequential_pass(apply_filter(mixed, "B2a", gates)),
    }
    return streams, chain, s3_choice


def drift_baseline(bars: pd.DataFrame, rolls, cut: pd.Timestamp) -> pd.Series:
    """Mean move in points from each regular-session minute's open to the close of that day's last bar before 16:00
    (the replay's flat exit), over every non-roll trading day, by period label and minute of the day."""
    ny = bars.index.tz_convert(NY)
    mins = np.asarray(ny.hour * 60 + ny.minute, dtype=np.int64)
    rth = (mins >= 9 * 60 + 30) & (mins < 16 * 60)
    b = pd.DataFrame({"day": ny[rth].normalize().tz_localize(None), "min": mins[rth],
                      "open": bars["open"].to_numpy(float)[rth], "close": bars["close"].to_numpy(float)[rth]})
    b = b[~b["day"].dt.date.isin(set(rolls))]
    b["move"] = b["day"].map(b.groupby("day")["close"].last()) - b["open"]
    b["label"] = period_label(b["day"], cut).to_numpy()
    return b.groupby(["label", "min"])["move"].mean()


def hold_drift(trades: pd.DataFrame, bars: pd.DataFrame, replay: pd.DataFrame, ids, cut: pd.Timestamp, rolls) -> pd.DataFrame:
    """Per trade in `ids`: its replayed R held to 16:00 (hold_r), the R of the same-direction trade from the same
    minute averaged over every non-roll trading day with the same period label, at the same costs (drift_r), and the
    difference (excess_r = d x (the trade's move - the mean move) / 25 points)."""
    t = trades.loc[ids]
    ny = t["entry_time"].dt.tz_convert(NY)
    day = ny.dt.normalize().dt.tz_localize(None)
    on_roll = day.dt.date.isin(set(rolls))
    if on_roll.any():
        raise ValueError(f"{int(on_roll.sum())} trades fall on roll dates, which have no drift baseline")
    label = period_label(day, cut)
    d = t["direction"].astype(int).to_numpy()
    key = pd.MultiIndex.from_arrays([label.to_numpy(), (ny.dt.hour * 60 + ny.dt.minute).to_numpy(np.int64)])
    avg = drift_baseline(bars, rolls, cut).reindex(key).to_numpy(float)
    if np.isnan(avg).any():
        raise ValueError(f"{int(np.isnan(avg).sum())} trades have no drift baseline (entry outside 09:30-16:00)")
    drift_r = ((d * avg - 2 * SLIPPAGE) * POINT_VALUE - COMMISSION_RT) / (FIXED_STOP * POINT_VALUE)
    hold_r = variant_frame(t, replay, pd.Series("hold_to_1600", index=t.index))["r"].to_numpy(float)
    return pd.DataFrame({"day": day.to_numpy(), "label": label.to_numpy(), "period": np.where(label == "benchmark", "benchmark", "development"),
                         "side": np.where(d > 0, "long", "short"), "hold_r": hold_r, "drift_r": drift_r, "excess_r": hold_r - drift_r}, index=t.index)


def mean_se(x: pd.Series, day: pd.Series) -> tuple[int, float, float]:
    """Trades, mean, and the standard error of the mean clustered by day (trades on one day share its close)."""
    x = x.astype(float)
    n = len(x)
    if n == 0:
        return 0, float("nan"), float("nan")
    m = float(x.mean())
    g = (x - m).groupby(np.asarray(day)).sum()
    k = len(g)
    return n, m, float(np.sqrt(k / (k - 1) * (g ** 2).sum()) / n) if k > 1 else float("nan")


def direction_table(trades: pd.DataFrame, replay: pd.DataFrame, s3_choice: pd.Series, drift: pd.DataFrame) -> list[str]:
    """Continuation by direction and period under the sealed bracket, S3's own per-trade bracket and the hold, with
    the drift control; and the hold against the drift by year."""
    ids = drift.index
    t = trades.loc[ids]
    outcomes = {"sealed bracket": variant_frame(t, replay, pd.Series("ledger_bracket", index=ids))["r"],
                "S3 walk-forward bracket": variant_frame(t, replay, s3_choice.loc[ids])["r"],
                "held to 16:00 (R per 25 points)": drift["hold_r"],
                "held to 16:00, excess over the drift": drift["excess_r"]}
    s = ["## Continuation by direction\n",
         "Replayed continuation entries before the sequential pass, flat at 16:00. Cells: trades, mean R (standard error of the mean, clustered by day). "
         "The drift is the same-direction trade from the same minute on every non-roll trading day of the same year (benchmark: of the benchmark period) at the same costs; "
         "the excess is the trade held to 16:00 minus that drift, and is zero on average if the direction call adds nothing to the market's drift at that time of day.\n",
         "| outcome | period | long | short | both |", "|---|---|---|---|---|"]
    for name, x in outcomes.items():
        for per in ("development", "benchmark"):
            cells = []
            for side in ("long", "short", "both"):
                m = (drift["period"] == per) & ((drift["side"] == side) | (side == "both"))
                n, mu, se = mean_se(x[m], drift.loc[m, "day"])
                cells.append(f"{n}, {mu:+.3f} ({se:.3f})" if n else "0, n/a")
            s.append(f"| {name} | {per} | " + " | ".join(cells) + " |")
    s += ["", "### Held to 16:00 against the drift, by year (R per 25 points)\n",
          "| year | long: trades, held, drift, excess | short: trades, held, drift, excess | both: excess (se) |", "|---|---|---|---|"]
    for lab in sorted(drift["label"].unique()):
        g = drift[drift["label"] == lab]
        cells = []
        for side in ("long", "short"):
            q = g[g["side"] == side]
            cells.append(f"{len(q)}, {q['hold_r'].mean():+.3f}, {q['drift_r'].mean():+.3f}, {q['excess_r'].mean():+.3f}" if len(q) else "0, n/a")
        n, mu, se = mean_se(g["excess_r"], g["day"])
        s.append(f"| {lab} | {cells[0]} | {cells[1]} | {mu:+.3f} ({se:.3f}) |")
    s.append("")
    return s


def report(streams: dict, chain: dict, cal: pd.DatetimeIndex, cut: pd.Timestamp, gate_note: str, direction_lines: list[str]) -> str:
    s = ["# B3: candidate streams under the frozen firm rules\n", gate_note, ""]
    s.append("Every stream goes through the sequential pass (one position at a time, three-loss session stop, each trade's own exit time) and is scored with the frozen evaluator's walk-forward pass and payout functions under each firm preset, with the sealed run's sizing (two-trade evaluation risk, $500 funded risk) and the sealed cut. The benchmark year is reported beside and never used to choose. EV per evaluation is the frozen calculator: pass x payout x median payout - fee.\n")
    chain_txt = "; ".join(f"{k}: {v}" for k, v in chain.items()) if chain else f"none (the chain needs {CHAIN_START} earlier development years), so S3 and S4 keep the sealed bracket"
    s.append(f"Walk-forward bracket for continuation (S3, S4), chosen on earlier development years only: {chain_txt}.\n")
    s.append("## Summary, topstep_50k\n\n| stream | period | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation |\n|---|---|---|---|---|---|---|---|---|---|---|")
    scored = {name: score(st, cal, cut) for name, st in streams.items()}
    for name, sc in scored.items():
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            r = p["firms"].set_index("firm").loc["topstep_50k"].to_dict()
            r["firm"] = "topstep_50k"
            s.append(f"| {name} | {per} | {p['trades']} | {p['expectancy_r']:+.3f} | {p['total_r']:+.1f} | {r['pass_rate']:.1%} | {r['pass_stderr']:.1%} | {r['payout_rate']:.1%} | {r['payout_stderr']:.1%} | {r['payout_median_amount']:,.0f} | {ev_per_eval(r):+,.0f} |")
    s.append("")
    for name, sc in scored.items():
        s.append(f"## {name}\n")
        for per in ("development", "benchmark"):
            p = sc[per]
            if p["firms"].empty:
                continue
            s.append(f"{per}: {p['trades']} trades, {p['expectancy_r']:+.3f} R per trade, {p['total_r']:+.1f} R.\n")
            s.append(f"| firm | eval risk | P(pass) within {MAX_EVAL_DAYS} days | +/- | days to pass (median) | starts (open) | P(payout before breach) within {MAX_FUNDED_DAYS} days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
            for r in p["firms"].to_dict("records"):
                s.append(format_row(r)[:-1] + f"| {ev_per_eval(r):+,.0f} |")
            s.append("")
    s += direction_lines
    return "\n".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--oos-start", default="2025-10-06")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--report", required=True, help="sealed/run1/report.md: its firm rows are the reproduction gate")
    ap.add_argument("--replay-csv", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = load_trades(a.trades)
    rolls = sorted(roll_days(bars))
    with open(a.manifest) as fh:
        m = json.load(fh)
    if sorted(pd.Timestamp(d).date() for d in m["data"]["roll_dates_excluded"]) != rolls:
        raise SystemExit("roll dates from bars differ from the manifest; refusing to report")
    trades, n_excl = exclude_roll_trades(trades, rolls)
    if len(trades) != int(m["outputs"]["n_trades"]) - int(m["hygiene"]["trades_excluded"]):
        raise SystemExit("analysed population differs from the sealed population; refusing to report")
    cut = pd.Timestamp(a.oos_start) - pd.Timedelta(days=1)
    cal = trading_days_of(bars)
    with open(a.report) as fh:
        sealed = sealed_firm_rows(fh.read())
    gate = score(sequential_pass(trades), cal, cut)
    for per in ("development", "benchmark"):
        mine = [format_row(r) for r in gate[per]["firms"].to_dict("records")]
        if mine != sealed[per] or len(mine) != len(FIRMS):
            raise SystemExit(f"refusing to report: the {per} firm rows do not reproduce the sealed report\nsealed: {sealed[per]}\nmine:   {mine}")
    replay = pd.read_csv(a.replay_csv)
    try:
        n_checked = check_alignment(trades, replay)
        streams, chain, s3_choice = build_streams(trades, bars, replay, cut)
        cont = s3_choice.index[trades.loc[s3_choice.index, "setup"].astype(str) == "continuation"]
        drift = hold_drift(trades, bars, replay, cont, cut, rolls)
    except ValueError as e:
        raise SystemExit(f"refusing to report: {e}")
    gate_note = (f"Data hygiene: {n_excl} trades on {len(rolls)} contract-roll dates excluded, as in the sealed report. Reproduction gate: the sealed ledger scored here reproduces all {2 * len(FIRMS)} firm rows of sealed/run1/report.md character for character. "
                 f"Replay join: checked on {n_checked} stop or target exits before 16:00 (R and exit time).")
    text = report(streams, chain, cal, cut, gate_note, direction_table(trades, replay, s3_choice, drift))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(text)
    print(text[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
