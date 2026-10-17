import json
import os

import numpy as np
import pandas as pd
import pytest

import research.jj_lab as lab
import research.jj_lab_engine_b1 as L
from research.jj_system import generate_trades as live

from tests.test_jj_system import HIGH_BEFORE, frame, opening_continuation, rally_then_red

NY = "America/New_York"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def walk(seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Four simulated weeks of full-Globex bars and a calendar that touches every news path."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(pd.Timestamp("2026-06-01 00:00", tz=NY), pd.Timestamp("2026-06-26 16:59", tz=NY), freq="1min")
    idx = idx[(idx.hour != 17) & ~((idx.dayofweek == 5) | ((idx.dayofweek == 4) & (idx.hour >= 17)) | ((idx.dayofweek == 6) & (idx.hour < 18)))]
    vol = np.where((idx.hour >= 9) & (idx.hour < 16), 6.0, 2.5)
    c = 20000 + np.cumsum(rng.standard_t(4, len(idx)) * vol / 1.4)
    o = np.r_[c[0], c[:-1]] + rng.normal(0, 0.3, len(idx))
    h = np.maximum(o, c) + np.abs(rng.normal(0, vol * 0.5))
    lo = np.minimum(o, c) - np.abs(rng.normal(0, vol * 0.5))
    q = lambda x: np.round(x * 4) / 4  # noqa: E731
    f = pd.DataFrame({"open": q(o), "high": q(h), "low": q(lo), "close": q(c), "volume": 100.0}, index=idx)
    ev = pd.DataFrame({"time": [pd.Timestamp(x, tz=NY) for x in ("2026-06-09 08:30", "2026-06-10 10:00", "2026-06-17 14:00", "2026-06-17 14:30",
                                                              "2026-06-18 08:15", "2026-06-18 08:30", "2026-06-22 10:00")],
                       "country": "USD", "impact": ["High", "Medium", "High", "High", "High", "Medium", "High"],
                       "title": ["CPI m/m", "JOLTS", "FOMC Statement", "FOMC Press Conference", "Release", "Claims", "Fed Chair Speaks"]})
    return f, ev


def test_at_its_defaults_the_lab_engine_is_the_live_system():
    f, ev = walk()
    a, b = live(f, events=ev), L.generate_trades(f, events=ev)
    assert len(a) > 300
    pd.testing.assert_frame_equal(a, b)
    for bars in (opening_continuation(20005), rally_then_red(20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)])):
        g = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
        pd.testing.assert_frame_equal(live(g), L.generate_trades(g))


def test_every_version_of_batch_1_runs_and_changes_something():
    f, ev = walk()
    base = live(f, events=ev)
    b = json.load(open(os.path.join(ROOT, "research/jj_lab/batch_01.json")))
    assert len(b["variants"]) == 15 and b["engine"] == "research.jj_lab_engine_b1"
    for name, v in b["variants"].items():
        t = L.generate_trades(f, lab.config(L, v["dials"]), events=ev)
        if name == "L03":  # three losing attempts then an A+ before the window ends: none in these four weeks
            one = L.generate_trades(f, L.LabConfig(max_reversion_losses=1), events=ev)
            assert not L.generate_trades(f, L.LabConfig(max_reversion_losses=1, fourth_aplus=True), events=ev).equals(one)
            continue
        if name in ("L07", "L08"):  # no news candle or 18:00 gap over 50 points in these four weeks: see the tests below
            continue
        assert not t.equals(base), name  # every other dial matters somewhere in four simulated weeks


def test_the_dials_do_what_they_say():
    f, ev = walk()
    run = lambda **kw: L.generate_trades(f, L.LabConfig(**kw), events=ev)  # noqa: E731
    assert run(book=False).query("session == 'book'").empty
    capped = run(book_max_levels=2)
    assert (capped.query("session == 'book'").groupby("trading_day").size() <= 2).all()
    assert run(layering=False)["layer"].sum() == 0
    assert run(allow_grade_a=False).query("setup == 'reversion' and grade == 'A'").empty
    ny = run(half_in_ny=False).query("session in ['09:30', '14:00', 'news', 'fri']")
    assert (ny["target_points"] != 19.0).all()
    ev_half = run(evening_force_half=True).query("setup == 'reversion' and session in ['18:00', '20:00']")
    assert len(ev_half) and (ev_half["target_points"] == 19.0).all()
    pm = run(pm_minutes=60).query("session == '14:00'")
    assert (pd.to_datetime(pm["signal_time"]).dt.tz_convert(NY).dt.hour < 15).all()


def test_a_huge_news_candle_is_continued_only_in_its_version():
    bars = {"2026-10-15 08:27": (20000, 20000, 19998, 20000), "2026-10-15 08:29": (20000, 20000.5, 19999.5, 20000.25),
            "2026-10-15 08:30": (20000, 20000.5, 19939, 19940), "2026-10-15 08:31": (19940, 19941, 19920, 19921)}  # a 60-point red candle
    g = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    ev = pd.DataFrame({"time": [pd.Timestamp("2026-10-15 08:30", tz=NY)], "country": ["USD"], "impact": ["High"], "title": ["CPI m/m"]})
    assert L.generate_trades(g, events=ev).query("session == 'news' and setup == 'continuation'").empty
    t = L.generate_trades(g, L.LabConfig(news_cont_body=50.0), events=ev).query("session == 'news' and setup == 'continuation'")
    assert len(t) == 1 and t.iloc[0]["direction"] == "short" and t.iloc[0]["target_points"] == 76.0


def test_no_continuation_into_a_huge_evening_gap_only_in_its_version():
    bars = {"2026-10-14 18:00": (19940, 19945, 19938, 19944), "2026-10-14 18:01": (19944, 19946, 19941, 19942),  # a 60-point gap down
            "2026-10-14 18:02": (19942, 19945.5, 19940, 19945), "2026-10-14 18:03": (19945, 19949, 19945, 19948),  # breaks the 18:01 high
            "2026-10-14 18:30": (19948, 20000, 19948, 19999)}
    g = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    t = L.generate_trades(g).query("session == '18:00' and setup == 'continuation'")
    assert len(t) == 1 and t.iloc[0]["direction"] == "long"  # toward the gap, as the live system does
    assert L.generate_trades(g, L.LabConfig(evening_max_gap=50.0)).query("session == '18:00' and setup == 'continuation'").empty


def test_the_comparison_needs_20_days_and_a_bound_clear_of_zero():
    days = [f"2026-10-{d:02d}" for d in range(1, 31)]
    jj = pd.Series(0.0, index=days)
    better = pd.Series(np.r_[np.full(30, 1.0)] + np.tile([0.1, -0.1], 15), index=days)
    assert lab.compare(better.iloc[:19], jj, 15)["verdict"] == "too early"
    assert lab.compare(better, jj, 15)["verdict"] == "beats JJ"
    assert lab.compare(-better, jj, 15)["verdict"] == "trails JJ"
    noisy = pd.Series(np.tile([3.0, -3.0], 15), index=days)
    assert lab.compare(noisy, jj, 15)["verdict"] == "too early"


def test_daily_r_counts_a_quiet_day_as_zero():
    s = lab.daily_r([{"date": "2026-10-19", "r": 1.5}, {"date": "2026-10-19", "r": -1.0}], ["2026-10-19", "2026-10-20"])
    assert s.to_dict() == {"2026-10-19": pytest.approx(0.5), "2026-10-20": 0.0}
