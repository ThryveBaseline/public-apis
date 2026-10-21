from __future__ import annotations

from datetime import datetime, timedelta
import json
import math
from pathlib import Path
import re

from .models import Blocked, Intent, finite, stable_id, utc

WORKING = {"NEW", "PARTIALLY_FILLED"}
TERMINAL = {"FILLED", "CANCELLED", "REJECTED", "EXPIRED", "DONE_FOR_DAY", "COMPLETE"}
EMERGENCY_EXIT_REASONS = {
    "MISSING_OR_WRONG_PROTECTION", "FILL_EXCEEDS_RESERVED_RISK", "OPEN_RISK_EXCEEDED",
    "ENTRY_SLIPPAGE_ALLOWANCE_EXCEEDED", "PARTIAL_ENTRY_CHANGED_AFTER_BREAKEVEN",
    "BROKER_MARGIN_TERMS_CHANGED", "DRAWDOWN_LIMIT", "BROKER_AVAILABLE_MARGIN_EXHAUSTED",
}


class Executor:
    def __init__(self, broker, ledger, terms, *, symbol, kill_file, cutoff, expiry, now, demo_mechanics=False):
        if not re.fullmatch(r"XCME:MNQ\.[HMUZ]\d{2}", symbol):
            raise Blocked("EXPLICIT_MNQ_EXPIRY_REQUIRED")
        self.broker, self.ledger, self.terms = broker, ledger, terms
        self.symbol, self.kill_file, self.cutoff, self.expiry = symbol, Path(kill_file), utc(cutoff), utc(expiry)
        self.now = now
        if demo_mechanics and broker.environment != "demo":
            raise Blocked("LIVE_DISABLED")
        self.demo_mechanics = demo_mechanics
        self.reconciled_at = None
        self.position_snapshot_confirmed_at = None
        self.balance = None
        self.orders = {}
        self.feed_at = None

    def _halt(self, reason):
        self.ledger.halt(reason)
        raise Blocked(reason)

    def risk_equity(self):
        # Open losses reduce risk capacity immediately; open gains do not enlarge
        # it. A larger simulated account must not enlarge the allocated lane.
        offset = self.ledger.meta("broker_cash_offset", 0)
        return min(self.ledger.account()["realized_equity"],
                   *(finite(self.balance[key]) - offset for key in ("cashBalance", "totalEquity", "netLiquidity")))

    def ready(self):
        now = utc(self.now())
        if self.kill_file.exists():
            self._halt("KILL_SWITCH")
        if now >= self.cutoff:
            self._halt("CUTOFF_REACHED")
        if now >= self.expiry:
            self._halt("CONTRACT_ROLL_REQUIRED")
        if not self.reconciled_at or now - self.reconciled_at > timedelta(seconds=15):
            self._halt("STALE_RECONCILIATION")
        if not self.feed_at or now - self.feed_at > timedelta(seconds=5) or self.feed_at > now + timedelta(seconds=1):
            self._halt("STALE_FEED")
        if self.ledger.meta("halt"):
            raise Blocked("ACCOUNT_HALTED")
        if self.broker.environment != "demo" or not self.broker.account_verified:
            raise Blocked("LIVE_DISABLED")
        self.terms.validate()

    def submit(self, intent, quote):
        if self.ledger.intent(intent.id):
            return "DUPLICATE"
        self.ready()
        if intent.direction not in (-1, 1) or intent.action not in ("ENTRY", "BOOK"):
            raise Blocked("INVALID_ENTRY_INTENT")
        now = utc(self.now())
        if now - utc(intent.time) > timedelta(seconds=5) or utc(intent.time) > now + timedelta(seconds=1):
            raise Blocked("STALE_SIGNAL")
        bid, ask = finite(quote["bid"], positive=True), finite(quote["ask"], positive=True)
        # Delayed demo mechanics have a distinct, explicitly marked path. A fresh
        # receipt of delayed prices never qualifies real-time strategy timing.
        quote_clock = utc(quote["received_at"]) if self.demo_mechanics else utc(quote["time"])
        if bid > ask or now - quote_clock > timedelta(seconds=5) or quote_clock > now + timedelta(seconds=1):
            raise Blocked("INVALID_EXECUTION_QUOTE")
        # Absolute prices retained pending demo qualification of conflicting offset docs.
        reference = intent.level if intent.action == "BOOK" else (ask if intent.direction > 0 else bid)
        for value in (reference, intent.stop_points, intent.target_points):
            if finite(value, positive=True) * 4 != round(value * 4):
                raise Blocked("OFF_TICK_PRICE")
        if intent.action == "BOOK" and (reference - (ask if intent.direction > 0 else bid)) * intent.direction <= 0:
            raise Blocked("BOOK_LEVEL_ALREADY_CROSSED")
        equity = self.risk_equity()
        if self.ledger.identity["starting_cash"] - equity >= self.terms.max_drawdown_dollars:
            self._halt("DRAWDOWN_LIMIT")
        available = min(equity, finite(self.balance["cashBalanceAvailable"]), finite(self.balance["netLiquidityAvailable"]))
        row = self.ledger.reserve(intent, self.terms, equity, available, reference)
        if row is None:
            return "DUPLICATE"
        if not row["quantity"]:
            return "SKIPPED"
        body = {"exchSym": self.symbol, "side": "BUY" if intent.direction > 0 else "SELL", "quantity": row["quantity"],
                "orderType": "STOP" if intent.action == "BOOK" else "MARKET", "duration": "1",
                "stopLoss": row["stop"], "takeProfit": row["target"]}
        if intent.action == "BOOK":
            body["stopPrice"] = reference
        def before_send():
            # Ordinary pacing must not let a signal/quote expire or cross cutoff
            # between validation and transmission. A blocked reservation is kept.
            self.ready()
            if utc(self.now()) > min(utc(intent.time), quote_clock) + timedelta(seconds=5):
                raise Blocked("ENTRY_EXPIRED_BEFORE_TRANSMISSION")
        try:
            response = self.broker.place(body, before_send=before_send)
            self.ledger.acknowledge(intent.id, response.get("orderId"))
        except Exception:
            self.ledger.unknown(intent.id)
            raise Blocked("SUBMISSION_UNKNOWN_NO_RETRY") from None
        # Acceptance is not a fill and not proof of protection.
        self.reconcile()
        return "ACKNOWLEDGED"

    def reconcile(self, *, align_brackets=True):
        self.reconciled_at = None
        self.position_snapshot_confirmed_at = None
        try:
            snap = self.broker.snapshot()
            self._reconcile(snap, align_brackets=align_brackets)
        except Blocked as exc:
            self.reconciled_at = None
            self.ledger.halt(str(exc))
            raise
        except Exception:
            self._halt("RECONCILIATION_FAILED")
        self.reconciled_at = utc(self.now())
        return snap

    def _protective_children(self, row, parent, exposure, children):
        side = "SELL" if exposure > 0 else "BUY"
        protective = [o for o in children if o.get("status") in WORKING and o.get("side") == side and
                      o.get("exchSym") == self.symbol and o.get("duration") == "1" and
                      finite(o["quantity"]) - finite(o.get("fillQuantity", 0)) == abs(exposure)]
        stops = [o for o in protective if o.get("orderType") == "STOP" and abs(finite(o.get("stopPrice", 0)) - row["stop"]) < 0.001]
        targets = [o for o in protective if o.get("orderType") == "LIMIT" and abs(finite(o.get("limitPrice", 0)) - row["target"]) < 0.001]
        working = {o["orderId"] for o in children if o.get("status") not in TERMINAL}
        if len(stops) != 1 or len(targets) != 1 or working != {stops[0]["orderId"], targets[0]["orderId"]} or set(parent.get("childOrders", [])) != working:
            raise Blocked("MISSING_OR_WRONG_PROTECTION")
        return {"stop": stops[0], "target": targets[0]}

    def _resolve_amendment(self, row, parent, exposure, children):
        pending = self.ledger.meta("pending_child_amendments", {})
        change = pending.get(row["id"])
        if not change:
            return row
        proposed = {**dict(row), change["field"]: change["price"]}
        try:
            accepted = self._protective_children(proposed, parent, exposure, children)
        except Blocked:
            # An intact OLD bracket still does not authorize repeating an uncertain
            # PUT. A missing leg takes priority and invokes emergency recovery.
            self._protective_children(row, parent, exposure, children)
            raise Blocked("CHILD_AMENDMENT_UNCONFIRMED_NO_RETRY") from None
        if accepted[change["field"]]["orderId"] != change["order_id"]:
            raise Blocked("MISSING_OR_WRONG_PROTECTION")
        self.ledger.db.execute("UPDATE intents SET stop=?,target=? WHERE id=?", (proposed["stop"], proposed["target"], row["id"]))
        pending.pop(row["id"])
        self.ledger.set_meta("pending_child_amendments", pending)
        return proposed

    def _amend_child(self, iid, field, price):
        row = self.ledger.intent(iid)
        exposure = self.ledger.net_for_intent(iid)
        if not exposure:
            return
        parent = self.orders[row["order_id"]]
        children = [o for o in self.orders.values() if str(o.get("parentOrderId", "")) == row["order_id"]]
        child = self._protective_children(row, parent, exposure, children)[field]
        pending = self.ledger.meta("pending_child_amendments", {})
        if iid in pending:
            self._halt("CHILD_AMENDMENT_UNCONFIRMED_NO_RETRY")
        # Persist BEFORE the request: process death must not cause a repeated PUT.
        pending[iid] = {"field": field, "price": price, "order_id": child["orderId"]}
        self.ledger.set_meta("pending_child_amendments", pending)
        try:
            # Ironbeam staff instruct using the CHILD orderId. Parent bracket
            # changes have reported cancellation/execution side effects.
            self.broker.update(child["orderId"], {"quantity": child["quantity"],
                               "stopPrice" if field == "stop" else "limitPrice": price})
        except Exception:
            self._halt("CHILD_AMENDMENT_UNCERTAIN")
        # Check both legs, fills and exposure after EACH change, before another PUT.
        self.reconcile(align_brackets=False)

    def _reconcile(self, snap, *, align_brackets=True):
        self.position_snapshot_confirmed_at = None
        account = self.broker.account
        balances = [b for b in snap["balances"] if b.get("accountId") == account and b.get("currencyCode") == "USD" and b.get("balanceType") == "CURRENT_OPEN"]
        if len(balances) != 1:
            raise Blocked("USD_BALANCE_MISSING")
        self.balance = balances[0]
        for key in ("cashBalance", "cashBalanceAvailable", "netLiquidityAvailable", "totalEquity", "netLiquidity"):
            finite(self.balance[key])
        self.orders = {str(o["orderId"]): o for o in snap["orders"] if o.get("accountId") == account}
        known = {r["order_id"]: r["id"] for r in self.ledger.intents() if r["order_id"]}
        # Flatten orders are separately journaled and must survive a restart.
        known.update(self.ledger.meta("exit_orders", {}))
        for oid, order in self.orders.items():
            parent = str(order.get("parentOrderId", ""))
            if parent in known:
                known[oid] = known[parent]
        for oid, iid in known.items():
            if oid in self.orders:
                self.ledger.order(self.orders[oid], iid)
        # Stable chronological replay deduplicates snapshots after reconnect.
        for fill in sorted(snap["fills"], key=lambda f: (f.get("fillDate", ""), str(f.get("orderUpdateId", "")))):
            oid = str(fill.get("orderId", ""))
            if fill.get("accountId") == account and oid in known:
                if fill.get("exchSym") != self.symbol:
                    raise Blocked("FILL_SYMBOL_MISMATCH")
                self.ledger.fill(fill, known[oid], self.terms.fee_round_trip / 2)
        for oid, order in self.orders.items():
            if oid not in known and order.get("status") not in TERMINAL:
                raise Blocked("UNEXPECTED_BROKER_ORDER")
        net = 0
        position_sides = set()
        for position in snap["positions"]:
            if position.get("accountId") != account:
                continue
            qty = finite(position["quantity"])
            if qty == 0:
                continue
            if position.get("exchSym") != self.symbol or position.get("side") not in ("LONG", "SHORT") or not qty.is_integer() or qty < 0:
                raise Blocked("UNEXPECTED_BROKER_POSITION")
            position_sides.add(position["side"])
            net += int(qty) * (1 if position["side"] == "LONG" else -1)
        if len(position_sides) > 1:
            raise Blocked("UNEXPECTED_HEDGED_BROKER_POSITION")
        if net != self.ledger.account()["net_quantity"]:
            raise Blocked("POSITION_RECONCILIATION_MISMATCH")
        for row in self.ledger.intents():
            if row["status"] in ("SKIPPED", "CLOSED", "CANCELLED", "REJECTED"):
                continue
            if not row["order_id"] or row["status"] in ("SUBMITTING", "UNKNOWN"):
                raise Blocked("UNCERTAIN_SUBMISSION_REQUIRES_RECONCILIATION")
            parent = self.orders.get(row["order_id"])
            if not parent:
                raise Blocked("ORDER_ACK_MISSING")
            intent = json.loads(row["payload"])
            if parent.get("exchSym") != self.symbol or parent.get("side") != ("BUY" if intent["direction"] > 0 else "SELL") or finite(parent["quantity"]) != row["quantity"]:
                raise Blocked("PARENT_ORDER_MISMATCH")
            exposure = self.ledger.net_for_intent(row["id"])
            children = [o for o in self.orders.values() if str(o.get("parentOrderId", "")) == row["order_id"]]
            if exposure:
                row = self._resolve_amendment(row, parent, exposure, children)
                self._protective_children(row, parent, exposure, children)
                # Absolute brackets must be translated to the actual average fill.
                # OpenAPI schema prose and reported offset behavior conflict.
                average = finite(parent["fillPrice"], positive=True)
                aligned = self.ledger.meta("aligned_entry", {})
                previous_average = aligned.get(row["id"])
                if previous_average != average and row["id"] in self.ledger.meta("breakeven_intents", []):
                    raise Blocked("PARTIAL_ENTRY_CHANGED_AFTER_BREAKEVEN")
                if align_brackets and not self.ledger.meta("halt") and previous_average != average:
                    basis = row["stop"] + intent["direction"] * intent["stop_points"] if previous_average is None else previous_average
                    if abs(average - basis) > self.terms.slippage_points + 0.000001:
                        raise Blocked("ENTRY_SLIPPAGE_ALLOWANCE_EXCEEDED")
                    # A fractional-tick average is rounded toward lower stop risk.
                    raw_stop = average - intent["direction"] * intent["stop_points"]
                    raw_target = average + intent["direction"] * intent["target_points"]
                    new_stop = (math.ceil(raw_stop*4) if intent["direction"] > 0 else math.floor(raw_stop*4)) / 4
                    new_target = (math.ceil(raw_target*4) if intent["direction"] > 0 else math.floor(raw_target*4)) / 4
                    aligned[row["id"]] = average
                    if new_stop != row["stop"] or new_target != row["target"]:
                        self.ledger.audit("BRACKET_ALIGNMENT_REQUEST", {"intent": row["id"], "stop": new_stop, "target": new_target})
                        if new_stop != row["stop"]:
                            self._amend_child(row["id"], "stop", new_stop)
                        if new_target != row["target"]:
                            self._amend_child(row["id"], "target", new_target)
                        self.ledger.set_meta("aligned_entry", aligned)
                        return self._reconcile(self.broker.snapshot())
                    self.ledger.set_meta("aligned_entry", aligned)
                direction = 1 if exposure > 0 else -1
                avg = finite(parent["fillPrice"], positive=True)
                actual_risk = abs(exposure) * (max(0, direction * (avg - row["stop"])) * 2 + self.terms.slippage_points * 2 + self.terms.fee_round_trip)
                if actual_risk > row["risk"] + 0.000001:
                    raise Blocked("FILL_EXCEEDS_RESERVED_RISK")
            elif parent["status"] in TERMINAL:
                if any(o.get("status") not in TERMINAL for o in children):
                    raise Blocked("ORPHAN_OCO_ORDER")
                self.ledger.db.execute("UPDATE intents SET status=? WHERE id=?", ("CLOSED" if parent["status"] == "FILLED" else "CANCELLED", row["id"]))
            elif parent["status"] not in WORKING:
                raise Blocked("ORDER_NOT_CONFIRMED")
        # Balance events are independent of fills. A cash/fee posting delay must
        # not conceal a missing stop that needs immediate protective recovery.
        if abs(self.balance["cashBalance"] - self.ledger.meta("broker_cash_offset", 0) - self.ledger.account()["realized_equity"]) > 0.01:
            raise Blocked("CASH_OR_FEES_RECONCILIATION_REQUIRED")
        self.position_snapshot_confirmed_at = utc(self.now())
        margin_response = self.broker.call("GET", "/info/security/margin", query={"symbols": self.symbol})
        margin_rows = [m for m in margin_response.get("securityMarginAndValues", []) if m.get("exchSym") == self.symbol]
        if len(margin_rows) != 1:
            raise Blocked("CURRENT_BROKER_MARGIN_MISSING")
        margin = margin_rows[0]
        millis = utc(self.now()).timestamp() * 1000
        scheduled = [finite(m["margin"], positive=True) for m in margin.get("marginScheduleDetails", []) if finite(m["startTime"]) <= millis < finite(m["endTime"])]
        required_margin = max(scheduled) if scheduled else max(finite(margin["initialMarginLong"], positive=True), finite(margin["initialMaginShort"], positive=True))
        if required_margin > self.terms.margin_per_contract:
            raise Blocked("BROKER_MARGIN_TERMS_CHANGED")
        risk, _ = self.ledger.reservations()
        if net and min(self.balance["cashBalanceAvailable"], self.balance["netLiquidityAvailable"]) < 0:
            raise Blocked("BROKER_AVAILABLE_MARGIN_EXHAUSTED")
        if self.ledger.identity["starting_cash"] - self.risk_equity() >= self.terms.max_drawdown_dollars:
            raise Blocked("DRAWDOWN_LIMIT")
        if risk > self.risk_equity() * 0.06 + 0.000001:
            raise Blocked("OPEN_RISK_EXCEEDED")

    def breakeven(self, iid):
        self.reconcile()
        row = self.ledger.intent(iid)
        if not row or not self.ledger.net_for_intent(iid):
            return
        parent = self.orders[row["order_id"]]
        entry = finite(parent["fillPrice"], positive=True)
        # Never loosen protection. Keep the same target; quantity changes unsupported.
        direction = json.loads(row["payload"])["direction"]
        entry = (math.ceil(entry * 4) if direction > 0 else math.floor(entry * 4)) / 4
        if direction * (entry - row["stop"]) <= 0:
            return
        moved = self.ledger.meta("breakeven_intents", [])
        self.ledger.set_meta("breakeven_intents", sorted(set(moved + [iid])))
        self._amend_child(iid, "stop", entry)

    def cancel_book(self):
        self.reconcile()
        for row in self.ledger.intents():
            if json.loads(row["payload"])["action"] == "BOOK" and row["order_id"]:
                parent = self.orders.get(row["order_id"], {})
                if parent.get("status") in WORKING:
                    # At 09:30 cancel the unfilled remainder too. Existing filled
                    # exposure must retain its correctly sized native children.
                    self.broker.cancel(row["order_id"])
        self.reconcile()

    def flatten(self, reason, *, intent_id=None):
        """Demo-only cancel-confirm-snapshot-close. No production reduce-only claim.

        The API exposes no documented atomic flatten or reduce-only flag. This
        sequence is qualified in mocks, and remains a broker-demo release blocker.
        A timeout is durable UNKNOWN and is never retried automatically.
        """
        if self.broker.environment != "demo" or not self.broker.account_verified:
            raise Blocked("LIVE_DISABLED")
        previous_halt = self.ledger.meta("halt")
        self.ledger.halt(reason)
        if self.ledger.meta("flatten_unknown"):
            raise Blocked("FLATTEN_UNKNOWN_NO_RETRY")
        snap = self.broker.snapshot()
        known = {r["order_id"] for r in self.ledger.intents() if r["order_id"]}
        selected = {r["order_id"] for r in self.ledger.intents() if r["order_id"] and (intent_id is None or r["id"] == intent_id)}
        for order in snap["orders"]:
            if order.get("accountId") != self.broker.account:
                continue
            if order["status"] not in TERMINAL:
                if order["orderId"] not in known and order.get("parentOrderId") not in known:
                    raise Blocked("UNEXPECTED_ORDER_MANUAL_RECOVERY_REQUIRED")
                if order["orderId"] in selected or order.get("parentOrderId") in selected:
                    self.broker.cancel(order["orderId"])
        snap = self.broker.snapshot()
        if any(o["status"] not in TERMINAL and (o["orderId"] in selected or o.get("parentOrderId") in selected) for o in snap["orders"]):
            raise Blocked("FLATTEN_CANCEL_NOT_CONFIRMED")
        # Ingest fills that raced cancellation before calculating any close quantity.
        mapping = {r["order_id"]: r["id"] for r in self.ledger.intents() if r["order_id"]}
        mapping.update(self.ledger.meta("exit_orders", {}))
        for o in snap["orders"]:
            if o.get("parentOrderId") in mapping:
                mapping[o["orderId"]] = mapping[o["parentOrderId"]]
        for f in snap["fills"]:
            if f.get("accountId") == self.broker.account and f.get("orderId") in mapping:
                self.ledger.fill(f, mapping[f["orderId"]], self.terms.fee_round_trip / 2)
        broker_net = sum(int(p["quantity"]) * (1 if p["side"] == "LONG" else -1) for p in snap["positions"] if p.get("accountId") == self.broker.account and p.get("exchSym") == self.symbol)
        if broker_net != self.ledger.account()["net_quantity"]:
            raise Blocked("FLATTEN_POSITION_MISMATCH")
        for row in self.ledger.intents():
            if intent_id is not None and row["id"] != intent_id:
                continue
            qty = self.ledger.net_for_intent(row["id"])
            if not qty:
                continue
            self.ledger.set_meta("flatten_unknown", True)  # durable BEFORE network
            try:
                response = self.broker.place({"exchSym": self.symbol, "side": "SELL" if qty > 0 else "BUY", "quantity": abs(qty), "orderType": "MARKET", "duration": "0"})
                if not response.get("orderId"):
                    raise Blocked("EXIT_ACK_MISSING")
                exits = self.ledger.meta("exit_orders", {})
                exits[str(response["orderId"])] = row["id"]
                self.ledger.set_meta("exit_orders", exits)
                self.ledger.set_meta("flatten_unknown", False)
            except Exception:
                raise Blocked("FLATTEN_UNKNOWN_NO_RETRY") from None
        self.reconcile()
        if intent_id is None and self.ledger.account()["net_quantity"] != 0:
            raise Blocked("FLATTEN_NOT_CONFIRMED")
        if intent_id is not None:
            if self.ledger.net_for_intent(intent_id):
                raise Blocked("EXIT_NOT_CONFIRMED")
            if previous_halt is None:
                self.ledger.set_meta("halt", None)
