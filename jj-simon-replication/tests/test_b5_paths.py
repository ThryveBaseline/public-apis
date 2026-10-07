import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.evaluate import trading_days_of
from fpt.propfirm import EVAL, INACTIVE
from fpt.strategy import StrategyConfig, generate_trades
from research import b5_paths
from research.anatomy import load_trades
from research.b5_paths import (CAPS, PATH_DAYS, SIZINGS, START_CASH, SlotAccount, check_gates, day_arrays, path_bounds, phase_streams, run,
                               simulate)
from research.candidates import FUNDED_RISK, PRESETS, whole_contracts
from research.ledger_filters import sequential_pass


def _arrays(rows, width=2):
    return day_arrays([np.array(x, dtype=float) for x in rows], width)


def _one_path(ev_rows, fu_rows, firm="topstep_50k_x", policy="ask", cap=1, days=None):
    days = days or len(ev_rows)
    dates = pd.DatetimeIndex(pd.bdate_range("2024-01-02", periods=days))
    return simulate(dates, _arrays(ev_rows), _arrays(fu_rows), np.array([0]), np.array([days]), firm, policy, cap)


def test_a_hand_computed_path():
    """$800 a day passes the evaluation on day 4 ($49 + $149 paid); $300 a day pays $675 on the fifth funded day,
    $1,012.50 five winning days later (the limit now at the starting balance) and $1,181.25 five days after that,
    each credited five trading days after its day; the last is still pending when the 20-day path ends."""
    res = _one_path([[0.8]] * 20, [[0.6]] * 20)
    assert res["evals"][0] == 1 and res["passes"][0] == 1 and res["activations"][0] == 1 and res["fees"][0] == pytest.approx(198.0)
    assert res["payouts"][0] == 3 and res["paid"][0] == pytest.approx(675.0 + 1012.5 + 1181.25) and res["first_payout"][0] == 9
    assert res["final_cash"][0] == pytest.approx(START_CASH - 198.0 + 675.0 + 1012.5 + 1181.25)
    assert res["low"][0] == pytest.approx(START_CASH - 198.0) and not res["ruined"][0]
    assert res["eval_log"] == [(0, 0, "pass", 4)] and res["xfa_log"] == [(0, 4, "payout", 5, pytest.approx(675.0))]


def test_a_losing_stream_ruins_the_path_on_the_predicted_day():
    """Two stop-outs a day fail every evaluation on its first day: forty are bought at $49 and the forty-first is
    unaffordable ($40 left), with nothing live and nothing pending."""
    res = _one_path([[-1.02, -1.02]] * 60, [[-1.02, -1.02]] * 60)
    assert res["evals"][0] == 40 and res["fees"][0] == pytest.approx(40 * 49.0) and res["final_cash"][0] == pytest.approx(40.0)
    assert res["ruined"][0] and res["ruin_day"][0] == 40
    assert len(res["eval_log"]) == 40 and all(x[2] == "fail" and x[3] == 1 for x in res["eval_log"])


def test_an_open_evaluation_is_billed_monthly_and_closed_after_30_days():
    """No trades: each evaluation runs 30 trading days (six weeks of business days), billed at purchase and 30
    calendar days later, and is closed; the next is bought the following day."""
    res = _one_path([[]] * 61, [[]] * 61)
    assert [x[2:] for x in res["eval_log"]] == [("open", -1), ("open", -1)] and [x[1] for x in res["eval_log"]] == [0, 30]
    assert res["evals"][0] == 3 and res["fees"][0] == pytest.approx(5 * 49.0)  # two evaluations billed twice, the third once


def test_an_evaluation_whose_fee_cannot_be_paid_is_cancelled(monkeypatch):
    """Bought on 2024-01-02 with $11 left; the second fee falls due on the first trading day 30 calendar days later
    (2024-02-01, the 23rd business day), cannot be paid, and the path is ruined that day."""
    monkeypatch.setattr(b5_paths, "START_CASH", 60.0)
    res = _one_path([[]] * 40, [[]] * 40)
    assert res["evals"][0] == 1 and res["cancelled"][0] == 1 and res["eval_log"] == [] and res["ruined"][0]
    assert res["final_cash"][0] == pytest.approx(11.0) and res["ruin_day"][0] == 23


def test_a_pending_payout_is_waited_for_and_arrives_five_trading_days_later(monkeypatch):
    """$198: one evaluation ($49), passed on day 4 and activated ($149), leaves nothing. The funded account asks for
    $675 on its fifth day (day 9) and breaches on day 10: nothing live and no cash, but a payout pending, so no ruin.
    The $675 arrives on day 14, five trading days after the request, and buys the next evaluation that day."""
    monkeypatch.setattr(b5_paths, "START_CASH", 198.0)
    res = _one_path([[0.8]] * 30, [[0.6]] * 9 + [[-5.0]] + [[0.6]] * 20)
    assert [x[1] for x in res["eval_log"]][:2] == [0, 13] and res["first_payout"][0] == 9
    assert res["xfa_log"][0] == (0, 4, "payout", 5, pytest.approx(675.0)) and res["xfa_breaches"][0] >= 1
    assert not res["ruined"][0]


def test_a_phase_with_no_trade_still_runs(stream):
    """Stops of 300 points: one micro fits the $1,000 evaluation budget ($601 at a full stop-out) and none the $500
    funded one. The run completes, the gates compare against a stream with no trade, and nothing is ever paid."""
    pre, cal, cut = stream
    wide = pre.copy()
    wide["stop_points"] = 300.0
    ev, fu = phase_streams(wide, "topstep_50k_x", "whole micros", 1.0)
    assert len(ev) and fu.empty
    out = run(wide, cal[cal <= cut], cut, "topstep_50k_x", "ask", "whole micros", 1.0, 1)
    assert out["paths"] > 100 and out["funded_trades"] == 0 and out["paid_mean"] == 0.0 and out["gate_evaluations"] > 0
    assert run(wide, cal[cal <= cut], cut, "topstep_50k_x", "wait", "whole micros", 1.0, 5)["paid_mean"] == 0.0


def test_the_plan_runs_whole_micros_on_topstepx_only():
    from research.b5_paths import plan_runs
    sel = [{"stream": "S1", "firm": "topstep_50k", "size": 1.00, "policy": "ask", "runs": True},
           {"stream": "S1", "firm": "topstep_50k_x", "size": 0.95, "policy": "ask", "runs": True},
           {"stream": "S1", "firm": "topstep_50k_x", "size": 1.00, "policy": "wait", "runs": False},
           {"stream": "S3", "firm": "topstep_50k", "size": 1.00, "policy": "wait", "runs": True}]
    got = [(x["stream"], x["firm"], x["policy"], x["sizing"], x["size"]) for x in plan_runs(sel)]
    assert got == [("S1", "topstep_50k", "ask", "fractional", 1.00), ("S1", "topstep_50k_x", "ask", "whole micros", 1.0),
                   ("S1", "topstep_50k_x", "ask", "fractional", 0.95), ("S3", "topstep_50k", "wait", "fractional", 1.00),
                   ("S3", "topstep_50k_x", "wait", "whole micros", 1.0)]


def test_the_frozen_row_is_the_periods_own(stream):
    from research.b5_paths import frozen_row
    from research.candidates import bootstrap, score_sized
    pre, cal, cut = stream
    for period in ("development", "benchmark"):
        want = bootstrap(score_sized(sequential_pass(pre), cal, cut, 0.95, "topstep_50k_x")[period], START_CASH)
        assert frozen_row(pre, cal, cut, "topstep_50k_x", "fractional", 0.95, period) == want


def test_a_slot_restarts_its_payout_count_with_a_purchase():
    a = SlotAccount(PRESETS["topstep_50k_x"], 2, FUNDED_RISK, start_phase=INACTIVE, restart_failed=False, topstep_xfa=True)
    a.payout_count[:] = 3
    a.purchase(np.array([True, False]))
    assert list(a.payout_count) == [0, 3] and a.phase[0] == EVAL and a.phase[1] == INACTIVE


def test_path_bounds():
    dates = pd.DatetimeIndex(pd.bdate_range("2019-01-02", "2021-12-31"))
    last = pd.Timestamp("2021-06-30")
    starts, ends = path_bounds(dates, last)
    span = pd.Timedelta(days=PATH_DAYS)
    assert len(starts) and (dates[starts] + span - pd.Timedelta(days=1) <= last).all() and not (dates[starts[-1] + 1] + span - pd.Timedelta(days=1) <= last)
    assert (dates[ends - 1] < dates[starts] + span).all() and (dates[ends] >= dates[starts] + span).all()
    one, end = path_bounds(dates, None)
    assert list(one) == [0] and dates[end[0] - 1] < dates[0] + span <= dates[end[0]]


@pytest.fixture(scope="module")
def stream(tmp_path_factory):
    bars = synthetic_minute_bars(days=640, seed=4)
    p = tmp_path_factory.mktemp("b5") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    pre = load_trades(str(p))
    cal = trading_days_of(bars)
    day = pre["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    cut = (day.max() - pd.DateOffset(months=3)).normalize()
    return pre, cal, cut


def test_phase_streams(stream):
    pre, _, _ = stream
    ev, fu = phase_streams(pre, "topstep_50k_x", "fractional", 0.95)
    assert ev is fu and np.allclose(ev["r"], sequential_pass(pre)["r"].astype(float) * 0.95)
    ev, fu = phase_streams(pre, "topstep_50k_x", "whole micros", 0.95)
    for got, want in ((ev, whole_contracts(pre, 1000.0, 50)), (fu, whole_contracts(pre, FUNDED_RISK, 50))):
        assert list(got.index) == list(want.index) and np.allclose(got["r"], want["r"])


@pytest.mark.parametrize("policy", ["ask", "wait"])
@pytest.mark.parametrize("sizing", SIZINGS)
def test_runs_pass_their_gates_and_conserve_cash(stream, policy, sizing, monkeypatch):
    """Every path of every configuration: each evaluation and first payout equals its walk-forward reference (the
    gates run inside `run`), and the cash at the end is the start, less every fee, plus every payout."""
    pre, cal, cut = stream
    kept = {}
    real = b5_paths.summarize

    def keep(res, *a):
        kept["res"] = res
        return real(res, *a)
    monkeypatch.setattr(b5_paths, "summarize", keep)
    for cap in CAPS:
        out = run(pre, cal[cal <= cut], cut, "topstep_50k_x", policy, sizing, 1.0, cap)
        res = kept["res"]
        assert out["paths"] > 100 and out["gate_evaluations"] > out["paths"] and out["gate_funded"] > 0
        assert np.allclose(res["final_cash"], b5_paths.START_CASH - res["fees"] + res["paid"])
        starts = pd.DataFrame(res["eval_log"], columns=["path", "start", "outcome", "days"])
        assert not starts.duplicated(["path", "start"]).any()  # at most one purchase a day
        assert 0.0 <= out["p_ruin"] <= 1.0 and out["cash_p10"] <= out["cash_p50"] <= out["cash_p90"]
    bm = run(pre, cal[cal > cut], None, "topstep_50k_x", policy, sizing, 1.0, 5)
    assert bm["paths"] == 1


def test_the_gates_refuse_a_mismatch(stream):
    pre, cal, cut = stream
    part = cal[cal <= cut]
    ev, fu = phase_streams(pre, "topstep_50k_x", "fractional", 1.0)
    from fpt.evaluate import _daily_r
    dates, rs = _daily_r(ev[(ev["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut).to_numpy()], part)
    dates = pd.DatetimeIndex(dates)
    w = max(len(x) for x in rs)
    starts, ends = path_bounds(dates, cut)
    res = simulate(dates, day_arrays(rs, w), day_arrays(rs, w), starts[:20], ends[:20], "topstep_50k_x", "ask", 5)
    sub = ev[(ev["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut).to_numpy()]
    check_gates(res, sub, sub, part, "topstep_50k_x", "ask")
    path, start, outcome, days = res["eval_log"][0]
    res["eval_log"][0] = (path, start, "fail" if outcome != "fail" else "pass", days)
    with pytest.raises(ValueError, match="differ from the walk-forward reference"):
        check_gates(res, sub, sub, part, "topstep_50k_x", "ask")


def test_the_reading_rule():
    from research.b5_paths import qualifies
    ok = {"paths": 10, "p_ruin": 0.10, "cash_p50": 2000.01, "cash_p25": 1000.0}
    assert qualifies(ok)
    for k, v in (("p_ruin", 0.1001), ("cash_p50", 2000.0), ("cash_p25", 999.99), ("paths", 0)):
        assert not qualifies({**ok, k: v})
    assert not qualifies({})


def test_no_positive_configuration_stops_b5():
    from research.b5_paths import report
    sel = [{"stream": "S1", "firm": "topstep_50k_x", "size": 1.0, "policy": "ask", "pass_rate": 0.3, "fees": 100.0, "paid_mean": 300.0, "ev": -10.0, "runs": False}]
    text = report(sel, [], ["B3's streams"], "gates", "abc", pd.Timestamp("2025-10-05"))
    assert "B5 stops here" in text and "## Results" not in text


def test_cli_end_to_end_on_four_years(sealed_4y, tmp_path, monkeypatch):
    """The real pipeline on four years of synthetic bars, cut to one stream, preset and policy for time: the pins, the
    selection from B4's lifetime EV, the runs with their gates, and the reading."""
    import os
    from research import b5_paths
    monkeypatch.setattr(b5_paths, "STREAMS", ("S4 S3 + A+ reversion, sealed bracket",))
    monkeypatch.setattr(b5_paths, "RUNS", (("topstep_50k_x", 1.00),))
    monkeypatch.setattr(b5_paths, "POLICIES", {"ask": "ask whenever eligible"})
    docs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research")
    regs = ["--registration", f"{docs}/preregistration_b5_bootstrap.md", "--trend-registration", f"{docs}/preregistration_trend_exit.md",
            "--conditions-registration", f"{docs}/preregistration_conditional_edge.md"]
    args = [*sealed_4y["b3"], *regs, "--out", str(tmp_path / "b5.md")]
    monkeypatch.setattr("sys.argv", ["b5_paths.py", *args])
    with pytest.raises(SystemExit, match="the registered cut is --oos-start 2025-10-06"):
        b5_paths.main()
    monkeypatch.setattr("sys.argv", ["b5_paths.py", *args, "--allow-other-cut"])
    assert b5_paths.main() == 0
    text = (tmp_path / "b5.md").read_text()
    assert "NOT THE REGISTERED RUN" in text and b5_paths.REGISTRATION_SHA256 in text and "## Which configurations run" in text
    assert "| S4 S3 + A+ reversion, sealed bracket | topstep_50k_x | 1.00 | ask |" in text
    if "| yes |" in text.split("## Results")[0]:
        assert "## Reading (the registered rule)" in text and "| whole micros | 5 | development |" in text and "| 1.00 of the budget | 1 | benchmark |" in text
    else:
        assert "B5 stops here" in text
    for which, pos in (("B5", 1), ("trend-exit", 3), ("conditional-edge", 5)):
        fake = tmp_path / f"{which}.md"
        fake.write_text("edited")
        bad = list(regs)
        bad[pos] = str(fake)
        monkeypatch.setattr("sys.argv", ["b5_paths.py", *sealed_4y["b3"], *bad, "--out", str(tmp_path / "x.md"), "--allow-other-cut"])
        with pytest.raises(SystemExit, match=f"the {which} registration file"):
            b5_paths.main()
