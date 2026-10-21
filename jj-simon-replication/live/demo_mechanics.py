"""Small real DEMO broker trial, explicitly independent of signal timing.

Never enables automated JJ routing. This verifies a subset of mechanics, not a
full broker trading day or all failure cases. It may place one simulated MNQ
entry and its close, only after isLive=false and isolated-account checks.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path

from .account_lock import account_lock
from .execution import Executor, TERMINAL
from .ironbeam import Ironbeam, protected_json
from .ledger import Ledger
from .models import Blocked, Intent, RiskTerms, UTC, finite, stable_id, utc


def demo_smoke(path, output, *, broker=None, now=lambda:datetime.now(UTC)):
    config = json.loads(Path(path).read_text())
    if config.get("environment")!="demo" or config.get("mode")!="demo-mechanics":
        raise Blocked("EXPLICIT_DEMO_MECHANICS_CONFIG_REQUIRED")
    output = Path(output)
    if output.exists():
        raise Blocked("RECEIPT_EXISTS_USE_NEW_PATH")
    if config.get("schedule_confirmed") is not True or utc(config["cutoff"]) <= now()+timedelta(minutes=10):
        raise Blocked("BROKER_SESSION_SCHEDULE_UNCONFIRMED")
    terms = RiskTerms(**config["risk_terms"])
    terms.validate()
    allocation = finite(config["starting_cash"],positive=True)
    if allocation > 2000:
        raise Blocked("DEMO_ALLOCATION_LIMIT_2000")
    report = {"evidence_type":"BROKER_DEMO_MECHANICS","status":"BLOCKED","live":"LIVE_DISABLED",
              "scope":"MECHANICS_SMOKE_SUBSET","real_time_signal_timing":"NOT_VALIDATED","full_trading_day":"NOT_RUN","checks":{}}
    state = Path(config["state_directory"]).expanduser()
    state.mkdir(parents=True,exist_ok=True,mode=0o700)
    e, ledger = None, None
    with account_lock("demo",config["account"]):
        try:
            b = broker or Ironbeam("demo")
            if b.environment != "demo":
                raise Blocked("LIVE_DISABLED")
            if broker is None:
                b.authenticate(protected_json(config["credentials_file"]))
            b.bind_account(config["account"])
            report["checks"]["verified_simulated_account"]="CLEAR"
            snapshot = b.snapshot()
            if any(finite(p["quantity"])!=0 for p in snapshot["positions"] if p.get("accountId")==b.account):
                raise Blocked("DEMO_ACCOUNT_MUST_START_FLAT")
            if any(o["status"] not in TERMINAL for o in snapshot["orders"] if o.get("accountId")==b.account):
                raise Blocked("DEMO_ACCOUNT_HAS_WORKING_ORDERS")
            symbol = config["execution_symbol"]
            definitions = b.call("GET","/info/security/definitions",query={"symbols":symbol}).get("securityDefinitions",[])
            matches = [d for d in definitions if d.get("exchSym")==symbol]
            if len(matches)!=1:
                raise Blocked("CONTRACT_DEFINITION_MISSING")
            definition = matches[0]
            if definition.get("allowTrading") is not True or definition.get("currencyCode")!="USD" or finite(definition["minPriceIncrement"])!=.25 or finite(definition["minPriceIncrementValue"])!=.5:
                raise Blocked("MNQ_DEFINITION_NOT_CONFIRMED")
            expiry = datetime.fromtimestamp(finite(definition["expirationTime"])/1000,UTC)
            ledger = Ledger(state/"mechanics.sqlite",lane="demo",account=b.account,starting_cash=allocation)
            if ledger.intents() or ledger.meta("smoke_started"):
                raise Blocked("EXISTING_DEMO_TRIAL_REQUIRES_RECONCILIATION")
            # Pin the starting excess simulated cash once; never recompute after a
            # fill or use an adjustment to make a reconciliation discrepancy pass.
            balances = [r for r in snapshot["balances"] if r.get("accountId")==b.account and r.get("currencyCode")=="USD" and r.get("balanceType")=="CURRENT_OPEN"]
            if len(balances)!=1 or finite(balances[0]["cashBalance"])<allocation:
                raise Blocked("INSUFFICIENT_DEMO_CASH")
            with ledger.transaction():
                ledger.set_meta("smoke_started",utc(now()).isoformat())
                ledger.set_meta("broker_cash_offset",finite(balances[0]["cashBalance"])-allocation)
            e = Executor(b,ledger,terms,symbol=symbol,kill_file=state/"KILL",cutoff=utc(config["cutoff"]),expiry=expiry,now=now,demo_mechanics=True)
            e.reconcile()
            stream = b.stream([symbol])
            quote = None
            try:
                deadline = utc(now())+timedelta(seconds=30)
                for count, message in enumerate(stream):
                    received = utc(now())
                    for q in message.get("q",[]):
                        if q.get("s")==symbol:
                            stamp = datetime.fromtimestamp(min(finite(q["bt"]),finite(q["at"]))/1000,UTC)
                            delay = (received-stamp).total_seconds()
                            expected = finite(config["expected_delay_seconds"])
                            if abs(delay-expected)>10:
                                raise Blocked("UNEXPECTED_DEMO_QUOTE_DELAY")
                            quote={"bid":q["b"],"ask":q["a"],"time":stamp.isoformat(),"received_at":received.isoformat()}
                            report["observed_quote_delay_seconds"]=round(delay,3)
                    if quote:
                        e.reconcile()
                        e.feed_at=received
                        intent=Intent(stable_id(["demo-smoke",received.isoformat()]),received.isoformat(),"ENTRY","DEMO_MECHANICS","not_a_JJ_signal",1,25,38)
                        if e.submit(intent,quote)!="ACKNOWLEDGED" or ledger.account()["net_quantity"]!=1:
                            raise Blocked("DEMO_ENTRY_FILL_NOT_CONFIRMED")
                        report["checks"]["one_MNQ_entry_native_stop_target_reconciled"]="CLEAR"
                        break
                    if received >= deadline or count>=100:
                        raise Blocked("DEMO_QUOTE_MISSING")
            finally:
                stream.close()
            if not quote:
                raise Blocked("DEMO_QUOTE_MISSING")
            ledger.halt("INTENTIONAL_DEMO_STREAM_DISCONNECT")
            e.reconcile()
            second = b.stream([])
            try:
                next(second)
                e.reconcile()
            finally:
                second.close()
            report["checks"]["disconnect_fresh_stream_reconcile"]="CLEAR"
            e.flatten("DEMO_TRIAL_CLEANUP")
            report["checks"]["cancel_confirm_close_flat"]="CLEAR"
            report["status"]="CLEAR"
        except Blocked as error:
            report["reason"]=str(error)
        except Exception:
            report["reason"]="DEMO_TRIAL_UNEXPECTED_FAILURE"
        finally:
            if e is not None and report["status"]=="BLOCKED":
                try:
                    e.flatten("DEMO_TRIAL_FAILURE_CLEANUP")
                    report["cleanup"]="CONFIRMED_FLAT"
                except Exception:
                    report["cleanup"]="UNCONFIRMED_CHECK_BROKER_PORTAL"
            if ledger:
                report["ledger_net_quantity"]=ledger.account()["net_quantity"]
                ledger.close()
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report
