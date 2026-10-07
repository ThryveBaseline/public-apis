import numpy as np
import pandas as pd
import pytest

from research.bracket_replay import COMMISSION_RT, POINT_VALUE, dropped_rows, grid, replay
from research.ledger_filters import apply_filter, build_gates, check_alignment, composite_frame, consecutive_loss_stop, evaluate, move_away_gate, select, sequential_pass
from tests.test_anatomy import _bars, _trade

NY = "America/New_York"


def _ledger(day, specs):
    """specs: list of (minute_after_0930, setup, grade, direction, r, fair_value[, distance_from_fv])."""
    rows = []
    for spec in specs:
        m, setup, grade, d, r, fv = spec[:6]
        e = day.replace(hour=9, minute=30) + pd.Timedelta(minutes=m)
        t = _trade(e, e + pd.Timedelta(minutes=3), d, 20000.0, r, setup=setup, reason="target" if r > 0 else "stop")
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
    c3 = select(t, "B2c3", gates)
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
    rep = pd.concat([rep, dropped_rows(rep)], ignore_index=True)
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
    rep = pd.concat([rep, dropped_rows(rep)], ignore_index=True)
    perm = {1: 2, 2: 3, 3: 1}
    bad = rep.assign(trade=rep["trade"].map(lambda k: perm.get(k, k)))
    with pytest.raises(ValueError, match="misaligned"):
        check_alignment(t.reset_index(drop=True), bad)


def test_composite_coverage_is_required():
    t, bars, days = _consistent_ledger()
    rep = replay(t, bars, grid())  # no dropped markers: the no-context entry is neither replayed nor marked
    with pytest.raises(ValueError, match="does not cover"):
        check_alignment(t.reset_index(drop=True), rep)


def test_sequential_pass_blocks_overlap_and_uses_only_printed_outcomes():
    """The review's scenario: under a long-hold bracket, an open trade blocks the next entry, and its eventual
    outcome cannot stop or free a trade that entered before it printed."""
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(2, "reversion", "A", -1, -1.0, 20000), (8, "reversion", "A", -1, -1.0, 20000),
                      (15, "reversion", "A", -1, 1.5, 20000), (30, "reversion", "A", -1, 1.5, 20000), (240, "reversion", "A", -1, 1.5, 20000)])
    # trade 2 (09:45) now holds until 13:00 and wins; trade 3 (10:00) would enter while it is open
    t.loc[2, "exit_time"] = day.replace(hour=13, minute=0)
    kept = sequential_pass(t)
    assert list(kept.index) == [0, 1, 2, 4]  # 3 is blocked by the open position; 4 (13:30) is taken after it exits
    # if trade 2 eventually loses, trade 3 is still blocked by the position (not by a streak it could not have seen),
    # and trade 4 is blocked by the three-loss streak that has now printed
    t.loc[2, "r"] = -1.0; t.loc[2, "pnl_dollars"] = -500.0
    assert list(sequential_pass(t).index) == [0, 1, 2]


def test_cap_counts_only_reversions_actually_taken():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(2, "reversion", "A", -1, 1.5, 20000), (5, "reversion", "A", -1, 1.5, 20000), (20, "reversion", "A", -1, 1.5, 20000),
                      (30, "reversion", "A", -1, 1.5, 20000), (40, "reversion", "A", -1, 1.5, 20000)])
    t.loc[0, "exit_time"] = day.replace(hour=9, minute=40)  # trade 0 is open across trade 1's entry
    kept = sequential_pass(t, cap=3)
    assert list(kept.index) == [0, 2, 3]  # trade 1 was never taken, so it does not use a cap slot


def test_funded_band_is_the_menu_target():
    bars, day, fv, seti = _gate_bars()
    t = _ledger(day, [(20, "reversion", "A+", -1, 1.5, fv, 62.0)])  # menu target for 62 points of room is 75
    for m in range(46, 50):
        seti(m, "high", fv + 62); seti(m, "close", fv + 60)  # a 62-point move since the last return to fair
    gates = build_gates(t, bars)
    assert gates["b1"].iloc[0] and not gates["b1f"].iloc[0]  # beyond the 38 band, not beyond the 75 target


def _engine_ledger(tmp_path, bars, cfg, name):
    """Frozen-engine trades written and read back exactly as the sealed ledger is."""
    from fpt.strategy import generate_trades
    from research.anatomy import load_trades
    p = tmp_path / name
    generate_trades(bars, cfg).to_csv(p, index=False)
    return load_trades(str(p))


@pytest.mark.parametrize("seed", [7, 13])
def test_sequential_pass_reproduces_the_engine_loss_stop(tmp_path, seed):
    """Engine without its three-loss stop, then the pass, must equal the engine with the stop."""
    from dataclasses import replace
    from fpt.data import synthetic_minute_bars
    from fpt.strategy import StrategyConfig
    bars = synthetic_minute_bars(days=120, seed=seed)
    cfg = StrategyConfig()
    with_stop = _engine_ledger(tmp_path, bars, cfg, "stop.csv")
    without = _engine_ledger(tmp_path, bars, replace(cfg, max_consecutive_losses=None), "nostop.csv")
    assert len(without) > len(with_stop)  # the stop binds, so the test means something
    passed = sequential_pass(without)
    assert list(passed["entry_time"]) == list(with_stop.sort_values("entry_time")["entry_time"])


def test_wide_open_days_match_the_engine_big_open_rule(tmp_path):
    from fpt.data import synthetic_minute_bars
    from fpt.strategy import StrategyConfig
    from research.ledger_filters import wide_open_days
    bars = synthetic_minute_bars(days=160, seed=5, open_shock_points=40.0)
    t = _engine_ledger(tmp_path, bars, StrategyConfig(), "wide.csv")
    cont = t[t["setup"].astype(str) == "continuation"]
    wide = wide_open_days(cont, bars)
    assert wide.any() and (~wide).any()
    assert ((cont["stop_points"].astype(float) == 50.0).to_numpy() == wide).all()


def test_long_side_gate_and_engine_boundary():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    fv = 20000.0
    i = bars.index.get_loc(day.replace(hour=9, minute=35))
    bars.iloc[i, bars.columns.get_loc("low")] = fv - 38.0  # exactly the band below fair value
    t = _ledger(day, [(20, "reversion", "A+", 1, 1.5, fv)])  # a long reversion fades price below fair value
    assert move_away_gate(t, bars, since_last_cross=False, inclusive=True).iloc[0]   # engine: passes at equality
    assert not move_away_gate(t, bars, since_last_cross=False).iloc[0]              # his "more than": strict
    bars.iloc[i, bars.columns.get_loc("low")] = fv - 45.0
    for m in range(35, 50):  # price stays below fair value after the move, so the last return to fair is 09:34
        bars.iloc[bars.index.get_loc(day.replace(hour=9, minute=m)), bars.columns.get_loc("close")] = fv - 30.0
    assert move_away_gate(t, bars, since_last_cross=True).iloc[0]
    bars.iloc[bars.index.get_loc(day.replace(hour=9, minute=45)), bars.columns.get_loc("close")] = fv + 1.0  # back through fair at 09:45
    assert not move_away_gate(t, bars, since_last_cross=True).iloc[0]  # the 45-point move is before the return: reset


def test_label_mismatch_raises_instead_of_failing_the_gate():
    bars = _bars(days=2)
    day = bars.index[0].normalize()
    t = _ledger(day, [(10, "reversion", "A+", -1, 1.5, 20000, 40.0), (20, "reversion", "A+", -1, 1.5, 20000, 40.0)])
    gates = build_gates(t, bars)
    shifted = t.set_axis([5, 6])
    with pytest.raises(ValueError, match="not ledger positions"):
        apply_filter(shifted, "B2b1", gates)


def test_stale_replay_gets_the_right_refusal():
    t, bars, days = _consistent_ledger()
    rep = replay(t, bars, grid()).drop(columns=["exit_time"])
    with pytest.raises(ValueError, match="no exit_time column"):
        check_alignment(t.reset_index(drop=True), rep)
