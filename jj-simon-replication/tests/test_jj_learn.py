import numpy as np
import pandas as pd

import research.forward_jj as fj
import research.jj_lab_engine_b2 as B
import research.jj_learn as JL
from research.jj_system import generate_trades as live
from research.jj_whatif import r_of, replay_signals

from tests.test_jj_lab import walk


def test_the_learning_engine_is_the_live_system_with_or_without_its_journal():
    f, ev = walk()
    a = live(f, events=ev)
    j = []
    pd.testing.assert_frame_equal(a, B.generate_trades(f, events=ev, journal=j))
    pd.testing.assert_frame_equal(a, B.generate_trades(f, events=ev))
    J = pd.DataFrame(j)
    sig = J[J["event"] == "signal"]
    assert sig["taken"].astype(bool).sum() == int((a["session"] != "book").sum())  # one taken signal per trade from a signal
    assert len(J[J["event"] == "order"]) >= int((a["session"] == "book").sum())  # every filled order was placed
    assert set(sig["reason"]) - {"taken"}  # and the rules passed on some


def test_a_replay_reproduces_every_plain_trade_exactly():
    f, ev = walk()
    j = []
    t = B.generate_trades(f, events=ev, journal=j)
    J = pd.DataFrame(j)
    sig = J[(J["event"] == "signal") & (J["taken"] == True)].copy()  # noqa: E712
    managed = {(m["session"], str(m["signal_time"])) for m in j if m["event"] == "manage"}
    rep = sig.join(replay_signals(f, sig, fj.trading_days(f.index)))
    rep["key"] = rep["session"] + "|" + rep["setup"] + "|" + rep["time"].astype(str)
    t["key"] = t["session"] + "|" + t["setup"] + "|" + t["signal_time"].astype(str)
    m = t.merge(rep, on="key", suffixes=("", "_s"))
    plain = m[m["exit_reason"].isin(["stop", "target"]) & ~m.apply(lambda x: (x["session"], str(x["signal_time"])) in managed, axis=1)]
    assert len(plain) > 50
    cell = plain.apply(lambda x: x[f"{x['stop_points']:g}/{x['target_points']:g}"], axis=1)
    np.testing.assert_allclose(cell.to_numpy(float), plain["r"].to_numpy(float), atol=1e-9)
    assert r_of(38.0, 25.0) == (38 - 0.25) / 25


def test_the_report_checks_itself_against_the_live_ledger():
    f, ev = walk()
    days = [pd.Timestamp(d) for d in sorted(pd.to_datetime(live(f, events=ev)["trading_day"]).unique())]
    lv = fj.ledger_rows(live(f, events=ev, days=days))
    rep = JL.learn(f, days, ev, float("-inf"), lv)
    assert rep["in_step"] and rep["n_days"] == len(days) and rep["trades"] == len(lv)
    assert {"session", "bias", "hour", "exit_reason"} <= set(rep["sessions"]) and rep["rules"] and rep["exits"] and rep["findings"]
    assert rep["overall"]["total_r"] == round(float(lv["r"].astype(float).sum()), 3)
    bad = lv.copy()
    bad.loc[0, "r"] = bad.loc[0, "r"] + 1
    off = JL.learn(f, days, ev, float("-inf"), bad)
    assert off["in_step"] is False and "out of step" in off["findings"][0] or "differ" in off["findings"][0]
    assert "## Findings" in JL.markdown(rep)


def test_the_new_settings_change_the_whole_system():
    f, ev = walk()
    run = lambda **kw: B.generate_trades(f, B.LabConfig(**kw), events=ev)  # noqa: E731
    base = run()
    assert run(sessions_off=("book", "20:00")).query("session in ['book', '20:00']").empty
    assert not run(filters_off=("grade_b",)).equals(base) and not run(mgmt_off=("flip_exit",)).equals(base)
    t = run(rev_bracket=(("09:30", 25.0, 76.0),)).query("session == '09:30' and setup == 'reversion'")
    assert len(t) and (t["target_points"] == 76.0).all()
