"""Read-only entitlement/connectivity probe. Only authentication uses POST."""
from datetime import datetime

from . import LIVE_STATUS
from .models import Blocked, UTC, finite


def probe(broker, credentials, *, account=None, symbols=(), sample_stream=False):
    report = {"live": LIVE_STATUS, "environment": broker.environment, "authentication": "BLOCKED", "account": "BLOCKED",
              "market_data": "BLOCKED", "stream": "BLOCKED", "bracket_demo": "BLOCKED"}
    broker.authenticate(credentials)
    report["authentication"] = "CLEAR"
    trader = broker.call("GET", "/info/trader")
    accounts = trader.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise Blocked("NO_ENTITLED_ACCOUNTS")
    report["account_count"] = len(accounts)
    if account is None:
        if len(accounts) != 1:
            raise Blocked("EXPLICIT_ACCOUNT_SELECTION_REQUIRED")
        account = accounts[0]
    broker.bind_account(account)
    balances = broker.call("GET", f"/account/{account}/balance", query={"balanceType": "CURRENT_OPEN"}).get("balances", [])
    if not any(b.get("accountId") == account and b.get("currencyCode") == "USD" for b in balances):
        raise Blocked("USD_BALANCE_MISSING")
    report["account"] = "CLEAR"
    # Discover, never automatically roll or guess the front contract.
    report["contracts"] = {}
    for group in ("NQ", "MNQ"):
        found = broker.call("GET", f"/info/symbol/search/futures/XCME/{group}")
        report["contracts"][group] = [r["symbol"] for r in found.get("symbols", [])]
    if not symbols:
        report["blocker"] = "SELECT_AND_VERIFY_MATCHING_NQ_MNQ_EXPIRIES"
        return report
    query = {"symbols": ",".join(symbols)}
    definitions = broker.call("GET", "/info/security/definitions", query=query).get("securityDefinitions", [])
    margins = broker.call("GET", "/info/security/margin", query=query).get("securityMarginAndValues", [])
    broker.call("GET", "/info/security/status", query=query)
    report["instruments"] = []
    for symbol in symbols:
        matches = [d for d in definitions if d.get("exchSym") == symbol]
        if len(matches) != 1:
            raise Blocked("SYMBOL_OR_DATA_ENTITLEMENT_MISSING")
        d = matches[0]
        expected_tick_value = 0.5 if ":MNQ." in symbol else 5.0
        if finite(d["minPriceIncrement"]) != 0.25 or finite(d["minPriceIncrementValue"]) != expected_tick_value or d.get("currencyCode") != "USD":
            raise Blocked("INSTRUMENT_VALUE_MISMATCH")
        expiry = datetime.fromtimestamp(finite(d["expirationTime"]) / 1000, UTC)
        if expiry <= datetime.now(UTC):
            raise Blocked("EXPIRED_CONTRACT")
        report["instruments"].append({"symbol": symbol, "expiry": expiry.isoformat(), "tick": 0.25, "tick_value": expected_tick_value,
                                      "trading_allowed": d.get("allowTrading") is True,
                                      "margin_available": any(m.get("exchSym") == symbol for m in margins)})
    report["instrument_definitions"] = "CLEAR"
    if sample_stream:
        connection = broker.stream(list(symbols))
        try:
            for i, message in enumerate(connection):
                trades = message.get("tr", [])
                if trades:
                    age = (datetime.now(UTC).timestamp() * 1000 - finite(trades[-1]["st"])) / 1000
                    report["stream"] = "CLEAR"
                    report["market_data"] = "CLEAR"
                    report["market_data_scope"] = "TRADE_SAMPLE_ONLY"
                    report["observed_send_time_age_seconds"] = round(age, 2)
                    report["real_time_signal_timing"] = "BLOCKED"
                    break
                if i >= 5:
                    break
        finally:
            connection.close()
    report["blocker"] = "BROKER_DEMO_EXECUTION_AND_TIMESTAMP_SEMANTICS_NOT_YET_VERIFIED"
    return report
