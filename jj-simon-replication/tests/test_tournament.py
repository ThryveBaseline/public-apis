import json

import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import forward as fw
from research import tournament as tt


@pytest.fixture(scope="module")
def history():
    bars = synthetic_minute_bars(days=210, seed=9, start="2026-01-05")
    bars["symbol"] = "1001"
    return bars


def _csv(bars, path):
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    out["instrument_id"] = out["symbol"]
    out.to_csv(path)


def test_init_then_days(history, tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "MAX_GAP", pd.Timedelta(hours=18))  # regular-session synthetic bars; the gap rule is tested in test_forward
    monkeypatch.setattr(fw, "classify_gaps", lambda idx: {"halts": [], "session": [], "roll": [], "overnight": []})
    first = pd.Timestamp("2026-10-06", tz="America/New_York")
    sealed, fwd = history[history.index < first], history[history.index >= first]
    days = sorted(set(fwd.index.tz_convert("America/New_York").normalize()))
    _csv(sealed, tmp_path / "sealed.csv")
    (tmp_path / "manifest.json").write_text(json.dumps({"data": {"sha256": fw.sha256(str(tmp_path / "sealed.csv"))}}))
    common = ["--csv", str(tmp_path / "sealed.csv"), "--source-tz", "UTC", "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["tournament.py", "init", *common, "--out", str(tmp_path / "init.json")])
    assert tt.main() == 0
    pinned = json.loads((tmp_path / "init.json").read_text())
    assert sorted(pinned["variants"]) == sorted(tt.VARIANTS) and sum(pinned["tail_check_trades"].values()) > 0
    assert "r_per_trade" not in json.dumps(pinned) and "research/tournament.py" in pinned["code"]  # init reports no performance
    day = ["tournament.py", "day", *common, "--init", str(tmp_path / "init.json"), "--state", str(tmp_path / "state.json"),
           "--summary", str(tmp_path / "summary.json"), "--forward-csv", str(tmp_path / "fwd.csv")]
    monkeypatch.setattr("sys.argv", day)
    _csv(fwd[fwd.index < days[4]], tmp_path / "fwd.csv")
    assert tt.main() == 0
    s3 = json.loads((tmp_path / "state.json").read_text())
    assert len(s3["dates"]) == 3
    full = tt.variant_trades(history, [])  # the whole history's trades on those dates: the forward run must match them
    want = fw.ledger_rows(full, [pd.Timestamp(d) for d in s3["dates"]])
    assert fw.same_rows(pd.DataFrame(s3["trades"])[fw.LEDGER_KEY].astype({"date": str}), want[fw.LEDGER_KEY])
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["sessions"] == 3 and len(summary["variants"]) == len(tt.VARIANTS) and summary["z"] > 2.9
    assert not any(v["promotable"] for v in summary["variants"].values())  # fewer than 50 trades each
    _csv(fwd, tmp_path / "fwd.csv")
    assert tt.main() == 0
    s_all = json.loads((tmp_path / "state.json").read_text())
    assert s_all["dates"][:3] == s3["dates"] and len(s_all["runs"]) == 2
    monkeypatch.setattr(tt, "VARIANTS", {**tt.VARIANTS, "T99": ("extra", tt.B0)})
    with pytest.raises(SystemExit, match="changed since init"):
        tt.main()


def test_the_promotion_bound():
    led = pd.DataFrame({"candidate": ["T01"] * 60, "date": [f"2026-10-{6 + i // 3:02d}" for i in range(60)], "r": [1.0, -1.0, 2.0] * 20})
    s = tt.summarize(led, sorted(set(led["date"])))["variants"]["T01"]
    assert s["trades"] == 60 and s["r_per_trade"] == pytest.approx(2 / 3) and s["promotable"] == (s["lower_bound"] > 0)
    assert tt.summarize(led.iloc[:30], ["2026-10-06"])["variants"]["T01"]["promotable"] is False  # under 50 trades
