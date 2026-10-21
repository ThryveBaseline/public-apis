from dataclasses import replace
from datetime import timedelta
import json
import pytest

from live.ironbeam import Ironbeam
from live.models import Blocked
from .test_execution import rig, entry, quote


def test_changed_fill_price_aligns_absolute_bracket(rig):
    w, b, l, e = rig
    q = quote(w)
    w.price += 0.25
    e.submit(entry(w), q)
    assert l.intent("one")["stop"] == w.price-25
    assert l.intent("one")["target"] == w.price+38
    updates = [c for c in w.calls if c[0] == "PUT"]
    parent = w.orders[l.intent("one")["order_id"]]
    assert len(updates) == 2
    assert {c[2]["orderId"] for c in updates} == set(parent["childOrders"])
    assert all("stopLoss" not in c[2] and "takeProfit" not in c[2] for c in updates)


def test_excess_entry_slippage_halts(rig):
    w, b, l, e = rig
    q = quote(w)
    w.price += 1
    with pytest.raises(Blocked, match="SLIPPAGE"):
        e.submit(entry(w), q)
    assert l.meta("halt")


def test_strategy_exit_resumes_only_after_confirmed_flat(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    e.flatten("STRATEGY_EXIT", intent_id="one")
    assert l.account()["net_quantity"] == 0
    assert l.meta("halt") is None
    e.submit(entry(w, "two"), quote(w))
    assert l.account()["net_quantity"] == 1


def test_unexpected_external_position_halts(rig):
    w, b, l, e = rig
    w.net = 1
    with pytest.raises(Blocked, match="POSITION"):
        e.reconcile()
    assert not w.placements()


def test_missing_snapshot_field_does_not_mean_flat(rig):
    w, b, l, e = rig
    original = b.request
    b.request = lambda method, url, *args: {} if url.endswith("/positions") else original(method, url, *args)
    with pytest.raises(Blocked, match="INCOMPLETE"):
        b.snapshot()


def test_failed_account_check_revokes_old_authority(rig):
    w, b, l, e = rig
    w.is_live = True
    with pytest.raises(Blocked):
        b.bind_account(w.account)
    assert not b.account_verified
    with pytest.raises(Blocked, match="LIVE_DISABLED"):
        b.place({})


def test_host_cannot_be_changed_to_production(rig):
    w, b, l, e = rig
    b.base = "https://live.ironbeamapi.com/v2"
    with pytest.raises(Blocked, match="HOST"):
        b.place({})


def test_order_cannot_override_the_verified_account(rig):
    w,b,l,e=rig
    before=len(w.calls)
    for call in (lambda:b.place({"accountId":"OTHER"}), lambda:b.call("POST","/order/OTHER/place",body={})):
        with pytest.raises(Blocked,match="ACCOUNT_MISMATCH"):
            call()
    assert len(w.calls)==before


def test_stop_wrong_direction_or_wrong_quantity_blocks(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    stop["quantity"] = 2
    with pytest.raises(Blocked, match="PROTECTION"):
        e.reconcile()


def test_orphan_target_after_stop_blocks_new_trades(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    w.fill_order(stop["orderId"], 1, stop["stopPrice"])
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    target["status"] = "NEW"
    with pytest.raises(Blocked, match="ORPHAN"):
        e.reconcile()


def test_fill_revision_never_rewrites_cash(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    before = l.account()
    w.fills[0]["fillPrice"] += 1
    with pytest.raises(Blocked, match="REVISION"):
        e.reconcile()
    assert l.account() == before


def test_opposite_side_cannot_net_away_existing_protection(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    assert e.submit(entry(w, "opposite", direction=-1), quote(w)) == "SKIPPED"
    assert len(w.placements()) == 1


def test_unknown_or_changed_cash_halts(rig):
    w, b, l, e = rig
    w.cash += 500
    with pytest.raises(Blocked, match="CASH"):
        e.reconcile()


def test_cancel_fill_race_is_accounted_before_flatten(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    original = b.cancel
    raced = []
    def cancel(oid):
        order = w.orders[oid]
        if order["orderType"] == "STOP" and not raced:
            raced.append(True)
            w.fill_order(oid, 1, order["stopPrice"])
        return original(oid)
    b.cancel = cancel
    e.flatten("CUTOFF")
    assert l.account()["net_quantity"] == 0 and w.net == 0
    assert len(w.placements()) == 1  # no accidental reversing market order


def test_reconnect_monitors_until_target_fills_without_new_entry(rig):
    from live.recovery import RecoveryMonitor
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    class Socket:
        def recv(self):
            w.fill_order(target["orderId"],1,target["limitPrice"])
            return '{"p":{"ping":"ping"}}'
        def close(self):
            pass
    result = RecoveryMonitor(e, sleep=lambda _:None).run(max_connections=1,connect=lambda *a,**kw:Socket())
    assert result == "RECONCILED_FLAT_ENTRIES_STILL_DISABLED"
    assert w.stream_ids == 1 and len(w.placements()) == 1
    assert l.meta("halt") is not None


def test_recovery_cutoff_does_not_depend_on_market_ticks(rig):
    from live.recovery import RecoveryMonitor
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    w.clock = e.cutoff
    assert RecoveryMonitor(e).step()
    assert w.net == 0 and len(w.placements()) == 2


def test_broker_margin_increase_cannot_use_old_terms(rig):
    w, b, l, e = rig
    w.margin = 500
    with pytest.raises(Blocked, match="MARGIN_TERMS_CHANGED"):
        e.reconcile()
    assert not w.placements()


def test_future_quote_is_not_fresh(rig):
    w, b, l, e = rig
    q = {**quote(w),"time":(w.clock+timedelta(minutes=1)).isoformat()}
    with pytest.raises(Blocked,match="QUOTE"):
        e.submit(entry(w),q)


def test_delayed_demo_mechanics_is_explicit_and_separate_from_timing(rig):
    w, b, l, e = rig
    delayed = {**quote(w),"time":(w.clock-timedelta(minutes=10)).isoformat(),"received_at":w.clock.isoformat()}
    with pytest.raises(Blocked,match="QUOTE"):
        e.submit(entry(w),delayed)
    e.demo_mechanics = True  # dedicated demo harness; runtime never sets this
    e.submit(entry(w),delayed)
    assert len(w.placements())==1


def test_extra_sim_cash_cannot_inflate_personal_risk_or_margin(rig):
    w, b, l, e = rig
    w.cash=100000
    l.set_meta("broker_cash_offset",98000)
    e.reconcile()
    e.submit(entry(w),quote(w))
    assert w.placements()[0][2]["quantity"]==1
