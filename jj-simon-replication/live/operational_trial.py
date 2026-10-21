"""Accelerated synthetic trading-day exercise, never a profitability backtest."""
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import time

from .execution import Executor, TERMINAL
from .feed import MinuteFeed
from .ironbeam import Ironbeam
from .ledger import Ledger
from .models import Bar, Blocked, Intent, NY, RiskTerms, UTC
from .runtime import Runtime
from .tests.mock_broker import MockWire


def full_day_mock(output):
    output = Path(output)
    if output.exists():
        raise Blocked("RECEIPT_EXISTS_USE_NEW_PATH")
    start_wall = time.monotonic()
    start = datetime(2026, 10, 21, 18, tzinfo=NY).astimezone(UTC)
    end = datetime(2026, 10, 22, 17, tzinfo=NY).astimezone(UTC)
    cutoff = datetime(2026, 10, 22, 16, 10, tzinfo=NY).astimezone(UTC)
    events, peak_risk, ticks = [], 0, 0
    with tempfile.TemporaryDirectory(prefix="jj-operational-day-") as directory:
        root = Path(directory)
        calendar = root / "calendar"
        calendar.mkdir()
        (calendar / "ff_thisweek_20261020T120000Z.json").write_text(json.dumps([
            {"date":"2026-10-22T12:00:00-04:00","country":"USD","impact":"Low","title":"Synthetic fixture"}]))
        w = MockWire()
        w.clock, w.price = start, 20000
        broker = Ironbeam(request=w.request, pacer=w.pacer)
        broker.authenticate({"username":"mock","password":"mock","apikey":"mock"})
        broker.bind_account(w.account)
        ledger = Ledger(root / "personal-mock.sqlite", lane="mock", account=w.account)
        e = Executor(broker,ledger,RiskTerms(1.5,.25,100,200,300,True),symbol="XCME:MNQ.Z26",
                     kill_file=root/"KILL",cutoff=cutoff,expiry=end+timedelta(days=50),now=lambda:w.clock)
        feed = MinuteFeed("XCME:NQ.Z26",timestamp_verified=True,sequence_contiguous=True,complete_from=start)
        runtime = Runtime(e,feed,calendar_dir=calendar,prior_high=21000)
        context = datetime(2026,10,21,9,30,tzinfo=NY).astimezone(UTC)
        while context < datetime(2026,10,21,17,tzinfo=NY).astimezone(UTC):
            runtime.completed_bar(Bar(context,20000,20000,20000,20000,1))
            context += timedelta(minutes=1)
        runtime.route_orders = True

        def enter(name, action="ENTRY"):
            intent = Intent(name,w.clock.isoformat(),action,"OPERATIONAL_FIXTURE","broker_mechanics",1,25,38,
                            20001 if action=="BOOK" else None)
            result = e.submit(intent,runtime.quote)
            events.append({"time":w.clock.astimezone(NY).isoformat(),"event":name,"result":result})
            return result

        def fill_child(name, kind):
            parent = ledger.intent(name)["order_id"]
            child = next(o for o in w.orders.values() if o.get("parentOrderId")==parent and o["orderType"]==kind)
            w.fill_order(child["orderId"],child["quantity"]-child["fillQuantity"],child["stopPrice" if kind=="STOP" else "limitPrice"])
            e.reconcile()
            events.append({"time":w.clock.astimezone(NY).isoformat(),"event":name+"_"+kind,"result":"RECONCILED"})

        moment = start
        while moment <= end:
            w.clock = moment
            ticks += 1
            millis = int(moment.timestamp()*1000)
            message = {"q":[{"s":e.symbol,"b":w.price,"a":w.price,"bt":millis,"at":millis}],
                       "tr":[{"s":feed.symbol,"p":20000,"sz":1,"sq":ticks,"st":millis}]}
            if ticks % 12 == 1:
                e.reconcile()
            runtime.on_message(message,moment)
            local = moment.astimezone(NY)
            minute = local.strftime("%H:%M") if local.second==0 else ""
            if moment < cutoff:
                runtime.watchdog(moment)
                if minute in ("18:05","20:05","14:05","16:09"):
                    assert enter("probe_"+minute)=="ACKNOWLEDGED"
                elif minute=="18:06":
                    fill_child("probe_18:05","STOP")
                elif minute=="20:06":
                    fill_child("probe_20:05","LIMIT")
                elif minute=="22:00":
                    assert enter("overnight_book","BOOK")=="ACKNOWLEDGED"
                elif minute=="00:00":
                    assert ledger.reservations()[0]>0 and w.net==0
                    events.append({"time":local.isoformat(),"event":"midnight_pending_risk_persisted","result":"CLEAR"})
                elif minute=="03:00":
                    parent = w.orders[ledger.intent("overnight_book")["order_id"]]
                    w.fill_order(parent["orderId"],parent["quantity"],20001)
                    e.reconcile()
                elif minute=="03:01":
                    fill_child("overnight_book","LIMIT")
                elif minute=="09:35":
                    assert enter("simultaneous_a")=="ACKNOWLEDGED"
                    assert enter("simultaneous_b")=="ACKNOWLEDGED"
                    assert enter("simultaneous_c")=="SKIPPED"
                elif minute=="09:36":
                    e.flatten("STRATEGY_EXIT",intent_id="simultaneous_a")
                    e.flatten("STRATEGY_EXIT",intent_id="simultaneous_b")
                elif minute=="14:06":
                    fill_child("probe_14:05","LIMIT")
            elif moment==cutoff:
                try:
                    runtime.watchdog(moment)
                except Blocked as error:
                    assert str(error)=="RUNTIME_STOPPED"
                assert w.net==0 and ledger.account()["net_quantity"]==0
                runtime.route_orders = False
                events.append({"time":local.isoformat(),"event":"session_cutoff_confirmed_flat","result":"CLEAR"})
            elif minute=="16:11":
                before = len(w.placements())
                try:
                    enter("after_cutoff_forbidden")
                    raise AssertionError("late entry accepted")
                except Blocked:
                    pass
                assert len(w.placements())==before
            risk, _ = ledger.reservations()
            assert risk <= e.risk_equity()*.06+0.000001
            peak_risk = max(peak_risk,risk)
            moment += timedelta(seconds=5)
        e.reconcile()
        assert all(o["status"] in TERMINAL for o in w.orders.values())
        assert w.net == 0 and ledger.reservations()==(0,0)
        # A flat fixture generates no entry signals. Separate synthetic parity tests
        # and mock-demo prove the causal JJ signal -> bracket path.
        decisions = [json.loads(r[0]) for r in ledger.db.execute("SELECT value FROM audit WHERE kind='STRATEGY_DECISION'")]
        assert not any(d["action"] in ("ENTRY","BOOK") for d in decisions)
        bars = len(runtime.engine.bars)
        ledger.close()
    receipt = {
        "evidence_type":"ACCELERATED_SYNTHETIC_OPERATIONAL_DAY","status":"CLEAR","live":"LIVE_DISABLED",
        "broker_demo":"BLOCKED","broker_demo_reason":"API_CREDENTIALS_PENDING","real_time_signal_timing":"NOT_VALIDATED",
        "wall_clock_broker_trading_day":"NOT_RUN","start_et":start.astimezone(NY).isoformat(),"end_et":end.astimezone(NY).isoformat(),
        "simulated_hours":(end-start).total_seconds()/3600,"actual_elapsed_seconds":round(time.monotonic()-start_wall,3),
        "synthetic_ticks":ticks,"journaled_bars_including_context":bars,"peak_reserved_risk_dollars":peak_risk,
        "final_position":0,"open_orders":0,"separate_ledger_reconciled":True,"events":events,
        "fixture_description":"Flat hand-authored NQ ticks; explicitly marked broker-mechanics intents and injected broker fills. No historical prices or profitability evaluation.",
        "code_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return {k:receipt[k] for k in ("status","evidence_type","simulated_hours","synthetic_ticks","final_position","broker_demo","live")}
