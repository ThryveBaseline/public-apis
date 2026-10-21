"""Bounded regressions derived from Ironbeam reports; not broker qualification.

Sources and still-required demo experiments: live/IRONBEAM_API_REVIEW.md.
"""
from datetime import timedelta
from io import BytesIO
from urllib.error import HTTPError

import pytest

from live.execution import Executor
from live.feed import MinuteFeed
from live.ironbeam import RateLimited, http_request
from live.ledger import Ledger
from live.models import Blocked
from live.recovery import RecoveryMonitor
from live.runtime import Runtime
from .test_execution import rig, entry, quote


@pytest.mark.parametrize("leg", ["STOP", "LIMIT"])
def test_successful_child_put_that_removes_a_leg_is_not_success(rig, leg):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    original = b.request
    def request(method, *args):
        response = original(method, *args)
        if method == "PUT":
            next(o for o in w.orders.values() if o["orderType"] == leg)["status"] = "CANCELLED"
        return response
    b.request = request
    with pytest.raises(Blocked, match="MISSING_OR_WRONG_PROTECTION"):
        e.breakeven("one")
    assert l.meta("halt") and len([c for c in w.calls if c[0] == "PUT"]) == 1
    assert RecoveryMonitor(e).step()
    assert w.net == 0 and len(w.placements()) == 2


@pytest.mark.parametrize("accepted", [False, True])
def test_uncertain_child_amendment_survives_restart_without_a_second_put(rig, tmp_path, accepted):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    original = b.request
    put_attempts = []
    def request(method, *args):
        if method == "PUT":
            put_attempts.append(True)
            if accepted:
                original(method, *args)
            raise Blocked("TRANSPORT_UNCERTAIN")
        return original(method, *args)
    b.request = request
    with pytest.raises(Blocked, match="CHILD_AMENDMENT_UNCERTAIN"):
        e.breakeven("one")
    assert "one" in l.meta("pending_child_amendments")
    l.close()
    restored = Ledger(tmp_path / "mock.sqlite", lane="mock", account=w.account)
    try:
        restarted = Executor(b, restored, e.terms, symbol=e.symbol, kill_file=e.kill_file,
                             cutoff=e.cutoff, expiry=e.expiry, now=e.now)
        if accepted:
            restarted.reconcile()
            restarted.breakeven("one")
            assert restored.intent("one")["stop"] == w.price
            assert not restored.meta("pending_child_amendments")
        else:
            with pytest.raises(Blocked, match="CHILD_AMENDMENT_UNCONFIRMED_NO_RETRY"):
                restarted.reconcile()
            with pytest.raises(Blocked, match="CHILD_AMENDMENT_UNCONFIRMED_NO_RETRY"):
                restarted.breakeven("one")
        assert restored.meta("halt") and put_attempts == [True]
        assert w.net == 1 and len(w.placements()) == 1
    finally:
        restored.close()


def test_missing_stop_precedes_cash_lag_and_alignment_attempt(rig):
    w, b, l, e = rig
    original = b.request
    def request(method, url, *args):
        response = original(method, url, *args)
        if url.endswith("/place"):
            next(o for o in w.orders.values() if o["orderType"] == "STOP")["status"] = "REJECTED"
            w.cash += 1  # asynchronous fee/balance posting must not hide lost stop
        return response
    b.request = request
    q = quote(w)
    w.price += .25  # alignment would previously have run before checking children
    with pytest.raises(Blocked, match="MISSING_OR_WRONG_PROTECTION"):
        e.submit(entry(w), q)
    assert not [c for c in w.calls if c[0] == "PUT"]
    b.request = original
    with pytest.raises(Blocked, match="CASH_OR_FEES"):
        RecoveryMonitor(e).step()
    assert w.net == 0 and len(w.placements()) == 2
    assert e.position_snapshot_confirmed_at is None


def test_partial_entry_after_stop_move_still_requires_recovery_when_halted(rig):
    w, b, l, e = rig
    w.partial = 1
    e.submit(entry(w, stop=12.5), quote(w))
    e.breakeven("one")
    w.fill_order(l.intent("one")["order_id"], 1, w.price + .25)
    l.halt("STREAM_DISCONNECTED")
    w.partial = None
    assert RecoveryMonitor(e).step()
    assert w.net == 0 and l.account()["net_quantity"] == 0
    assert len(w.placements()) == 2


def test_all_rest_requests_are_paced_and_429_blocks_without_retry(rig):
    w, b, l, e = rig
    original = b.request
    sent = []
    def request(method, url, *args):
        sent.append(w.request_clock)
        if url.endswith("/limited"):
            raise RateLimited("75")
        return original(method, url, *args)
    b.request = request
    for _ in range(3):
        e.reconcile()
    with pytest.raises(RateLimited):
        b.call("GET", "/limited")
    assert all(right - left >= .25 for left, right in zip(sent, sent[1:]))
    count = len(sent)
    for method, path in [("GET", "/info/trader"), ("PUT", f"/order/{w.account}/update/1"),
                         ("POST", f"/order/{w.account}/place"), ("DELETE", f"/order/{w.account}/cancel/1")]:
        with pytest.raises(Blocked, match="RATE_LIMIT_COOLDOWN"):
            b.call(method, path)
    w.advance_requests(74)
    with pytest.raises(Blocked, match="RATE_LIMIT_COOLDOWN"):
        b.snapshot()
    assert len(sent) == count
    w.advance_requests(1)
    b.snapshot()  # reads recover; no queued mutation exists
    assert not w.placements()


def test_http_429_honors_retry_after_without_exposing_broker_text(monkeypatch):
    class Opener:
        def open(self, *args, **kwargs):
            raise HTTPError("https://demo.ironbeamapi.com/v2/private", 429, "PRIVATE",
                            {"Retry-After": "90"}, BytesIO(b"PRIVATE"))
    monkeypatch.setattr("live.ironbeam.build_opener", lambda *args: Opener())
    with pytest.raises(RateLimited) as error:
        http_request("GET", "https://demo.ironbeamapi.com/v2/private", {}, None, 15)
    assert error.value.retry_after == 90 and str(error.value) == "HTTP_429"
    assert RateLimited().retry_after == 30
    assert RateLimited("nan").retry_after == 30


def test_pacing_cannot_transmit_an_entry_after_cutoff(rig):
    w, b, l, e = rig
    e.cutoff = w.clock + timedelta(seconds=.1)
    def sleep(seconds):
        w.advance_requests(seconds)
        w.clock += timedelta(seconds=seconds)
    b.pacer.sleep = sleep
    with pytest.raises(Blocked, match="SUBMISSION_UNKNOWN_NO_RETRY"):
        e.submit(entry(w), quote(w))
    assert not w.placements() and l.meta("halt")


def test_balance_storm_is_coalesced_and_stale_ws_new_cannot_override_rest(rig, tmp_path):
    w, b, l, e = rig
    e.submit(entry(w), quote(w))
    runtime = Runtime(e, MinuteFeed("XCME:NQ.Z26"), calendar_dir=tmp_path, prior_high=21000)
    before = len(w.calls)
    for _ in range(100):
        runtime.on_message({"b": {"a": w.account}}, w.clock)
    assert len(w.calls) == before and runtime.account_dirty
    # Even before the coalescing interval, entry routing must flush dirty state.
    runtime._flush_account_events(w.clock, force=True)
    assert len(w.calls) == before + 5 and not runtime.account_dirty
    target = next(o for o in w.orders.values() if o["orderType"] == "LIMIT")
    w.fill_order(target["orderId"], 1, target["limitPrice"])
    runtime.on_message({"o": {"a": w.account, "id": target["orderId"], "st": 0}}, w.clock)
    assert l.account()["net_quantity"] == 0 and l.intent("one")["status"] == "CLOSED"
    assert len(w.placements()) == 1
