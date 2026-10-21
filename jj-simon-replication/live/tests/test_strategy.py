"""Synthetic correctness fixtures only: no market history or performance study."""
from datetime import timedelta
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from live.models import Bar, Blocked
from live.strategy import StreamingJJ, verify_frozen
from research.jj_system import generate_trades

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("frozen_jj_test_fixtures", ROOT / "tests/test_jj_system.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def stream(frame, calendar=None, end=None):
    engine = StreamingJJ(calendar=calendar)
    actions = []
    for ts, row in frame.iterrows():
        if end and ts > end:
            break
        actions.extend(engine.on_bar(Bar(ts.to_pydatetime(), *[float(row[k]) for k in ("open", "high", "low", "close", "volume")])))
    return engine, actions


def entries(actions, day="2026-10-15", session=None):
    rows = []
    for a in actions:
        if a.action != "ENTRY" or (session and a.session != session):
            continue
        signal = pd.Timestamp(a.time).tz_convert(reference.NY) - pd.Timedelta(minutes=1)
        if (signal.tz_localize(None) + pd.Timedelta(hours=6)).date().isoformat() != day:
            continue
        rows.append((str(signal), a.session, a.setup, a.grade, a.direction, a.stop_points, a.target_points))
    return sorted(rows)


def expected(frame, events=None, session=None, day="2026-10-15"):
    closed = generate_trades(frame, events=events, days=[pd.Timestamp(day)])
    return sorted((str(row.signal_time), row.session, row.setup, row.grade, 1 if row.direction == "long" else -1, row.stop_points, row.target_points)
                  for row in closed.itertuples() if row.entry_kind == "market" and (not session or row.session == session))


@pytest.mark.parametrize("body", [20005, 20030])
def test_causal_opening_brackets_match_frozen_synthetic_fixture(body):
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=reference.HIGH_BEFORE, bars=reference.opening_continuation(body))
    engine, actions = stream(frame)
    assert entries(actions) == expected(frame)
    assert entries(actions)
    # It emits at 09:31 before any subsequent candle or eventual exit is visible.
    _, prefix = stream(frame, end=pd.Timestamp("2026-10-15 09:30", tz=reference.NY))
    assert entries(prefix) == entries(actions)


@pytest.mark.parametrize("top,red,after", [
    (20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)]),
    (20024, 20018, [(20018, 20018.5, 20017, 20017), (20017, 20017, 19995, 19996)]),
    (20016, 20012, [(20012, 20012, 19990, 19990)]),
    (20060, 20046, [(20046, 20046.5, 20036, 20037), (20037, 20037, 20025, 20026), (20026, 20027, 20025.5, 20026.5), (20026.5, 20026.5, 20018, 20019), (20019, 20019, 19990, 19992)])
])
def test_reversion_room_and_layering_parity(top, red, after):
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=reference.HIGH_BEFORE, bars=reference.rally_then_red(top, red, after))
    _, actions = stream(frame)
    assert entries(actions) == expected(frame)


def test_all_time_high_displacement_exclusion():
    bars = reference.rally_then_red(20045, 20034, [(20034, 20034.5, 20033, 20033), (20033, 20033, 19990, 19992)])
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", bars=bars)
    _, actions = stream(frame)
    assert entries(actions) == expected(frame) == []


def test_news_and_fomc_parity():
    bars = {"2026-10-15 08:30": (20000, 20000.5, 19960, 19962), "2026-10-15 08:31": (19962, 19963, 19958, 19959),
            "2026-10-15 08:32": (19959, 19966, 19958.5, 19965), "2026-10-15 08:33": (19965, 20010, 19965, 20008),
            "2026-10-15 13:57": (20000, 20002, 20000, 20000), "2026-10-15 13:59": (20000.5, 20000.5, 19999.75, 20000),
            "2026-10-15 14:00": (20000, 20011, 20000, 20010)}
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=reference.HIGH_BEFORE, bars=bars)
    calendar = {"2026-10-15": [(510, "High", "CPI m/m"), (840, "High", "FOMC Statement")]}
    events = pd.DataFrame([{"time": pd.Timestamp("2026-10-15", tz=reference.NY) + pd.Timedelta(minutes=m), "country": "USD", "impact": imp, "title": title} for m, imp, title in calendar["2026-10-15"]])
    _, actions = stream(frame, calendar)
    assert entries(actions) == expected(frame, events)
    assert not [a for a in actions if a.action == "ENTRY" and a.session == "14:00" and a.setup == "continuation"]


def test_no_premature_terminal_exit_at_end_of_prefix():
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 09:32", spikes=reference.HIGH_BEFORE, bars=reference.opening_continuation(20005))
    engine, actions = stream(frame)
    assert len(engine.positions) == 1
    assert not [a for a in actions if a.action == "FLATTEN" and "2026-10-15" in a.time]


def test_overnight_book_emitted_before_crossing_and_cancelled():
    bars = {"2026-10-14 09:30": (20000, 20000, 20000, 20000)}
    for k in range(10):
        p = 20000 + 10 * k
        bars[f"2026-10-14 13:{10+2*k:02}"] = (p, p+12, p, p+10)
        bars[f"2026-10-14 13:{11+2*k:02}"] = (p+10, p+11, p+4, p+10)
    bars["2026-10-14 13:31"] = (20100, 20101, 20099, 20100)
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 09:29", spikes=reference.HIGH_BEFORE, bars=bars)
    _, actions = stream(frame)
    book = [a for a in actions if a.action == "BOOK" and a.time.startswith("2026-10-15T01:30")]
    assert book and all(a.direction == -1 for a in book)
    assert any(a.action == "CANCEL_BOOK" and a.time.startswith("2026-10-15T13:30") for a in actions)


def test_replay_has_identical_decision_ids_and_rejects_revision():
    frame = reference.frame("2026-10-14 09:30", "2026-10-15 09:35", bars=reference.opening_continuation(20005))
    engine, first = stream(frame)
    _, second = stream(frame)
    assert first == second
    last = engine.bars[-1]
    assert engine.on_bar(last) == []
    with pytest.raises(Blocked, match="REVISION"):
        engine.on_bar(Bar(last.time, last.open, last.high+1, last.low, last.close))


def test_frozen_source_hashes():
    verify_frozen(ROOT)


@pytest.mark.parametrize("session,start", [("18:00", "2026-10-14 18:00"), ("20:00", "2026-10-14 20:00"), ("14:00", "2026-10-15 14:00")])
def test_evening_asia_pm_causal_continuations(session, start):
    begin = pd.Timestamp(start)
    stamp = lambda offset: (begin+pd.Timedelta(minutes=offset)).strftime("%Y-%m-%d %H:%M")
    pivot_offset, previous_offset = (-63, -61) if session == "18:00" else (-3, -1)
    bars = {stamp(pivot_offset): (20000,20002,20000,20000), stamp(previous_offset): (20000.5,20000.5,19999.75,20000),
            stamp(0): (19999 if session == "18:00" else 20000,20006,19999,20005), stamp(1): (20005,20006,20004,20005),
            stamp(30): (20005,20050,20005,20045)}
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=reference.HIGH_BEFORE, bars=bars)
    _, actions = stream(frame)
    assert entries(actions, session=session) == expected(frame, session=session)
    assert entries(actions, session=session)


def test_friday_bos_only_reversal_and_one_attempt():
    bars = {"2026-10-16 15:00": (20000,20000,20000,20000),
            "2026-10-16 15:40": (20000,20030,20000,20029),
            "2026-10-16 15:41": (20029,20040,20028,20038),
            "2026-10-16 15:42": (20038,20044,20037,20043),
            "2026-10-16 15:43": (20043,20044,20035,20039),
            "2026-10-16 15:44": (20039,20046,20036,20045),
            "2026-10-16 15:45": (20045,20045,20034,20034),
            "2026-10-16 15:46": (20034,20034,19990,19991)}
    frame = reference.frame("2026-10-14 08:00", "2026-10-16 16:59", spikes={"2026-10-14 10:00":21000}, bars=bars)
    _, actions = stream(frame)
    found = entries(actions, day="2026-10-16", session="fri")
    assert found == expected(frame, session="fri", day="2026-10-16")
    assert len(found) == 1 and found[0][3] == "A+"


def test_scheduled_speech_blocks_new_entries_rest_of_session():
    bars = reference.rally_then_red(20045,20034,[(20034,20034.5,20033,20033),(20033,20033,19990,19992)])
    frame = reference.frame("2026-10-13 08:00", "2026-10-15 16:59", spikes=reference.HIGH_BEFORE, bars=bars)
    calendar = {"2026-10-15": [(580,"High","Chair Speaks")]}
    events = pd.DataFrame([{"time": pd.Timestamp("2026-10-15 09:40",tz=reference.NY), "country":"USD","impact":"High","title":"Chair Speaks"}])
    _, actions = stream(frame,calendar)
    assert entries(actions) == expected(frame, events) == []


def test_profitable_continuation_moves_break_even_at_phase_end():
    bars = reference.opening_continuation(20005)
    bars["2026-10-15 09:33"]=(20005,20010,20005,20010)
    frame=reference.frame("2026-10-14 09:30","2026-10-15 09:34",bars=bars)
    _, actions=stream(frame)
    moves=[a for a in actions if a.action=="BREAKEVEN"]
    assert len(moves)==1 and moves[0].time.startswith("2026-10-15T13:35")
    assert moves[0].reference==next(a.id for a in actions if a.action=="ENTRY")


def test_three_losses_reanchor_and_stop_session_parity():
    bars = {"2026-10-15 09:30": (20000,20000,20000,20000)}
    for start, base in (("09:40",20000), ("09:50",20000), ("10:00",20030)):
        ts = pd.Timestamp("2026-10-15 "+start)
        for i in range(5):
            o=base+9*i
            bars[(ts+pd.Timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M")] = (o,o+9.5,o,o+9)
        bars[(ts+pd.Timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")] = (base+45,base+45.5,base+34,base+34)
        bars[(ts+pd.Timedelta(minutes=6)).strftime("%Y-%m-%d %H:%M")] = (base+34,base+60,base+33,base+59)
        bars[(ts+pd.Timedelta(minutes=7)).strftime("%Y-%m-%d %H:%M")] = (base+59,base+59,base,base)
    # After two losses the third must be A+ (a break of structure), not displacement.
    bars.update({"2026-10-15 10:03": (20067,20069,20066,20068),
                 "2026-10-15 10:04": (20068,20076,20064,20075),
                 "2026-10-15 10:05": (20075,20075,20065,20071),
                 "2026-10-15 10:06": (20071,20072,20063,20063),
                 "2026-10-15 10:07": (20063,20090,20062,20089),
                 "2026-10-15 10:08": (20089,20089,20030,20030)})
    frame = reference.frame("2026-10-13 08:00","2026-10-15 10:10",spikes=reference.HIGH_BEFORE,bars=bars)
    engine, actions = stream(frame)
    assert entries(actions) == expected(frame)
    assert engine.sessions["09:30"].losses_in_row == 3
    assert engine.sessions["09:30"].stopped


def test_holiday_opening_range_filter_and_no_wide_bracket():
    bars = {"2026-11-11 09:27": (20000,20002,20000,20000), "2026-11-11 09:29": (20000.5,20000.5,19999.75,20000),
            "2026-11-11 09:30": (20000,20031,20000,20030), "2026-11-11 09:31": (20030,20031,20029,20030),
            "2026-11-11 10:20": (20030,20110,20030,20109)}
    frame = reference.frame("2026-11-09 08:00","2026-11-11 16:59",spikes={"2026-11-09 10:00":21000},bars=bars)
    _, actions = stream(frame)
    found = entries(actions,day="2026-11-11")
    assert found == expected(frame,day="2026-11-11")
    assert found and found[0][-2:] == (25,38)
