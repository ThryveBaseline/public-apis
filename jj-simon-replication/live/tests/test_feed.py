from datetime import datetime, timedelta, timezone
from dataclasses import replace
import pytest


@pytest.mark.parametrize("value",[None,123,"not-a-timestamp"])
def test_incomplete_or_invalid_schedule_is_a_controlled_block(value):
    from live.models import Blocked, utc
    with pytest.raises(Blocked,match="INVALID_TIMESTAMP"):
        utc(value)

from live.feed import MinuteFeed
from live.models import Blocked, RiskTerms, trading_day

T = datetime(2026, 10, 22, 13, 30, tzinfo=timezone.utc)


def tick(seq=1, seconds=0, price=20000):
    return {"s": "XCME:NQ.Z26", "st": int((T+timedelta(seconds=seconds)).timestamp()*1000), "sq": seq, "p": price, "sz": 1}


def test_finalized_bar_only_after_next_minute_and_dedup():
    feed = MinuteFeed("XCME:NQ.Z26", timestamp_verified=True, sequence_contiguous=True, complete_from=T)
    assert feed.on_trade(tick(), T) == []
    assert feed.on_trade(tick(), T) == []
    assert feed.on_trade(tick(2, 30, 20001), T+timedelta(seconds=30)) == []
    bars = feed.on_trade(tick(3, 60, 20002), T+timedelta(seconds=60))
    assert len(bars) == 1 and bars[0].close == 20001 and bars[0].volume == 2
    assert feed.qualified


@pytest.mark.parametrize("kind", ["revised", "reordered", "sequence_gap", "minute_gap", "stale", "symbol"])
def test_feed_integrity_fail_closed(kind):
    feed = MinuteFeed("XCME:NQ.Z26", timestamp_verified=True, sequence_contiguous=True)
    feed.on_trade(tick(), T)
    second, now = tick(2, 1), T+timedelta(seconds=1)
    if kind == "revised":
        second = tick(1, 0, 20001)
    elif kind == "reordered":
        second = tick(2, -1)
    elif kind == "sequence_gap":
        second = tick(3, 1)
    elif kind == "minute_gap":
        second, now = tick(2, 121), T+timedelta(seconds=121)
    elif kind == "stale":
        now += timedelta(seconds=10)
    else:
        second["s"] = "XCME:NQ.H27"
    with pytest.raises(Blocked):
        feed.on_trade(second, now)
    assert not feed.qualified


def test_delayed_demo_is_never_classified_live():
    feed = MinuteFeed("XCME:NQ.Z26", expected_delay_seconds=600, timestamp_verified=True, sequence_contiguous=True)
    feed.on_trade(tick(), T+timedelta(seconds=600))
    assert not feed.qualified


def test_watchdog_does_not_depend_on_new_ticks():
    feed = MinuteFeed("XCME:NQ.Z26")
    feed.on_trade(tick(), T)
    with pytest.raises(Blocked, match="STALE"):
        feed.watchdog(T+timedelta(seconds=6))


def test_first_partial_minute_is_never_a_strategy_candle():
    feed = MinuteFeed("XCME:NQ.Z26")
    assert feed.on_trade(tick(1,30),T+timedelta(seconds=30)) == []
    assert feed.on_trade(tick(2,60),T+timedelta(seconds=60)) == []
    complete = feed.on_trade(tick(3,120),T+timedelta(seconds=120))
    assert len(complete)==1 and complete[0].time==T+timedelta(minutes=1)


def test_exchange_day_and_dst():
    assert trading_day(datetime.fromisoformat("2026-10-25T18:00:00-04:00")) == "2026-10-26"
    assert trading_day(datetime.fromisoformat("2026-11-01T18:00:00-05:00")) == "2026-11-02"


@pytest.mark.parametrize("stop,expected", [(12.5, 2), (25, 1), (50, 0)])
def test_whole_micro_risk_sizing(stop, expected):
    terms = RiskTerms(1.5, 0.25, 100, 200, 300, True)
    qty, each = terms.size(2000, 0, 2000, 0, stop)
    assert qty == expected and qty*each <= 60


@pytest.mark.parametrize("field,value", [("fee_round_trip", -1), ("slippage_points", float("nan")), ("margin_per_contract", 0), ("max_drawdown_dollars", float("inf")), ("confirmed", False)])
def test_invalid_or_unconfirmed_terms_rejected(field, value):
    terms = replace(RiskTerms(1.5, 0.25, 100, 200, 300, True), **{field: value})
    with pytest.raises(Blocked):
        terms.size(2000, 0, 2000, 0, 25)
