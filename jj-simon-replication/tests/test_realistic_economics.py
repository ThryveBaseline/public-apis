import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import realistic_economics as rex
from research.b5_paths import TOPSTEPX, day_arrays, simulate
from research.forward import candidate_trades, rth_sessions

NY = "America/New_York"


def test_the_worst_excursion():
    idx = pd.date_range(pd.Timestamp("2026-03-02 09:30", tz=NY), periods=6, freq="1min")
    bars = pd.DataFrame({"open": 100.0, "high": [101, 102, 103, 104, 105, 106], "low": [99, 97, 98, 96, 99, 100], "close": 100.0}, index=idx)
    t = pd.DataFrame({"entry_time": [idx[1], idx[1]], "exit_time": [idx[3], idx[4]], "direction": ["long", "short"], "entry": [100.0, 100.0]})
    # long: the lowest low from the entry bar to the exit bar, both included (96); short: the highest high (105)
    assert list(rex.mae_points(t, bars)) == [4.0, 5.0]


@pytest.fixture(scope="module")
def setup():
    bars = synthetic_minute_bars(days=300, seed=11, start="2025-01-06")
    bars["symbol"] = "1001"
    pre = candidate_trades(bars, [])["S4"].copy()
    pre["mae_points"] = rex.mae_points(pre, bars)
    return pre, rth_sessions(bars.index)


def test_the_real_fee_buys_fewer_micros(setup):
    pre, _ = setup
    a = rex.micro_stream(pre, 1000.0, 50, 0.50)
    b = rex.micro_stream(pre, 1000.0, 50, 1.22)
    common = a.index.intersection(b.index)
    assert (b.loc[common, "micros"] <= a.loc[common, "micros"]).all() and (b.loc[common, "micros"] < a.loc[common, "micros"]).any()
    same = common[(b.loc[common, "micros"] == a.loc[common, "micros"]).to_numpy()]
    assert (b.loc[same, "r"] < a.loc[same, "r"]).all()  # the same micros cost more: every trade comes out lower
    assert (a["w"] <= a["r"] + 1e-12).all() and (a["w"] <= 0).all()


def test_dips_change_nothing_when_no_trade_ever_goes_against(setup):
    pre, sessions = setup
    flat = pre.assign(mae_points=0.0)
    # no fee charged up front and no adverse excursion: the two-step trade is the one-step trade, on every path
    x = rex.run_variant(flat, sessions, sessions[-1], "wait", 3, 0.0, dips=False)
    y = rex.run_variant(flat, sessions, sessions[-1], "wait", 3, 0.0, dips=True)
    assert x["paths"] > 10 and x.keys() == y.keys()
    for k in x:
        assert x[k] == y[k] or (np.isnan(x[k]) and np.isnan(y[k])), k
    real = rex.run_variant(pre, sessions, sessions[-1], "wait", 3, 1.22, dips=True)
    assert real["cash_mean"] <= x["cash_mean"]


def test_a_dip_through_the_limit_fails_the_account():
    dates = pd.bdate_range("2026-03-02", periods=5)
    win = [np.array([0.5])] + [np.zeros(0)] * 4  # a winner of half the evaluation budget on day one
    dip = [np.array([-2.1, 2.6])] + [np.zeros(0)] * 4  # the same trade, first $2,100 against: through the $2,000 limit
    out = {}
    for name, rows in (("closed", win), ("dips", dip)):
        r = day_arrays(rows, 2)
        res = simulate(dates, r, r, np.array([0]), np.array([5]), TOPSTEPX, "ask", 1)
        out[name] = [o for _, _, o, _ in res["eval_log"]]
    assert "fail" not in out["closed"] and out["dips"][0] == "fail"


def test_split_rows_interleave_the_worst_point(setup):
    pre, sessions = setup
    st = rex.micro_stream(pre, 500.0, 50, 1.22)
    dates = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(st["entry_time"]).tz_convert(NY).tz_localize(None).normalize())))
    one, two = rex.split_rows(st, dates, False), rex.split_rows(st, dates, True)
    for a, b in zip(one, two):
        assert len(b) == 2 * len(a) and np.allclose(b[0::2] + b[1::2], a)
