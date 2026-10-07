import io
import json

import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import forward
from research.forward import (candidate_trades, classify_gaps, ledger_rows, merge_ledger, micros, rth_sessions, same_rows, scorable_dates, tail_check,
                              thresholds)

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


def _cut(idx, a, b):
    return idx[(idx < pd.Timestamp(a, tz=NY)) | (idx >= pd.Timestamp(b, tz=NY))]


def _kinds(g):
    return {k: len(v) for k, v in g.items() if v}


def test_the_gap_rule():
    idx = _globex("2026-10-04 18:00", "2026-10-17 00:00")
    g = classify_gaps(idx)
    assert _kinds(g) == {"halts": 9} and {k for _, _, k in g["halts"]} == {"daily break"}  # eight daily breaks and the weekend
    assert _kinds(classify_gaps(_cut(idx, "2026-10-07 10:00", "2026-10-07 11:00"))) == {"halts": 9, "session": 1}
    assert _kinds(classify_gaps(_cut(idx, "2026-10-07 01:00", "2026-10-07 02:00"))) == {"halts": 9, "overnight": 1}  # reported, not refused
    # an outage from mid-session to the evening reopen is not a scheduled halt (the second review's finding)
    assert _kinds(classify_gaps(_cut(idx, "2026-10-07 11:00", "2026-10-07 17:00"))) == {"halts": 8, "session": 1}
    # across 00:00 UTC (20:00 ET in October), where the continuous series rolls
    assert _kinds(classify_gaps(_cut(idx, "2026-10-07 19:30", "2026-10-07 20:30"))) == {"halts": 9, "roll": 1}
    # 13:00 and 13:15 ends are exempt only on their listed dates (the third review's finding): Columbus Day is a normal session
    assert _kinds(classify_gaps(_cut(idx, "2026-10-12 13:00", "2026-10-12 17:00"))) == {"halts": 8, "session": 1}
    assert _kinds(classify_gaps(_cut(idx, "2026-10-14 13:15", "2026-10-14 17:00"))) == {"halts": 8, "session": 1}
    # exactly 30 minutes without a bar is not a gap; 31 is
    assert not classify_gaps(_cut(idx, "2026-10-07 10:00", "2026-10-07 10:30"))["session"]
    assert classify_gaps(_cut(idx, "2026-10-07 10:00", "2026-10-07 10:31"))["session"]
    # a lost session from one daily break to the next day's reopen is not a halt: Thursday is not a listed closure
    assert _kinds(classify_gaps(_cut(idx, "2026-10-07 18:00", "2026-10-08 18:00"))) == {"halts": 7, "session": 1}  # two daily breaks merge into the gap


def test_the_listed_holidays():
    idx = _globex("2026-11-22 18:00", "2027-01-09 00:00")
    real = _cut(idx, "2026-11-26 13:00", "2026-11-26 18:00")  # Thanksgiving: a 13:00 halt, reopening that evening
    real = _cut(real, "2026-11-27 13:15", "2026-11-29 18:00")  # the Friday after: a 13:15 close to the Sunday reopen
    real = _cut(real, "2026-12-24 13:15", "2026-12-27 18:00")  # Christmas Eve's early close, then Christmas closed
    real = _cut(real, "2026-12-31 17:00", "2027-01-03 18:00")  # New Year's Day closed
    g = classify_gaps(real)
    assert not g["session"] and not g["roll"] and not g["overnight"]
    kinds = {x[:10]: k for x, _, k in g["halts"] if k != "daily break"}
    assert kinds == {"2026-11-26": "holiday halt", "2026-11-27": "early close", "2026-12-24": "early close"}
    _, skipped = scorable_dates(real, pd.Timestamp("2026-11-23"), [])
    assert {d.strftime("%Y-%m-%d") for d, _ in skipped} == {"2026-12-25", "2027-01-01"}
    # the same Christmas shape on a weekday that is not a listed closure stops the run
    assert classify_gaps(_cut(idx, "2026-12-17 13:15", "2026-12-20 18:00"))["session"]


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
    out["instrument_id"] = out["symbol"]
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
    pin = tmp_path / "baseline.sha256"
    monkeypatch.setattr(forward, "BASELINE_PIN", str(pin))
    monkeypatch.setattr("sys.argv", ["forward.py", "baseline", *common, "--out", str(tmp_path / "base.md"), "--private-out", str(tmp_path / "base.csv")])
    assert forward.main() == 0
    base = (tmp_path / "base.md").read_text()
    assert "Tail check" in base and "| S3 | development |" in base and "| S4 | benchmark |" in base and "gap rule" in base
    block = forward.read_baseline(base)
    assert set(block) == {"thresholds", "code", "candidates"} and "research/forward.py" in block["code"] and "fpt/strategy.py" in block["code"]
    # the synthetic bars have no Globex hours, so every night would be a gap across 00:00 UTC: the rule itself is tested above
    monkeypatch.setattr(forward, "classify_gaps", lambda idx: {"halts": [], "session": [], "roll": [], "overnight": []})
    state, pub, prv = tmp_path / "state.json", tmp_path / "status.md", tmp_path / "status_private.md"
    day_args = [*common, "--baseline", str(tmp_path / "base.md"), "--state", str(state), "--out", str(pub), "--private-out", str(prv),
                "--ledger-csv", str(tmp_path / "ledger.csv"), "--forward-csv", str(tmp_path / "fwd.csv")]
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args])
    _csv(fwd[fwd.index < days[5]], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="baseline report is not the pinned one"):
        forward.main()
    pin.write_text(forward.sha256(str(tmp_path / "base.md")) + "  research/forward_v1_baseline.md\n")
    # six days, the sixth cut at noon: the first five are scored (each has a bar on a later date), the sixth is not
    _csv(fwd[fwd.index < days[5] + pd.Timedelta(hours=12)], tmp_path / "fwd.csv")
    assert forward.main() == 0
    s5 = json.loads(state.read_text())
    assert len(s5["dates"]) == 5 and s5["dates"][-1] == days[4].strftime("%Y-%m-%d") and len(s5["runs"]) == 1 and s5["runs"][0]["previous_state_sha256"] is None
    assert s5["code"] == block["code"]
    led5 = pd.DataFrame(s5["trades"])
    full = candidate_trades(history, [])  # the full history's trades on those dates: the forward run must match them
    want = ledger_rows(full, [pd.Timestamp(d) for d in s5["dates"]])
    assert same_rows(led5[forward.LEDGER_KEY].astype({"date": str}), want[forward.LEDGER_KEY])
    assert len(pd.read_csv(tmp_path / "ledger.csv")) == len(led5)
    published = pub.read_text().split("state sha256 ")[1].split(" ")[0]
    assert published == forward.sha256(str(state))
    # thirteen days: the state extends, the first five are unchanged, and the ten-session checkpoint is reported
    _csv(fwd[fwd.index < days[13]], tmp_path / "fwd.csv")
    assert forward.main() == 0
    s12 = json.loads(state.read_text())
    assert len(s12["dates"]) == 12 and len(s12["runs"]) == 2 and s12["runs"][1]["dates_added"] == s12["dates"][5:]
    assert s12["runs"][1]["previous_state_sha256"] == published  # the chain matches the published hashes
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
    refuses("another protocol, baseline or code", lambda st: st["code"].update({"research/engine.py": "0" * 64}))
    refuses("another protocol, baseline or code", lambda st: st.update(baseline="0" * 64))
    with monkeypatch.context() as m:  # the code differs from the baseline's
        m.setattr(forward, "code_hashes", lambda: {**block["code"], "research/engine.py": "0" * 64})
        refuses("changed since the baseline")
    with monkeypatch.context() as m:
        m.setattr(forward, "CANDIDATES", {**forward.CANDIDATES, "S3": forward.CANDIDATES["S4"]})
        refuses("changed since the baseline")
    good = (tmp_path / "fwd.csv").read_bytes()
    # forward bars that overlap the sealed ones, or leave a hole after them
    _csv(history[history.index >= first - pd.Timedelta(days=3)], tmp_path / "fwd.csv")
    refuses("must start after the sealed bars")
    _csv(fwd[fwd.index >= days[1]], tmp_path / "fwd.csv")
    refuses("must continue the sealed ones")
    # a raw file with a repeated bar, a bar without its instrument, or a symbol that is not the instrument_id
    lines = good.decode().splitlines()
    (tmp_path / "fwd.csv").write_text("\n".join(lines[:50] + [lines[49]] + lines[50:]) + "\n")
    refuses("repeat or are out of order")
    raw = pd.read_csv(io.BytesIO(good))
    raw.loc[10, "symbol"] = np.nan
    raw.to_csv(tmp_path / "fwd.csv", index=False)
    refuses("equal to its instrument_id")
    raw = pd.read_csv(io.BytesIO(good)).assign(symbol="NQ.n.0")
    raw.to_csv(tmp_path / "fwd.csv", index=False)
    refuses("equal to its instrument_id")
    # a gap that stops the run, then recorded as an exchange halt by a person
    (tmp_path / "fwd.csv").write_bytes(good)
    bad = ("2026-10-14 11:00:00-04:00", "2026-10-14 18:00:00-04:00")
    monkeypatch.setattr(forward, "classify_gaps", lambda idx: {"halts": [], "session": [bad], "roll": [], "overnight": []})
    refuses("inside a 09:30-16:00 session")
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args, "--accept-gap", "2026-10-14 11:00"])
    refuses("needs --accept-reason")
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args, "--accept-gap", "2026-10-14 11:00", "--accept-reason", "CME halted equity futures (notice)"])
    assert forward.main() == 0
    assert json.loads(state.read_text())["accepted_gaps"][0]["from"] == bad[0] and "CME halted" in pub.read_text()
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args])
    assert forward.main() == 0  # once recorded, it stays accepted


def test_day_mode_on_globex_shaped_bars(history, tmp_path, monkeypatch):
    """The real gap rule end to end: forward bars with every Globex minute (flat outside the synthetic regular session)."""
    first = pd.Timestamp("2026-10-06", tz=NY)
    sealed = history[history.index < first]
    _csv(sealed, tmp_path / "sealed.csv")
    (tmp_path / "manifest.json").write_text(json.dumps({"data": {"sha256": forward.sha256(str(tmp_path / "sealed.csv"))}}))
    common = ["--csv", str(tmp_path / "sealed.csv"), "--source-tz", "UTC", "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr(forward, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(forward, "TAIL_WARMUP", 30)
    monkeypatch.setattr(forward, "BASELINE_PIN", str(tmp_path / "pin"))
    monkeypatch.setattr("sys.argv", ["forward.py", "baseline", *common, "--out", str(tmp_path / "base.md")])
    assert forward.main() == 0
    (tmp_path / "pin").write_text(forward.sha256(str(tmp_path / "base.md")))
    idx = _globex("2026-10-05 16:00", "2026-10-17 00:00")
    rth = history[(history.index >= idx[0]) & (history.index <= idx[-1])]
    g = rth.reindex(idx)
    g["close"] = g["close"].ffill()
    for c in ("open", "high", "low"):
        g[c] = g[c].fillna(g["close"])
    g = g.assign(volume=g["volume"].fillna(1.0), symbol="1001")
    state, pub = tmp_path / "state.json", tmp_path / "status.md"
    args = ["forward.py", "day", *common, "--baseline", str(tmp_path / "base.md"), "--state", str(state), "--out", str(pub),
            "--forward-csv", str(tmp_path / "fwd.csv")]
    monkeypatch.setattr("sys.argv", args)
    _csv(g[g.index < pd.Timestamp("2026-10-13", tz=NY)], tmp_path / "fwd.csv")
    assert forward.main() == 0
    st = json.loads(state.read_text())
    assert len(st["dates"]) == 4 and {k for _, _, k in st["runs"][0]["new_halts"]} == {"daily break"} and "Scheduled early ends: none" in pub.read_text()
    # an hour missing inside an unscored session stops the run; a person records it; a longer gap from the same minute stops it again
    hole = _cut(g.index, "2026-10-14 11:00", "2026-10-14 12:00")
    _csv(g.loc[hole], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="inside a 09:30-16:00 session"):
        forward.main()
    monkeypatch.setattr("sys.argv", args + ["--accept-gap", "2026-10-14 10:59", "--accept-reason", "test: an exchange halt"])
    assert forward.main() == 0 and json.loads(state.read_text())["accepted_gaps"][0]["to"].startswith("2026-10-14 12:00")
    assert len(json.loads(state.read_text())["dates"]) == 8
    monkeypatch.setattr("sys.argv", args)
    assert forward.main() == 0
    _csv(g.loc[_cut(g.index, "2026-10-14 11:00", "2026-10-14 13:00")], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="inside a 09:30-16:00 session"):
        forward.main()
    # the complete bars now: the scored 2026-10-14 was taken with its hole, so a trade there would come out differently or not at all
    _csv(g, tmp_path / "fwd.csv")
    scored = json.loads(state.read_text())
    try:
        forward.main()
        assert json.loads(state.read_text())["dates"] == scored["dates"]  # no trade touched the hole: nothing changes
    except SystemExit as e:
        assert "history is never rewritten" in str(e)
