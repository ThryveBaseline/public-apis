"""Private SQLite account ledger, separate from every existing research ledger."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
import os
from pathlib import Path
import sqlite3

from .models import Blocked, stable_id, finite


class Ledger:
    def __init__(self, path, *, lane, account, starting_cash=2000):
        if lane not in ("mock", "demo", "dry-run"):
            raise Blocked("LIVE_DISABLED")
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if p.is_symlink():
            raise Blocked("LEDGER_SYMLINK_REFUSED")
        self.db = sqlite3.connect(p, isolation_level=None, timeout=10)
        os.chmod(p, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY,at TEXT DEFAULT CURRENT_TIMESTAMP,kind TEXT NOT NULL,value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS intents(id TEXT PRIMARY KEY,created TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,
            quantity INTEGER NOT NULL,risk REAL NOT NULL,margin REAL NOT NULL,order_id TEXT UNIQUE,stop REAL,target REAL);
          CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,intent_id TEXT NOT NULL,payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS fills(id TEXT PRIMARY KEY,order_id TEXT NOT NULL,intent_id TEXT NOT NULL,
            side INTEGER NOT NULL,quantity INTEGER NOT NULL,price REAL NOT NULL,fee REAL NOT NULL,at TEXT NOT NULL,payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS bars(time TEXT PRIMARY KEY,payload TEXT NOT NULL);
        ''')
        identity = {"lane": lane, "account_hash": stable_id(account), "starting_cash": finite(starting_cash, positive=True)}
        with self.transaction():
            existing = self.meta("identity")
            if existing and existing != identity:
                raise Blocked("LEDGER_ACCOUNT_OR_LANE_MISMATCH")
            self.set_meta("identity", identity)
        self.identity = identity

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def meta(self, key, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_meta(self, key, value):
        self.db.execute("INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, sort_keys=True)))

    def audit(self, kind, value):
        self.db.execute("INSERT INTO audit(kind,value) VALUES(?,?)", (kind, json.dumps(value, sort_keys=True)))

    def halt(self, reason):
        self.set_meta("halt", reason)
        self.audit("HALT", {"reason": reason})

    def intents(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM intents ORDER BY rowid")]

    def intent(self, iid):
        row = self.db.execute("SELECT * FROM intents WHERE id=?", (iid,)).fetchone()
        return dict(row) if row else None

    def reservations(self):
        row = self.db.execute("SELECT coalesce(sum(risk),0),coalesce(sum(margin),0) FROM intents WHERE status NOT IN ('CLOSED','REJECTED','CANCELLED','SKIPPED')").fetchone()
        return tuple(row)

    def reserve(self, intent, terms, equity, available_margin, reference_price):
        with self.transaction():
            if self.intent(intent.id):
                return None
            if self.meta("halt"):
                raise Blocked("ACCOUNT_HALTED")
            risk, margin = self.reservations()
            qty, each = terms.size(equity, risk, available_margin, margin, intent.stop_points)
            # One netting account cannot preserve opposite concurrent brackets.
            for old in self.intents():
                if old["status"] not in ("CLOSED", "REJECTED", "CANCELLED", "SKIPPED") and json.loads(old["payload"])["direction"] != intent.direction:
                    qty = 0
            status = "SUBMITTING" if qty else "SKIPPED"
            stop = reference_price - intent.direction * intent.stop_points
            target = reference_price + intent.direction * intent.target_points
            self.db.execute("INSERT INTO intents VALUES(?,?,?,?,?,?,?,?,?,?)", (
                intent.id, intent.time, json.dumps(asdict(intent), sort_keys=True), status, qty, qty * each,
                qty * terms.margin_per_contract, None, stop, target))
            self.audit(status, {"intent": intent.id, "quantity": qty, "reserved_risk": qty * each,
                "sizing_equity":equity,"available_margin":available_margin,"prior_reserved_risk":risk,
                "prior_reserved_margin":margin,"reference_price":reference_price,"risk_terms":asdict(terms)})
            return self.intent(intent.id)

    def acknowledge(self, iid, order_id):
        if not order_id:
            self.unknown(iid)
            raise Blocked("ORDER_ACK_MISSING")
        self.db.execute("UPDATE intents SET status='ACKNOWLEDGED',order_id=? WHERE id=?", (str(order_id), iid))

    def unknown(self, iid):
        self.db.execute("UPDATE intents SET status='UNKNOWN' WHERE id=?", (iid,))
        self.halt("UNCERTAIN_SUBMISSION_REQUIRES_RECONCILIATION")

    def order(self, order, iid):
        self.db.execute("INSERT INTO orders VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (str(order["orderId"]), iid, json.dumps(order, sort_keys=True)))

    def fill(self, fill, iid, fee_side):
        # API provides orderUpdateId. Timestamp/price/size alone are not unique.
        if not fill.get("orderUpdateId") or not fill.get("orderId"):
            raise Blocked("FILL_ID_MISSING")
        qty = finite(fill["fillQuantity"], positive=True)
        if not qty.is_integer() or fill["side"] not in ("BUY", "SELL"):
            raise Blocked("INVALID_MNQ_FILL")
        price = finite(fill["fillPrice"], positive=True)
        key = stable_id([fill["orderId"], fill["orderUpdateId"]])
        payload = json.dumps(fill, sort_keys=True)
        previous = self.db.execute("SELECT payload FROM fills WHERE id=?", (key,)).fetchone()
        if previous:
            if previous[0] != payload:
                raise Blocked("FILL_REVISION")
            return False
        self.db.execute("INSERT INTO fills VALUES(?,?,?,?,?,?,?,?,?)", (key, str(fill["orderId"]), iid, 1 if fill["side"] == "BUY" else -1,
            int(qty), price, int(qty) * fee_side, fill["fillDate"], payload))
        return True

    def account(self, mark=None):
        """FIFO realized cash, net contracts and mark-to-market; fees labeled estimated.

        No strategy R or hypothetical trade result enters this account ledger.
        """
        cash = self.identity["starting_cash"] + self.meta("cash_adjustment", 0)
        lots = []
        fees = 0.0
        realized = 0.0
        for f in self.db.execute("SELECT * FROM fills ORDER BY at,rowid"):
            qty, side, price = f["quantity"], f["side"], f["price"]
            fees += f["fee"]
            while qty and lots and lots[0][0] != side:
                old_side, old_qty, old_price = lots[0]
                matched = min(qty, old_qty)
                realized += matched * (price - old_price) * old_side * 2
                qty -= matched
                if matched == old_qty:
                    lots.pop(0)
                else:
                    lots[0][1] -= matched
            if qty:
                lots.append([side, qty, price])
        unrealized = sum(side * qty * (mark - price) * 2 for side, qty, price in lots) if mark is not None else None
        return {"realized_equity": round(cash + realized - fees, 8), "realized_gross_pnl": round(realized, 8),
                "estimated_fees": round(fees, 8), "fee_status": "ESTIMATED_UNTIL_BROKER_STATEMENT",
                "net_quantity": sum(side * qty for side, qty, _ in lots), "unrealized_pnl": unrealized}

    def net_for_intent(self, iid):
        return self.db.execute("SELECT coalesce(sum(side*quantity),0) FROM fills WHERE intent_id=?", (iid,)).fetchone()[0]

    def bar(self, bar):
        payload = json.dumps(bar.record(), sort_keys=True)
        old = self.db.execute("SELECT payload FROM bars WHERE time=?", (bar.record()["time"],)).fetchone()
        if old:
            if old[0] != payload:
                raise Blocked("BAR_REVISION")
            return False
        self.db.execute("INSERT INTO bars VALUES(?,?)", (bar.record()["time"], payload))
        return True

    def close(self):
        self.db.close()
