import json

import research.personal_account as pa


def _t(entry_time, exit_time, entry, exit_, stop_points, direction="long", reason="target",
       date="2026-10-15", session="09:30"):
    """One recorded-shape trade. r follows the engine's own convention, r == (points - 0.25)
    / stop_points, so a test fixture can never drift from the thing it stands for."""
    d = 1.0 if direction == "long" else -1.0
    pts = (exit_ - entry) * d
    return {"date": date, "session": session, "setup": "reversion", "grade": "A+",
            "direction": direction, "entry_time": entry_time, "exit_time": exit_time,
            "entry": entry, "exit": exit_, "stop": entry - d * stop_points,
            "target": entry + d * stop_points * 1.52, "stop_points": stop_points,
            "target_points": stop_points * 1.52, "r": (pts - 0.25) / stop_points,
            "pnl_dollars": 1000 * (pts - 0.25) / stop_points, "contracts": 2,
            "exit_reason": reason, "layer": False, "attempt": 1, "candidate": "JJ"}


def test_dollars_come_from_the_prices_not_from_the_pnl_dollars_field():
    """pnl_dollars is r x $1,000 of bookkeeping. A 38-point winner on one micro is $76 gross,
    $73.60 net of the real round turn and a tick of entry slippage - not $1,510."""
    t = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 20038.0, 25.0)
    assert t["pnl_dollars"] == 1510.0
    res = pa.run([t])
    assert res["trades_taken"] == 1 and res["taken"][0]["micros"] == 1
    assert res["taken"][0]["gross_usd"] == 76.0
    assert res["taken"][0]["net_usd"] == 73.60
    assert res["end_cash"] == 2073.60


def test_exit_slippage_already_in_the_fill_is_not_charged_twice():
    """A stop exit's recorded fill is a tick past the stop. The loss must be exactly that fill
    plus the entry tick and the commission, not a second exit tick."""
    t = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 19974.75, 25.0,
           reason="stop")
    res = pa.run([t])
    x = res["taken"][0]
    assert x["gross_usd"] == -50.50          # 25.25 points, the tick already inside the fill
    assert x["net_usd"] == -52.90            # + $1.90 commission + $0.50 entry slippage
    assert x["net_usd"] == -pa.per_unit_risk(25.0)   # and that is exactly the risk it was sized on


def test_sizing_reads_the_initial_stop_distance_not_a_stop_moved_to_breakeven():
    """Two recorded trades carry a stop moved to entry while stop_points keeps the initial 25.
    Reading `stop` would size them as zero-risk and take an unbounded position."""
    t = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 20038.0, 25.0)
    t["stop"] = t["entry"]                   # the breakeven move, as recorded
    assert pa.size(t["stop_points"], 2000.0, 0.03) == 1


def test_a_fifty_point_stop_is_declined_until_the_account_can_afford_it():
    assert pa.per_unit_risk(50.0) == 102.90
    assert pa.size(50.0, 2000.0, 0.03) == 0          # $60 cap
    assert pa.size(50.0, 3430.0, 0.03) == 1          # $102.90 cap, the exact threshold


def test_the_arithmetic_minimum_cap_for_his_typical_stop():
    assert pa.per_unit_risk(25.0) == 52.90
    assert pa.size(25.0, 2000.0, 0.02645) == 1
    assert pa.size(25.0, 2000.0, 0.02600) == 0


def test_open_risk_is_what_binds_at_this_account_size_not_the_concurrency_cap():
    """Six 25-point winners in the same minute. $52.90 of risk each against a 6%-of-$2,000
    allowance is two positions, so open risk bites before the 3-position cap ever does, and the
    four it declines contribute nothing."""
    six = [_t("2026-10-15 09:31:00-04:00", "2026-10-15 09:45:00-04:00", 20000.0 + i,
              20038.0 + i, 25.0) for i in range(6)]
    res = pa.run(six)
    assert res["trades_taken"] == 2 and res["peak_concurrent"] == 2
    assert res["skipped_by_reason"] == {"total open risk cap": 4}
    assert all(s["kind"] == pa.POLICY for s in res["skipped"])
    assert res["net_usd"] == 2 * 73.60               # the declined four contribute nothing
    assert res["end_cash"] == 2000.0 + 2 * 73.60


def test_the_concurrency_cap_is_a_backstop_that_binds_only_when_sizing_leaves_slack():
    """Because sizing spends the per-trade cap and the open-risk allowance is twice it, two
    full-sized positions are the norm and the 3-position cap rarely speaks. It does speak when a
    trade sizes below its cap: at 1.5% a 12.5-point stop takes one micro and risks $27.90, so
    four would fit the $120 allowance and the position count is what holds the line."""
    six = [_t("2026-10-15 09:31:00-04:00", "2026-10-15 09:45:00-04:00", 20000.0 + i,
              20019.0 + i, 12.5) for i in range(6)]
    res = pa.run(six, cap_frac=0.015)
    assert res["taken"][0]["micros"] == 1
    assert res["trades_taken"] == 3 and res["peak_concurrent"] == pa.MAX_CONCURRENT
    assert res["skipped_by_reason"]["max concurrent positions"] == 3


def test_no_decision_can_see_a_trades_own_outcome():
    """The same entries with the outcomes swapped must produce the same TAKEN SET. If the loop
    ever consulted an exit, the selection would move with it."""
    good = [_t("2026-10-15 09:31:00-04:00", "2026-10-15 09:45:00-04:00", 20000.0 + i,
               20038.0 + i, 25.0) for i in range(6)]
    bad = [_t("2026-10-15 09:31:00-04:00", "2026-10-15 09:45:00-04:00", 20000.0 + i,
              19974.75 + i, 25.0, reason="stop") for i in range(6)]
    assert [x["ref"] for x in pa.run(good)["taken"]] == [x["ref"] for x in pa.run(bad)["taken"]]


def test_cash_from_a_close_is_available_to_a_later_entry_but_not_to_an_earlier_one():
    a = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:35:00-04:00", 20000.0, 20038.0, 25.0)
    b = _t("2026-10-15 09:40:00-04:00", "2026-10-15 09:50:00-04:00", 20100.0, 20138.0, 50.0)
    # alone, b's 50-point stop is unaffordable from $2,000; after a's win it still is
    assert pa.run([b])["trades_taken"] == 0
    res = pa.run([a, b])
    assert res["trades_taken"] == 1 and res["skipped"][0]["reason"] == "risk per trade cap"


def test_the_trading_floor_latches_off_for_good():
    """A winner after the floor is breached must not revive the account."""
    big = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 19250.0, 25.0,
             reason="stop")
    later = _t("2026-10-15 10:00:00-04:00", "2026-10-15 10:10:00-04:00", 20000.0, 20038.0, 25.0)
    res = pa.run([big, later])
    assert res["latched_off"] is True
    assert res["skipped"][0]["reason"] == "below the trading floor"
    assert res["trades_taken"] == 1


def test_an_entry_inside_the_no_entry_window_is_declined():
    t = _t("2026-10-15 16:45:00-04:00", "2026-10-15 16:50:00-04:00", 20000.0, 20038.0, 25.0)
    res = pa.run([t])
    assert res["trades_skipped"] == 1
    assert res["skipped"][0]["reason"].startswith("inside the no-entry window")


def test_a_position_open_at_the_flatten_time_is_flagged_not_given_an_invented_fill():
    t = _t("2026-10-15 15:00:00-04:00", "2026-10-15 17:30:00-04:00", 20000.0, 20038.0, 25.0)
    res = pa.run([t])
    assert res["trades_taken"] == 1 and res["open_at_flatten"] == 1


def test_the_closed_balance_drawdown_counts_the_opening_balance_as_the_first_peak():
    loss = _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 19974.75, 25.0,
              reason="stop")
    res = pa.run([loss])
    assert res["max_drawdown_closed_usd"] == 52.90
    assert res["closed_curve"] == [2000.0, 1947.10]


def test_the_recorded_state_is_never_written(tmp_path):
    """The account is an accounting view; the engine's record is an input it must not touch."""
    state = {"dates": ["2026-10-15"], "trades": [
        _t("2026-10-15 09:31:00-04:00", "2026-10-15 09:40:00-04:00", 20000.0, 20038.0, 25.0)]}
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    before = p.read_bytes()
    out, md = tmp_path / "out.json", tmp_path / "out.md"
    import sys
    argv = sys.argv
    sys.argv = ["personal_account", "--state", str(p), "--candidate", "JJ",
                "--out", str(out), "--md", str(md)]
    try:
        assert pa.main() == 0
    finally:
        sys.argv = argv
    assert p.read_bytes() == before
    doc = json.loads(out.read_text())
    assert doc["hypothetical"] is True
    assert doc["assumptions"]["start_cash"] == 2000.0
    assert doc["result"]["trades_taken"] == 1
    assert "optimistic" in doc["note"]


def test_every_skip_reason_is_classified():
    assert set(pa.REASONS.values()) == {pa.INFEASIBLE, pa.POLICY}
    for why in pa.REASONS:
        assert pa.REASONS[why] in (pa.INFEASIBLE, pa.POLICY)
