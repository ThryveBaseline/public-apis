import json

import numpy as np
import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import forward
from research.forward import candidate_trades, ledger_rows, merge_ledger, micros, same_rows, tail_check, thresholds


def test_whole_micros_within_the_budget():
    # a 25-point stop: $51 a micro at a full stop-out, so 19 in the evaluation ($969) and 9 funded ($459)
    assert list(micros(np.array([25.0, 25.0]), 1000.0)) == [19, 19] and micros(np.array([25.0]), 500.0)[0] == 9
    assert micros(np.array([500.0]), 1000.0)[0] == 0 and micros(np.array([499.0]), 1000.0)[0] == 1 and micros(np.array([2.0]), 1000.0)[0] == 50  # nothing fits; the cap


@pytest.fixture(scope="module")
def history():
    bars = synthetic_minute_bars(days=500, seed=5, start="2024-12-02")
    bars["symbol"] = "1001"
    return bars


def test_thresholds_have_every_checkpoint(history):
    t = candidate_trades(history, [])["S3"]
    sessions = pd.DatetimeIndex(sorted(set(history.index.tz_convert("America/New_York").normalize().tz_localize(None))))
    th = thresholds(t, sessions)
    for k in ("count_p01", "count_p99", "target_share_p01", "stop_share_p99", "flat_share_p01", "long_share_p99",
              "mean_r_20_p025", "drawdown_20_p99", "target_share_20_p01", "mean_r_30_p025", "drawdown_30_p99", "target_share_30_p01"):
        assert k in th and np.isfinite(th[k])
    assert th["count_p01"] <= th["count_p99"] and th["drawdown_30_p99"] >= th["drawdown_20_p99"] - 1e-9


def test_a_tail_rerun_reproduces_the_full_run(history, monkeypatch):
    monkeypatch.setattr(forward, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(forward, "TAIL_WARMUP", 30)
    full = candidate_trades(history, [])
    assert tail_check(history, [], full) > 0


def _rows(history, until):
    t = candidate_trades(history[history.index < pd.Timestamp(until, tz="America/New_York")], [])
    dates = sorted(set(pd.concat([x["date"] for x in t.values()])))
    return ledger_rows(t, dates), dates


def test_the_ledger_appends_and_never_rewrites(history):
    first, d1 = _rows(history, "2026-08-01")
    led, scored = merge_ledger(None, [], first, d1)
    assert same_rows(led[forward.LEDGER_KEY], first[forward.LEDGER_KEY]) and len(scored) == len({d.strftime("%Y-%m-%d") for d in d1})
    more, d2 = _rows(history, "2026-09-01")
    led2, scored2 = merge_ledger(led, scored, more, d2)
    assert len(led2) == len(more) and set(scored) < set(scored2)
    assert same_rows(led2[led2["date"].isin(scored)][forward.LEDGER_KEY].reset_index(drop=True), led[forward.LEDGER_KEY])
    changed = led.copy()
    changed.loc[0, "r"] = changed.loc[0, "r"] + 0.5
    with pytest.raises(ValueError, match="history is never rewritten"):
        merge_ledger(changed, scored, more, d2)
    with pytest.raises(ValueError, match="missing from this run"):
        merge_ledger(led, scored + ["2026-12-31"], more, d2)
    gone = led.iloc[1:].reset_index(drop=True)  # a scored date that had a trade now shows one more trade than recorded
    with pytest.raises(ValueError, match="history is never rewritten"):
        merge_ledger(gone, scored, more, d2)


def _csv(bars: pd.DataFrame, path):
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    out.to_csv(path)


def test_cli_baseline_then_days(history, tmp_path, monkeypatch):
    first = pd.Timestamp("2026-10-06", tz="America/New_York")
    sealed, fwd = history[history.index < first], history[history.index >= first]
    days = sorted(set(fwd.index.tz_convert("America/New_York").normalize()))
    assert len(days) >= 12
    _csv(sealed, tmp_path / "sealed.csv")
    man = {"data": {"sha256": forward.sha256(str(tmp_path / "sealed.csv"))}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    common = ["--csv", str(tmp_path / "sealed.csv"), "--source-tz", "UTC", "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr(forward, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(forward, "TAIL_WARMUP", 30)
    monkeypatch.setattr("sys.argv", ["forward.py", "baseline", *common, "--out", str(tmp_path / "base.md"), "--private-out", str(tmp_path / "base.csv")])
    assert forward.main() == 0
    base = (tmp_path / "base.md").read_text()
    assert "Tail check" in base and "| S3 | development |" in base and "| S4 | benchmark |" in base and "```json" in base
    day_args = [*common, "--baseline", str(tmp_path / "base.md"), "--ledger", str(tmp_path / "ledger.csv"), "--out", str(tmp_path / "status.md")]
    monkeypatch.setattr("sys.argv", ["forward.py", "day", *day_args, "--forward-csv", str(tmp_path / "fwd.csv")])
    _csv(fwd[fwd.index < days[5]], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="baseline report is not the pinned one"):
        forward.main()
    monkeypatch.setattr(forward, "BASELINE_SHA256", forward.sha256(str(tmp_path / "base.md")))
    # five complete days and a sixth cut at noon: the sixth is not scored
    _csv(fwd[fwd.index < days[5] + pd.Timedelta(hours=12)], tmp_path / "fwd.csv")
    assert forward.main() == 0
    scored = json.loads((tmp_path / "ledger.csv.dates.json").read_text())
    assert len(scored) == 5 and scored[-1] == days[4].strftime("%Y-%m-%d")
    led5 = pd.read_csv(tmp_path / "ledger.csv")
    full = candidate_trades(history, [])  # the full history's trades on those dates: the forward run must match them
    want = ledger_rows(full, [pd.Timestamp(d) for d in scored])
    assert same_rows(led5[forward.LEDGER_KEY].astype({"date": str}), want[forward.LEDGER_KEY])
    # twelve days: the ledger extends, the first five are unchanged, and the ten-session checkpoint is reported
    _csv(fwd[fwd.index < days[12]] if len(days) > 12 else fwd, tmp_path / "fwd.csv")
    assert forward.main() == 0
    led12 = pd.read_csv(tmp_path / "ledger.csv")
    assert len(json.loads((tmp_path / "ledger.csv.dates.json").read_text())) == 12
    assert same_rows(led12[led12["date"].isin(scored)][forward.LEDGER_KEY].reset_index(drop=True), led5[forward.LEDGER_KEY])
    status = (tmp_path / "status.md").read_text()
    assert "S3, first 10 sessions:" in status and "Paper Topstep 50K account" in status
    # a recorded trade edited by hand: the next run refuses
    if len(led12):
        bad = led12.copy()
        bad.loc[0, "exit"] = bad.loc[0, "exit"] + 1.0
        bad.to_csv(tmp_path / "ledger.csv", index=False)
        with pytest.raises(SystemExit, match="history is never rewritten"):
            forward.main()
    # forward bars that overlap the sealed ones: refused
    _csv(history[history.index >= first - pd.Timedelta(days=3)], tmp_path / "fwd.csv")
    with pytest.raises(SystemExit, match="must start after the sealed bars"):
        forward.main()
