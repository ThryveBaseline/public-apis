import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from fpt.evaluate import evaluate_trades, trading_days_of
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.bracket_replay import dropped_rows, grid, replay, walk_forward
from research.candidates import (ATR_NAMES, FIRMS, build_streams, format_row, hold_drift, mean_se, pooled_choices, score,
                                 sealed_firm_rows, variant_frame)
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
    streams, chain, s3_choice = build_streams(t, bars, rep, cut)
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


def test_hold_drift_is_the_direction_call_beyond_the_drift(engine):
    bars, trades = engine
    rep = replay(trades, bars, [v for v in grid() if v["name"] in ("hold_to_1600", "ledger_bracket")])
    cont = sorted(set(rep["trade"]) & set(trades.index[trades["setup"].astype(str) == "continuation"]))
    assert len(cont) > 20
    days = trading_days_of(bars)
    cut = days[len(days) // 2]
    roll = [trades.loc[cont[0], "entry_time"].tz_convert(NY).date()]  # treated as a roll date: no baseline, no trades
    ids = [k for k in cont if trades.loc[k, "entry_time"].tz_convert(NY).date() not in roll]
    dr = hold_drift(trades, bars, rep, ids, cut, roll)
    assert set(dr.loc[dr["period"] == "benchmark", "label"]) == {"benchmark"} and set(dr["period"]) == {"development", "benchmark"}
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
    with pytest.raises(ValueError, match="fall on roll dates"):
        hold_drift(trades, bars, rep, [cont[0]], cut, roll)


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
    (tmp_path / "manifest.json").write_text(json.dumps({"data": {"roll_dates_excluded": [str(d) for d in rolls]},
                                                        "outputs": {"n_trades": len(trades)}, "hygiene": {"trades_excluded": n_excl}}))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = ((day.max() - pd.DateOffset(months=2)).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["bracket_replay.py", *common, "--out", str(tmp_path / "b1.md"), "--private-out", str(tmp_path / "replay.csv")])
    assert bracket_replay.main() in (0, None)
    args = [*common, "--report", str(tmp_path / "report.md"), "--replay-csv", str(tmp_path / "replay.csv"), "--out", str(tmp_path / "b3.md")]
    monkeypatch.setattr("sys.argv", ["candidates.py", *args])
    assert candidates.main() == 0
    text = (tmp_path / "b3.md").read_text()
    assert "reproduces all 8 firm rows of sealed/run1/report.md character for character" in text
    assert "## Continuation by direction" in text and "| benchmark |" in text
    row = next(x for x in rep.text.splitlines() if x.startswith("| topstep_50k |"))
    cells = row.split(" | ")
    cells[4] = str(int(cells[4]) + 1)  # days to pass, in sample: one character's worth of difference
    (tmp_path / "report.md").write_text(rep.text.replace(row, " | ".join(cells), 1))
    with pytest.raises(SystemExit, match="refusing to report: the development firm rows"):
        candidates.main()
