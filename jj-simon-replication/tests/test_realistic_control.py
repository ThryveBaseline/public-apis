import numpy as np
import pytest

from fpt.data import synthetic_minute_bars
from research import realistic_control as rc
from research import realistic_economics as rex
from research.forward import candidate_trades, rth_sessions


@pytest.fixture(scope="module")
def setup():
    bars = synthetic_minute_bars(days=300, seed=11, start="2025-01-06")
    bars["symbol"] = "1001"
    pre = candidate_trades(bars, [])["S4"].copy()
    pre["mae_points"] = rex.mae_points(pre, bars)
    return pre, rth_sessions(bars.index)


def test_the_nulls_have_no_edge(setup):
    pre, _ = setup
    r = rc.net_r(pre)
    zero, m = rc.shift_null(pre)
    assert abs(rc.net_r(zero).mean()) < 1e-12 and m == pytest.approx(r.mean())
    assert np.allclose(rc.net_r(zero), r - m)  # the conversion back to points is exact
    flip, share = rc.relabel_null(pre, 0)
    r2 = rc.net_r(flip)
    moved = ~np.isclose(r2, r)
    assert 0 < share < 1 and abs(r2.mean()) < abs(r.mean()) / 5  # the mean brought to about zero
    side = r > 0 if r.mean() > 0 else r < 0  # only the side giving the stream its mean moves
    assert (side[moved]).all()
    for z in (zero, flip):  # a worst excursion is never less than the trade's loss
        assert (z["mae_points"] >= -z["pnl_points"] - 1e-9).all()


def test_control_rows(setup):
    pre, sessions = setup
    rows = rc.control_rows("S4", pre, sessions, sessions[-1], "development")
    assert len(rows) == 4
    for x in rows:
        assert x["actual"]["paths"] == x["shift"]["paths"] > 10
        assert x["relabel_range"][0] <= x["relabel"]["net_per_eval"] <= x["relabel_range"][1]
    text = rc.report(rows, "0" * 64)
    assert "edge's part" in text and text.count("| S4 | development | TopstepX fee, dips counted |") == 4
    b5 = rc.control_rows("S4", pre, sessions, sessions[-1], "development", rc.VARIANTS[1])
    assert all(x["variant"].startswith("B5") for x in b5) and b5[0]["shift"]["paths"] == rows[0]["shift"]["paths"]
