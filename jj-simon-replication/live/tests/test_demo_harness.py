from dataclasses import asdict
from datetime import timedelta
import json
import pytest

from live.account_lock import account_lock
from live.demo_mechanics import demo_smoke
from live.models import Blocked
from live.recovery import RecoveryMonitor
from .test_execution import rig, entry, quote


def config(w, e, tmp_path):
    p=tmp_path/"mechanics.json"
    p.write_text(json.dumps({"mode":"demo-mechanics","environment":"demo","account":w.account,
        "execution_symbol":e.symbol,"schedule_confirmed":True,"cutoff":e.cutoff.isoformat(),
        "state_directory":str(tmp_path/"trial"),"risk_terms":asdict(e.terms),"starting_cash":2000,
        "expected_delay_seconds":600}))
    return p


def test_delayed_demo_harness_runs_mechanics_but_never_certifies_timing(rig,tmp_path):
    w,b,l,e=rig
    connections=[]
    def stream(symbols):
        connections.append(symbols)
        ms=int((w.clock-timedelta(minutes=10)).timestamp()*1000)
        yield {"q":[{"s":e.symbol,"b":w.price,"a":w.price,"bt":ms,"at":ms}]}
    b.stream=stream
    report=demo_smoke(config(w,e,tmp_path),tmp_path/"receipt.json",broker=b,now=lambda:w.clock)
    assert report["status"]=="CLEAR" and report["scope"]=="MECHANICS_SMOKE_SUBSET"
    assert report["real_time_signal_timing"]=="NOT_VALIDATED" and report["full_trading_day"]=="NOT_RUN"
    assert report["live"]=="LIVE_DISABLED" and w.net==0
    assert len(w.placements())==2 and connections==[[e.symbol],[]]


def test_demo_harness_timeout_keeps_unknown_and_records_unconfirmed_cleanup(rig,tmp_path):
    w,b,l,e=rig
    ms=int((w.clock-timedelta(minutes=10)).timestamp()*1000)
    def stream(symbols):
        yield {"q":[{"s":e.symbol,"b":w.price,"a":w.price,"bt":ms,"at":ms}]}
    b.stream=stream
    w.timeout_after_accept=True
    report=demo_smoke(config(w,e,tmp_path),tmp_path/"receipt.json",broker=b,now=lambda:w.clock)
    assert report["status"]=="BLOCKED" and report["cleanup"]=="UNCONFIRMED_CHECK_BROKER_PORTAL"
    assert len(w.placements())==1


def test_demo_harness_rejects_production_before_touching_network(rig,tmp_path):
    w,b,l,e=rig
    path=config(w,e,tmp_path)
    data=json.loads(path.read_text())
    data["environment"]="live-readonly"
    path.write_text(json.dumps(data))
    before=len(w.calls)
    with pytest.raises(Blocked):
        demo_smoke(path,tmp_path/"receipt.json",broker=b,now=lambda:w.clock)
    assert len(w.calls)==before


def test_shared_account_lock_cannot_be_bypassed_with_another_state_directory():
    with account_lock("demo","SIM001"):
        with pytest.raises(Blocked,match="ANOTHER_RUNTIME"):
            with account_lock("demo","SIM001"):
                pass


def test_recovery_discovers_missing_stop_and_closes_without_waiting_for_cutoff(rig):
    w,b,l,e=rig
    e.submit(entry(w),quote(w))
    stop=next(o for o in w.orders.values() if o["orderType"]=="STOP")
    stop["status"]="CANCELLED"
    assert RecoveryMonitor(e).step()
    assert w.net==0 and l.meta("halt")


def test_recover_entrypoint_can_close_after_old_session_has_expired(rig,tmp_path):
    from live.ledger import Ledger
    from live.runner import recover_config
    w,b,l,e=rig
    state=tmp_path/"expired-session"
    persisted=Ledger(state/"demo.sqlite",lane="demo",account=w.account)
    e.ledger=persisted
    e.submit(entry(w),quote(w))
    persisted.close()
    path=config(w,e,tmp_path)
    data=json.loads(path.read_text())
    data.update(mode="demo",state_directory=str(state),trading_day="2026-10-22",parity_qualified=False)
    path.write_text(json.dumps(data))
    w.clock += timedelta(days=1)
    result=recover_config(path,broker=b,now=lambda:w.clock)
    assert result["status"]=="CLEAR" and result["scope"]=="RECOVERY_CONFIRMED_FLAT"
    assert w.net==0 and len(w.placements())==2
    restored=Ledger(state/"demo.sqlite",lane="demo",account=w.account)
    try:
        assert restored.meta("halt") is not None
    finally:
        restored.close()


def test_recover_entrypoint_never_creates_a_fresh_ledger(rig,tmp_path):
    from live.runner import recover_config
    w,b,l,e=rig
    with pytest.raises(Blocked,match="EXISTING_RECOVERY_LEDGER"):
        recover_config(config(w,e,tmp_path),broker=b,now=lambda:w.clock)
    assert not w.placements()
