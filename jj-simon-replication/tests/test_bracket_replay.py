import numpy as np
import pandas as pd
import pytest

from research.bracket_replay import COMMISSION_RT, POINT_VALUE, SLIPPAGE, grid, r_of, replay, replay_one, stop_points_for
from tests.test_anatomy import _bars, _trade

NY = "America/New_York"


def test_first_touch_order_target_then_stop():
    o = np.array([100.0, 101.0, 102.0]); h = np.array([105.0, 110.0, 139.0]); l = np.array([98.0, 97.0, 99.0]); c = np.array([101.0, 102.0, 130.0])
    xp, reason, held, amb = replay_one(o, h, l, c, 1, 100.0, 25.0, 38.0)
    assert reason == "target" and xp == 138.0 and held == 3 and not amb
    assert r_of(xp, 100.0, 1, 25.0) == pytest.approx((38 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE))


def test_ambiguous_bar_is_a_stop():
    o = np.array([100.0, 101.0]); h = np.array([105.0, 139.0]); l = np.array([98.0, 74.0]); c = np.array([101.0, 120.0])
    xp, reason, held, amb = replay_one(o, h, l, c, 1, 100.0, 25.0, 38.0)
    assert reason == "stop" and xp == 75.0 - SLIPPAGE and held == 2 and amb
    assert r_of(xp, 100.0, 1, 25.0) == pytest.approx((-25.25 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE))


def test_short_side_and_flat_at_close():
    o = np.array([100.0, 100.0]); h = np.array([110.0, 112.0]); l = np.array([95.0, 90.0]); c = np.array([100.0, 97.0])
    xp, reason, held, amb = replay_one(o, h, l, c, -1, 100.0, 25.0, 38.0)
    assert reason == "flat_1600" and xp == 97.0 + SLIPPAGE and held == 2
    assert r_of(xp, 100.0, -1, 25.0) == pytest.approx((2.75 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE))


def test_replay_on_bars_respects_16_00_and_late_entry():
    bars = _bars(days=3)
    day = bars.index[0].normalize()
    e = day.replace(hour=9, minute=40)
    i0 = bars.index.get_loc(e)
    # no touch all day; a +500 spike at 16:00 (outside the window) must not count; the 15:59 close is the exit
    extra = pd.DataFrame({"open": 20000.0, "high": 20500.0, "low": 20000.0, "close": 20000.0}, index=[day.replace(hour=16, minute=0)])
    bars2 = pd.concat([bars, extra]).sort_index()
    bars2.iloc[bars2.index.get_loc(day.replace(hour=15, minute=59)), bars2.columns.get_loc("close")] = 20003.0
    late = day.replace(hour=15, minute=59)
    t = pd.DataFrame([_trade(e, day.replace(hour=15, minute=59), 1, 20000.0, 0.1, reason="session_end"),
                      _trade(late, late, -1, 20000.0, 0.0, reason="session_end")])
    t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
    rep = replay(t, bars2, [v for v in grid() if v["family"] == "fixed"])
    r0 = rep[rep["trade"] == 0].iloc[0]
    assert r0["exit_reason"] == "flat_1600" and r0["exit"] == pytest.approx(20003.0 - SLIPPAGE) and r0["bars_held"] == bars2.index.get_loc(day.replace(hour=15, minute=59)) - i0 + 1
    r1 = rep[rep["trade"] == 1].iloc[0]
    assert r1["bars_held"] == 1 and r1["exit_reason"] == "flat_1600"


def test_scaled_stops_use_prior_session_context_and_tick_rounding():
    v_atr = {"family": "atr", "k": 0.1, "rr": 1.52}
    v_or = {"family": "or_prev", "k": 0.5, "rr": 1.52}
    v_px = {"family": "price", "k": 0.001, "rr": 1.52}
    assert stop_points_for(v_atr, 123.4, 10.0, 20000.0) == pytest.approx(12.25)
    assert stop_points_for(v_or, 123.4, 10.0, 20000.0) == pytest.approx(5.0)
    assert stop_points_for(v_px, 123.4, 10.0, 20000.0) == pytest.approx(20.0)
    assert np.isnan(stop_points_for(v_or, 123.4, float("nan"), 20000.0))
    assert stop_points_for(v_atr, 1.0, 10.0, 20000.0) == 2.0  # floor
    names = [v["name"] for v in grid()]
    assert names[0] == "fixed_25_38" and len(names) == 1 + 7 * 3 + 6 + 5 and len(set(names)) == len(names)
