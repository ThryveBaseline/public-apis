from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from .models import Bar, Blocked, UTC, NY, finite, utc


class MinuteFeed:
    """Fail-closed trade aggregation; never manufactures a zero-volume candle.

    Ironbeam calls `st` send time, NOT exchange execution time. Timestamp and
    sequence semantics must be qualified separately before broker demo routing.
    This class can collect dry-run data before that qualification.
    """
    def __init__(self, symbol, *, expected_delay_seconds=0, timestamp_verified=False, sequence_contiguous=False, complete_from=None):
        self.symbol, self.delay = symbol, expected_delay_seconds
        self.timestamp_verified, self.sequence_contiguous = timestamp_verified, sequence_contiguous
        self.last = None
        self.current = None
        self.last_received = None
        self.halted = None
        self.complete_from = utc(complete_from) if complete_from is not None else None

    @property
    def qualified(self):
        return self.timestamp_verified and self.sequence_contiguous and self.delay == 0 and self.halted is None

    def fail(self, reason):
        self.halted = reason
        raise Blocked(reason)

    def on_trade(self, trade, now):
        if self.halted:
            raise Blocked(self.halted)
        if trade.get("s") != self.symbol:
            self.fail("CONTRACT_OR_SYMBOL_CHANGED")
        now = utc(now)
        if self.complete_from is None:
            # Joining mid-minute cannot reconstruct its open/high/low. Only the
            # next entire minute is eligible; startup context must cover this gap.
            self.complete_from = (now - timedelta(seconds=self.delay)).replace(second=0, microsecond=0) + timedelta(minutes=1)
        ts = datetime.fromtimestamp(finite(trade["st"]) / 1000, UTC)
        age = (now - ts).total_seconds() - self.delay
        if age > 5 or age < -1:
            self.fail("STALE_OR_FUTURE_TRADE")
        price, size = finite(trade["p"], positive=True), finite(trade["sz"], positive=True)
        seq = finite(trade["sq"])
        if not seq.is_integer():
            self.fail("INVALID_SEQUENCE")
        signature = (seq, ts, price, size)
        if self.last:
            if signature == self.last:
                return []
            if seq <= self.last[0] or ts < self.last[1]:
                self.fail("REORDERED_OR_REVISED_TRADE")
            if self.sequence_contiguous and seq != self.last[0] + 1:
                self.fail("TRADE_SEQUENCE_GAP")
        self.last, self.last_received = signature, now
        minute = ts.replace(second=0, microsecond=0)
        out = []
        if self.current and minute > self.current.time:
            if minute - self.current.time != timedelta(minutes=1):
                self.fail("MINUTE_GAP_REQUIRES_BACKFILL")
            self.current.validate()
            out = [self.current] if self.current.time >= self.complete_from else []
            self.current = None
        if self.current is None:
            self.current = Bar(minute, price, price, price, price, size)
        else:
            b = self.current
            self.current = Bar(minute, b.open, max(b.high, price), min(b.low, price), price, b.volume + size)
        return out

    def watchdog(self, now):
        if not self.last_received or utc(now) - self.last_received > timedelta(seconds=5):
            self.fail("STALE_FEED")


def calendar_for_day(folder, day, *, max_age_days=7):
    """Reuse the existing read-only calendar snapshots; pin receipt before session."""
    import pandas as pd
    from research.news_calendar import snapshots, day_start
    d = pd.Timestamp(day)
    sunday = d - pd.Timedelta(days=(d.dayofweek + 1) % 7)
    begin = day_start(d).tz_convert("UTC")
    candidates = [s for s in snapshots(str(folder)) if s["week"] == sunday and begin - pd.Timedelta(days=max_age_days) <= s["fetched"] < begin]
    if not candidates:
        raise Blocked("NEWS_CALENDAR_MISSING_OR_STALE")
    selected = max(candidates, key=lambda s: s["fetched"])
    result = []
    for row in selected["events"].to_dict("records"):
        t = row["time"].to_pydatetime().astimezone(NY)
        if (t.replace(tzinfo=None) + timedelta(hours=6)).date().isoformat() == day and row["country"].upper() == "USD":
            result.append((t.hour * 60 + t.minute, row["impact"], row["title"]))
    digest = hashlib.sha256(Path(selected["path"]).read_bytes()).hexdigest()
    return result, {"file": Path(selected["path"]).name, "sha256": digest, "fetched": str(selected["fetched"])}


def check_calendar_receipt(folder, receipt):
    data = (Path(folder) / receipt["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != receipt["sha256"]:
        raise Blocked("NEWS_CALENDAR_REVISION")


def scheduled_context_gap(before, after):
    """Reuse the frozen session-gap calendar for seed continuity, never for margin.

    Actual broker order hours/cutoff still require a current confirmed schedule.
    """
    import pandas as pd
    from research.forward import _halt, CALENDAR_END
    a, b = pd.Timestamp(before).tz_convert(NY), pd.Timestamp(after).tz_convert(NY)
    return b.tz_localize(None).normalize() <= CALENDAR_END and _halt(a, b) is not None
