import numpy as np
import pandas as pd
import pytest

from research.bracket_replay import COMMISSION_RT, POINT_VALUE, grid, replay
from research.ledger_filters import apply_filter, build_gates, check_alignment, consecutive_loss_stop, evaluate, move_away_gate
from tests.test_anatomy import _bars, _trade

NY = "America/New_York"


def _ledger(day, specs):
    """specs: list of (minute_after_0930, setup, grade, direction, r, fair_value[, distance_from_fv])."""
    rows = []
    for spec in specs:
        m, setup, grade, d, r, fv = spec[:6]
        e = day.replace(hour=9, minute=30) + pd.Timedelta(minutes=m)
        t = _trade(e, e + pd.Timedelta(minutes=5), d, 20000.0, r, setup=setup, reason="target" if r > 0 else "stop")
        t["grade"] = grade; t["fair_value"] = fv; t["signal_time"] = e - pd.Timedelta(minutes=1)
        t["pnl_dollars"] = 500.0 * r
        if len(spec) > 6:
            t["distance_from_fv"] = spec[6]
        rows.append(t)
    t = pd.DataFrame(rows)
    for c in ("signal_time", "entry_time", "exit_time"):
        t[c] = pd.to_datetime(t[c])
    return t


def test_grade_cadence_and_cutoff_filters():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(2, "continuation", "A", 1, 1.5, 20000), (8, "reversion", "A", -1, -1.0, 20000), (12, "reversion", "A+", -1, 1.5, 20000),
                      (20, "reversion", "A", 1, -1.0, 20000), (40, "reversion", "A+", 1, 1.5, 20000), (70, "reversion", "A", -1, -1.0, 20000)])
    gates = build_gates(t, bars)
    assert len(apply_filter(t, "base", gates)) == 6
    a = apply_filter(t, "B2a", gates)
    assert (a["setup"] == "continuation").sum() == 1 and (a["grade"] == "A+").sum() == 2 and len(a) == 3
    c3 = apply_filter(t, "B2c3", gates)
    assert (c3["setup"] == "reversion").sum() == 3 and len(c3) == 4
    assert (apply_filter(t, "cut0945", gates)["setup"] == "reversion").sum() == 2


def test_consecutive_loss_stop_counts_every_trade_per_session():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(2, "continuation", "A", 1, -1.0, 20000), (8, "reversion", "A", -1, -1.0, 20000), (12, "reversion", "A+", -1, -1.0, 20000),
                      (20, "reversion", "A", 1, 1.5, 20000), (40, "reversion", "A+", 1, 1.5, 20000)])
    kept = consecutive_loss_stop(t)
    assert len(kept) == 3 and kept["r"].tolist() == [-1.0, -1.0, -1.0]


def _gate_bars():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    fv = 20000.0

    def seti(m, col, val):
        bars.iloc[bars.index.get_loc(day.replace(hour=9, minute=m)), bars.columns.get_loc(col)] = val
    # 09:32-09:40 price 50 above fair value; 09:41-09:45 closes back below it; 09:46-09:49 only 10 above
    for m in range(32, 41):
        seti(m, "high", fv + 50); seti(m, "close", fv + 30)
    for m in range(41, 46):
        seti(m, "close", fv - 5); seti(m, "high", fv + 2)
    for m in range(46, 50):
        seti(m, "high", fv + 10); seti(m, "close", fv + 8)
    return bars, day, fv, seti


def test_move_away_gate_since_open_since_last_cross_and_signal_bar():
    bars, day, fv, seti = _gate_bars()
    t = _ledger(day, [(20, "reversion", "A+", -1, 1.5, fv)])  # entry 09:50, signal 09:49, sealed target 38
    assert move_away_gate(t, bars, since_last_cross=False).iloc[0]       # 50 > 38 since the open
    assert not move_away_gate(t, bars, since_last_cross=True).iloc[0]    # only 10 since the 09:45 close through fair value
    assert not move_away_gate(t, bars, since_last_cross=False, threshold=[76.0]).iloc[0]  # the 76 band on a wide-open day
    seti(49, "high", fv + 45)  # the signal bar itself spikes: known at the decision, so it counts
    assert move_away_gate(t, bars, since_last_cross=True).iloc[0]
    t2 = _ledger(day, [(20, "continuation", "A", 1, 1.5, fv)])
    assert move_away_gate(t2, bars, since_last_cross=True).iloc[0]       # continuation is never gated


def test_room_rule_b2h_and_wide_day_room():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(10, "reversion", "A", -1, 1.5, 20000, 40.0), (20, "reversion", "A", -1, 1.5, 20000, 35.0)])
    gates = build_gates(t, bars)
    kept = apply_filter(t, "B2h", gates)
    assert len(kept) == 1 and kept["distance_from_fv"].iloc[0] == 40.0
    i = bars.index.get_loc(day.replace(hour=9, minute=30))
    bars.iloc[i, bars.columns.get_loc("close")] = 20000 + 30  # wide opening body: room must be >= 0.8 x 76
    gates = build_gates(t, bars)
    assert gates["wide"].all() and not gates["room_w"].any()


def test_base_reproduction_gate_refuses_a_ledger_that_breaks_the_stop():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(2, "continuation", "A", 1, -1.0, 20000), (8, "reversion", "A", -1, -1.0, 20000), (12, "reversion", "A", -1, -1.0, 20000),
                      (20, "reversion", "A", 1, -1.0, 20000)])  # a fourth trade after three losses: not an engine ledger
    with pytest.raises(ValueError, match="stop semantics"):
        evaluate(t, bars, day.strftime("%Y-%m-%d"))


def _consistent_ledger():
    """A ledger whose stop/target outcomes are what the bars produce, plus one trade without prior-session context."""
    bars = _bars(days=40)
    days = sorted(set(bars.index.normalize()))
    rows = []
    e0 = days[2].replace(hour=9, minute=40)
    rows.append(_trade(e0, e0 + pd.Timedelta(minutes=5), 1, 20000.25, 0.0, setup="continuation", reason="session_end"))
    eA = days[20].replace(hour=9, minute=40); iA = bars.index.get_loc(eA)
    bars.iloc[iA + 3, bars.columns.get_loc("high")] = 20000.25 + 40
    tA = _trade(eA, bars.index[iA + 3], 1, 20000.25, 0.0, setup="continuation", reason="target")
    tA["r"] = (38 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE); rows.append(tA)
    eB = days[22].replace(hour=10, minute=0); iB = bars.index.get_loc(eB)
    bars.iloc[iB + 2, bars.columns.get_loc("high")] = 20000.25 + 30
    tB = _trade(eB, bars.index[iB + 2], -1, 20000.25, 0.0, setup="reversion", reason="stop")
    tB["r"] = (-25.25 * POINT_VALUE - COMMISSION_RT) / (25 * POINT_VALUE); tB["grade"] = "A+"; tB["distance_from_fv"] = 45.0; tB["fair_value"] = 20000.25 - 45.0
    rows.append(tB)
    eC = days[24].replace(hour=10, minute=30)
    tC = _trade(eC, days[24].replace(hour=15, minute=59), -1, 20000.25, 0.0, setup="reversion", reason="session_end")
    tC["distance_from_fv"] = 70.0; tC["fair_value"] = 20000.25 - 70.0; rows.append(tC)
    t = pd.DataFrame(rows)
    for c in ("signal_time", "entry_time", "exit_time"):
        t[c] = pd.to_datetime(t[c])
    t["pnl_dollars"] = t["r"] * 500.0
    return t, bars, days


def test_composites_join_check_and_report():
    t, bars, days = _consistent_ledger()
    rep = replay(t, bars, grid())
    text, out = evaluate(t, bars, days[30].strftime("%Y-%m-%d"), rep)
    assert "Join check: the replayed sealed bracket equals the ledger R on all 2 stop or target exits before 16:00" in text
    labels = [lab for lab, _ in out["composites"]]
    assert labels[0].startswith("sealed bracket") and any(lab.startswith("funded as stated") for lab in labels)
    ctrl = out["composites"][0][1]
    assert len(ctrl) == 3  # the no-context trade is dropped for every variant
    funded = dict(out["composites"])["funded as stated (B2a, B2b1, B2c4, B2f1)"]
    assert set(funded["setup"]) <= {"continuation", "reversion"}


def test_composites_refuse_a_misaligned_replay():
    t, bars, days = _consistent_ledger()
    rep = replay(t, bars, grid())
    perm = {1: 2, 2: 3, 3: 1}
    bad = rep.assign(trade=rep["trade"].map(lambda k: perm.get(k, k)))
    with pytest.raises(ValueError, match="misaligned"):
        check_alignment(t.reset_index(drop=True), bad)
