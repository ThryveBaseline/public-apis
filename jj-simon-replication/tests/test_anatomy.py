import numpy as np
import pandas as pd
import pytest

from research.anatomy import anatomy, daily_context, excursions, load_trades

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


def test_load_trades_roundtrip(tmp_path):
    bars = _bars(days=2)
    d = bars.index[0].normalize()
    t = pd.DataFrame([_trade(d.replace(hour=9, minute=40), d.replace(hour=9, minute=50), 1, 20000.0, 1.5)])
    p = tmp_path / "trades.csv"
    t.to_csv(p, index=False)
    back = load_trades(str(p))
    assert back["entry_time"].dt.tz is not None and str(back["entry_time"].dt.tz) == NY
    assert back["direction"].iloc[0] == 1
