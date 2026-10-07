import json

import pandas as pd
import pytest

from fpt.data import synthetic_minute_bars
from research import forward as fw
from research import forward_b0
from research.engine import ResearchConfig, generate_trades


@pytest.fixture(scope="module")
def history():
    bars = synthetic_minute_bars(days=470, seed=8, start="2025-01-06")
    bars["symbol"] = "1001"
    return bars


def _csv(bars, path):
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    out["instrument_id"] = out["symbol"]
    out.to_csv(path)


def test_the_b0_stream_runs_beside_v1_without_touching_it(history, tmp_path, monkeypatch):
    for name in ("CANDIDATES", "PROTOCOL_SHA256", "BASELINE_PIN", "TRADE_MODULES"):  # restored after the test
        monkeypatch.setattr(fw, name, getattr(fw, name))
    v1 = dict(fw.CANDIDATES)
    monkeypatch.setattr(forward_b0, "BASELINE_PIN", str(tmp_path / "pin"))
    monkeypatch.setattr(fw, "TAIL_SESSIONS", 90)
    monkeypatch.setattr(fw, "TAIL_WARMUP", 30)
    monkeypatch.setattr(fw, "MAX_GAP", pd.Timedelta(hours=18))  # regular-session synthetic bars; the gap rule is tested in test_forward
    monkeypatch.setattr(fw, "classify_gaps", lambda idx: {"halts": [], "session": [], "roll": [], "overnight": []})
    first = pd.Timestamp("2026-10-06", tz="America/New_York")
    sealed, fwd = history[history.index < first], history[history.index >= first]
    days = sorted(set(fwd.index.tz_convert("America/New_York").normalize()))
    _csv(sealed, tmp_path / "sealed.csv")
    (tmp_path / "manifest.json").write_text(json.dumps({"data": {"sha256": fw.sha256(str(tmp_path / "sealed.csv"))}}))
    common = ["--csv", str(tmp_path / "sealed.csv"), "--source-tz", "UTC", "--manifest", str(tmp_path / "manifest.json"),
              "--protocol", "docs/research/forward_protocol_b0.md"]
    monkeypatch.setattr("sys.argv", ["forward_b0.py", "baseline", *common, "--out", str(tmp_path / "base.md")])
    assert forward_b0.main() == 0
    block = fw.read_baseline((tmp_path / "base.md").read_text())
    assert list(block["candidates"]) == ["B0"] and "research/forward_b0.py" in block["code"] and "| B0 | development |" in (tmp_path / "base.md").read_text()
    (tmp_path / "pin").write_text(fw.sha256(str(tmp_path / "base.md")))
    _csv(fwd[fwd.index < days[6]], tmp_path / "fwd.csv")
    monkeypatch.setattr("sys.argv", ["forward_b0.py", "day", *common, "--baseline", str(tmp_path / "base.md"), "--state", str(tmp_path / "state.json"),
                                     "--out", str(tmp_path / "status.md"), "--forward-csv", str(tmp_path / "fwd.csv")])
    assert forward_b0.main() == 0
    st = json.loads((tmp_path / "state.json").read_text())
    assert len(st["dates"]) == 5 and {t["candidate"] for t in st["trades"]} <= {"B0"}
    full = generate_trades(history, ResearchConfig())  # Baseline 0 on the whole history: the forward stream must equal it on its dates
    full = full.assign(candidate="B0", date=fw.ny_date(full["entry_time"]), micros_eval=0, micros_funded=0)
    want = fw.ledger_rows({"B0": full}, [pd.Timestamp(d) for d in st["dates"]])
    assert len(want) > 0 and fw.same_rows(pd.DataFrame(st["trades"])[fw.LEDGER_KEY].astype({"date": str}), want[fw.LEDGER_KEY])
    assert list(v1) == ["S3", "S4"]
