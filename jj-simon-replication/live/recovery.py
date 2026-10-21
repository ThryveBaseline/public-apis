"""Reconnect in protection-monitoring mode; never restore entry authority blindly."""
import time

from .models import Blocked, utc
from .execution import EMERGENCY_EXIT_REASONS


class RecoveryMonitor:
    def __init__(self, executor, *, sleep=time.sleep):
        self.executor, self.sleep = executor, sleep

    def confirmed_flat(self):
        e = self.executor
        active = any(r["status"] not in ("CLOSED", "CANCELLED", "REJECTED", "SKIPPED") for r in e.ledger.intents())
        return not active and e.ledger.account()["net_quantity"] == 0 and e.position_snapshot_confirmed_at is not None

    def step(self):
        e = self.executor
        # Reconcile executions even if the market feed is unavailable. The actual
        # broker snapshots are authoritative; a stream disconnect is not an exit.
        try:
            e.reconcile()
        except Blocked as error:
            e.ledger.audit("RECOVERY_BLOCKED", {"reason": str(error)})
            if self.confirmed_flat():
                return True
            if str(error) in EMERGENCY_EXIT_REASONS:
                # A disconnected stream must not hide a subsequently cancelled
                # stop or a partial exit that leaves unprotected exposure.
                e.flatten("RECOVERY_PROTECTION_FAILURE")
        now = utc(e.now())
        if self.confirmed_flat():
            return True
        if e.kill_file.exists() or now >= e.cutoff:
            e.flatten("RECOVERY_CUTOFF_OR_KILL")
        return self.confirmed_flat()

    def run(self, *, max_connections=None, connect=None):
        e = self.executor
        e.ledger.halt("RECOVERY_MONITOR_ONLY")
        connections = 0
        while max_connections is None or connections < max_connections:
            connections += 1
            try:
                if self.step():
                    return "RECONCILED_FLAT_ENTRIES_STILL_DISABLED"
                # A fresh stream ID on every connection, account events only.
                connection = e.broker.stream([], connect=connect)
                try:
                    for _ in connection:
                        if self.step():
                            return "RECONCILED_FLAT_ENTRIES_STILL_DISABLED"
                finally:
                    connection.close()
            except Blocked as error:
                e.ledger.audit("RECOVERY_RETRY", {"reason": str(error)})
                self.sleep(5)
        raise Blocked("RECOVERY_STILL_BLOCKED")
