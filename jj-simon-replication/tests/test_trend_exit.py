import os

import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.bracket_replay import COMMISSION_RT, POINT_VALUE, dropped_rows, grid, replay
from research.trend_exit import TREND_K, TREND_NAMES, check_against_b2, paired_test, replay_trend, trend_choice, trend_variants


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    bars = synthetic_minute_bars(days=120, seed=9)
    p = tmp_path_factory.mktemp("te") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    return bars, load_trades(str(p))


def test_the_registered_family_has_no_target(engine):
    bars, t = engine
    v = trend_variants()
    assert [x["name"] for x in v] == ["trend_0.2", "trend_0.3", "trend_0.4", "trend_0.5", "trend_0.7", "trend_1"] == TREND_NAMES
    assert all(x["family"] == "atr" and np.isinf(x["rr"]) for x in v)
    rep = replay(t, bars, v)
    assert set(rep["exit_reason"]) <= {"stop", "flat_1600"} and (rep["exit_reason"] == "flat_1600").any()
    assert np.isinf(rep["target_pts"]).all()
    row = rep.iloc[0]
    tr = t.loc[int(row["trade"])]
    d = int(tr["direction"])
    assert row["r"] == pytest.approx(((row["exit"] - tr["entry"]) * d * POINT_VALUE - COMMISSION_RT) / (row["stop_pts"] * POINT_VALUE))


def test_replay_trend_refuses_another_population(engine):
    bars, t = engine
    b2 = replay(t, bars, [x for x in grid() if x["name"] in ("ledger_bracket", "hold_to_1600")])
    b2 = pd.concat([b2, dropped_rows(b2)], ignore_index=True)
    rep = replay_trend(t, bars, b2)
    assert set(rep.loc[rep["variant"] != "_dropped", "variant"]) == set(TREND_NAMES)
    short = b2[b2["trade"] != b2.loc[b2["variant"] != "_dropped", "trade"].iloc[0]]
    with pytest.raises(ValueError, match="not the same population"):
        replay_trend(t, bars, short)


def test_trend_choice_maps_years_and_the_benchmark():
    when = ["2012-03-01", "2013-05-02", "2014-06-02", "2014-10-01", "2015-02-02"]
    t = pd.DataFrame({"entry_time": [pd.Timestamp(f"{w} 09:35", tz=NY) for w in when]}, index=range(5))
    got = trend_choice(t, {2013: "trend_0.4", 2014: "trend_0.5", "benchmark": "trend_0.7"}, pd.Timestamp("2014-09-30"))
    assert list(got) == [None, "trend_0.4", "trend_0.5", "trend_0.7", "trend_0.7"]


def test_paired_test_statistic_and_rule():
    rows_t, rows_s, meta = [], [], []
    k = 0
    for y, bonus in ((2013, 0.2), (2014, 0.2), (2015, -0.1), (2016, 0.2), (2017, 0.2)):
        for i in range(40):
            day = pd.Timestamp(f"{y}-02-01 09:35", tz=NY) + pd.Timedelta(days=i)
            base = 1.0 if i % 2 else -1.0
            rows_t.append((k, "trend_0.5", base + bonus, day.isoformat()))
            rows_s.append((k, "atr_0.4_rr2.00", base, day.isoformat()))
            meta.append((k, day))
            k += 1
    cols = ["trade", "variant", "r", "exit_time"]
    trend_rep = pd.DataFrame(rows_t, columns=cols)
    b2 = pd.DataFrame(rows_s, columns=cols)
    for rep in (trend_rep, b2):
        rep["stop_pts"] = 25.0
    t = pd.DataFrame({"entry_time": [d for _, d in meta], "setup": "continuation", "direction": 1}, index=[i for i, _ in meta])
    t["pnl_dollars"] = 0.0
    tchoice = pd.Series("trend_0.5", index=t.index, dtype=object)
    s3 = pd.Series("atr_0.4_rr2.00", index=t.index, dtype=object)
    res = paired_test(t, trend_rep, b2, s3, tchoice, pd.Timestamp("2017-12-31"))
    assert res["n"] == 200 and res["delta"] == pytest.approx((4 * 0.2 - 0.1) / 5)
    d = np.array([0.2] * 80 + [-0.1] * 40 + [0.2] * 80)  # the differences: 0.2 in four years, -0.1 in one
    assert res["se"] == pytest.approx(np.std(d, ddof=1) / np.sqrt(200))  # one trade a day: the clustered SE is the plain one
    assert res["years_pos"] == 4 and res["years_n"] == 5 and res["passes"]
    tchoice.iloc[:40] = None  # entries before the chain sit out
    assert paired_test(t, trend_rep, b2, s3, tchoice, pd.Timestamp("2017-12-31"))["n"] == 160


def _paired(diffs_by_year):
    """A paired-test input with one entry a day: S3 alternates +1/-1 R, the trend exit adds the year's differences."""
    rows_t, rows_s, meta = [], [], []
    k = 0
    for y, diffs in diffs_by_year.items():
        for i, dv in enumerate(diffs):
            day = pd.Timestamp(f"{y}-02-01 09:35", tz=NY) + pd.Timedelta(days=i)
            base = 1.0 if i % 2 else -1.0
            rows_t.append((k, "trend_0.5", base + dv, day.isoformat()))
            rows_s.append((k, "atr_0.4_rr2.00", base, day.isoformat()))
            meta.append((k, day))
            k += 1
    cols = ["trade", "variant", "r", "exit_time"]
    trend_rep, b2 = pd.DataFrame(rows_t, columns=cols), pd.DataFrame(rows_s, columns=cols)
    for rep in (trend_rep, b2):
        rep["stop_pts"] = 25.0
    t = pd.DataFrame({"entry_time": [d for _, d in meta], "setup": "continuation", "direction": 1, "pnl_dollars": 0.0}, index=[i for i, _ in meta])
    return paired_test(t, trend_rep, b2, pd.Series("atr_0.4_rr2.00", index=t.index, dtype=object), pd.Series("trend_0.5", index=t.index, dtype=object), pd.Timestamp("2017-12-31"))


def test_the_rule_needs_both_p_below_alpha_and_sixty_percent_of_years():
    years = (2013, 2014, 2015, 2016, 2017)
    three = _paired({y: [0.2 if j < 3 else -0.1] * 40 for j, y in enumerate(years)})  # 3 of 5 years positive: exactly 60%
    assert three["years_pos"] == 3 and three["p"] < 0.05 and three["passes"]
    two = _paired({y: [0.2 if j < 2 else -0.1] * 40 for j, y in enumerate(years)})  # 2 of 5: significant, too few years
    assert two["years_pos"] == 2 and two["delta"] > 0 and two["p"] < 0.05 and not two["passes"]
    noisy = _paired({y: [1.0 if i % 2 else -0.9 for i in range(40)] for y in years})  # every year positive, p far above 0.05
    assert noisy["years_pos"] == 5 and noisy["p"] >= 0.05 and not noisy["passes"]


def test_where_b2s_target_never_filled_the_trend_exit_is_the_same_trade(engine):
    bars, t = engine
    names = [f"atr_{k:g}_rr2.00" for k in TREND_K if k < 1.0]
    b2 = replay(t, bars, [x for x in grid() if x["name"] in names + ["ledger_bracket"]])
    b2 = pd.concat([b2, dropped_rows(b2)], ignore_index=True)
    rep = replay_trend(t, bars, b2)
    live = b2[b2["variant"].isin(names)]
    assert check_against_b2(rep, b2) == int((live["exit_reason"] != "target").sum()) > 0
    assert (live["exit_reason"] == "target").any()
    hit = live.index[live["exit_reason"] == "target"][0]
    moved = b2.copy()
    moved.loc[hit, "r"] += 5.0  # a filled target is not compared
    check_against_b2(rep, moved)
    miss = live.index[live["exit_reason"] != "target"][0]
    moved.loc[miss, "r"] += 0.01
    with pytest.raises(ValueError, match="differs from B2's"):
        check_against_b2(rep, moved)


def _boom(*_a, **_k):
    raise ValueError("boom")


def test_cli_end_to_end_on_four_years(sealed_4y, tmp_path, monkeypatch):
    """Four years of synthetic bars (the walk-forward needs four development years), a roll, the real pipeline, the
    pinned registration; and the refusal of any other registration text."""
    from research import trend_exit
    reg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research", "preregistration_trend_exit.md")
    args = [*sealed_4y["b3"], "--registration", reg, "--out", str(tmp_path / "te.md")]
    monkeypatch.setattr("sys.argv", ["trend_exit.py", *args])
    assert trend_exit.main() == 0
    text = (tmp_path / "te.md").read_text()
    assert trend_exit.REGISTRATION_SHA256 in text and "## The test" in text and ("**Passes**" in text or "**Fails**" in text)
    assert "| S5 continuation, walk-forward trend exit | development | 2022-01-01 |" in text and "Walk-forward k, chosen on earlier development years only: 2022:" in text
    assert "S3's chain for comparison: 2022:" in text and "replays agree in R and exit time" in text
    heads = ["## The test", "## R per trade by direction", "Exit mix of the trend exit: development", "## Streams under the firm rules", "### B3 summary",
             "### Size sensitivity", "### Whole micro contracts", "### Lifetime (B4)"]
    at = [text.index(h) for h in heads]
    assert at == sorted(at)  # the test first; every section of the streams after it
    for name in ("S3 from 2022", "S5 continuation, walk-forward trend exit", "S4 from 2022", "S6 S5 + A+ reversion, from 2022"):
        assert f"| {name} | development | 2022-01-01 |" in text
    monkeypatch.setattr(trend_exit, "scoring_sections", _boom)
    assert trend_exit.main() == 0  # a failure in the firm scoring leaves the test standing
    text = (tmp_path / "te.md").read_text()
    assert "## The test" in text and "The firm scoring of the streams stopped: boom" in text
    monkeypatch.undo()
    fake = tmp_path / "reg.md"
    fake.write_text("edited")
    monkeypatch.setattr("sys.argv", ["trend_exit.py", *[str(fake) if x == reg else x for x in args]])
    with pytest.raises(SystemExit, match="is not the pinned one"):
        trend_exit.main()
