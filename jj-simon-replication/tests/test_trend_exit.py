import json
import os

import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.bracket_replay import COMMISSION_RT, POINT_VALUE, dropped_rows, grid, replay
from research.trend_exit import (TREND_NAMES, paired_test, replay_trend, trend_choice, trend_variants)


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
    assert res["years_pos"] == 4 and res["years_n"] == 5 and res["passes"]  # one trade a day: the clustered SE of a constant shift is ~0
    tchoice.iloc[:40] = None  # entries before the chain sit out
    assert paired_test(t, trend_rep, b2, s3, tchoice, pd.Timestamp("2017-12-31"))["n"] == 160


def test_cli_end_to_end_on_four_years(tmp_path, monkeypatch):
    """Four years of synthetic bars (the walk-forward needs four development years), a roll, the real pipeline, the
    pinned registration; and the refusal of any other registration text."""
    from fpt.data import load_minute_bars, roll_days
    from fpt.evaluate import evaluate_trades
    from research import bracket_replay, candidates, trend_exit
    from research.anatomy import exclude_roll_trades
    bars = synthetic_minute_bars(days=1080, seed=5, start="2019-01-07")
    bars["symbol"] = np.where(bars.index < bars.index[len(bars) // 2], 1000, 1001)
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    csv = tmp_path / "bars.csv"
    out.to_csv(csv)
    loaded = load_minute_bars(str(csv), source_tz="UTC")
    rolls = sorted(roll_days(loaded))
    led = tmp_path / "trades.csv"
    generate_trades(loaded, StrategyConfig()).to_csv(led, index=False)
    trades = load_trades(str(led))
    rep = evaluate_trades(trades, loaded, exclude_dates=rolls, oos_months=3)
    (tmp_path / "report.md").write_text(rep.text)
    kept, n_excl = exclude_roll_trades(trades, rolls)
    man = {"data": {"roll_dates_excluded": [str(d) for d in rolls], "sha256": candidates.sha256(str(csv))},
           "outputs": {"n_trades": len(trades), "trades_sha256": candidates.sha256(str(led)), "report_sha256": candidates.sha256(str(tmp_path / "report.md"))},
           "hygiene": {"trades_excluded": n_excl}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = ((day.max() - pd.DateOffset(months=3)).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["bracket_replay.py", *common, "--out", str(tmp_path / "b1.md"), "--private-out", str(tmp_path / "replay.csv")])
    assert bracket_replay.main() in (0, None)
    reg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research", "preregistration_trend_exit.md")
    args = [*common, "--report", str(tmp_path / "report.md"), "--replay-csv", str(tmp_path / "replay.csv"), "--registration", reg, "--out", str(tmp_path / "te.md")]
    monkeypatch.setattr("sys.argv", ["trend_exit.py", *args])
    assert trend_exit.main() == 0
    text = (tmp_path / "te.md").read_text()
    assert trend_exit.REGISTRATION_SHA256 in text and "## The test" in text and ("**Passes**" in text or "**Fails**" in text)
    assert "| S5 continuation, walk-forward trend exit | development |" in text and "Walk-forward k, chosen on earlier development years only: 2022:" in text
    fake = tmp_path / "reg.md"
    fake.write_text("edited")
    monkeypatch.setattr("sys.argv", ["trend_exit.py", *[str(fake) if x == reg else x for x in args]])
    with pytest.raises(SystemExit, match="is not the pinned one"):
        trend_exit.main()
