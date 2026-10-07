import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.evaluate import trading_days_of
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.candidates import ny_day
from research.ledger_filters import sequential_pass
from research.lifetime import lifetime_rows
from research.structure_control import relabelled, rows_for, shifted


@pytest.fixture(scope="module")
def stream(tmp_path_factory):
    bars = synthetic_minute_bars(days=200, seed=9)
    p = tmp_path_factory.mktemp("sc") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    st = sequential_pass(load_trades(str(p)))
    day = st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    return st, trading_days_of(bars), (day.max() - pd.DateOffset(months=2)).normalize()


def test_the_shift_zeroes_the_development_mean_and_keeps_every_other_column(stream):
    st, _, cut = stream
    zero, m = shifted(st, cut)
    dev = (ny_day(st) <= cut).to_numpy()
    assert abs(zero.loc[dev, "r"].mean()) < 1e-12 and m == pytest.approx(st.loc[dev, "r"].mean())
    assert np.allclose(zero["r"], st["r"].astype(float) - m)  # the benchmark moves by the same development mean
    assert zero.drop(columns="r").equals(st.drop(columns="r"))


def test_the_relabel_null_keeps_outcome_sizes_and_zeroes_the_development_mean(stream):
    st, _, cut = stream
    dev = (ny_day(st) <= cut).to_numpy()
    for sign in (1.0, -1.0):  # a stream with a positive mean and its mirror with a negative one
        s = st.assign(r=st["r"].astype(float) * sign)
        flip, share = relabelled(s, cut)
        r0, r1 = s["r"].to_numpy(float), flip["r"].to_numpy(float)
        m = r0[dev].mean()
        side = r0 < 0 if m < 0 else r0 > 0
        target = np.quantile(r0[dev & ((r0 > 0) if m < 0 else (r0 < 0))], 0.5, method="lower")
        moved = r1 != r0
        assert moved.any() and (side[moved]).all() and np.allclose(r1[moved], target)  # only the mean's side moves, to the other side's median
        step = abs(target - r0[side & dev]).max()
        assert abs(r1[dev].sum()) <= step and 0 < share < 1  # as close to zero as one more trade can bring it
        bm_side = side & ~dev
        assert (moved & ~dev).sum() == round(share * bm_side.sum())
        assert flip.drop(columns="r").equals(s.drop(columns="r"))


def test_rows_pair_the_stream_with_both_nulls_on_topstepx(stream, monkeypatch):
    from research import structure_control
    st, cal, cut = stream
    monkeypatch.setattr(structure_control, "RUNS_X", (("topstep_50k_x", 0.95),))
    monkeypatch.setattr(structure_control, "SEEDS", (0, 1, 2))
    rows = rows_for("s", st, cal, cut)
    real = lifetime_rows(st, cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait"))
    null = lifetime_rows(shifted(st, cut)[0], cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait"))
    nulls2 = [lifetime_rows(relabelled(st, cut, seed)[0], cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait")) for seed in (0, 1, 2)]
    assert len(rows) == len(real) == len(null)
    for i, (r, a, b) in enumerate(zip(rows, real, null)):
        assert (r["period"], r["policy"], r["horizon"]) == (a["period"], a["policy"], a["horizon"])
        assert r["ev"] == pytest.approx(a["ev"], nan_ok=True) and r["ev0"] == pytest.approx(b["ev"], nan_ok=True)
        evs = [n2[i]["ev"] for n2 in nulls2]
        assert r["ev1"] == pytest.approx(np.mean(evs), nan_ok=True) and r["ev1_sd"] == pytest.approx(np.std(evs, ddof=1), nan_ok=True)
    assert all(x["firm"] == "topstep_50k_x" for x in rows)


def test_a_stream_with_no_other_side_has_no_relabel_null(stream):
    st, _, cut = stream
    up = st.assign(r=st["r"].astype(float).abs() + 0.1)  # every trade a winner
    same, share = relabelled(up, cut)
    assert np.isnan(share) and same["r"].equals(up["r"])


def test_cli_runs_through_b3s_gates(sealed_4y, tmp_path, monkeypatch):
    from research import structure_control
    monkeypatch.setattr(structure_control, "STREAMS", ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket"))
    monkeypatch.setattr(structure_control, "RUNS_X", (("topstep_50k_x", 1.00),))
    monkeypatch.setattr(structure_control, "SEEDS", (0, 1))
    monkeypatch.setattr("sys.argv", ["structure_control.py", *sealed_4y["b3"], "--out", str(tmp_path / "sc.md")])
    assert structure_control.main() == 0
    text = (tmp_path / "sc.md").read_text()
    assert "reproduces all 8 firm rows" in text and "## topstep_50k_x at 1.00 of the budget" in text
    for name in ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket"):
        assert text.count(f"| {name} |") == 2 * 2 * 3  # periods x policies x horizons
