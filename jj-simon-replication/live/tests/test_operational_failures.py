"""Injected operational failures; synthetic fixtures only, no market history."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys

import pytest

from live.execution import Executor
from live.ledger import Ledger
from live.models import Blocked
from live.recovery import RecoveryMonitor
from .test_execution import rig, entry, quote


@pytest.mark.parametrize("field,value", [
    ("status", "REJECTED"), ("status", "CANCELLED"), ("quantity", 2),
    ("quantity", 0), ("side", "BUY"), ("stopPrice", 19900), ("duration", "0"),
])
def test_bad_stop_is_detected_and_account_can_be_closed(rig, field, value):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    stop[field] = value
    with pytest.raises(Blocked, match="PROTECTION"):
        e.reconcile()
    with pytest.raises(Blocked):
        e.submit(entry(w, "forbidden"), quote(w))
    e.flatten("PROTECTION_FAILURE")
    assert w.net == 0 and len(w.placements()) == 2


def test_partial_target_with_sibling_cancelled_requires_emergency_close(rig):
    w, b, l, e = rig
    e.submit(entry(w, stop=12.5), quote(w))
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    assert w.net == 1
    with pytest.raises(Blocked, match="PROTECTION"):
        e.reconcile()
    e.flatten("PARTIAL_EXIT_LOST_STOP")
    assert w.net == 0 and l.account()["net_quantity"] == 0
    assert w.placements()[-1][2]["quantity"] == 1


def test_partial_target_with_resized_stop_remains_protected(rig):
    w, b, l, e = rig
    e.submit(entry(w, stop=12.5), quote(w))
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    stop.update(status="NEW", quantity=1)
    e.reconcile()
    assert l.account()["net_quantity"] == 1
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    e.reconcile()
    assert l.account()["net_quantity"] == 0


def test_partial_overnight_parent_remaining_quantity_cancelled_at_open(rig):
    w,b,l,e=rig
    e.submit(entry(w,stop=12.5,action="BOOK",level=w.price+1),quote(w))
    parent=w.orders[l.intent("one")["order_id"]]
    w.fill_order(parent["orderId"],1,w.price+1)
    e.reconcile()
    e.cancel_book()
    assert parent["status"]=="CANCELLED" and w.net==1
    assert all(w.orders[child]["quantity"]==1 and w.orders[child]["status"]=="NEW" for child in parent["childOrders"])


def test_extra_working_child_is_not_ignored(rig):
    w,b,l,e=rig
    e.submit(entry(w),quote(w))
    parent=l.intent("one")["order_id"]
    w.new_order({"exchSym":e.symbol,"side":"SELL","quantity":1,"orderType":"STOP","duration":"1","stopPrice":19000},parent)
    with pytest.raises(Blocked,match="PROTECTION"):
        e.reconcile()


def test_opposing_broker_positions_cannot_masquerade_as_flat(rig):
    w,b,l,e=rig
    snapshot=b.snapshot()
    snapshot["positions"]=[{"accountId":w.account,"exchSym":e.symbol,"side":side,"quantity":1} for side in ("LONG","SHORT")]
    b.snapshot=lambda:snapshot
    with pytest.raises(Blocked,match="HEDGED"):
        e.reconcile()
    assert e.position_snapshot_confirmed_at is None


def test_exit_cancel_timeout_never_sends_a_market_close_blindly(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    def failed_cancel(_):
        raise Blocked("TRANSPORT_UNCERTAIN")
    b.cancel = failed_cancel
    with pytest.raises(Blocked):
        e.flatten("CUTOFF")
    assert len(w.placements()) == 1 and w.net == 1
    assert l.meta("halt")


def test_transport_loss_during_reconciliation_clears_entry_authority(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    original = b.request
    b.request = lambda *args: (_ for _ in ()).throw(Blocked("TRANSPORT_UNCERTAIN"))
    with pytest.raises(Blocked):
        e.reconcile()
    assert e.reconciled_at is None
    b.request = original
    e.reconcile()
    with pytest.raises(Blocked):
        e.submit(entry(w, "must-not-resume"), quote(w))
    assert len(w.placements()) == 1


def test_open_losses_reduce_new_trade_risk_capacity(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    w.price -= 20
    e.reconcile()
    assert e.risk_equity() == pytest.approx(1959.25)
    # 29 points + conservative fees/slippage exceeds 3% of reduced equity.
    candidate = replace(entry(w, "reduced-capacity"), stop_points=29)
    assert e.submit(candidate, quote(w)) == "SKIPPED"


def test_flat_recovery_can_finish_despite_margin_change(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    w.margin = 1000
    w.clock = e.cutoff
    assert RecoveryMonitor(e).step()
    assert len(w.placements()) == 1


def test_simultaneous_signals_share_atomic_risk_reservations(rig, tmp_path):
    w, b, l, e = rig
    path = tmp_path / "mock.sqlite"
    def reserve(index):
        local = Ledger(path, lane="mock", account=w.account)
        try:
            return local.reserve(entry(w, f"simultaneous-{index}"), e.terms, 2000, 2000, w.price)
        finally:
            local.close()
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(reserve, range(16)))
    assert sum(r["quantity"] for r in rows) == 2
    assert l.reservations()[0] <= 120
    assert all(r["risk"] <= 60 for r in rows)


@pytest.mark.parametrize("after_ack", [False, True])
def test_actual_process_death_durably_prevents_duplicate_submission(rig, tmp_path, after_ack):
    w, b, l, e = rig
    path = tmp_path / "crash.sqlite"
    # No orderly database close: exercise SQLite WAL durability under os._exit.
    script = '''
import os, sys
from live.ledger import Ledger
from live.models import Intent, RiskTerms
ledger=Ledger(sys.argv[1],lane="mock",account="SIM001")
intent=Intent("crash-order","2026-10-22T13:31:00+00:00","ENTRY","09:30","synthetic",1,25,38)
ledger.reserve(intent,RiskTerms(1.5,.25,100,200,300,True),2000,2000,20005)
if sys.argv[2] == "True":
    ledger.acknowledge(intent.id,"1")
os._exit(77)
'''
    result = subprocess.run([sys.executable, "-c", script, str(path), str(after_ack)], cwd=Path(__file__).resolve().parents[2])
    assert result.returncode == 77
    # Model the broker accepting the order independently of the dead client.
    parent = w.new_order({"exchSym":e.symbol,"side":"BUY","quantity":1,"orderType":"MARKET","duration":"1","stopLoss":w.price-25,"takeProfit":w.price+38})
    w.fill_order(parent["orderId"],1,w.price)
    recovered = Ledger(path, lane="mock", account=w.account)
    try:
        new = Executor(b,recovered,e.terms,symbol=e.symbol,kill_file=e.kill_file,cutoff=e.cutoff,expiry=e.expiry,now=e.now)
        if after_ack:
            new.reconcile()
            assert recovered.account()["net_quantity"] == 1
        else:
            with pytest.raises(Blocked):
                new.reconcile()
        assert new.submit(entry(w,"crash-order"),quote(w)) == "DUPLICATE"
        assert not w.placements()
    finally:
        recovered.close()
