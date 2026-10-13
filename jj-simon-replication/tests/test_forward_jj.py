import json

import numpy as np
import pandas as pd
import pytest

import research.forward_jj as fj
from research.news_calendar import events_for

NY = "America/New_York"


def _ff(path, events):
    path.write_text(json.dumps([{"title": t, "country": c, "date": d, "impact": i, "forecast": "", "previous": ""} for t, c, d, i in events]))


def test_a_day_takes_its_calendar_from_a_snapshot_fetched_before_it_began(tmp_path):
    week = [("CPI m/m", "USD", "2026-10-15T08:30:00-04:00", "High"), ("ECB Speaks", "EUR", "2026-10-13T04:00:00-04:00", "Medium"),
            ("Retail Sales", "USD", "2026-10-16T08:30:00-04:00", "High"), ("Holiday", "USD", "2026-10-12T00:00:00-04:00", "Holiday")]
    _ff(tmp_path / "ff_thisweek_20261014T070000Z.json", week)  # 03:00 ET on the 14th: before the 15th began (18:00 on the 14th)
    _ff(tmp_path / "ff_thisweek_20261015T230000Z.json", week[:2])  # fetched during the 16th's day: too late for it
    cal, missing = events_for([pd.Timestamp("2026-10-15"), pd.Timestamp("2026-10-16"), pd.Timestamp("2026-10-20")], str(tmp_path))
    assert sorted(cal["title"]) == ["CPI m/m", "Retail Sales"] and missing == [pd.Timestamp("2026-10-20")]
    cal, _ = events_for([pd.Timestamp("2026-10-14")], str(tmp_path))  # began 18:00 on the 13th, before either fetch
    assert cal.empty


def test_scorable_days_need_a_later_day_and_no_roll():
    idx = pd.date_range(pd.Timestamp("2026-10-14 09:00", tz=NY), pd.Timestamp("2026-10-16 10:00", tz=NY), freq="1min")
    idx = idx[idx.hour != 17]
    sym = pd.Series(np.where(idx < pd.Timestamp("2026-10-14 20:00", tz=NY), "NQZ6", "NQH7"), index=idx)
    days, rolls = fj.scorable(idx, sym, pd.Timestamp("2026-10-14"))
    assert days == [pd.Timestamp("2026-10-14")] and rolls == [pd.Timestamp("2026-10-15")]  # 20:00 on the 14th is in the 15th's day
    late = pd.Series(np.where(idx < pd.Timestamp("2026-10-15 20:00", tz=NY), "NQZ6", "NQH7"), index=idx)
    days, rolls = fj.scorable(idx, late, pd.Timestamp("2026-10-15"))
    assert days == [pd.Timestamp("2026-10-15")] and rolls == []  # the 16th holds the roll but is not complete yet


def _led(rows):
    return pd.DataFrame([{"date": d, "entry_time": pd.Timestamp(e, tz=NY), "exit_time": pd.Timestamp(x, tz=NY), "r": r, "grade": g, "setup": s,
                          "stop_points": 25.0} for d, e, x, r, g, s in rows])


def test_an_evaluation_takes_one_trade_at_a_time_and_stops_the_day_at_1500():
    led = _led([("2026-10-15", "2026-10-15 09:31", "2026-10-15 09:40", -1.01, "A+", "continuation"),  # a loss: take the next
                ("2026-10-15", "2026-10-15 09:35", "2026-10-15 09:50", -1.0, "A", "reversion"),  # overlaps: another account
                ("2026-10-15", "2026-10-15 09:55", "2026-10-15 10:10", 1.51, "A", "reversion"),  # day at +0.50
                ("2026-10-15", "2026-10-15 10:20", "2026-10-15 10:40", 1.51, "A", "reversion"),  # day at +2.01: done
                ("2026-10-15", "2026-10-15 10:50", "2026-10-15 11:10", 1.51, "A", "reversion"),
                ("2026-10-16", "2026-10-16 09:31", "2026-10-16 09:40", 1.51, "A", "reversion"),  # one full win is the day
                ("2026-10-16", "2026-10-16 09:50", "2026-10-16 10:00", 1.51, "A+", "reversion")])
    ev = fj.route(led, funded=False)
    assert list(ev["entry_time"].dt.strftime("%m-%d %H:%M")) == ["10-15 09:31", "10-15 09:55", "10-15 10:20", "10-16 09:31"]
    fu = fj.route(led, funded=True)
    assert list(fu["entry_time"].dt.strftime("%m-%d %H:%M")) == ["10-16 09:50"]  # breaks of structure only, never a continuation


def test_history_is_never_rewritten():
    t = pd.DataFrame({k: ["x"] for k in fj.LEDGER_KEY})
    for k in fj.NUM:
        t[k] = [1.0]
    t["date"], t["entry_time"], t["session"], t["attempt"] = ["2026-10-15"], ["2026-10-15 09:31"], ["09:30"], [1]
    led = fj.merge([], [], t, ["2026-10-15"])
    assert len(led) == 1
    changed = t.assign(r=[2.0])
    with pytest.raises(ValueError, match="never rewritten"):
        fj.merge(json.loads(led.to_json(orient="records")), ["2026-10-15"], changed, ["2026-10-15"])
    with pytest.raises(ValueError, match="missing"):
        fj.merge(json.loads(led.to_json(orient="records")), ["2026-10-15"], t, [])


def test_the_paper_account_runs_on_trading_days():
    led = _led([("2026-10-15", "2026-10-14 18:02", "2026-10-14 18:30", 1.51, "A+", "continuation"),
                ("2026-10-15", "2026-10-15 09:31", "2026-10-15 09:40", 1.51, "A", "reversion"),
                ("2026-10-16", "2026-10-16 09:31", "2026-10-16 09:40", -1.01, "A+", "reversion")])
    p = fj.paper_account(led, ["2026-10-15", "2026-10-16"])
    assert p["evals"] == 1 and p["final_cash"] < 2000 and not p["ruined"]
