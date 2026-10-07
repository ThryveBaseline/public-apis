import numpy as np
import pandas as pd
import pytest

from research.bracket_replay import COMMISSION_RT, POINT_VALUE, SLIPPAGE, grid, r_of, replay, replay_one, report, stop_points_for
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
    bars = _bars(days=40)
    day = sorted(set(bars.index.normalize()))[30]
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
    assert names[:2] == ["ledger_bracket", "fixed_25_38"] and len(names) == 2 + 7 * 3 + 6 + 5 and len(set(names)) == len(names)


def test_common_population_and_reproduction_check():
    bars = _bars(days=40)
    days = sorted(set(bars.index.normalize()))
    rows = []
    # A: too early for a previous-session ATR -> dropped for every variant
    e0 = days[2].replace(hour=9, minute=40)
    rows.append(_trade(e0, e0 + pd.Timedelta(minutes=5), 1, 20000.25, 1.0))
    # B: sealed wide-open bracket 50/75 reaching its target
    eB = days[20].replace(hour=9, minute=40); iB = bars.index.get_loc(eB)
    bars.iloc[iB + 3, bars.columns.get_loc("high")] = 20000.25 + 80
    tB = _trade(eB, bars.index[iB + 3], 1, 20000.25, 0.0, stop=50.0, target=75.0, reason="target")
    tB["r"] = (75 * POINT_VALUE - COMMISSION_RT) / (50 * POINT_VALUE); rows.append(tB)
    # C: 25/38 short stopped out
    eC = days[22].replace(hour=10, minute=0); iC = bars.index.get_loc(eC)
    bars.iloc[iC + 2, bars.columns.get_loc("high")] = 20000.25 + 30
    tC = _trade(eC, bars.index[iC + 2], -1, 20000.25, 0.0, reason="stop")
    tC["r"] = (-25.25 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE); rows.append(tC)
    # D: a ledger session_end exit
    eD = days[25].replace(hour=10, minute=30)
    rows.append(_trade(eD, days[25].replace(hour=15, minute=59), 1, 20000.25, 0.0, reason="session_end"))
    t = pd.DataFrame(rows)
    t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
    rep = replay(t, bars, grid())
    assert rep.attrs["n_no_context"] == 1
    per_variant = rep.groupby("variant")["trade"].nunique()
    assert per_variant.nunique() == 1 and per_variant.iloc[0] == 3
    text = report(t, rep, days[30].strftime("%Y-%m-%d"), 0, 0, 0, rep.attrs["n_no_context"])
    assert "reaches the same exit reason on 100.00% and the largest absolute R difference is 0.0000" in text
    assert "1 ledger `session_end` trades" in text and "1 sealed wide-open trades that carried 50/75" in text
    assert "1 entries dropped for every variant" in text


def test_report_end_to_end_formats_walk_forward_rows():
    """Six development years on synthetic bars so the sequential chain has rows to format."""
    rng = np.random.default_rng(1)
    idx = []
    d0 = pd.Timestamp("2018-01-08", tz=NY)
    k = 0
    while len(idx) < 7 * 60:
        day = d0 + pd.offsets.BDay(k); k += 1
        idx.append(pd.date_range(day.replace(hour=9, minute=30), day.replace(hour=16), freq="1min", inclusive="left"))
    index = idx[0].append(idx[1:])
    n = len(index)
    px = 7000 + rng.normal(0, 3, n).cumsum()
    bars = pd.DataFrame({"open": px, "high": px + np.abs(rng.normal(0, 4, n)), "low": px - np.abs(rng.normal(0, 4, n)), "close": px + rng.normal(0, 1, n)}, index=index)
    bars["symbol"] = "A"
    days = sorted(set(index.normalize()))
    rows = []
    for j, d in enumerate(days):
        if j < 16 or j % 3:
            continue
        e = d.replace(hour=9, minute=35 + (j % 20)); i = index.get_loc(e)
        rows.append(_trade(e, e + pd.Timedelta(minutes=15), 1 if j % 2 else -1, float(bars["open"].iloc[i]) + 0.25, 0.0,
                           setup="continuation" if j % 2 else "reversion", reason="stop"))
    t = pd.DataFrame(rows); t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
    rep = replay(t, bars, grid())
    oos = days[-30].strftime("%Y-%m-%d")
    text = report(t, rep, oos, 0, 0, 0, rep.attrs["n_no_context"])
    assert "### Sequential walk-forward, family `all`" in text
    assert "| sealed bracket in year |" in text
    assert "Trade-weighted out-of-year expectancy of the chain" in text
    assert "Reproduction check, ledger bracket" in text
