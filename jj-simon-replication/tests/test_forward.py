import json

import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import forward
from research.forward import (candidate_trades, ledger_rows, merge_ledger, micros, rth_sessions, same_rows, scorable_dates, tail_check, thresholds,
                              unscheduled_gaps)

NY = "America/New_York"


def test_whole_micros_within_the_budget():
    # a 25-point stop: $51 a micro at a full stop-out, so 19 in the evaluation ($969) and 9 funded ($459)
    assert list(micros(np.array([25.0, 25.0]), 1000.0)) == [19, 19] and micros(np.array([25.0]), 500.0)[0] == 9
    assert micros(np.array([500.0]), 1000.0)[0] == 0 and micros(np.array([499.0]), 1000.0)[0] == 1 and micros(np.array([2.0]), 1000.0)[0] == 50  # nothing fits; the cap


def _globex(start: str, end: str) -> pd.DatetimeIndex:
    """Every minute of the Globex week: Sunday 18:00 to Friday 17:00 ET, with the 17:00-18:00 break."""
    idx = pd.date_range(pd.Timestamp(start, tz=NY), pd.Timestamp(end, tz=NY), freq="1min", inclusive="left")
    keep = (idx.hour != 17) & ~((idx.weekday == 4) & (idx.hour >= 17)) & (idx.weekday != 5) & ~((idx.weekday == 6) & (idx.hour < 18))
    return idx[keep]


def test_sessions_are_dates_with_a_0930_bar():
    idx = _globex("2026-10-04 18:00", "2026-10-10 00:00")  # Sunday evening to Friday 17:00
    s = rth_sessions(idx)
    assert [d.strftime("%a") for d in s] == ["Mon", "Tue", "Wed", "Thu", "Fri"]  # Sunday evening is not a session


def test_the_gap_rule():
    idx = _globex("2026-10-04 18:00", "2026-10-17 00:00")
    assert unscheduled_gaps(idx) == ([], [])  # the daily break and the weekend end at the 18:00 reopen
    session_hole = idx[(idx < pd.Timestamp("2026-10-07 10:00", tz=NY)) | (idx >= pd.Timestamp("2026-10-07 11:00", tz=NY))]
    s, n = unscheduled_gaps(session_hole)
    assert len(s) == 1 and n == [] and s[0][0].startswith("2026-10-07 09:59")
    night_hole = idx[(idx < pd.Timestamp("2026-10-07 01:00", tz=NY)) | (idx >= pd.Timestamp("2026-10-07 02:00", tz=NY))]
    assert unscheduled_gaps(night_hole)[0] == [] and len(unscheduled_gaps(night_hole)[1]) == 1  # reported, not refused
    lost_day = idx[(idx < pd.Timestamp("2026-10-07 18:00", tz=NY)) | (idx >= pd.Timestamp("2026-10-08 18:00", tz=NY))]
    assert unscheduled_gaps(lost_day) == ([], [])  # ends at a reopen: caught by the missing 09:30 bar instead
    _, skipped = scorable_dates(lost_day, pd.Timestamp("2026-10-06"), [])
    assert (pd.Timestamp("2026-10-08"), "no 09:30 bar (market closed or data missing)") in skipped
    early = idx[~((idx >= pd.Timestamp("2026-10-09 13:15", tz=NY)) & (idx < pd.Timestamp("2026-10-11 18:00", tz=NY)))]
    assert unscheduled_gaps(early) == ([], [])  # an early close: the gap runs to the Sunday reopen


def test_a_date_is_scored_once_a_later_date_has_a_bar():
    idx = _globex("2026-10-04 18:00", "2026-10-10 00:00")
    cut = idx[idx < pd.Timestamp("2026-10-08 16:00", tz=NY)]  # Thursday's session ended, no evening bar yet
    scored, skipped = scorable_dates(cut, pd.Timestamp("2026-10-06"), [])
    assert [d.strftime("%Y-%m-%d") for d in scored] == ["2026-10-06", "2026-10-07"] and skipped == []
    evening = idx[idx < pd.Timestamp("2026-10-09 00:05", tz=NY)]  # Thursday's evening seen: Thursday is scored
    assert scorable_dates(evening, pd.Timestamp("2026-10-06"), [])[0][-1] == pd.Timestamp("2026-10-08")
    scored, skipped = scorable_dates(evening, pd.Timestamp("2026-10-06"), [pd.Timestamp("2026-10-07").date()])
    assert pd.Timestamp("2026-10-07") not in scored and (pd.Timestamp("2026-10-07"), "roll date") in skipped


@pytest.fixture(scope="module")
def history():
    bars = synthetic_minute_bars(days=500, seed=5, start="2024-12-02")
    bars["symbol"] = "1001"
    return bars


def test_thresholds_have_every_checkpoint(history):
    t = candidate_trades(history, [])["S3"]
    th = thresholds(t, rth_sessions(history.index))
    for k in ("count_p01", "count_p99", "target_share_p01", "stop_share_p99", "flat_share_p01", "long_share_p99",
              "mean_r_20_p025", "drawdown_20_p99", "target_share_20_p01", "mean_r_30_p025", "drawdown_30_p99", "target_share_30_p01"):
        assert k in th and np.isfinite(th[k])
    assert th["count_p01"] <= th["count_p99"] and th["drawdown_30_p99"] >= th["drawdown_20_p99"] - 1e-9


def test_a_tail_rerun_reproduces_the_full_run(history, monkeypatch):
    monkeypatch.setattr(forward, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(forward, "TAIL_WARMUP", 30)
    full = candidate_trades(history, [])
    assert tail_check(history, [], full) > 0
    flat = history.iloc[:390 * 40].assign(open=20000.0, high=20000.0, low=20000.0, close=20000.0)  # a market that never moves: no trade
    with pytest.raises(SystemExit, match="compared no trade"):
        tail_check(flat, [], candidate_trades(flat, []))


def _rows(history, until):
    t = candidate_trades(history[history.index < pd.Timestamp(until, tz=NY)], [])
    dates = sorted(set(pd.concat([x["date"] for x in t.values()])))
    return ledger_rows(t, dates), dates


def test_the_ledger_appends_and_never_rewrites(history):
    first, d1 = _rows(history, "2026-08-01")
    led, scored = merge_ledger(None, [], first, d1)
    assert same_rows(led[forward.LEDGER_KEY], first[forward.LEDGER_KEY]) and len(scored) == len({d.strftime("%Y-%m-%d") for d in d1})
    more, d2 = _rows(history, "2026-09-01")
    led2, scored2 = merge_ledger(led, scored, more, d2)
    assert len(led2) == len(more) and set(scored) < set(scored2)
    assert same_rows(led2[led2["date"].isin(scored)][forward.LEDGER_KEY].reset_index(drop=True), led[forward.LEDGER_KEY])
    changed = led.copy()
    changed.loc[0, "r"] = changed.loc[0, "r"] + 0.5
    with pytest.raises(ValueError, match="history is never rewritten"):
        merge_ledger(changed, scored, more, d2)
    with pytest.raises(ValueError, match="missing from this run"):
        merge_ledger(led, scored + ["2026-12-31"], more, d2)
    gone = led.iloc[1:].reset_index(drop=True)  # a scored date that had a trade now shows one more trade than recorded
    with pytest.raises(ValueError, match="history is never rewritten"):
        merge_ledger(gone, scored, more, d2)


def _csv(bars: pd.DataFrame, path):
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    out.to_csv(path)


def test_cli_baseline_then_days(history, tmp_path, monkeypatch):
    first = pd.Timestamp("2026-10-06", tz=NY)
    sealed, fwd = history[history.index < first], history[history.index >= first]
    days = sorted(set(fwd.index.tz_convert(NY).normalize()))
    assert len(days) >= 13
    _csv(sealed, tmp_path / "sealed.csv")
    man = {"data": {"sha256": forward.sha256(str(tmp_path / "sealed.csv")), "roll_dates_excluded": "[]"}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    common = ["--csv", str(tmp_path / "sealed.csv"), "--source-tz", "UTC", "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr(forward, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(forward, "TAIL_WARMUP", 30)
    monkeypatch.setattr(forward, "MAX_GAP", pd.Timedelta(hours=18))  # the synthetic bars hold the regular session only
    monkeypatch.setattr("sys.argv", ["forward.py", "baseline", *common, "--out", str(tmp_path / "base.md"), "--private-out", str(tmp_path / "base.csv")])
    assert forward.main() == 0
    base = (tmp_path / "base.md").read_text()
    assert "Tail check" in base and "| S3 | development |" in base and "| S4 | benchmark |" in base and "```json" in base and "gap rule" in base
    state, pub, prv = tmp_path / "state.json", tmp_path / "status.md", tmp_path / "status_private.md"
    day_args = [*common, "--baseline", str(tmp_path / "base.md"), "--state", str(state), "--out", str(pub), "--private-out", str(prv),
                "--ledger-csv", str(tmp_path / "ledger.csv"), "--forward-csv", str(tmp_path / "fwd.csv")]
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args])
    _csv(fwd[fwd.index < days[5]], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="baseline report is not the pinned one"):
        forward.main()
    monkeypatch.setattr(forward, "BASELINE_SHA256", forward.sha256(str(tmp_path / "base.md")))
    # six days, the sixth cut at noon: the first five are scored (each has a bar on a later date), the sixth is not
    _csv(fwd[fwd.index < days[5] + pd.Timedelta(hours=12)], tmp_path / "fwd.csv")
    assert forward.main() == 0
    s5 = json.loads(state.read_text())
    assert len(s5["dates"]) == 5 and s5["dates"][-1] == days[4].strftime("%Y-%m-%d") and len(s5["runs"]) == 1
    assert set(s5["code"]) == set(forward.TRADE_CODE)
    led5 = pd.DataFrame(s5["trades"])
    full = candidate_trades(history, [])  # the full history's trades on those dates: the forward run must match them
    want = ledger_rows(full, [pd.Timestamp(d) for d in s5["dates"]])
    assert same_rows(led5[forward.LEDGER_KEY].astype({"date": str}), want[forward.LEDGER_KEY])
    assert len(pd.read_csv(tmp_path / "ledger.csv")) == len(led5)
    # thirteen days: the state extends, the first five are unchanged, and the ten-session checkpoint is reported
    _csv(fwd[fwd.index < days[13]], tmp_path / "fwd.csv")
    assert forward.main() == 0
    s12 = json.loads(state.read_text())
    assert len(s12["dates"]) == 12 and len(s12["runs"]) == 2 and s12["runs"][1]["dates_added"] == s12["dates"][5:]
    led12 = pd.DataFrame(s12["trades"])
    assert same_rows(led12[led12["date"].isin(s5["dates"])][forward.LEDGER_KEY].reset_index(drop=True), led5[forward.LEDGER_KEY])
    public, private = pub.read_text(), prv.read_text()
    assert "S3, first 10 sessions:" in public and "S3, first 10 sessions: count" in private
    assert "R per trade" not in public and "Paper Topstep 50K account" not in public and "Paper Topstep 50K account" in private
    # the same file again: nothing added, nothing changed
    assert forward.main() == 0 and json.loads(state.read_text())["dates"] == s12["dates"]

    def refuses(match, edit=None):
        saved = state.read_text()
        if edit:
            st = json.loads(saved)
            edit(st)
            state.write_text(json.dumps(st))
        with pytest.raises(SystemExit, match=match):
            forward.main()
        state.write_text(saved)

    if len(led12):
        refuses("history is never rewritten", lambda st: st["trades"][0].update(exit=st["trades"][0]["exit"] + 1.0))
    refuses("missing from this run", lambda st: st["dates"].append("2026-12-31"))
    refuses("protocol version 2", lambda st: st["code"].update({"research/engine.py": "0" * 64}))
    refuses("another protocol or baseline", lambda st: st.update(baseline="0" * 64))
    good = (tmp_path / "fwd.csv").read_text()
    # forward bars that overlap the sealed ones, or leave a hole after them
    _csv(history[history.index >= first - pd.Timedelta(days=3)], tmp_path / "fwd.csv")
    refuses("must start after the sealed bars")
    _csv(fwd[fwd.index >= days[1]], tmp_path / "fwd.csv")
    refuses("must continue the sealed ones")
    # a raw file with a repeated bar, or a bar without its instrument
    lines = good.splitlines()
    (tmp_path / "fwd.csv").write_text("\n".join(lines[:50] + [lines[49]] + lines[50:]) + "\n")
    refuses("repeat or are out of order")
    raw = pd.read_csv(pd.io.common.StringIO(good))
    raw.loc[10, "symbol"] = np.nan
    raw.to_csv(tmp_path / "fwd.csv", index=False)
    refuses("symbol")
    # bars missing from 10:00 on one day to 11:00 the next (longer than the test's 18-hour limit), inside sessions
    hole = fwd[fwd.index < days[13]]
    hole = hole[(hole.index < days[7] + pd.Timedelta(hours=10)) | (hole.index >= days[8] + pd.Timedelta(hours=11))]
    _csv(hole, tmp_path / "fwd.csv")
    refuses("inside a 09:30-16:00 session")
