from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc


class Blocked(RuntimeError):
    """A safe, non-sensitive reason code; never include broker response bodies."""


def finite(value, *, positive=False) -> float:
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise Blocked("INVALID_NUMBER")
    return result


def utc(value: str | datetime) -> datetime:
    try:
        t = datetime.fromisoformat(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        raise Blocked("INVALID_TIMESTAMP") from None
    if not isinstance(t, datetime):
        raise Blocked("INVALID_TIMESTAMP")
    if t.tzinfo is None:
        raise Blocked("NAIVE_TIMESTAMP")
    return t.astimezone(UTC)


def trading_day(value: datetime) -> str:
    local = utc(value).astimezone(NY)
    return (local.date() + timedelta(days=int(local.hour >= 18))).isoformat()


def stable_id(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:32]


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0

    def validate(self):
        ts = utc(self.time)
        if ts.second or ts.microsecond:
            raise Blocked("UNALIGNED_BAR")
        for x in (self.open, self.high, self.low, self.close):
            finite(x, positive=True)
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close) or self.low > self.high:
            raise Blocked("INVALID_OHLC")
        if finite(self.volume) < 0:
            raise Blocked("INVALID_VOLUME")

    def record(self):
        return {**asdict(self), "time": utc(self.time).isoformat()}

    @classmethod
    def restore(cls, value):
        return cls(**{**value, "time": utc(value["time"])})


@dataclass(frozen=True)
class Intent:
    id: str
    time: str
    action: str
    session: str = ""
    setup: str = ""
    direction: int = 0
    stop_points: float = 0
    target_points: float = 0
    level: float | None = None
    grade: str = ""
    reference: str = ""


@dataclass(frozen=True)
class RiskTerms:
    # No assumed live broker fees, margin, cutoff or drawdown authorization.
    fee_round_trip: float
    slippage_points: float
    margin_per_contract: float
    margin_cushion: float
    max_drawdown_dollars: float
    confirmed: bool = False

    def validate(self):
        for v in (self.fee_round_trip, self.slippage_points, self.margin_cushion):
            if finite(v) < 0:
                raise Blocked("INVALID_RISK_TERMS")
        finite(self.margin_per_contract, positive=True)
        finite(self.max_drawdown_dollars, positive=True)
        if not self.confirmed:
            raise Blocked("BROKER_TERMS_UNCONFIRMED")

    def per_contract(self, stop_points):
        # Entry and stop slippage; gaps may exceed this planning allowance.
        return (Decimal(str(finite(stop_points, positive=True))) + 2 * Decimal(str(self.slippage_points))) * 2 + Decimal(str(self.fee_round_trip))

    def size(self, equity, reserved_risk, available_margin, reserved_margin, stop_points):
        self.validate()
        e = Decimal(str(finite(equity, positive=True)))
        r = Decimal(str(finite(reserved_risk)))
        available = Decimal(str(finite(available_margin))) - Decimal(str(finite(reserved_margin))) - Decimal(str(self.margin_cushion))
        if min(r, Decimal(str(reserved_margin))) < 0:
            raise Blocked("INVALID_RESERVATION")
        risk = self.per_contract(stop_points)
        budget = min(e * Decimal("0.03"), e * Decimal("0.06") - r)
        qty = min(int((budget / risk).to_integral_value(rounding=ROUND_FLOOR)),
                  int((available / Decimal(str(self.margin_per_contract))).to_integral_value(rounding=ROUND_FLOOR)))
        return max(0, qty), float(risk)
