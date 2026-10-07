import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from fpt.evaluate import evaluate_trades, trading_days_of
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.bracket_replay import dropped_rows, grid, replay, walk_forward
from research.candidates import (ATR_NAMES, FIRMS, NEEDED_VARIANTS, START_CASH, bootstrap, build_streams, check_grid, firm_rows, format_bootstrap,
                                 format_row, hold_drift, mean_se, pooled_choices, s3_bracket, score, score_whole, sealed_firm_rows, variant_frame,
                                 whole_contracts)
from research.ledger_filters import sequential_pass

NY = "America/New_York"


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    bars = synthetic_minute_bars(days=200, seed=9)
    p = tmp_path_factory.mktemp("eng") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    return bars, load_trades(str(p))


def test_firm_rows_reproduce_the_frozen_evaluator(engine):
    bars, trades = engine
    rep = evaluate_trades(trades, bars, oos_months=2)
    last = trades["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None).max()
    cut = (last - pd.DateOffset(months=2)).normalize()
    mine = score(sequential_pass(trades), trading_days_of(bars), cut)
    for label, part in (("in_sample", "development"), ("out_of_sample", "benchmark")):
        theirs = rep.tables[f"firms_{label}"]
        ours = mine[part]["firms"]
        cols = [c for c in ours.columns]
        pd.testing.assert_frame_equal(ours[cols].reset_index(drop=True), theirs[cols].reset_index(drop=True), check_dtype=False)
    # and the report rows parse back to exactly our formatted rows
    parsed = sealed_firm_rows(rep.text)
    assert parsed["development"] == [format_row(r) for r in mine["development"]["firms"].to_dict("records")]
    assert parsed["benchmark"] == [format_row(r) for r in mine["benchmark"]["firms"].to_dict("records")]
    assert len(parsed["development"]) == len(FIRMS)


def test_pooled_choices_match_the_replay_chain():
    rows, meta, when = [], [], []
    k = 0
    years = [2010, 2011, 2012, 2013, 2014]
    spec = [(2010, 1, 5.0, -1.0, "06-02"), (2011, 200, -0.10, 0.05, "06-02"), (2012, 200, -0.10, 0.05, "06-02"), (2013, 200, 0.2, 0.0, "06-02"),
            (2014, 200, 0.2, 0.0, "06-02"), (2014, 1000, -1.0, 1.0, "11-03")]  # the last development year also holds benchmark trades
    for year, n, ra, rb, md in spec:
        for _ in range(n):
            rows += [(k, "A", ra), (k, "B", rb)]
            meta.append((k, "development" if md == "06-02" else "benchmark", year))
            when.append(pd.Timestamp(f"{year}-{md} 09:35", tz=NY))
            k += 1
    rep = pd.DataFrame(rows, columns=["trade", "variant", "r"])
    m = pd.DataFrame(meta, columns=["trade", "period", "year"]).set_index("trade")
    _, pooled, lines = walk_forward(rep, m, years, {"x": ["A", "B"]})
    text = "\n".join(lines)
    trades = pd.DataFrame({"setup": "continuation", "entry_time": when}, index=range(k))
    ch = pooled_choices(rep, trades, "continuation", ["A", "B"], years, pd.Timestamp("2014-09-30"))
    for y in (2013, 2014):
        assert f"| {y} | {ch[y]} |" in text
    assert ch[2013] == "B" and ch["benchmark"] == "A" == pooled.loc[["A", "B"]].idxmax()  # by 2014 the pooled record favours A
    # the benchmark trades favour B; a cut that let them in would flip the benchmark choice
    assert pooled_choices(rep, trades, "continuation", ["A", "B"], years, pd.Timestamp("2014-12-31"))["benchmark"] == "B"
    assert pooled_choices(rep, trades, "continuation", ["A", "B"], years[:2], pd.Timestamp("2011-12-31")) == {}  # too few years for a chain


def _consistent(tmp_path):
    from tests.test_ledger_filters import _consistent_ledger
    t, bars, days = _consistent_ledger()
    rep = replay(t, bars, grid())
    rep = pd.concat([rep, dropped_rows(rep)], ignore_index=True)
    rep["exit_time"] = rep["exit_time"].astype(str).where(rep["variant"] != "_dropped")
    return t.reset_index(drop=True), bars, days, rep


def test_streams_and_variant_frame(tmp_path):
    t, bars, days, rep = _consistent(tmp_path)
    cut = pd.Timestamp(days[30].strftime("%Y-%m-%d")) - pd.Timedelta(days=1)
    pre, streams, chain, s3_choice = build_streams(t, bars, rep, cut)
    assert set(pre) == set(streams) and all(len(streams[k]) <= len(pre[k]) for k in pre)
    assert set(s3_choice) <= {"ledger_bracket", *ATR_NAMES}
    assert (s3_choice[t.loc[s3_choice.index, "setup"] == "reversion"] == "ledger_bracket").all()
    s1 = streams["S1 continuation only, sealed bracket"]
    assert set(s1["setup"]) == {"continuation"}
    s4 = streams["S4 S3 + A+ reversion, sealed bracket"]
    assert set(s4.loc[s4["setup"] == "reversion", "grade"]) <= {"A+"}
    for name, st in streams.items():
        st = st.sort_values("entry_time")
        if len(st) > 1 and name != "S0 sealed ledger":
            assert (st["exit_time"].to_numpy()[:-1] < st["entry_time"].to_numpy()[1:]).all()  # one position at a time
    with pytest.raises(ValueError, match="not in the replay file"):
        variant_frame(t, rep, pd.Series("no_such_bracket", index=t.index[:1]))


def _check_drift(bars, trades, min_trades=20):
    """hold_drift against a brute force: the replay's hold is the engine's fill to the last close before 16:00, and
    the excess is d x (move - the mean move of the same minute over the same label's other non-roll days) / 25."""
    from research.anatomy import daily_context
    rep = replay(trades, bars, [v for v in grid() if v["name"] in ("hold_to_1600", "ledger_bracket")])
    cont = sorted(set(rep["trade"]) & set(trades.index[trades["setup"].astype(str) == "continuation"]))
    assert len(cont) > min_trades
    days = trading_days_of(bars)
    cut = days[len(days) // 2]
    roll = [trades.loc[cont[0], "entry_time"].tz_convert(NY).date()]  # treated as a roll date: no baseline, no trades
    ids = [k for k in cont if trades.loc[k, "entry_time"].tz_convert(NY).date() not in roll]
    dr = hold_drift(trades, bars, rep, ids, cut, roll)
    assert set(dr.loc[dr["period"] == "benchmark", "label"]) == {"benchmark"} and set(dr["period"]) == {"development", "benchmark"}
    atr = daily_context(bars)["daily_atr"]
    ny = bars.index.tz_convert(NY)
    mins = ny.hour * 60 + ny.minute
    rth = bars[(mins >= 570) & (mins < 960)]
    rny = rth.index.tz_convert(NY)
    last = rth["close"].groupby(rny.normalize()).last()

    def label(day):
        return str(day.year) if day.tz_localize(None) <= cut else "benchmark"
    for k in ids:
        et = trades.loc[k, "entry_time"]
        d = int(trades.loc[k, "direction"])
        e = et.tz_convert(NY)
        move = last[e.normalize()] - bars.loc[et, "open"]
        # the engine fills at the entry bar's open plus slippage; the hold exits at the last close before 16:00 less slippage
        assert dr.loc[k, "hold_r"] == pytest.approx(((d * move - 2 * 0.25) * 20 - 5) / 500)
        at = (rny.hour == e.hour) & (rny.minute == e.minute)
        opens = pd.Series(rth.loc[at, "open"].to_numpy(), index=rny[at].normalize())
        moves = [last[D] - o for D, o in opens.items() if D.date() not in roll and label(D) == label(e.normalize())]
        assert dr.loc[k, "excess_r"] == pytest.approx(d * (move - np.mean(moves)) / 25)
        a = atr.get(e.normalize().tz_localize(None), np.nan)
        if np.isfinite(a):
            assert dr.loc[k, "excess_atr"] == pytest.approx(d * (move - np.mean(moves)) / a)
        else:
            assert np.isnan(dr.loc[k, "excess_atr"])
    with pytest.raises(ValueError, match="fall on roll dates"):
        hold_drift(trades, bars, rep, [cont[0]], cut, roll)
    return dr


def test_hold_drift_is_the_direction_call_beyond_the_drift(engine):
    bars, trades = engine
    _check_drift(bars, trades)


def test_hold_drift_on_globex_hours_closes_at_the_last_bar_before_1600(tmp_path):
    """Globex bars run to 16:59 and from 18:00 (and cross a DST change): the hold and its drift end at the last bar
    before 16:00, never at the day's last bar."""
    from tests.test_engine import _globex_bars
    bars = _globex_bars(days=40)
    p = tmp_path / "t.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    dr = _check_drift(bars, load_trades(str(p)), min_trades=8)
    assert dr["excess_atr"].notna().sum() >= 8


def test_mean_se_clusters_by_day():
    x = pd.Series([0.5, -1.0, 2.0, 0.25, -0.75])
    day = pd.Series(pd.date_range("2025-01-06", periods=5))
    n, m, se = mean_se(x, day)
    assert n == 5 and m == pytest.approx(x.mean()) and se == pytest.approx(x.std(ddof=1) / np.sqrt(5))
    n2, m2, se2 = mean_se(pd.concat([x, x]), pd.concat([day, day]))  # an identical twin on the same day adds no information
    assert n2 == 10 and m2 == pytest.approx(m) and se2 == pytest.approx(se)


def test_cli_gate_reproduces_the_sealed_rows_and_refuses_a_changed_one(tmp_path, monkeypatch):
    """The real pipeline on synthetic bars with one contract roll: frozen engine, frozen report, the replay CLI, then
    this CLI, whose gate must pass on the untouched report and refuse a report with one character changed."""
    import json
    from fpt.data import load_minute_bars, roll_days
    from research import bracket_replay, candidates
    from research.anatomy import exclude_roll_trades
    bars = synthetic_minute_bars(days=130, seed=5)
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
    rep = evaluate_trades(trades, loaded, exclude_dates=rolls, oos_months=2)
    (tmp_path / "report.md").write_text(rep.text)
    kept, n_excl = exclude_roll_trades(trades, rolls)
    assert n_excl > 0
    man = {"data": {"roll_dates_excluded": [str(d) for d in rolls], "sha256": candidates.sha256(str(csv))},
           "outputs": {"n_trades": len(trades), "trades_sha256": candidates.sha256(str(led)), "report_sha256": candidates.sha256(str(tmp_path / "report.md"))},
           "hygiene": {"trades_excluded": n_excl}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = ((day.max() - pd.DateOffset(months=2)).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["bracket_replay.py", *common, "--out", str(tmp_path / "b1.md"), "--private-out", str(tmp_path / "replay.csv")])
    assert bracket_replay.main() in (0, None)
    args = [*common, "--report", str(tmp_path / "report.md"), "--replay-csv", str(tmp_path / "replay.csv"), "--out", str(tmp_path / "b3.md")]
    monkeypatch.setattr("sys.argv", ["candidates.py", *args])
    assert candidates.main() == 0
    text = (tmp_path / "b3.md").read_text()
    assert f"reproduces all 8 firm rows of {tmp_path / 'report.md'} character for character" in text
    assert "## Continuation by direction" in text and "| benchmark |" in text and "## Whole contracts, topstep_50k" in text
    row = next(x for x in rep.text.splitlines() if x.startswith("| topstep_50k |"))
    cells = row.split(" | ")
    cells[4] = str(int(cells[4]) + 1)  # days to pass, in sample: one character's worth of difference
    (tmp_path / "report.md").write_text(rep.text.replace(row, " | ".join(cells), 1))
    with pytest.raises(SystemExit, match="the report given .* is not the sealed run's"):
        candidates.main()  # a changed report is not the sealed one
    man["outputs"]["report_sha256"] = candidates.sha256(str(tmp_path / "report.md"))
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="refusing to report: the development firm rows"):
        candidates.main()  # and were its hash on record, its rows would still fail the gate
    rp = pd.read_csv(tmp_path / "replay.csv")
    rp[rp["variant"] != ATR_NAMES[-1]].to_csv(tmp_path / "replay.csv", index=False)
    (tmp_path / "report.md").write_text(rep.text)
    man["outputs"]["report_sha256"] = candidates.sha256(str(tmp_path / "report.md"))
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    with pytest.raises(SystemExit, match="lacks 1 of the variants"):
        candidates.main()  # a replay file without the whole grid would silently change the chain


def test_bootstrap_rows_reproduce_the_frozen_report(engine):
    bars, trades = engine
    rep = evaluate_trades(trades, bars, oos_months=2)
    last = trades["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None).max()
    mine = score(sequential_pass(trades), trading_days_of(bars), (last - pd.DateOffset(months=2)).normalize())
    for label, part in (("in sample", "development"), ("out of sample", "benchmark")):
        text = rep.text.split(f"## Bootstrap survival from the measured inputs ({label}, topstep_50k")[1].split("\n## ")[0]
        r = mine[part]["firms"].set_index("firm").loc["topstep_50k"].to_dict()
        r["firm"] = "topstep_50k"
        for c in START_CASH:
            assert format_bootstrap(c, bootstrap(r, c)) in text.splitlines()


def test_s3_bracket_maps_years_and_the_benchmark():
    """Development continuation trades take their calendar year's link (sealed before the chain), benchmark trades
    the all-development link whatever their calendar year, reversion the sealed bracket."""
    when = ["2010-03-01", "2012-11-01", "2013-05-02", "2014-06-02", "2014-09-30", "2014-10-01", "2014-12-30", "2015-02-02", "2014-06-03"]
    setup = ["continuation"] * 8 + ["reversion"]
    t = pd.DataFrame({"setup": setup, "entry_time": [pd.Timestamp(f"{w} 09:35", tz=NY) for w in when]}, index=range(10, 19))
    got = s3_bracket(t, {2013: "x", 2014: "y", "benchmark": "z"}, pd.Timestamp("2014-09-30"))
    assert list(got) == ["ledger_bracket", "ledger_bracket", "x", "y", "y", "z", "z", "z", "ledger_bracket"]
    assert list(got.index) == list(t.index)
    assert (s3_bracket(t, {}, pd.Timestamp("2014-09-30")) == "ledger_bracket").all()


def test_whole_contracts_size_in_micros_and_leave_the_sealed_brackets_unchanged(engine):
    bars, trades = engine
    # sizes: 25 points is 20 micros at $1,000 and 10 at $500; 207 points is 2 and 1 micros (83%); 300 points cannot
    # be taken at $500 and is 1 micro (60%) at $1,000; 4 points hits the 50-micro cap (40%) at $1,000
    t = trades.head(4).copy()
    t["stop_pts"] = [25.0, 207.0, 300.0, 4.0]
    t["r"] = 1.0
    t["entry_time"] = [pd.Timestamp(f"2025-01-0{i + 6} 09:35", tz=NY) for i in range(4)]
    t["exit_time"] = t["entry_time"] + pd.Timedelta(minutes=5)
    ev, fu = whole_contracts(t, 1000.0, 50), whole_contracts(t, 500.0, 50)
    assert list(ev["size"].round(4)) == [1.0, 0.828, 0.6, 0.4] and list(ev["r"].round(4)) == [1.0, 0.828, 0.6, 0.4]
    assert list(fu["size"].round(4)) == [1.0, 0.828, 0.8]  # 300 points: zero micros at $500, not taken
    t.loc[t.index[0], "stop_pts"] = np.nan
    with pytest.raises(ValueError, match="no positive stop"):
        whole_contracts(t, 500.0, 50)
    # the sealed ledger's 25 and 50-point stops size exactly, so the whole-contract rows equal the frozen ones
    last = trades["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None).max()
    cut = (last - pd.DateOffset(months=2)).normalize()
    cal = trading_days_of(bars)
    assert set(trades["stop_points"]) <= {25.0, 50.0}
    frac = score(sequential_pass(trades), cal, cut)
    whole = score_whole(trades, cal, cut)
    for per in ("development", "benchmark"):
        assert whole[per]["eval_size"] == 1.0 and whole[per]["funded_size"] == 1.0
        pd.testing.assert_frame_equal(whole[per]["firms"], frac[per]["firms"].iloc[:1])
    # and a split evaluation / funded stream is scored on its own two streams
    d = trades["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut
    st = sequential_pass(trades)
    sd = st[st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut]
    half = sd.iloc[: len(sd) // 2]
    mixed = firm_rows(sd, cal[cal <= cut], firms=("topstep_50k",), funded_part=half)
    assert mixed.iloc[0]["n_eval_starts"] == frac["development"]["firms"].iloc[0]["n_eval_starts"] and d.any()


def test_check_grid_refuses_an_incomplete_replay():
    full = pd.DataFrame({"variant": NEEDED_VARIANTS})
    check_grid(full)
    with pytest.raises(ValueError, match="lacks 2 of the variants"):
        check_grid(full[~full["variant"].isin(["hold_to_1600", ATR_NAMES[3]])])
