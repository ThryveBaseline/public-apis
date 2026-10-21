"""Deterministic broker simulator, NOT a claim about Ironbeam's demo behavior."""
from copy import deepcopy
from datetime import datetime, timezone
from urllib.parse import urlparse

from live.models import Blocked


class MockWire:
    def __init__(self):
        self.account = "SIM001"
        self.orders, self.fills, self.calls = {}, [], []
        self.price, self.cash, self.net, self.avg = 20005.0, 2000.0, 0, 0
        self.partial = None
        self.timeout_after_accept = False
        self.is_live = False
        self.margin = 100
        self.next_id = 0
        self.stream_ids = 0
        self.clock = datetime(2026, 10, 22, 13, 31, tzinfo=timezone.utc)

    def request(self, method, url, headers, body, timeout):
        path = urlparse(url).path.removeprefix("/v2")
        self.calls.append((method, path, deepcopy(body)))
        if path == "/auth":
            return {"status": "OK", "token": "MOCK_SECRET_NEVER_LOG"}
        if path == "/info/trader":
            return {"status": "OK", "accounts": [self.account], "isLive": self.is_live}
        if path == "/info/security/margin":
            return {"securityMarginAndValues": [{"exchSym":"XCME:MNQ.Z26", "initialMarginLong":self.margin, "initialMaginShort":self.margin}]}
        if path == "/info/security/definitions":
            return {"securityDefinitions":[{"exchSym":"XCME:MNQ.Z26","allowTrading":True,"currencyCode":"USD",
                "minPriceIncrement":.25,"minPriceIncrementValue":.5,"expirationTime":1797890400000}]}
        if path == "/stream/create":
            self.stream_ids += 1
            return {"streamId": str(self.stream_ids)}
        if path.startswith("/market/") and "/subscribe/" in path:
            return {"status": "OK"}
        if path.endswith("/ANY"):
            return {"orders": deepcopy(list(self.orders.values()))}
        if path.endswith("/fills"):
            return {"fills": deepcopy(self.fills)}
        if path.endswith("/balance"):
            equity = self.cash + self.net * (self.price - self.avg) * 2
            return {"balances": [{"accountId": self.account, "currencyCode": "USD", "balanceType": "CURRENT_OPEN", "cashBalance": self.cash,
                                 "totalEquity": equity, "netLiquidity": equity,
                                 "cashBalanceAvailable": self.cash, "netLiquidityAvailable": self.cash}]}
        if path.endswith("/positions"):
            return {"positions": [] if not self.net else [{"accountId": self.account, "exchSym": "XCME:MNQ.Z26", "side": "LONG" if self.net > 0 else "SHORT", "quantity": abs(self.net), "price": self.avg}]}
        if path.endswith("/place"):
            order = self.new_order(body)
            if body["orderType"] == "MARKET":
                self.fill_order(order["orderId"], min(body["quantity"], self.partial or body["quantity"]), self.price)
            if self.timeout_after_accept:
                raise Blocked("TRANSPORT_UNCERTAIN")
            return {"orderId": order["orderId"], "strategyId": "strategy-" + order["orderId"]}
        if "/update/" in path:
            order = self.orders[path.rsplit("/", 1)[1]]
            order["stopLoss"], order["takeProfit"] = body["stopLoss"], body["takeProfit"]
            for oid in order["childOrders"]:
                child = self.orders[oid]
                if child["orderType"] == "STOP":
                    child["stopPrice"] = body["stopLoss"]
                else:
                    child["limitPrice"] = body["takeProfit"]
            return {"orderId": order["orderId"]}
        if "/cancel/" in path:
            order = self.orders[path.rsplit("/", 1)[1]]
            if order["status"] not in ("FILLED", "CANCELLED"):
                order["status"] = "CANCELLED"
            return {"orderId": order["orderId"]}
        raise AssertionError((method, path))

    def new_order(self, body, parent=None):
        self.next_id += 1
        order = {**body, "orderId": str(self.next_id), "accountId": self.account, "status": "NEW", "fillQuantity": 0, "fillPrice": 0, "childOrders": []}
        if parent:
            order["parentOrderId"] = parent
        self.orders[order["orderId"]] = order
        return order

    def fill_order(self, oid, qty, price):
        order = self.orders[oid]
        before = order["fillQuantity"]
        order["fillQuantity"] += qty
        order["fillPrice"] = (order["fillPrice"] * before + price * qty) / order["fillQuantity"]
        order["status"] = "FILLED" if order["fillQuantity"] == order["quantity"] else "PARTIALLY_FILLED"
        self.fills.append({"orderId": oid, "orderUpdateId": str(len(self.fills) + 1), "accountId": self.account,
                           "exchSym": order["exchSym"], "side": order["side"], "fillQuantity": qty,
                           "fillTotalQuantity": order["fillQuantity"], "fillPrice": price, "fillDate": self.clock.isoformat()})
        direction = 1 if order["side"] == "BUY" else -1
        if self.net and (self.net > 0) != (direction > 0):
            closing = min(qty, abs(self.net))
            self.cash += closing * (price - self.avg) * (1 if self.net > 0 else -1) * 2
        elif self.net:
            self.avg = (self.avg * abs(self.net) + price * qty) / (abs(self.net) + qty)
        else:
            self.avg = price
        self.net += direction * qty
        self.cash -= 0.75 * qty
        if "stopLoss" in order:
            if not order["childOrders"]:
                for kind, field, value in (("STOP", "stopPrice", order["stopLoss"]), ("LIMIT", "limitPrice", order["takeProfit"])):
                    child = self.new_order({"exchSym": order["exchSym"], "side": "SELL" if direction > 0 else "BUY", "quantity": order["fillQuantity"], "orderType": kind, "duration": "1", field: value}, oid)
                    order["childOrders"].append(child["orderId"])
            else:
                for child_id in order["childOrders"]:
                    self.orders[child_id]["quantity"] = order["fillQuantity"]
        if order.get("parentOrderId"):
            parent = self.orders[order["parentOrderId"]]
            for sibling in parent["childOrders"]:
                if sibling != oid:
                    self.orders[sibling]["status"] = "CANCELLED"
            if parent["status"] == "PARTIALLY_FILLED":
                parent["status"] = "CANCELLED"

    def placements(self):
        return [c for c in self.calls if c[1].endswith("/place")]
