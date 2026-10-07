import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.strategy import StrategyConfig
from fpt.strategy import generate_trades as frozen
from research.anatomy import load_trades
from research.bracket_replay import grid, replay
from research.engine import ResearchConfig, generate_trades


def _globex_bars(days=40, seed=3, start="2025-02-03"):
    """Globex-style bars (18:00 the evening before to 16:59, across a DST change): a busy first half hour, then a quiet
    tape, so some positions are still open at 16:00 and at the end of the New York day."""
    rng = np.random.default_rng(seed)
    parts = [pd.date_range(d - pd.Timedelta(hours=6), d + pd.Timedelta(hours=17), freq="1min", inclusive="left") for d in pd.bdate_range(start, periods=days, tz=NY)]
    index = parts[0].append(parts[1:])
    m = index.hour * 60 + index.minute
    vol = np.where((m >= 570) & (m < 600), 8.0, 0.8)
    px = 20000 + np.cumsum(rng.normal(0, 1, len(index)) * vol)
    o = np.r_[px[0], px[:-1]]
    hi = np.maximum(o, px) + np.abs(rng.normal(0, 1, len(index))) * vol / 2
    lo = np.minimum(o, px) - np.abs(rng.normal(0, 1, len(index))) * vol / 2

    def q(x):
        return np.round(x * 4) / 4
    return pd.DataFrame({"open": q(o), "high": q(hi), "low": q(lo), "close": q(px), "volume": 100}, index=index)


@pytest.fixture(scope="module")
def rth():
    return synthetic_minute_bars(days=40, seed=9)


@pytest.fixture(scope="module")
def globex_short():
    return _globex_bars(days=15)


@pytest.fixture(scope="module")
def globex():
    return _globex_bars()


FROZEN_CASES = [{}, {"allow_grade_a": False}, {"pm_session": True}, {"stop_mode": "atr_tier", "size_mode": "tier"}, {"flat_at_window_end": True},
                {"continuation_direction": "side_of_fv"}, {"displacement_mode": "wick"}, {"require_band_touch": True, "reversion_end": "10:00"},
                {"rolling_fair_value": False}, {"stop_scope": "day", "max_consecutive_losses": 2}, {"big_open_scope": "session"},
                {"big_open_scope": "am", "big_open_measure": "range"}, {"continuation_end": "09:45", "skip_first_minutes": 3},
                {"target_points": None, "rr": 2.0}, {"max_target_overshoot_pct": None}, {"extra_sessions": (("14:00", "14:05", "15:00"),)}]


@pytest.mark.parametrize("kw", FROZEN_CASES, ids=[",".join(k) or "default" for k in FROZEN_CASES])
def test_defaults_reproduce_the_frozen_engine(rth, globex_short, kw):
    n = 0
    for bars in (rth, globex_short):
        theirs = frozen(bars, StrategyConfig(**kw))
        pd.testing.assert_frame_equal(generate_trades(bars, ResearchConfig(**kw)), theirs)
        if not kw:  # the sealed sizing is one contract on 25 and on 50 points, so one_contract changes nothing there
            pd.testing.assert_frame_equal(generate_trades(bars, ResearchConfig(one_contract=True)), theirs)
            assert (theirs["exit_reason"] == "session_end").any() or bars is rth
        n += len(theirs)
    assert n > 0


def test_grade_a_per_setup(rth):
    pd.testing.assert_frame_equal(generate_trades(rth, ResearchConfig(allow_grade_a_continuation=False, allow_grade_a_reversion=False)),
                                  frozen(rth, StrategyConfig(allow_grade_a=False)))
    t = generate_trades(rth, ResearchConfig(allow_grade_a_reversion=False))
    assert set(t.loc[t["setup"] == "reversion", "grade"]) == {"A+"}
    assert (t.loc[t["setup"] == "continuation", "grade"] == "A").any()
    with pytest.raises(ValueError, match="needs continuation_rr"):
        generate_trades(rth, ResearchConfig(continuation_atr_k=0.4))


def _ledger(trades, tmp_path):
    p = tmp_path / "t.csv"
    trades.to_csv(p, index=False)
    return load_trades(str(p))


def _utc(s):
    return pd.to_datetime(s, utc=True).to_numpy()


def test_flat_time_equals_the_replay_of_each_trades_own_bracket(globex, tmp_path):
    base = frozen(globex, StrategyConfig())
    flat = generate_trades(globex, ResearchConfig(flat_time="16:00"))
    keys = ["signal_time", "entry_time", "setup", "grade", "direction", "entry", "stop", "target", "stop_points", "contracts"]
    pd.testing.assert_frame_equal(flat[keys], base[keys])  # the same entries: nothing is taken after 11:00
    assert (base["exit_reason"] == "session_end").sum() >= 3 and set(flat["exit_reason"]) <= {"stop", "target", "flat"}
    ny = pd.to_datetime(flat["exit_time"]).dt.tz_convert(NY)
    assert ((ny.dt.hour * 60 + ny.dt.minute) < 960).all()
    rep = replay(_ledger(base, tmp_path), globex, [v for v in grid() if v["name"] == "ledger_bracket"]).set_index("trade")
    assert len(rep) >= 15 and (rep["exit_reason"] == "flat_1600").sum() >= 2  # the first sessions have no daily ATR: not replayed
    np.testing.assert_allclose(flat.loc[rep.index, "r"].to_numpy(float), rep["r"].to_numpy(float), rtol=0, atol=1e-9)
    assert (_utc(flat.loc[rep.index, "exit_time"]) == _utc(rep["exit_time"])).all()
    assert ((flat.loc[rep.index, "exit_reason"] == "flat") == (rep["exit_reason"] == "flat_1600")).all()


def test_atr_continuation_bracket_equals_the_replay_on_common_entries(globex, tmp_path):
    base = frozen(globex, StrategyConfig(reversion_end="09:30"))
    assert set(base["setup"]) == {"continuation"}
    mine = generate_trades(globex, ResearchConfig(reversion_end="09:30", flat_time="16:00", continuation_atr_k=0.4, continuation_rr=2.0, one_contract=True))
    assert set(mine["setup"]) == {"continuation"} and (mine["stop_points"] > 25).all() and (mine["contracts"] == 1).all()
    rep = replay(_ledger(base, tmp_path), globex, [v for v in grid() if v["name"] == "atr_0.4_rr2.00"]).set_index("trade")
    rep["entry_utc"] = _utc(base.loc[rep.index, "entry_time"])
    m = mine.assign(entry_utc=_utc(mine["entry_time"])).set_index("entry_utc")
    common = rep[rep["entry_utc"].isin(m.index)]
    assert len(common) >= 5
    got = m.loc[common["entry_utc"]]
    np.testing.assert_allclose(got["stop_points"].to_numpy(float), common["stop_pts"].to_numpy(float))
    np.testing.assert_allclose(got["r"].to_numpy(float), common["r"].to_numpy(float), rtol=0, atol=1e-9)
    assert (_utc(got["exit_time"]) == _utc(common["exit_time"])).all()
    # the frozen sizing would give these stops zero contracts at $500 risk and skip them
    assert frozen(globex, StrategyConfig(reversion_end="09:30", stop_points=float(mine["stop_points"].min()), target_points=None, big_open_candle_points=None)).empty


def test_engine_check_rebuilds_a_sealed_ledger_and_refuses_otherwise(rth, tmp_path, monkeypatch, capsys):
    import json
    from research import engine_check
    out = rth.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    csv = tmp_path / "bars.csv"
    out.to_csv(csv)
    from fpt.data import load_minute_bars
    led = tmp_path / "trades.csv"
    frozen(load_minute_bars(str(csv), source_tz="UTC"), StrategyConfig()).to_csv(led, index=False)  # as scripts/seal_run.py
    man = tmp_path / "manifest.json"
    good = {"data": {"sha256": engine_check.sha256(str(csv))}, "outputs": {"trades_sha256": engine_check.sha256(str(led)), "n_trades": 1}}
    man.write_text(json.dumps(good))
    monkeypatch.setattr("sys.argv", ["engine_check.py", "--csv", str(csv), "--source-tz", "UTC", "--manifest", str(man)])
    assert engine_check.main() == 0 and "PASS" in capsys.readouterr().out
    man.write_text(json.dumps({**good, "outputs": {**good["outputs"], "trades_sha256": "0" * 64}}))
    with pytest.raises(SystemExit, match="FAIL"):
        engine_check.main()
    man.write_text(json.dumps({**good, "data": {"sha256": "0" * 64}}))
    with pytest.raises(SystemExit, match="not the sealed run's"):
        engine_check.main()
