"""Incremental strategy journal and guarded demo routing, never paper-job imports."""
from __future__ import annotations

from datetime import datetime, timedelta
import json

from .feed import calendar_for_day, check_calendar_receipt, scheduled_context_gap
from .models import Bar, Blocked, UTC, finite, trading_day, utc
from .strategy import StreamingJJ
from .execution import EMERGENCY_EXIT_REASONS


class Runtime:
    def __init__(self, executor, feed, *, calendar_dir, prior_high, route_orders=False, calendar_loader=calendar_for_day):
        self.executor, self.ledger, self.feed = executor, executor.ledger, feed
        self.calendar_dir, self.calendar_loader = calendar_dir, calendar_loader
        self.route_orders = route_orders
        self.engine = StreamingJJ(prior_high=prior_high)
        self.quote = None
        self.account_dirty = False
        # Recovery replays only our own recorded minute journal, never emits past orders.
        self.engine.calendar = self.ledger.meta("strategy_calendar", {})
        for row in self.ledger.db.execute("SELECT payload FROM bars ORDER BY time"):
            self.engine.on_bar(Bar.restore(json.loads(row[0])))

    def load_calendar(self, day):
        receipts = self.ledger.meta("calendar_receipts", {})
        if day in receipts:
            check_calendar_receipt(self.calendar_dir, receipts[day])
            return
        events, receipt = self.calendar_loader(self.calendar_dir, day)
        self.engine.calendar[day] = events
        receipts[day] = receipt
        self.ledger.set_meta("calendar_receipts", receipts)
        self.ledger.set_meta("strategy_calendar", self.engine.calendar)

    def completed_bar(self, bar):
        bar.validate()
        day = trading_day(bar.time)
        self.load_calendar(day)
        if self.engine.bars and utc(bar.time) <= utc(self.engine.bars[-1].time):
            # Ledger validates identical duplicates and rejects revised history.
            if not self.ledger.db.execute("SELECT 1 FROM bars WHERE time=?",(bar.record()["time"],)).fetchone():
                raise Blocked("LATE_BAR_REQUIRES_REPLAY")
            self.ledger.bar(bar)
            return []
        if self.engine.bars and utc(bar.time) - utc(self.engine.bars[-1].time) != timedelta(minutes=1):
            # Missing minutes must be explained/backfilled before re-enabling routing.
            # The strategy supports sparse bars; transport completeness is separate.
            if self.route_orders and not scheduled_context_gap(self.engine.bars[-1].time, bar.time):
                raise Blocked("CONTEXT_OR_RECOVERY_GAP")
        # Journal first. Crash here => no stale entry is submitted after restart.
        if not self.ledger.bar(bar):
            return []
        actions = self.engine.on_bar(bar)
        for action in actions:
            self.ledger.audit("STRATEGY_DECISION", {"id": action.id, "action": action.action, "time": action.time, "session": action.session})
            if not self.route_orders:
                continue
            if action.action in ("ENTRY", "BOOK"):
                if not self.feed.qualified:
                    raise Blocked("FEED_SEMANTICS_NOT_QUALIFIED")
                if self.quote is None:
                    raise Blocked("EXECUTION_QUOTE_MISSING")
                self._flush_account_events(utc(self.executor.now()), force=True)
                self.executor.submit(action, self.quote)
            elif action.action == "BREAKEVEN":
                self.executor.breakeven(action.reference)
            elif action.action == "CANCEL_BOOK":
                self.executor.cancel_book()
            elif action.action == "EXIT":
                self.executor.flatten("STRATEGY_EXIT", intent_id=action.reference)
            elif action.action == "FLATTEN":
                self.executor.flatten("STRATEGY_CUTOFF")
        return actions

    def _flush_account_events(self, now, *, force=False):
        last = self.executor.reconciled_at
        if self.account_dirty and (force or not last or utc(now) - last >= timedelta(seconds=2)):
            self.executor.reconcile()
            self.account_dirty = False

    def on_message(self, message, now):
        if "r" in message:
            raise Blocked("BROKER_ACCOUNT_RESET")
        risks = message.get("ria", []) + ([message["ri"]] if "ri" in message else [])
        if any(r.get("a") == self.executor.broker.account and r.get("le") and r["le"][-1] != 12 for r in risks):
            raise Blocked("BROKER_LIQUIDATION_EVENT")
        # st/status in WebSocket frames is never execution truth. Balance frames
        # can arrive on every price change: coalesce those, refresh before entry.
        if any(k in message for k in ("o", "f", "ps", "psa", "b", "ba", "ri", "ria")):
            self.account_dirty = True
            self._flush_account_events(now, force=any(k in message for k in ("o", "f", "ps", "psa", "ri", "ria")))
        for q in message.get("q", []):
            if q.get("s") == self.executor.symbol:
                # Quote bid/ask timestamps are separately checked; receiving an old quote
                # does not make it fresh.
                at = datetime.fromtimestamp(min(finite(q["bt"]), finite(q["at"])) / 1000, UTC)
                self.quote = {"bid": finite(q["b"], positive=True), "ask": finite(q["a"], positive=True), "time": at.isoformat()}
        actions = []
        for trade in message.get("tr", []):
            if trade.get("s") != self.feed.symbol:
                continue
            bars = self.feed.on_trade(trade, now)
            self.executor.feed_at = utc(now)
            for bar in bars:
                actions.extend(self.completed_bar(bar))
        return actions

    def watchdog(self, now):
        if self.executor.kill_file.exists() or utc(now) >= self.executor.cutoff:
            if self.route_orders:
                self.executor.flatten("KILL_SWITCH" if self.executor.kill_file.exists() else "BROKER_CUTOFF")
            raise Blocked("RUNTIME_STOPPED")
        self.feed.watchdog(now)
        self._flush_account_events(now)
        if not self.executor.reconciled_at or utc(now) - self.executor.reconciled_at > timedelta(seconds=10):
            self.executor.reconcile()

    def run_connection(self):
        self.executor.reconcile()
        try:
            for event in self.executor.broker.stream([self.feed.symbol, self.executor.symbol] if self.feed.symbol != self.executor.symbol else [self.feed.symbol]):
                now = datetime.now(UTC)
                self.on_message(event, now)
                self.watchdog(now)
        except Blocked as exc:
            self.ledger.halt(str(exc))
            # Native protection is left at broker during ordinary disconnects.
            # Missing protection attempts a demo emergency exit, never a new entry.
            if self.route_orders and str(exc) in EMERGENCY_EXIT_REASONS:
                self.executor.flatten("PROTECTION_FAILURE")
            raise
        except (KeyboardInterrupt, SystemExit):
            self.ledger.halt("OPERATOR_INTERRUPTED_MONITOR_RECOVERY_REQUIRED")
            raise Blocked("OPERATOR_INTERRUPTED_MONITOR_RECOVERY_REQUIRED") from None
        except Exception:
            self.ledger.halt("UNEXPECTED_RUNTIME_FAILURE")
            raise Blocked("UNEXPECTED_RUNTIME_FAILURE") from None
