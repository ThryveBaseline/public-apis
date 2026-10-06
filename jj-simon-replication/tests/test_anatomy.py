import numpy as np
import pandas as pd
import pytest

from research.anatomy import anatomy, daily_context, excursions, exclude_roll_trades, load_trades

NY = "America/New_York"


def _bars(days=20, start="2025-01-06"):
    idx = []
    d0 = pd.Timestamp(start, tz=NY)
    for k in range(days * 2):  # skip weekends crudely by stepping business days
        day = d0 + pd.offsets.BDay(k)
        idx.append(pd.date_range(day.replace(hour=9, minute=30), day.replace(hour=16, minute=0), freq="1min", inclusive="left"))
        if len(idx) >= days:
            break
    index = idx[0].append(idx[1:])
    n = len(index)
    base = 20000.0 + np.arange(n) * 0.0
    df = pd.DataFrame({"open": base, "high": base + 5, "low": base - 5, "close": base}, index=index)
    return df


def _trade(entry_time, exit_time, direction, entry, r, stop=25.0, target=38.0, setup="continuation", reason="target"):
    return {"signal_time": entry_time, "entry_time": entry_time, "exit_time": exit_time, "session": "0930", "setup": setup, "grade": "A",
            "direction": direction, "fair_value": entry, "atr": 10.0, "tier": 1, "stop_points": stop, "contracts": 1, "entry": entry,
            "stop": entry - direction * stop, "target": entry + direction * target, "exit": entry + direction * (target if r > 0 else -stop),
            "exit_reason": reason, "pnl_points": target if r > 0 else -stop, "pnl_dollars": 0.0, "risk_dollars": 500.0, "r": r, "bars_held": 10,
            "distance_from_fv": 0.0, "ambiguous_bar": False}


def test_excursions_long_and_short():
    bars = _bars(days=3)
    day = bars.index[0].normalize()
    # long trade: push highs to +40 over bars 5..10 after entry, lows to -12 on bar 3
    e = day.replace(hour=9, minute=40)
    x = day.replace(hour=9, minute=55)
    i0 = bars.index.get_loc(e)
    bars.iloc[i0 + 3, bars.columns.get_loc("low")] = 20000 - 12
    bars.iloc[i0 + 6, bars.columns.get_loc("high")] = 20000 + 40
    bars.iloc[i0 + 60, bars.columns.get_loc("high")] = 20000 + 90  # after exit, before 16:00: counts for mfe_day only
    t = pd.DataFrame([_trade(e, x, 1, 20000.0, 1.5)])
    t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
    ex = excursions(t, bars)
    assert ex.loc[0, "mfe_held"] == pytest.approx(40)
    assert ex.loc[0, "mae_held"] == pytest.approx(12)
    assert ex.loc[0, "mfe_day"] == pytest.approx(90)
    # short trade on day 2: lows to -30 while held, highs +8 adverse
    day2 = bars.index[bars.index.normalize() > day][0].normalize()
    e2 = day2.replace(hour=10, minute=0); x2 = day2.replace(hour=10, minute=20)
    j0 = bars.index.get_loc(e2)
    bars.iloc[j0 + 2, bars.columns.get_loc("high")] = 20000 + 8
    bars.iloc[j0 + 10, bars.columns.get_loc("low")] = 20000 - 30
    t2 = pd.DataFrame([_trade(e2, x2, -1, 20000.0, -1.0, reason="stop")])
    ex2 = excursions(t2, bars)
    assert ex2.loc[0, "mfe_held"] == pytest.approx(30)
    assert ex2.loc[0, "mae_held"] == pytest.approx(8)


def test_daily_context_and_report_sections():
    bars = _bars(days=20)
    ctx = daily_context(bars)
    assert {"daily_atr", "opening_range"} <= set(ctx.columns)
    assert ctx["opening_range"].iloc[0] == pytest.approx(10.0)  # +5/-5 synthetic bars
    assert ctx["daily_atr"].iloc[-1] == pytest.approx(10.0)
    days = sorted(set(bars.index.normalize()))
    rows = []
    for k, d in enumerate(days[:16]):
        e = d.replace(hour=9, minute=33 + (k % 20)); x = e + pd.Timedelta(minutes=15)
        rows.append(_trade(e, x, 1 if k % 2 else -1, 20000.0, 1.5 if k % 3 else -1.0, setup="continuation" if k % 2 else "reversion", reason="target" if k % 3 else "stop"))
    t = pd.DataFrame(rows)
    oos = days[12].strftime("%Y-%m-%d")
    text, per_trade = anatomy(t, bars, oos)
    assert "## By period and setup" in text and "## Bracket geometry by year" in text and "## Excursion quantiles" in text
    assert (per_trade["period"] == "benchmark").sum() == 4 and (per_trade["period"] == "development").sum() == 12
    assert set(per_trade["entry_bucket"]) <= {"09:30-09:35", "09:35-09:45", "09:45-10:00", "10:00-10:30", "10:30-11:00", "after 11:00"}
    assert per_trade["regime"].isin(["low", "mid", "high", "n/a"]).all()
    assert per_trade["rel_regime"].isin(["low", "mid", "high", "n/a"]).all()
    assert "## By period, setup and grade" in text and "stop as % of price" in text
    assert {"prev_close", "atr_pct"} <= set(ctx.columns)


def test_load_trades_roundtrip(tmp_path):
    bars = _bars(days=2)
    d = bars.index[0].normalize()
    t = pd.DataFrame([_trade(d.replace(hour=9, minute=40), d.replace(hour=9, minute=50), 1, 20000.0, 1.5)])
    p = tmp_path / "trades.csv"
    t.to_csv(p, index=False)
    back = load_trades(str(p))
    assert back["entry_time"].dt.tz is not None and str(back["entry_time"].dt.tz) == NY
    assert back["direction"].iloc[0] == 1


def _globex_bars(weeks=4, start="2025-01-05"):
    """Sunday 18:00 through Friday 17:00 New York, one bar a minute, with a 17:00-18:00 break."""
    sunday = pd.Timestamp(start, tz=NY)
    parts = []
    for w in range(weeks):
        d = sunday + pd.Timedelta(days=7 * w)
        parts.append(pd.date_range(d.replace(hour=18), d + pd.Timedelta(days=1), freq="1min", inclusive="left"))
        for k in range(1, 5):
            dd = d + pd.Timedelta(days=k)
            parts.append(pd.date_range(dd.replace(hour=0), dd.replace(hour=17), freq="1min", inclusive="left"))
            parts.append(pd.date_range(dd.replace(hour=18), dd + pd.Timedelta(days=1), freq="1min", inclusive="left"))
        fri = d + pd.Timedelta(days=5)
        parts.append(pd.date_range(fri.replace(hour=0), fri.replace(hour=17), freq="1min", inclusive="left"))
    index = parts[0].append(parts[1:])
    base = np.full(len(index), 20000.0)
    df = pd.DataFrame({"open": base, "high": base + 5, "low": base - 5, "close": base}, index=index)
    # make Sunday evenings quiet and weekdays wide so a calendar-date grouping would be visibly wrong
    ny = df.index.tz_convert(NY)
    wk = (ny.dayofweek < 5) & (ny.hour >= 9) & (ny.hour < 16)
    df.loc[wk, "high"] = base[wk] + 60
    df.loc[wk, "low"] = base[wk] - 60
    df["symbol"] = "A"
    return df


def test_daily_context_uses_globex_session_not_calendar_date():
    bars = _globex_bars(weeks=5)
    ctx = daily_context(bars)
    assert (ctx.index.dayofweek != 6).all()  # no Sunday rows
    assert ctx["daily_atr"].dropna().iloc[-1] == pytest.approx(120.0)  # every session ranges 120, nothing diluted by Sunday stubs
    monday = ctx.index[ctx.index.dayofweek == 0][0]
    assert ctx.loc[monday, "opening_range"] == pytest.approx(120.0)
    assert ctx["atr_pct"].dropna().iloc[-1] == pytest.approx(120.0 / 20000.0)


def test_roll_day_trades_are_excluded_like_the_sealed_report():
    bars = _bars(days=4)
    days = sorted(set(bars.index.normalize()))
    rows = [_trade(d.replace(hour=9, minute=40), d.replace(hour=9, minute=50), 1, 20000.0, 1.5) for d in days]
    t = pd.DataFrame(rows)
    kept, n = exclude_roll_trades(t, [days[1].date()])
    assert n == 1 and len(kept) == 3
    text, per_trade = anatomy(t, bars, days[3].strftime("%Y-%m-%d"), exclude_dates=[days[1].date()])
    assert "Data hygiene: 1 trades on 1 contract-roll dates excluded" in text
    assert len(per_trade) == 3


def test_stop_bar_favourable_extreme_is_not_counted_and_16_00_bar_is_outside():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    e = day.replace(hour=9, minute=40); x = day.replace(hour=9, minute=50)
    i0 = bars.index.get_loc(e); i1 = bars.index.get_loc(x)
    bars.iloc[i1, bars.columns.get_loc("high")] = 20000 + 40   # ambiguous exit bar: both stop and target inside
    bars.iloc[i1, bars.columns.get_loc("low")] = 20000 - 30
    bars.iloc[i0 + 2, bars.columns.get_loc("high")] = 20000 + 9
    t = pd.DataFrame([_trade(e, x, 1, 20000.0, -1.0, reason="stop")])
    ex = excursions(t, bars)
    assert ex.loc[0, "mfe_held"] == pytest.approx(9)     # the stop bar's high is not a "nearly hit the target"
    assert ex.loc[0, "mae_held"] == pytest.approx(30)    # the stop bar's low still counts against
    # a bar opening at 16:00 must not feed mfe_day
    bars2 = bars.copy()
    extra = pd.DataFrame({"open": 20000.0, "high": 20000 + 500, "low": 20000.0, "close": 20000.0}, index=[day.replace(hour=16, minute=0)])
    bars2 = pd.concat([bars2, extra]).sort_index()
    ex2 = excursions(t, bars2)
    assert ex2.loc[0, "mfe_day"] < 100


def test_year_table_prints_integers():
    bars = _bars(days=6)
    days = sorted(set(bars.index.normalize()))
    t = pd.DataFrame([_trade(d.replace(hour=9, minute=40), d.replace(hour=9, minute=50), 1, 20000.0, 1.5) for d in days])
    text, _ = anatomy(t, bars, days[-1].strftime("%Y-%m-%d"))
    assert "| 2025 | 6 |" in text and "2025.0" not in text
