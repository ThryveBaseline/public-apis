import json

import numpy as np
import pandas as pd
import pytest

from fpt.data import NY
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import daily_context, load_trades
from research.bracket_replay import grid, replay
from research.conditions import HYPOTHESES, holm, session_context, evaluate_hypothesis, trade_frame, walk_forward_threshold
from tests.test_engine import _globex_bars


@pytest.fixture(scope="module")
def year_and_a_bit(tmp_path_factory):
    """About fourteen months of Globex-style bars and the frozen engine's trades on them, replayed."""
    bars = _globex_bars(days=300, start="2024-06-03", seed=11)
    p = tmp_path_factory.mktemp("cond") / "t.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    t = load_trades(str(p))
    rep = replay(t, bars, [v for v in grid() if v["name"] in ("ledger_bracket", "hold_to_1600")])
    return bars, t, rep


def _sessions(bars):
    naive = bars.index.tz_convert(NY).tz_localize(None)
    return naive, (naive + pd.Timedelta(hours=6)).normalize()


def test_session_context_matches_a_brute_force_and_never_looks_past_0930():
    bars = _globex_bars(days=40)
    ctx = session_context(bars)
    naive, sess = _sessions(bars)
    keys = sorted(set(sess))
    D, prev = keys[30], keys[29]
    s_prev = bars[sess == prev]
    assert ctx.loc[D, "prev_close"] == s_prev["close"].iloc[-1]
    assert ctx.loc[D, "prev_high"] == s_prev["high"].max() and ctx.loc[D, "prev_low"] == s_prev["low"].min()
    assert ctx.loc[D, "atr"] == daily_context(bars)["daily_atr"].loc[D]
    bar0930 = bars[naive == D + pd.Timedelta(hours=9, minutes=30)].iloc[0]
    assert ctx.loc[D, "open"] == bar0930["open"] and ctx.loc[D, "body"] == abs(bar0930["close"] - bar0930["open"])
    over = bars[(sess == D) & (naive < D + pd.Timedelta(hours=9, minutes=30))]
    assert naive[(sess == D) & (naive < D + pd.Timedelta(hours=9, minutes=30))].min() == D - pd.Timedelta(hours=6)  # from 18:00 the evening before
    assert ctx.loc[D, "overnight_range"] == over["high"].max() - over["low"].min()
    closes = pd.Series(bars["close"].to_numpy(), index=sess).groupby(level=0).last()
    i = keys.index(D)
    assert ctx.loc[D, "trend20"] == np.sign(closes.iloc[i - 1] - closes.iloc[i - 21])
    # everything from 09:31 on day D onward changes: D's row and every earlier row must not
    later = naive >= D + pd.Timedelta(hours=9, minutes=31)
    moved = bars.copy()
    for c in ("open", "high", "low", "close"):
        moved.loc[later, c] = moved.loc[later, c] * 1.07 + 13.0
    ctx2 = session_context(moved)
    pd.testing.assert_frame_equal(ctx2.loc[:D], ctx.loc[:D])
    assert not ctx2.loc[keys[31]].equals(ctx.loc[keys[31]])


def test_walk_forward_threshold_uses_only_earlier_development_years():
    years = pd.Series([2010] * 3 + [2011] * 3 + [2012] * 3 + [2013] * 3)
    vals = pd.Series([1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 20.0, 21.0, 22.0, 100.0, 101.0, 102.0])
    dev = pd.Series([True] * 9 + [False] * 3)  # 2013 is benchmark: never in any threshold
    labels = pd.Series(["2010", "2011", "2012", "benchmark"])
    got = walk_forward_threshold(vals, years, dev, labels)
    assert np.isnan(got.iloc[0]) and got.iloc[1] == 2.0 and got.iloc[2] == 6.5 and got.iloc[3] == 11.0


def test_holm_counts_the_whole_registered_family():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    got = holm([0.01, 0.04, 0.03, float("nan")])  # four registered tests, one not computable
    assert got[:3] == pytest.approx([0.04, 0.09, 0.09]) and np.isnan(got[3])
    assert holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])


def test_test_one_difference_se_p_and_years():
    rng = np.random.default_rng(4)
    rows = []
    for y in (2011, 2012, 2013, 2014, 2015):
        for k in range(60):
            fav = k % 2 == 0
            rows.append({"population": "continuation", "period": "development", "year": y, "day": pd.Timestamp(f"{y}-03-01") + pd.Timedelta(days=k),
                         "H1": 1.0 if fav else 0.0, "r": (0.3 if fav else -0.1) + rng.normal(0, 0.5) + (0.0 if y != 2013 else (-0.8 if fav else 0.0))})
    rows.append({"population": "continuation", "period": "development", "year": 2015, "day": pd.Timestamp("2015-12-30"), "H1": np.nan, "r": 50.0})  # undefined: sits out
    f = pd.DataFrame(rows)
    res = evaluate_hypothesis(f, "H1", "continuation")
    d = res["development"]
    fav, oth = f[f["H1"] == 1.0], f[f["H1"] == 0.0]
    assert d["n_fav"] == 150 and d["n_oth"] == 150
    assert d["delta"] == pytest.approx(fav["r"].mean() - oth["r"].mean())
    se = np.sqrt((fav["r"].std(ddof=1) ** 2) / 150 + (oth["r"].std(ddof=1) ** 2) / 150)  # one trade per day: clustered = iid
    assert d["se"] == pytest.approx(se, rel=1e-9)
    assert d["years_n"] == 5 and d["years_pos"] == 4  # 2013 is reversed
    assert 0 < d["p"] < 0.01 and res["benchmark"]["n_fav"] == 0


def test_trade_frame_flags_match_an_independent_computation(year_and_a_bit):
    bars, t, rep = year_and_a_bit
    days = sorted(set(t["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)))
    cut = days[int(len(days) * 0.75)]
    f = trade_frame(t, bars, rep, cut, [])
    assert {"continuation", "reversion A+"} <= set(f["population"]) and set(f["period"]) == {"development", "benchmark"}
    ctx = session_context(bars)
    ok_days = ctx[ctx["open"].notna() & (ctx["atr"] > 0)]
    dev_days = ok_days[ok_days.index <= cut]

    def wf(series_by_day, label):
        src = series_by_day[series_by_day.index <= cut] if label == "benchmark" else series_by_day[(series_by_day.index <= cut) & (series_by_day.index.year < int(label))]
        src = src.dropna()
        return src.median() if len(src) else np.nan
    body_atr = dev_days["body"] / dev_days["atr"]
    on_atr = dev_days["overnight_range"] / dev_days["atr"]
    checked = {h: 0 for h, *_ in HYPOTHESES}
    for k, row in f.iterrows():
        tr = t.loc[k]
        D = tr["entry_time"].tz_convert(NY).normalize().tz_localize(None)
        c = ctx.loc[D]
        d = int(tr["direction"])
        lab = str(D.year) if D <= cut else "benchmark"
        assert row["label"] == lab
        gap = c["open"] - c["prev_close"]
        exp = {"H1": float(d == c["trend20"]) if c["trend20"] in (-1.0, 1.0) else np.nan,
               "H2": float(d == np.sign(gap)) if gap != 0 else np.nan,
               "H5": float((d > 0 and c["open"] > c["prev_high"]) or (d < 0 and c["open"] < c["prev_low"])),
               "H9": float(d == -np.sign(gap)) if gap != 0 else np.nan}
        tb, to = wf(body_atr, lab), wf(on_atr, lab)
        exp["H3"] = float(c["body"] / c["atr"] >= tb) if np.isfinite(tb) else np.nan
        exp["H4"] = float(c["overnight_range"] / c["atr"] <= to) if np.isfinite(to) else np.nan
        exp["H8"] = exp["H1"]
        for h, val in exp.items():
            got = row[h]
            assert (np.isnan(val) and np.isnan(got)) or got == val, (k, h, got, val)
            checked[h] += int(np.isfinite(val))
    # the extension and room thresholds come from the tested population's own earlier development entries
    for h, pop, above in (("H6", "continuation", False), ("H7", "reversion A+", True)):
        g = f[f["population"] == pop]
        for k, row in g.iterrows():
            lab = row["label"]
            src = g[(g["period"] == "development") & ((g["year"] < int(lab)) if lab != "benchmark" else True)]["ext_atr"].dropna()
            thr = src.median() if len(src) else np.nan
            want = np.nan if not (np.isfinite(thr) and np.isfinite(row["ext_atr"])) else float(row["ext_atr"] >= thr if above else row["ext_atr"] <= thr)
            assert (np.isnan(want) and np.isnan(row[h])) or row[h] == want
            checked[h] += int(np.isfinite(want))
        assert f.loc[f["population"] != pop, h].isna().all()
    assert all(checked[h] > 0 for h in checked), checked


def test_cli_end_to_end_and_its_refusals(tmp_path, monkeypatch):
    from fpt.data import load_minute_bars, roll_days
    from research import bracket_replay, conditions
    from research.anatomy import exclude_roll_trades
    from research.candidates import sha256
    bars = _globex_bars(days=60, start="2025-01-06", seed=5)
    bars["symbol"] = np.where(bars.index < bars.index[len(bars) // 2], 1000, 1001)
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    csv = tmp_path / "bars.csv"
    out.to_csv(csv)
    loaded = load_minute_bars(str(csv), source_tz="UTC")
    rolls = sorted(roll_days(loaded))
    assert len(rolls) == 1
    led = tmp_path / "trades.csv"
    generate_trades(loaded, StrategyConfig()).to_csv(led, index=False)
    trades = load_trades(str(led))
    kept, n_excl = exclude_roll_trades(trades, rolls)
    man = {"data": {"roll_dates_excluded": [str(d) for d in rolls], "sha256": sha256(str(csv))},
           "outputs": {"n_trades": len(trades), "trades_sha256": sha256(str(led))}, "hygiene": {"trades_excluded": n_excl}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = (day.max() - pd.Timedelta(days=20)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["bracket_replay.py", *common, "--out", str(tmp_path / "b1.md"), "--private-out", str(tmp_path / "replay.csv")])
    assert bracket_replay.main() in (0, None)
    reg = tmp_path / "registration.md"
    reg.write_text("registered text")
    args = [*common, "--replay-csv", str(tmp_path / "replay.csv"), "--registration", str(reg), "--out", str(tmp_path / "c.md"), "--private-out", str(tmp_path / "private" / "c.csv")]
    monkeypatch.setattr("sys.argv", ["conditions.py", *args])
    assert conditions.main() == 0
    text = (tmp_path / "c.md").read_text()
    assert sha256(str(reg)) in text and "Passing conditions:" in text
    assert all(f"| {h} | " in text for h, *_ in HYPOTHESES)
    assert (tmp_path / "private" / "c.csv").exists()
    rp = pd.read_csv(tmp_path / "replay.csv")
    rp[rp["variant"] != "hold_to_1600"].to_csv(tmp_path / "replay.csv", index=False)
    with pytest.raises(SystemExit, match="lacks hold_to_1600"):
        conditions.main()
    man["outputs"]["trades_sha256"] = "0" * 64
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="the trades given .* is not the sealed run's"):
        conditions.main()
