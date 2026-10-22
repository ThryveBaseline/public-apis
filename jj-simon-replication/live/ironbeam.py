"""REST and WebSocket v2 transport; pinned to official hosts and demo-only mutations.

Source: https://docs.ironbeamapi.com/ OpenAPI 2.1, inspected 2026-10-21.
No guessed client-order-id or unsupported trailing/offset fields. A timeout on a
mutation is UNKNOWN, never an invitation to retry.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import os
from pathlib import Path
import re
import stat
from threading import Lock
import time
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import Blocked

BASES = {"demo": "https://demo.ironbeamapi.com/v2", "live-readonly": "https://live.ironbeamapi.com/v2"}


class RateLimited(Blocked):
    def __init__(self, retry_after=None):
        seconds = 30.0  # conservative local policy, not a broker SLA
        try:
            seconds = float(retry_after)
        except (TypeError, ValueError):
            try:
                seconds = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                pass
        self.retry_after = max(30.0, seconds) if math.isfinite(seconds) else 30.0
        super().__init__("HTTP_429")


class RequestPacer:
    """All REST traffic shares 250ms spacing; a 429 never queues a stale order.

    Ironbeam staff publish 10 requests/sec. Headroom accommodates account polling
    and amendments. During a cooldown callers fail closed WITHOUT sending traffic
    or automatically retrying a mutation. Recovery may retry reads later.
    """
    def __init__(self, *, clock=time.monotonic, sleep=time.sleep):
        self.clock, self.sleep = clock, sleep
        self.next_request = self.cooldown_until = 0.0
        self.lock = Lock()

    def wait(self):
        with self.lock:
            if self.clock() < self.cooldown_until:
                raise Blocked("RATE_LIMIT_COOLDOWN")
            delay = self.next_request - self.clock()
            if delay > 0:
                self.sleep(delay)
            self.next_request = self.clock() + 0.25

    def limited(self, seconds):
        with self.lock:
            self.cooldown_until = max(self.cooldown_until, self.clock() + seconds)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked("HTTP_REDIRECT_REFUSED")


def protected_json(path):
    p = Path(path).expanduser()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(p, flags)
    except OSError:
        raise Blocked("CREDENTIAL_FILE_UNAVAILABLE") from None
    with os.fdopen(fd) as fh:
        info = os.fstat(fh.fileno())
        if not stat.S_ISREG(info.st_mode) or (os.name == "posix" and (info.st_uid != os.getuid() or info.st_mode & 0o077)):
            raise Blocked("CREDENTIAL_FILE_MUST_BE_OWNER_ONLY")
        try:
            data = json.load(fh)
        except (ValueError, OSError):
            raise Blocked("INVALID_CREDENTIAL_FILE") from None
    username, password, apikey = data.get("username"), data.get("password"), data.get("apikey")
    if not (isinstance(username, str) and username and isinstance(password, str) and password):
        raise Blocked("CREDENTIAL_FIELDS_MISSING")
    # Official /auth contract: a standard account authenticates with the issued API key in
    # the password field; the apikey field is Enterprise-only and OPTIONAL. The server
    # validates apikey whenever present, so an absent key is omitted, never sent empty.
    credentials = {"username": username, "password": password}
    if apikey is not None:
        if not (isinstance(apikey, str) and apikey):
            raise Blocked("CREDENTIAL_SHAPE_UNRECOGNIZED")
        credentials["apikey"] = apikey
    return credentials


def http_request(method, url, headers, body, timeout):
    raw = None if body is None else json.dumps(body).encode()
    request = Request(url, data=raw, headers=headers, method=method)
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            result = json.load(response)
    except HTTPError as error:
        # Do not include URL, token, credential data, or broker's free-text message.
        if error.code == 429:
            raise RateLimited(error.headers.get("Retry-After") if error.headers else None) from None
        raise Blocked(f"HTTP_{error.code}") from None
    except Blocked:
        raise
    except Exception:
        raise Blocked("TRANSPORT_UNCERTAIN") from None
    if not isinstance(result, dict):
        raise Blocked("INVALID_BROKER_RESPONSE")
    return result


class Ironbeam:
    def __init__(self, environment="demo", *, request=http_request, pacer=None):
        if environment not in BASES:
            raise Blocked("LIVE_DISABLED")
        self.environment = environment
        self.base = BASES[environment]
        self.request = request
        self.pacer = pacer if pacer is not None else RequestPacer()
        self._token = None
        self.account = None
        self.account_verified = False

    def __repr__(self):
        return f"Ironbeam(environment={self.environment!r}, credentials=<redacted>)"

    def call(self, method, path, *, body=None, query=None, before_send=None):
        if self.base != BASES.get(self.environment):
            raise Blocked("API_HOST_MISMATCH")
        order_mutation = path.startswith("/order/") and method != "GET"
        if method != "GET" and path != "/auth" and not order_mutation:
            raise Blocked("UNSUPPORTED_MUTATION")
        if order_mutation and (self.environment != "demo" or not self.account_verified):
            raise Blocked("LIVE_DISABLED")
        if order_mutation:
            if not path.startswith(f"/order/{self.account}/") or (body and body.get("accountId",self.account)!=self.account):
                raise Blocked("ORDER_ACCOUNT_MISMATCH")
        if not path.startswith("/") or "?" in path or ".." in path:
            raise Blocked("INVALID_API_PATH")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        url = self.base + path + ("?" + urlencode(query) if query else "")
        self.pacer.wait()
        if before_send is not None:
            before_send()
        try:
            result = self.request(method, url, headers, body, 15)
        except RateLimited as error:
            self.pacer.limited(error.retry_after)
            raise
        except Blocked:
            raise
        except Exception:
            raise Blocked("TRANSPORT_UNCERTAIN") from None
        if result.get("status", "OK") not in ("OK", "SUCCESS"):
            raise Blocked("BROKER_REJECTED")
        return result

    def authenticate(self, credentials):
        self._token = None
        self.account_verified = False
        response = self.call("POST", "/auth", body=credentials)
        if not isinstance(response.get("token"), str) or not response["token"]:
            raise Blocked("AUTH_TOKEN_MISSING")
        self._token = response["token"]

    def bind_account(self, account):
        self.account_verified = False
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,10}", account):
            raise Blocked("INVALID_ACCOUNT_ID")
        result = self.call("GET", "/info/trader")
        trader = result.get("traderInfo", result.get("trader", result))
        accounts = trader.get("accounts", [])
        if not isinstance(accounts, list) or account not in accounts:
            raise Blocked("ACCOUNT_NOT_ENTITLED")
        if self.environment == "demo" and trader.get("isLive") is not False:
            raise Blocked("DEMO_ACCOUNT_NOT_VERIFIED")
        self.account = account
        self.account_verified = self.environment == "demo"
        return result

    def get(self, suffix):
        if not self.account:
            raise Blocked("ACCOUNT_NOT_BOUND")
        return self.call("GET", f"/account/{self.account}/{suffix}")

    def snapshot(self):
        if not self.account:
            raise Blocked("ACCOUNT_NOT_BOUND")
        result = {
            "orders": self.call("GET", f"/order/{self.account}/ANY").get("orders"),
            "fills": self.get("fills").get("fills"),
            "positions": self.get("positions").get("positions"),
            "balances": self.call("GET", f"/account/{self.account}/balance", query={"balanceType": "CURRENT_OPEN"}).get("balances"),
        }
        if not all(isinstance(v, list) for v in result.values()):
            raise Blocked("INCOMPLETE_BROKER_SNAPSHOT")
        return result

    def place(self, body, *, before_send=None):
        if not self.account:
            raise Blocked("ACCOUNT_NOT_BOUND")
        return self.call("POST", f"/order/{self.account}/place", body={"accountId": self.account, **body, "waitForOrderId": True}, before_send=before_send)

    def update(self, order_id, body):
        oid = quote(str(order_id), safe="")
        return self.call("PUT", f"/order/{self.account}/update/{oid}", body={**body, "orderId": str(order_id)})

    def cancel(self, order_id):
        return self.call("DELETE", f"/order/{self.account}/cancel/{quote(str(order_id), safe='')}")

    def stream(self, symbols, *, connect=None):
        """One connection only. Caller reconciles and creates a NEW stream after loss.

        websocket-client is imported lazily; mock tests need no network dependency.
        Never print repr(socket), exception strings or the URL (token in query).
        """
        if connect is None:
            try:
                import websocket
                connect = websocket.create_connection
            except ImportError:
                raise Blocked("WEBSOCKET_DEPENDENCY_MISSING") from None
        stream_id = self.call("GET", "/stream/create").get("streamId")
        if not stream_id or not self._token:
            raise Blocked("STREAM_AUTH_MISSING")
        url = self.base.replace("https://", "wss://") + "/stream/" + quote(str(stream_id), safe="") + "?" + urlencode({"token": self._token})
        ws = None
        try:
            ws = connect(url, timeout=5, enable_multithread=True)
            for kind in (("trades", "quotes") if symbols else ()):
                self.call("GET", f"/market/{kind}/subscribe/{quote(str(stream_id), safe='')}", query={"symbols": ",".join(symbols)})
            while True:
                raw = ws.recv()
                if not raw:
                    raise Blocked("STREAM_DISCONNECTED")
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise Blocked("INVALID_STREAM_MESSAGE")
                yield event
        except Blocked:
            raise
        except Exception:
            raise Blocked("STREAM_DISCONNECTED") from None
        finally:
            if ws:
                ws.close()
