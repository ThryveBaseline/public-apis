"""One guarded foreground session; deployment must not auto-restart order authority."""
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path

from .execution import Executor
from .feed import MinuteFeed
from .ironbeam import Ironbeam, protected_json
from .ledger import Ledger
from .models import Bar, Blocked, RiskTerms, UTC, finite, trading_day, utc
from .models import stable_id
from .runtime import Runtime
from .recovery import RecoveryMonitor
from .probe import probe
from .account_lock import account_lock


def recover_config(path, *, broker=None, now=lambda:datetime.now(UTC), monitor_factory=RecoveryMonitor):
    """Recover an EXISTING demo ledger even after its session/cutoff has passed.

    No feed, strategy, warmup, parity flag or current-day requirement can prevent
    monitoring old exposure. This path has no mechanism to restore entry routing.
    """
    config = json.loads(Path(path).read_text())
    if config.get("environment") != "demo" or config.get("mode") not in ("demo", "demo-mechanics"):
        raise Blocked("DEMO_RECOVERY_ONLY")
    state = Path(config["state_directory"]).expanduser()
    database = state / ("mechanics.sqlite" if config["mode"]=="demo-mechanics" else "demo.sqlite")
    if not database.is_file():
        raise Blocked("EXISTING_RECOVERY_LEDGER_REQUIRED")
    terms=RiskTerms(**config["risk_terms"])
    terms.validate()
    with account_lock("demo", config["account"]):
        b=broker or Ironbeam("demo")
        if b.environment != "demo":
            raise Blocked("LIVE_DISABLED")
        if broker is None:
            b.authenticate(protected_json(config["credentials_file"]))
        b.bind_account(config["account"])
        definitions=b.call("GET","/info/security/definitions",query={"symbols":config["execution_symbol"]}).get("securityDefinitions",[])
        matching=[d for d in definitions if d.get("exchSym")==config["execution_symbol"]]
        if len(matching)!=1:
            raise Blocked("RECOVERY_INSTRUMENT_UNCONFIRMED")
        expiry=datetime.fromtimestamp(finite(matching[0]["expirationTime"])/1000,UTC)
        ledger=Ledger(database,lane="demo",account=config["account"],starting_cash=config["starting_cash"])
        try:
            ledger.halt("RECOVERY_MONITOR_ONLY")
            executor=Executor(b,ledger,terms,symbol=config["execution_symbol"],kill_file=state/"KILL",cutoff=utc(config["cutoff"]),expiry=expiry,now=now)
            outcome=monitor_factory(executor).run()
            return {"status":"CLEAR","scope":"RECOVERY_CONFIRMED_FLAT","reason":outcome,"live":"LIVE_DISABLED"}
        finally:
            ledger.close()


def run_config(path):
    config = json.loads(Path(path).read_text())
    if config.get("mode") not in ("demo", "dry-run"):
        raise Blocked("LIVE_DISABLED")
    # Explicit contract mapping: NQ signal source, same-expiry MNQ execution.
    signal, execution = config["signal_symbol"], config["execution_symbol"]
    if not signal.startswith("XCME:NQ.") or not execution.startswith("XCME:MNQ.") or signal.split(".")[-1] != execution.split(".")[-1]:
        raise Blocked("NQ_MNQ_CONTRACT_MAPPING_REQUIRED")
    now = datetime.now(UTC)
    if config["trading_day"] != trading_day(now) or utc(config["cutoff"]) <= now:
        raise Blocked("CURRENT_BROKER_SESSION_SCHEDULE_REQUIRED")
    if config.get("schedule_confirmed") is not True:
        raise Blocked("BROKER_CUTOFF_AND_HOLIDAY_SCHEDULE_UNCONFIRMED")
    if not config.get("prior_high"):
        raise Blocked("PRIOR_ALL_TIME_HIGH_REQUIRED")
    route = config["mode"] == "demo"
    if route and not all(config.get(k) is True for k in ("timestamp_verified", "sequence_contiguous", "demo_brackets_qualified", "parity_qualified")):
        raise Blocked("DEMO_ROUTING_QUALIFICATION_REQUIRED")
    terms = RiskTerms(**config["risk_terms"])
    if route:
        terms.validate()
    state_dir = Path(config["state_directory"]).expanduser()
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    # One process for this account, including separate demo/dry-run files.
    locks = Path.home() / ".local/share/jj-live/locks"
    locks.mkdir(parents=True, exist_ok=True, mode=0o700)
    environment = "demo" if route else config.get("environment", "demo")
    lock_path = locks / (stable_id([environment, config["account"]]) + ".lock")
    lock = open(lock_path, "a")
    os.chmod(lock_path, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        raise Blocked("ANOTHER_RUNTIME_OWNS_ACCOUNT") from None
    ledger = None
    try:
        broker = Ironbeam("demo" if route else config.get("environment", "demo"))
        instrument_report = probe(broker, protected_json(config["credentials_file"]), account=config["account"], symbols=[signal,execution])
        if any(not item["trading_allowed"] for item in instrument_report["instruments"]):
            raise Blocked("BROKER_CONTRACT_NOT_TRADABLE")
        if any(utc(item["expiry"]) != utc(config["expiry"]) for item in instrument_report["instruments"]):
            raise Blocked("CONFIGURED_CONTRACT_EXPIRY_MISMATCH")
        ledger = Ledger(state_dir / f'{config["mode"]}.sqlite', lane=config["mode"], account=config["account"], starting_cash=config["starting_cash"])
        executor = Executor(broker, ledger, terms, symbol=execution, kill_file=state_dir / "KILL", cutoff=utc(config["cutoff"]), expiry=utc(config["expiry"]), now=lambda: datetime.now(UTC))
        feed = MinuteFeed(signal, expected_delay_seconds=config.get("expected_delay_seconds", 0), timestamp_verified=config.get("timestamp_verified", False), sequence_contiguous=config.get("sequence_contiguous", False))
        runtime = Runtime(executor, feed, calendar_dir=config["calendar_directory"], prior_high=finite(config["prior_high"], positive=True), route_orders=route)
        if not runtime.engine.bars:
            # Only explicit recent context is loaded. No completed-day scores or historical study.
            seed = Path(config["context_file"])
            if hashlib.sha256(seed.read_bytes()).hexdigest() != config["context_sha256"]:
                raise Blocked("CONTEXT_HASH_MISMATCH")
            for line in seed.read_text().splitlines():
                bar = Bar.restore(json.loads(line))
                bar.validate()
                if utc(bar.time) >= now:
                    raise Blocked("CONTEXT_CONTAINS_FUTURE_BAR")
                runtime.load_calendar(trading_day(bar.time))
                ledger.bar(bar)
                runtime.engine.on_bar(bar)
        if not runtime.engine.active or not runtime.engine.bars:
            raise Blocked("PREVIOUS_0930_CONTEXT_REQUIRED")
        try:
            runtime.run_connection()
        except Blocked:
            if route:
                outcome = RecoveryMonitor(executor).run()
                return {"status": "BLOCKED", "reason": outcome, "live": "LIVE_DISABLED"}
            raise
        return {"status": "CLEAR", "live": "LIVE_DISABLED"}
    finally:
        if ledger:
            ledger.close()
        lock.close()
