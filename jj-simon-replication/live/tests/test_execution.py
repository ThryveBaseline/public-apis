from dataclasses import replace
from datetime import timedelta
import json
import pytest

from live.execution import Executor
from live.ironbeam import Ironbeam, protected_json
from live.ledger import Ledger
from live.models import Blocked, Intent, RiskTerms
from .mock_broker import MockWire


@pytest.fixture
def rig(tmp_path):
    wire = MockWire()
    broker = Ironbeam(request=wire.request, pacer=wire.pacer)
    broker.authenticate({"username": "mock", "password": "mock", "apikey": "mock"})
    broker.bind_account(wire.account)
    ledger = Ledger(tmp_path / "mock.sqlite", lane="mock", account=wire.account)
    terms = RiskTerms(1.5, 0.25, 100, 200, 300, confirmed=True)
    executor = Executor(broker, ledger, terms, symbol="XCME:MNQ.Z26", kill_file=tmp_path / "KILL", cutoff=wire.clock + timedelta(hours=5), expiry=wire.clock + timedelta(days=30), now=lambda: wire.clock)
    executor.feed_at = wire.clock
    executor.reconcile()
    yield wire, broker, ledger, executor
    ledger.close()


def entry(wire, name="one", stop=25, direction=1, action="ENTRY", level=None):
    return Intent(name, wire.clock.isoformat(), action, "09:30", "continuation", direction, stop, 38 if stop == 25 else 19, level, "A+")


def quote(wire):
    return {"bid": wire.price, "ask": wire.price, "time": wire.clock.isoformat()}


def test_market_bracket_target_oco_actual_cash(rig):
    w, b, l, e = rig
    assert e.submit(entry(w), quote(w)) == "ACKNOWLEDGED"
    assert w.placements()[0][2]["quantity"] == 1
    assert l.account()["net_quantity"] == 1
    parent = w.orders[l.intent("one")["order_id"]]
    assert len(parent["childOrders"]) == 2
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    e.reconcile()
    assert l.account()["net_quantity"] == 0
    assert l.account()["realized_equity"] == 2074.5
    assert l.intent("one")["status"] == "CLOSED"
    assert l.reservations() == (0, 0)


def test_wide_stop_rejected_and_combined_risk_enforced(rig):
    w, b, l, e = rig
    assert e.submit(entry(w, "wide", 50), quote(w)) == "SKIPPED"
    assert not w.placements()
    assert e.submit(entry(w), quote(w)) == "ACKNOWLEDGED"
    assert e.submit(entry(w, "two"), quote(w)) == "ACKNOWLEDGED"
    assert e.submit(entry(w, "three"), quote(w)) == "SKIPPED"
    assert len(w.placements()) == 2
    assert l.reservations()[0] <= l.account()["realized_equity"] * 0.06


def test_partial_fill_stop_quantity_and_duplicate_snapshot(rig):
    w, b, l, e = rig
    w.partial = 1
    e.submit(entry(w, stop=12.5), quote(w))
    row = l.intent("one")
    assert row["quantity"] == 2 and l.account()["net_quantity"] == 1
    for child in w.orders[row["order_id"]]["childOrders"]:
        assert w.orders[child]["quantity"] == 1
    first = l.account()
    e.reconcile()
    assert l.account() == first
    w.fill_order(row["order_id"], 1, w.price)
    e.reconcile()
    assert l.account()["net_quantity"] == 2


def test_unknown_timeout_is_never_retried_after_restart(rig, tmp_path):
    w, b, l, e = rig
    w.timeout_after_accept = True
    with pytest.raises(Blocked, match="SUBMISSION_UNKNOWN"):
        e.submit(entry(w), quote(w))
    assert l.intent("one")["status"] == "UNKNOWN"
    assert e.submit(entry(w), quote(w)) == "DUPLICATE"
    with pytest.raises(Blocked):
        e.reconcile()
    assert len(w.placements()) == 1


def test_missing_stop_halts_and_emergency_flatten(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    stop["status"] = "REJECTED"
    with pytest.raises(Blocked, match="PROTECTION"):
        e.reconcile()
    assert l.meta("halt")
    e.flatten("PROTECTION_FAILURE")
    assert w.net == 0 and l.account()["net_quantity"] == 0


def test_breakeven_preserves_target_and_reconciles(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    target = l.intent("one")["target"]
    w.price += 10
    e.breakeven("one")
    assert l.intent("one")["stop"] == 20005
    assert l.intent("one")["target"] == target
    updates = [c for c in w.calls if c[0] == "PUT"]
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    assert updates == [("PUT", f"/order/{w.account}/update/{stop['orderId']}",
                        {"orderId": stop["orderId"], "quantity": 1, "stopPrice": 20005})]


def test_disconnect_recovery_protection_and_no_duplicate(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    l.halt("STREAM_DISCONNECTED")
    restarted = Executor(b, l, e.terms, symbol=e.symbol, kill_file=e.kill_file, cutoff=e.cutoff, expiry=e.expiry, now=e.now)
    restarted.reconcile()
    assert restarted.submit(entry(w), quote(w)) == "DUPLICATE"
    with pytest.raises(Blocked):
        restarted.submit(entry(w, "second"), quote(w))
    assert len(w.placements()) == 1 and w.net == 1


def test_stop_fills_while_disconnected(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    stop = next(o for o in w.orders.values() if o["orderType"] == "STOP")
    w.fill_order(stop["orderId"], 1, stop["stopPrice"] - 0.25)
    e.reconcile()
    assert l.account()["realized_equity"] == 1948.0
    assert l.account()["net_quantity"] == 0


@pytest.mark.parametrize("case", ["stale", "kill", "cutoff", "expiry", "margin", "drawdown"])
def test_entry_guards(rig, case):
    w, b, l, e = rig
    if case == "stale":
        e.feed_at -= timedelta(seconds=10)
    elif case == "kill":
        e.kill_file.touch()
    elif case == "cutoff":
        e.cutoff = w.clock
    elif case == "expiry":
        e.expiry = w.clock
    elif case == "margin":
        e.balance["cashBalanceAvailable"] = 10
    else:
        e.balance["cashBalance"] = 1500
    if case == "margin":
        assert e.submit(entry(w), quote(w)) == "SKIPPED"
    else:
        with pytest.raises(Blocked):
            e.submit(entry(w), quote(w))
    assert not w.placements()


def test_pending_stop_orders_reserve_risk_before_fill_and_cancel(rig):
    w, b, l, e = rig
    e.submit(entry(w, action="BOOK", level=w.price + 1), quote(w))
    assert w.net == 0 and l.reservations()[0] > 0
    e.cancel_book()
    assert l.reservations() == (0, 0)


def test_flatten_uncertainty_cannot_send_second_exit(rig):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    w.timeout_after_accept = True
    with pytest.raises(Blocked, match="FLATTEN_UNKNOWN"):
        e.flatten("CUTOFF")
    with pytest.raises(Blocked, match="FLATTEN_UNKNOWN"):
        e.flatten("CUTOFF")
    assert len(w.placements()) == 2


def test_every_production_order_path_blocked(rig):
    w, b, l, e = rig
    prod = Ironbeam("live-readonly", request=w.request, pacer=w.pacer)
    prod.authenticate({"username": "mock", "password": "mock", "apikey": "mock"})
    prod.bind_account(w.account)
    before = len(w.calls)
    for call in (lambda: prod.place({}), lambda: prod.update("1", {}), lambda: prod.cancel("1")):
        with pytest.raises(Blocked, match="LIVE_DISABLED"):
            call()
    assert len(w.calls) == before
    with pytest.raises(Blocked, match="LIVE_DISABLED"):
        Ironbeam("live")


def test_live_account_on_demo_host_blocked(rig):
    w, b, l, e = rig
    w.is_live = True
    with pytest.raises(Blocked, match="DEMO_ACCOUNT"):
        b.bind_account(w.account)


def test_secrets_require_private_file_and_never_in_repr(tmp_path):
    p = tmp_path / "credentials.json"
    p.write_text(json.dumps({"username": "u", "password": "SENSITIVE", "apikey": "KEY"}))
    p.chmod(0o644)
    with pytest.raises(Blocked, match="OWNER_ONLY"):
        protected_json(p)
    p.chmod(0o600)
    assert protected_json(p)["apikey"] == "KEY"
    b = Ironbeam()
    b._token = "SENSITIVE"
    assert "SENSITIVE" not in repr(b)


def test_new_stream_id_after_each_disconnect(rig):
    w, b, l, e = rig
    class Socket:
        def recv(self):
            return ""
        def close(self):
            pass
    for _ in range(2):
        with pytest.raises(Blocked, match="DISCONNECTED"):
            list(b.stream([e.symbol], connect=lambda *a, **kw: Socket()))
    assert w.stream_ids == 2


def test_ledger_lane_and_account_are_locked(rig, tmp_path):
    w, b, l, e = rig
    with pytest.raises(Blocked, match="MISMATCH"):
        Ledger(tmp_path / "mock.sqlite", lane="demo", account=w.account)
