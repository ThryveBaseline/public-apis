import json
from pathlib import Path
from live.verification import mock_demo


def test_full_tick_strategy_execution_restart_and_disconnect(tmp_path):
    output = tmp_path / "receipt.json"
    result = mock_demo(output)
    assert result["mock_workflow"] == "CLEAR"
    receipt = json.loads(output.read_text())
    assert receipt["evidence_type"] == "MOCK_ONLY"
    assert receipt["broker_demo"] == "BLOCKED"
    assert receipt["live"] == "LIVE_DISABLED"
    assert len(receipt["checks"]) == 5


def test_accelerated_full_day_evening_overnight_and_cutoff(tmp_path):
    from live.operational_trial import full_day_mock
    output = tmp_path / "day.json"
    result = full_day_mock(output)
    assert result["status"]=="CLEAR" and result["simulated_hours"]==23
    report = json.loads(output.read_text())
    assert report["synthetic_ticks"]==16561
    assert report["wall_clock_broker_trading_day"]=="NOT_RUN"
    assert report["real_time_signal_timing"]=="NOT_VALIDATED"
    assert report["final_position"]==0 and report["open_orders"]==0


def test_late_missing_bar_cannot_silently_change_replayed_state(tmp_path):
    from datetime import timedelta
    import pytest
    from live.feed import MinuteFeed
    from live.models import Bar, Blocked
    from live.runtime import Runtime
    from .test_execution import rig
    from live.ledger import Ledger
    from types import SimpleNamespace
    ledger=Ledger(tmp_path/"bars.sqlite",lane="mock",account="SIM001")
    try:
        runtime=Runtime(SimpleNamespace(ledger=ledger),MinuteFeed("XCME:NQ.Z26"),calendar_dir=tmp_path,prior_high=21000)
        runtime.load_calendar=lambda _:None
        from datetime import datetime, timezone
        start=datetime(2026,10,21,14,tzinfo=timezone.utc)
        first=Bar(start,20000,20000,20000,20000,1)
        runtime.completed_bar(first)
        runtime.completed_bar(Bar(start+timedelta(minutes=2),20000,20000,20000,20000,1))
        with pytest.raises(Blocked,match="LATE_BAR"):
            runtime.completed_bar(Bar(start+timedelta(minutes=1),20000,20000,20000,20000,1))
        assert ledger.db.execute("SELECT count(*) FROM bars").fetchone()[0]==2
        runtime.completed_bar(first)
        with pytest.raises(Blocked,match="REVISION"):
            runtime.completed_bar(Bar(start,20000,20001,20000,20000,1))
    finally:
        ledger.close()
