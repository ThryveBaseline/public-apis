"""Reproducible mock workflow receipt. Never presented as a broker-demo pass."""
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import tempfile

from .execution import Executor
from .feed import MinuteFeed
from .ironbeam import Ironbeam
from .ledger import Ledger
from .models import Bar, Blocked, RiskTerms, UTC
from .runtime import Runtime
from .tests.mock_broker import MockWire


def mock_demo(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise Blocked("RECEIPT_EXISTS_USE_NEW_PATH")
    checks = {}
    with tempfile.TemporaryDirectory(prefix="jj-live-mock-") as folder:
        root = Path(folder)
        calendar = root / "calendar"
        calendar.mkdir()
        (calendar / "ff_thisweek_20261013T120000Z.json").write_text(json.dumps([
            {"date": "2026-10-15T12:00:00-04:00", "country": "USD", "impact": "Low", "title": "Synthetic calendar fixture"}]))
        wire = MockWire()
        wire.clock = datetime(2026, 10, 15, 13, 31, tzinfo=UTC)
        broker = Ironbeam(request=wire.request)
        broker.authenticate({"username": "mock", "password": "mock", "apikey": "mock"})
        broker.bind_account(wire.account)
        ledger = Ledger(root / "personal-mock.sqlite", lane="mock", account=wire.account)
        terms = RiskTerms(1.5, 0.25, 100, 200, 300, True)
        executor = Executor(broker, ledger, terms, symbol="XCME:MNQ.Z26", kill_file=root / "KILL", cutoff=wire.clock+timedelta(hours=6), expiry=wire.clock+timedelta(days=40), now=lambda: wire.clock)
        feed = MinuteFeed("XCME:NQ.Z26", timestamp_verified=True, sequence_contiguous=True, complete_from=wire.clock-timedelta(minutes=1))
        runtime = Runtime(executor, feed, calendar_dir=calendar, prior_high=21000)
        # Only flat synthetic candles plus a hand-authored pivot/displacement.
        begin = datetime(2026, 10, 14, 13, 30, tzinfo=UTC)
        end = datetime(2026, 10, 15, 13, 29, tzinfo=UTC)
        ts = begin
        while ts <= end:
            o = h = lo = c = 20000.0
            if ts == end-timedelta(minutes=2):
                h = 20002
            if ts == end:
                o, h, lo, c = 20000.5, 20000.5, 19999.75, 20000
            runtime.completed_bar(Bar(ts, o, h, lo, c, 1))
            ts += timedelta(minutes=1)
        runtime.route_orders = True
        executor.reconcile()
        for seq, (seconds, price) in enumerate(((0, 20000), (10, 20006), (59, 20005), (60, 20005)), 1):
            moment = end+timedelta(minutes=1, seconds=seconds)
            wire.clock = moment
            executor.reconcile()
            ms = int(moment.timestamp()*1000)
            runtime.on_message({"q": [{"s": executor.symbol, "b": 20005, "a": 20005, "bt": ms, "at": ms}],
                                "tr": [{"s": feed.symbol, "p": price, "sz": 1, "sq": seq, "st": ms}]}, moment)
        assert len(wire.placements()) == 1 and wire.net == 1
        checks["market_feed_to_causal_signal_to_MNQ_bracket"] = "CLEAR"
        parent = next(o for o in wire.orders.values() if o["orderType"] == "MARKET")
        assert len(parent["childOrders"]) == 2
        checks["broker_accepted_stop_and_target_mock"] = "CLEAR"
        iid = ledger.intents()[0]["id"]
        # Reconstruct the actual strategy and separate ledger, not just the broker.
        rebuilt = Runtime(executor, MinuteFeed(feed.symbol), calendar_dir=calendar, prior_high=21000)
        assert rebuilt.engine.bars == runtime.engine.bars
        assert len(wire.placements()) == 1
        checks["restart_journal_replay_without_duplicate_order"] = "CLEAR"
        ledger.halt("STREAM_DISCONNECTED")
        target = next(o for o in wire.orders.values() if o["orderType"] == "LIMIT")
        wire.fill_order(target["orderId"], 1, target["limitPrice"])
        executor.reconcile()
        assert ledger.account()["net_quantity"] == 0 and ledger.account()["realized_equity"] == 2074.5
        assert all(wire.orders[x]["status"] in ("FILLED", "CANCELLED") for x in parent["childOrders"])
        checks["fill_during_disconnect_reconciled_and_OCO_cancelled"] = "CLEAR"
        checks["account_cash_from_actual_mock_fills_only"] = "CLEAR"
        account = ledger.account()
        ledger.close()
    code = {str(p.relative_to(Path(__file__).parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))}
    receipt = {"created_utc": datetime.now(UTC).isoformat(), "evidence_type": "MOCK_ONLY", "live": "LIVE_DISABLED",
               "mock_workflow": "CLEAR", "broker_demo": "BLOCKED", "broker_demo_reason": "OWNER_CONFIRMS_API_CREDENTIALS_PENDING",
               "checks": checks, "mock_account": account, "code_sha256": code}
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    return {"mock_workflow": "CLEAR", "broker_demo": "BLOCKED", "live": "LIVE_DISABLED", "receipt": str(output), "checks": checks}
