import numpy as np
import pandas as pd

from research.jj_system import JJConfig, generate_trades, trading_days

NY = "America/New_York"


def frame(start: str, end: str, price: float = 20000.0, spikes: dict | None = None, bars: dict | None = None) -> pd.DataFrame:
    """Flat 1-minute bars from start to end (New York time), the 17:00-17:59 halt and weekends left out, with some
    bars replaced: `bars` maps 'YYYY-MM-DD HH:MM' to (open, high, low, close); a flat bar copies the last close."""
    idx = pd.date_range(pd.Timestamp(start, tz=NY), pd.Timestamp(end, tz=NY), freq="1min")
    idx = idx[(idx.hour != 17) & ~((idx.dayofweek == 5) | ((idx.dayofweek == 4) & (idx.hour >= 17)) | ((idx.dayofweek == 6) & (idx.hour < 18)))]
    bars = {pd.Timestamp(k, tz=NY): v for k, v in (bars or {}).items()}
    spikes = {pd.Timestamp(k, tz=NY): v for k, v in (spikes or {}).items()}
    rows, last = [], price
    for ts in idx:
        if ts in bars:
            o, h, l, c = bars[ts]
        else:
            o = h = l = c = last
            if ts in spikes:
                h = spikes[ts]
        rows.append((o, h, l, c, 100.0))
        last = c
    return pd.DataFrame(rows, index=idx, columns=["open", "high", "low", "close", "volume"])


HIGH_BEFORE = {"2026-10-13 10:00": 21000.0}  # an old all-time high far above, outside the structure window


def test_trading_day_runs_from_the_evening():
    idx = pd.DatetimeIndex([pd.Timestamp("2026-10-14 17:59", tz=NY), pd.Timestamp("2026-10-14 18:00", tz=NY), pd.Timestamp("2026-10-15 16:59", tz=NY),
                            pd.Timestamp("2026-10-18 18:00", tz=NY)])
    assert [str(pd.Timestamp(x).date()) for x in trading_days(idx)] == ["2026-10-14", "2026-10-15", "2026-10-15", "2026-10-19"]


def opening_continuation(body_close: float) -> dict:
    return {"2026-10-15 09:27": (20000, 20002, 20000, 20000),  # a swing high at 20002
            "2026-10-15 09:29": (20000.5, 20000.5, 19999.75, 20000),  # a small red candle the opening candle displaces
            "2026-10-15 09:30": (20000, body_close + 1, 20000, body_close),  # green, closes through it
            "2026-10-15 09:31": (body_close, body_close + 1, body_close - 1, body_close),
            "2026-10-15 10:20": (body_close, body_close + 80, body_close, body_close + 79)}


def test_the_opening_continuation_and_its_bracket():
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=opening_continuation(20005)))
    c = t[t["setup"] == "continuation"]
    assert len(c) == 1
    x = c.iloc[0]
    assert x["session"] == "09:30" and x["direction"] == "long" and x["grade"] == "A+" and x["contracts"] == 2
    assert x["entry_time"] == pd.Timestamp("2026-10-15 09:31", tz=NY) and x["entry"] == 20005.25
    assert (x["stop_points"], x["target_points"], x["exit_reason"]) == (25.0, 38.0, "target")
    assert np.isclose(x["r"], (38 * 20 * 2 - 10) / 1000)


def test_a_big_opening_candle_takes_50_76_at_half_size():
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=opening_continuation(20030)))
    x = t[t["setup"] == "continuation"].iloc[0]
    assert (x["stop_points"], x["target_points"], x["contracts"], x["exit_reason"]) == (50.0, 76.0, 1, "target")


def rally_then_red(top_close: float, red_close: float, after: list) -> dict:
    """A doji open at 20000, a rally of green candles, then a red displacement."""
    b = {"2026-10-15 09:30": (20000, 20000, 20000, 20000)}
    steps = np.linspace(20000, top_close, 6)
    for k in range(5):
        b[f"2026-10-15 09:{40 + k}"] = (steps[k], steps[k + 1] + 0.5, steps[k], steps[k + 1])
    b["2026-10-15 09:45"] = (top_close, top_close + 0.5, red_close, red_close)
    for k, v in enumerate(after):
        b[f"2026-10-15 09:{46 + k}"] = v
    return b


def test_a_reversion_with_room_takes_25_38():
    bars = rally_then_red(20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)])
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars))
    x = t[t["setup"] == "reversion"].iloc[0]
    assert x["session"] == "09:30" and x["direction"] == "short" and x["grade"] == "A" and not x["layer"]
    assert (x["stop_points"], x["target_points"], x["contracts"], x["exit_reason"]) == (25.0, 38.0, 2, "target")
    assert x["entry_time"] == pd.Timestamp("2026-10-15 09:46", tz=NY)


def test_15_to_30_points_of_room_takes_12_5_19_at_double_size():
    bars = rally_then_red(20024, 20018, [(20018, 20018.5, 20017, 20017), (20017, 20017, 19995, 19996)])
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars))
    x = t[t["setup"] == "reversion"].iloc[0]
    assert (x["stop_points"], x["target_points"], x["contracts"], x["exit_reason"]) == (12.5, 19.0, 4, "target")


def test_no_reversion_under_15_points_or_without_a_move_away():
    bars = rally_then_red(20016, 20012, [(20012, 20012, 19990, 19990)])  # 12 points of room
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars))
    assert t[t["setup"] == "reversion"].empty


def test_at_all_time_highs_a_displacement_short_is_not_taken():
    bars = rally_then_red(20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)])
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", bars=bars))  # no older high: the rally is a new high
    assert t[t["setup"] == "reversion"].empty


def test_a_second_account_once_the_first_is_halfway():
    after = [(20046, 20046.5, 20036, 20037), (20037, 20037, 20025, 20026),  # the first short is 20 points in profit
             (20026, 20027, 20025.5, 20026.5), (20026.5, 20026.5, 20018, 20019),
             (20019, 20019, 19990, 19992)]
    bars = rally_then_red(20060, 20046, after)
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars))
    r = t[t["setup"] == "reversion"]
    assert len(r) == 2 and not r.iloc[0]["layer"] and r.iloc[1]["layer"] and r.iloc[1]["attempt"] == r.iloc[0]["attempt"]
    # the layer: three red candles together displace the last green one, with 26 points of room left (12.5/19); the
    # 09:49 break is not a third account, since the second is not yet halfway
    assert r.iloc[1]["signal_time"] == pd.Timestamp("2026-10-15 09:47", tz=NY) and r.iloc[1]["target_points"] == 19.0
    assert (r["exit_reason"] == "target").all()


def test_news_session_only_on_a_release_day():
    bars = {"2026-10-15 08:30": (20000, 20000.5, 19960, 19962),  # the news candle drops 38 points
            "2026-10-15 08:31": (19962, 19963, 19958, 19959), "2026-10-15 08:32": (19959, 19966, 19958.5, 19965),  # red, then green displacing it
            "2026-10-15 08:33": (19965, 20010, 19965, 20008)}  # 35 points of room after a 42-point move: 25/38
    f = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    assert generate_trades(f).query("session == 'news'").empty
    ev = pd.DataFrame({"time": [pd.Timestamp("2026-10-15 08:30", tz=NY)], "country": ["USD"], "impact": ["High"], "title": ["CPI m/m"]})
    t = generate_trades(f, events=ev)
    x = t[t["session"] == "news"].iloc[0]
    assert x["direction"] == "long" and x["anchor"] == 20000 and x["exit_reason"] == "target" and x["target_points"] == 38.0


def test_positions_close_at_the_firm_end_of_day():
    bars = opening_continuation(20005)
    del bars["2026-10-15 10:20"]
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars))
    x = t[t["setup"] == "continuation"].iloc[0]
    assert x["exit_reason"] == "firm_close" and x["exit_time"] == pd.Timestamp("2026-10-15 16:09", tz=NY)


def test_the_overnight_book_sells_breaks_back_toward_the_morning_open():
    bars = {"2026-10-14 09:30": (20000, 20000, 20000, 20000)}
    for k in range(10):  # a staircase up from 20000 to 20100 in the afternoon, leaving swing lows
        p = 20000 + 10 * k
        bars[f"2026-10-14 13:{10 + 2 * k:02d}"] = (p, p + 12, p + 5, p + 10)
        bars[f"2026-10-14 13:{11 + 2 * k:02d}"] = (p + 10, p + 11, p + 4, p + 10)
    bars["2026-10-14 13:31"] = (20100, 20101, 20099, 20100)
    bars["2026-10-14 23:00"] = (20100, 20100, 20040, 20041)  # overnight it falls through the lows
    f = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    t = generate_trades(f, days=[pd.Timestamp("2026-10-15")])
    b = t[t["session"] == "book"]
    assert len(b) >= 1 and (b["direction"] == "short").all() and (b["entry_kind"] == "stop").all()
    assert (b["entry_time"] == pd.Timestamp("2026-10-14 23:00", tz=NY)).all()


def test_a_later_start_gives_the_same_trades():
    bars = rally_then_red(20045, 20036, [(20036, 20036.5, 20035, 20035), (20035, 20035, 19990, 19992)])
    bars.update({k: v for k, v in opening_continuation(20005).items() if "09:3" not in k})
    full = generate_trades(frame("2026-10-12 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars), days=[pd.Timestamp("2026-10-15")])
    late = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars), days=[pd.Timestamp("2026-10-15")])
    pd.testing.assert_frame_equal(full, late)
    assert len(full)


def test_the_config_is_his_numbers():
    c = JJConfig()
    assert (c.stop, c.target, c.half_stop, c.half_target, c.wide_stop, c.wide_target) == (25, 38, 12.5, 19, 50, 76)
    assert (c.room_full, c.room_half, c.max_reversion_losses, c.continuation_minutes) == (30, 15, 3, 5)


def test_a_missing_minute_does_not_drop_the_entry():
    f = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=opening_continuation(20005))
    f = f.drop(pd.Timestamp("2026-10-15 09:31", tz=NY))  # no trade in that minute
    x = generate_trades(f).query("setup == 'continuation'").iloc[0]
    assert x["entry_time"] == pd.Timestamp("2026-10-15 09:32", tz=NY)


def test_an_evening_wick_above_the_high_does_not_block_a_morning_short():
    bars = rally_then_red(20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)])
    spikes = {"2026-10-14 18:05": 21000.25}  # one tick above the old high, the evening before
    t = generate_trades(frame("2026-10-13 08:00", "2026-10-15 16:59", spikes={**HIGH_BEFORE, **spikes}, bars=bars))
    assert len(t[(t["setup"] == "reversion") & (t["session"] == "09:30")]) == 1


def test_no_continuation_of_the_fomc_candle():
    bars = {"2026-10-15 13:57": (20000, 20002, 20000, 20000), "2026-10-15 13:59": (20000.5, 20000.5, 19999.75, 20000),
            "2026-10-15 14:00": (20000, 20011, 20000, 20010), "2026-10-15 14:30": (20010, 20060, 20010, 20058)}
    f = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    assert len(generate_trades(f).query("session == '14:00' and setup == 'continuation'")) == 1
    ev = pd.DataFrame({"time": [pd.Timestamp("2026-10-15 14:00", tz=NY)], "country": ["USD"], "impact": ["High"], "title": ["FOMC Statement"]})
    assert generate_trades(f, events=ev).query("session == '14:00' and setup == 'continuation'").empty


def test_the_book_is_placed_and_cancelled_without_the_exact_minutes():
    bars = {"2026-10-14 09:30": (20000, 20000, 20000, 20000)}
    for k in range(10):
        p = 20000 + 10 * k
        bars[f"2026-10-14 13:{10 + 2 * k:02d}"] = (p, p + 12, p + 5, p + 10)
        bars[f"2026-10-14 13:{11 + 2 * k:02d}"] = (p + 10, p + 11, p + 4, p + 10)
    bars["2026-10-14 13:31"] = (20100, 20101, 20099, 20100)
    bars["2026-10-15 10:00"] = (20100, 20100, 20040, 20041)  # falls through the lows after the book is cancelled
    f = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars)
    f = f.drop([pd.Timestamp("2026-10-14 21:29", tz=NY), pd.Timestamp("2026-10-15 09:29", tz=NY)])
    assert generate_trades(f, days=[pd.Timestamp("2026-10-15")]).query("session == 'book'").empty
    bars["2026-10-14 23:00"] = (20100, 20100, 20040, 20041)
    f2 = frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=HIGH_BEFORE, bars=bars).drop(pd.Timestamp("2026-10-14 21:29", tz=NY))
    assert len(generate_trades(f2, days=[pd.Timestamp("2026-10-15")]).query("session == 'book'")) >= 1
