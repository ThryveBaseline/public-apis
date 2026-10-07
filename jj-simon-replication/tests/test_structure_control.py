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
from research.structure_control import rows_for, shifted


@pytest.fixture(scope="module")
def stream(tmp_path_factory):
    bars = synthetic_minute_bars(days=200, seed=9)
    p = tmp_path_factory.mktemp("sc") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    st = sequential_pass(load_trades(str(p)))
    day = st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    return st, trading_days_of(bars), (day.max() - pd.DateOffset(months=2)).normalize()


def test_the_shift_removes_the_development_edge_and_nothing_else(stream):
    st, _, cut = stream
    zero, m = shifted(st, cut)
    dev = (ny_day(st) <= cut).to_numpy()
    assert abs(zero.loc[dev, "r"].mean()) < 1e-12 and m == pytest.approx(st.loc[dev, "r"].mean())
    assert np.allclose(zero["r"], st["r"].astype(float) - m)  # the benchmark moves by the same development mean
    assert zero.drop(columns="r").equals(st.drop(columns="r"))


def test_rows_pair_the_stream_with_its_shifted_copy(stream, monkeypatch):
    from research import structure_control
    st, cal, cut = stream
    monkeypatch.setattr(structure_control, "RUNS", (("topstep_50k_x", 0.95),))
    rows = rows_for("s", st, cal, cut)
    real = lifetime_rows(st, cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait"))
    null = lifetime_rows(shifted(st, cut)[0], cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait"))
    assert len(rows) == len(real) == len(null)
    for r, a, b in zip(rows, real, null):
        assert (r["period"], r["policy"], r["horizon"]) == (a["period"], a["policy"], a["horizon"])
        assert r["ev"] == pytest.approx(a["ev"], nan_ok=True) and r["ev0"] == pytest.approx(b["ev"], nan_ok=True)


def test_cli_runs_through_b3s_gates(sealed_4y, tmp_path, monkeypatch):
    from research import structure_control
    monkeypatch.setattr(structure_control, "STREAMS", ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket"))
    monkeypatch.setattr(structure_control, "RUNS", (("topstep_50k_x", 1.00),))
    monkeypatch.setattr("sys.argv", ["structure_control.py", *sealed_4y["b3"], "--out", str(tmp_path / "sc.md")])
    assert structure_control.main() == 0
    text = (tmp_path / "sc.md").read_text()
    assert "reproduces all 8 firm rows" in text and "## topstep_50k_x at 1.00 of the budget" in text
    for name in ("S0r sealed brackets, flat 16:00", "S1 continuation only, sealed bracket"):
        assert text.count(f"| {name} |") == 2 * 2 * 3  # periods x policies x horizons
