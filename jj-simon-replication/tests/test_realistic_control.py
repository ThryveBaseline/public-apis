import numpy as np
import pytest

from fpt.data import synthetic_minute_bars
from research import realistic_control as rc
from research import realistic_economics as rex
from research.b5_paths import eval_risk, TOPSTEPX
from research.candidates import FUNDED_RISK
from research.forward import candidate_trades, rth_sessions


@pytest.fixture(scope="module")
def setup():
    bars = synthetic_minute_bars(days=300, seed=11, start="2025-01-06")
    bars["symbol"] = "1001"
    pre = candidate_trades(bars, [])["S4"].copy()
    pre["mae_points"] = rex.mae_points(pre, bars)
    return pre, rth_sessions(bars.index)


@pytest.mark.parametrize("budget", [eval_risk(TOPSTEPX), FUNDED_RISK])
def test_the_nulls_have_no_dollar_edge_as_traded(setup, budget):
    pre, _ = setup
    st = rex.micro_stream(pre, budget, 50, 1.22)  # the phase's stream as the account trades it: sized, sequential-passed
    assert abs(st["r"].mean() * budget) > 1.0  # the stream itself has an edge to remove
    zero = rc.shift_null(st, budget)
    assert abs(zero["r"].mean() * budget) < 1e-9 and (zero.index == st.index).all()  # exactly zero dollars, the same trades
    assert (zero["w"] <= zero["r"] + 1e-12).all()
    assert np.allclose(zero["w"], np.minimum(st["w"], zero["r"]))  # the charge is taken at exit
    flip = rc.relabel_null(0)(st, budget)
    step = (st["r"].max() - st["r"].min()) / len(st)
    assert abs(flip["r"].mean()) <= step + 1e-12 and (flip.index == st.index).all()  # within one trade of zero
    moved = flip["r"] != st["r"]
    side = st["r"] > 0 if st["r"].mean() > 0 else st["r"] < 0  # only the side giving the stream its mean moves
    assert moved.any() and side[moved].all()
    assert (flip["w"] <= flip["r"] + 1e-12).all()


def test_the_null_is_applied_inside_the_paths(setup):
    pre, sessions = setup
    for label, fee, dips in rc.VARIANTS:  # each variant zeroes its own stream, net of its own fee
        x = rex.run_variant(pre, sessions, sessions[-1], "wait", None, fee, dips, null=rc.shift_null)
        a = rex.run_variant(pre, sessions, sessions[-1], "wait", None, fee, dips)
        assert abs(x["eval_dollars_per_trade"]) < 1e-6 and abs(x["funded_dollars_per_trade"]) < 1e-6, label
        assert x["eval_trades"] == a["eval_trades"] and x["funded_trades"] == a["funded_trades"]


def test_control_rows(setup):
    pre, sessions = setup
    rows = rc.control_rows("S4", pre, sessions, sessions[-1], "development")
    assert len(rows) == 4
    for x in rows:
        assert x["actual"]["paths"] == x["shift"]["paths"] > 10
        assert x["relabel_range"][0] <= x["relabel"]["net_per_eval"] <= x["relabel_range"][1]
        assert abs(x["relabel"]["eval_dollars_per_trade"]) < 5 and abs(x["shift"]["funded_dollars_per_trade"]) < 1e-6
    text = rc.report(rows, "0" * 64)
    assert "edge's part" in text and text.count("| S4 | development | TopstepX fee, dips counted |") == 4
