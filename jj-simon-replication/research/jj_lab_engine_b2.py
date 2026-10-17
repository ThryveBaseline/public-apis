"""The learning lab's engine, b2 (docs/research/jj_lab.md): research/jj_lab_engine_b1.py plus a journal of every
decision the rules make, and a wider set of settings for whole-system challengers. At its defaults it gives JJ system
v1's trades exactly, with or without the journal (tests/test_jj_learn.py); the live JJ stream never runs this file.

The journal (generate_trades(..., journal=[])) records, for each trading day:
  session   each session's opening: its fair value, opening candle, and (18:00) the gap
  anchor    every change of a session's fair value, with the reason
  signal    every trigger the rules saw (a break of structure, or a displacement toward fair value, inside a session
            window), whether it was taken, and if not, the rule that stopped it
  order     every overnight order placed
  manage    every break-even move and every early exit decision, with the reason
Below, the b1 and frozen engines' own descriptions.

The background lab's engine, batch 1 (docs/research/jj_lab.md): a copy of research/jj_system.py (JJ system v1,
frozen) with dials for the lab's one-setting versions. At its defaults it gives JJ system v1's trades exactly
(tests/test_jj_lab.py); the live JJ stream never runs this file. Below, the frozen engine's own description.

JJ Simon's system, his whole trading day, as one forward paper stream (docs/research/jj_system_v1.md).

Every rule here is his, from his own videos, at his latest stated version (by recording date where it is known,
otherwise upload date). Where he gives no number, the value is the one his own words imply; the spec lists each with
the quote. Nothing here was chosen, tuned or dropped on any backtest. This module is separate from fpt/ and
research/engine.py, which stay frozen.

The stream is his whole signal stream: every trade his rules take across the day, each position standing for one of
his accounts (he layers accounts, so positions can overlap). R is per trade at his evaluation sizing: two NQ on the
25/38 bracket, four on 12.5/19, one on 50/76 (the same dollar risk), with $2.50 a side per contract and 0.25 points
of slippage on market fills and stops, as every other stream here.

The trading day is the exchange's, 18:00 ET the evening before to 17:00 ET. Its sessions, in order: the 18:00 reopen,
20:00 Asia, the overnight book (21:30 to 09:29), 08:30 news (release days), 09:30 New York (with 10:00 releases),
14:00 New York PM (FOMC days included), and Friday's last hour (15:00-15:59). Positions run to their stop or target and
close at 16:10 ET at the latest (the firm's end of day: Topstep closes positions at 3:10 PM CT).

usage: generate_trades(bars, events=calendar) with 1-minute NQ bars (America/New_York index; open, high, low, close)
and the USD economic calendar (research/news_calendar.py); returns one row per closed position.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY  # noqa: E402

TICK = 0.25
VERSION = "jj_lab_engine_b2"


@dataclass(frozen=True)
class JJConfig:
    """His numbers (docs/research/jj_system_v1.md gives the source of each)."""
    stop: float = 25.0  # "3825": evaluations always 1:1.5
    target: float = 38.0
    half_stop: float = 12.5  # 15 to 30 points of room: "12519", double the contracts
    half_target: float = 19.0
    wide_stop: float = 50.0  # an opening candle body over 25 points: "5076", half the contracts
    wide_target: float = 76.0
    big_open_body: float = 25.0
    room_full: float = 30.0  # "I need at least 30 points in my favor to take this eval trade for a 2538"
    room_half: float = 15.0  # "15 to 30 points in my favor ... 19 points"; 14.75 rejected
    unfair_move: float = 38.0  # a continuation that "didn't make my 38 point unfair move" goes to break-even
    continuation_minutes: int = 5
    stall_candles: int = 2
    max_reversion_losses: int = 3  # three losing reversion attempts in a row end the session's reversions
    reanchor_after_losses: int = 2  # losing reversions move fair value to the consolidation (after the second in his latest example)
    bos_only_after_losses: int = 2  # "after two losses, I usually expect a structural breakdown"
    layer_progress: float = 0.5  # "After the first one is halfway to take profit, boom, there goes the next one"
    htf_hours: tuple = (6, 12)  # "inverting whatever happened for the previous 6 to 12 hours"
    reanchor_minutes: int = 30  # "There's the 30 minutes of consolidation"
    session_minutes: int = 90  # "First 90 minutes of every single session"; "I'll trade for 90 minutes. So, until 9:30."
    evening_continuations: int = 1  # "6 p.m. one continuation, one reversion. Asian session, same thing."
    evening_reversions: int = 1
    firm_close: str = "16:10"
    contracts: int = 2  # two NQ on 25/38 at a 50K evaluation
    point_value: float = 20.0
    commission_side: float = 2.50
    slippage: float = 0.25


@dataclass(frozen=True)
class LabConfig(JJConfig):
    """JJConfig plus the lab's dials; every default is JJ system v1."""
    evening_force_half: bool = False  # evening reversions always take 12.5/19 ("take profits of 19 points instead of 38")
    fourth_aplus: bool = False  # after three losing reversion attempts, one more on a break of structure (his April rule)
    book: bool = True  # the overnight orders
    book_max_levels: int | None = None  # only the nearest N overnight levels
    news_cont_body: float | None = None  # continue the news candle when its body is over this ("unless it's a huge candle")
    evening_max_gap: float | None = None  # no 18:00 continuation into a gap larger than this ("into the huge gap")
    pm_minutes: int | None = None  # the 14:00 session's length (None: session_minutes)
    allow_grade_a: bool = True  # displacement-only (grade A) reversions
    layering: bool = True  # further accounts on an attempt
    half_in_ny: bool = True  # 12.5/19 in the New York sessions ("Never less than 25 points in the New York session")
    cont_needs_htf: bool = False  # continuations only with the higher-time-frame bias (his July version)
    # b2: settings for whole-system challengers (every default is JJ system v1)
    sessions_off: tuple = ()  # sessions not traded: "18:00", "20:00", "book", "news", "09:30", "14:00", "fri"
    filters_off: tuple = ()  # rules switched off: "grade_b", "ath", "after_two_losses", "three_losses", "gap_rule",
    # "cont_htf_strong", "cont_drawdown", "band"
    mgmt_off: tuple = ()  # management switched off: "be_open", "be_release", "be_cont_unfair", "be_evening38", "flip_exit"
    rev_bracket: tuple = ()  # (session, stop, target) entries: that session's reversions use this bracket
    cont_bracket: tuple = ()  # (session, stop, target) entries: that session's continuations use this bracket

    def __post_init__(self) -> None:
        """A misspelled name would silently do nothing: refuse it."""
        bad = [x for x in self.sessions_off if x not in SESSIONS] + [x for x in self.filters_off if x not in FILTERS] + \
              [x for x in self.mgmt_off if x not in MGMT] + [e[0] for e in tuple(self.rev_bracket) + tuple(self.cont_bracket) if e[0] not in SESSIONS]
        if bad:
            raise ValueError(f"unknown names in the settings: {bad}")
        for e in tuple(self.rev_bracket) + tuple(self.cont_bracket):
            if len(e) != 3 or not (float(e[1]) > 0 and float(e[2]) > 0):
                raise ValueError(f"a bracket is (session, stop, target) with positive numbers: {e}")


SESSIONS = ("18:00", "20:00", "book", "news", "09:30", "14:00", "fri")
FILTERS = ("grade_b", "ath", "after_two_losses", "three_losses", "gap_rule", "cont_htf_strong", "cont_drawdown", "band")
MGMT = ("be_open", "be_release", "be_cont_unfair", "be_evening38", "flip_exit")


TRADE_COLUMNS = ["trading_day", "session", "setup", "grade", "direction", "signal_time", "entry_time", "exit_time", "entry", "stop",
                 "target", "exit", "exit_reason", "stop_points", "target_points", "contracts", "pnl_dollars", "r", "attempt", "layer",
                 "entry_kind", "anchor", "ambiguous_bar"]
NEWS_IMPACT = ("High", "Medium")  # red and orange folder; orange "if it moves", which the room rules test
SPEECH_WORDS = ("Speaks", "Testifies", "Press Conference")
FOMC_WORDS = ("FOMC", "Federal Funds Rate")
# His "bank holidays" (traded only on an influx at the open, and 38 not 76): the Federal Reserve holidays on which the
# stock market opens, and the exchange holidays with an early halt (research/forward.HOLIDAY_HALTS), to the forward
# calendar's end (2027-10-05).
BANK_HOLIDAYS = {"2026-10-12", "2026-11-11", "2026-11-26", "2027-01-18", "2027-02-15", "2027-05-31", "2027-06-18", "2027-07-05",
                 "2027-09-06"}


def _m(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def trading_days(index: pd.DatetimeIndex) -> np.ndarray:
    """The exchange trading day of each bar (18:00 ET the evening before to 17:00 ET), as a naive date."""
    ny = index.tz_convert(NY)
    return (ny.tz_localize(None) + pd.Timedelta(hours=6)).normalize().to_numpy()


@dataclass
class Session:
    name: str
    start: int  # bar index of the opening candle
    end: int  # last signal bar (inclusive)
    cont_end: int  # last continuation signal bar (inclusive); -1: no continuation phase
    anchor: float
    kind: str  # "evening", "day", "news", "friday"
    open_dir: int = 0
    open_body: float = 0.0
    stalled: bool = False
    against: int = 0
    cont_entries: int = 0
    attempts: int = 0
    losses_in_row: int = 0
    stopped: bool = False
    blocked_from: int = 10**12  # a scheduled speech: no new entry from this bar
    exc_up: float = 0.0  # the move away from fair value since price was last near it
    exc_dn: float = 0.0
    a5_from: str | None = None  # the session whose anchor this open is tested against (first move away: the new open)
    a5_old: float | None = None
    a5_done: bool = True
    cont_max: int | None = None
    rev_max: int | None = None
    aplus_only: bool = False
    holiday: bool = False
    ws: int = 0  # structure counts from this bar (the previous 09:30 open before the session)
    ath: float = np.inf  # the all-time high before the session
    disabled: bool = False
    fourth_used: bool = False


@dataclass
class Pos:
    session: str
    setup: str
    grade: str
    d: int
    signal_i: int
    entry_i: int
    entry: float
    stop: float
    target: float
    stop_pts: float
    target_pts: float
    n: int
    attempt: int
    layer: bool
    kind: str  # "market", or "stop" for an overnight order that fills inside its bar
    anchor: float
    evening38: bool = False
    exit_next: bool = False


def _contracts(cfg: JJConfig, stop_pts: float) -> int:
    if stop_pts == cfg.wide_stop:
        return max(1, cfg.contracts // 2)
    if stop_pts == cfg.half_stop:
        return cfg.contracts * 2
    return cfg.contracts


def _record(cfg: JJConfig, p: Pos, exit_px: float, reason: str, exit_i: int, times, ambiguous: bool, day) -> dict:
    pnl = (exit_px - p.entry) * p.d * cfg.point_value * p.n - 2 * cfg.commission_side * p.n
    risk = p.stop_pts * cfg.point_value * p.n
    return {"trading_day": day, "session": p.session, "setup": p.setup, "grade": p.grade, "direction": "long" if p.d > 0 else "short",
            "signal_time": times[p.signal_i], "entry_time": times[p.entry_i], "exit_time": times[exit_i], "entry": p.entry, "stop": p.stop,
            "target": p.target, "exit": exit_px, "exit_reason": reason, "stop_points": p.stop_pts, "target_points": p.target_pts,
            "contracts": p.n, "pnl_dollars": pnl, "r": pnl / risk, "attempt": p.attempt, "layer": p.layer, "entry_kind": p.kind,
            "anchor": p.anchor, "ambiguous_bar": ambiguous}


def events_by_day(events: pd.DataFrame | None, days) -> dict:
    """USD calendar events per trading day: {day: [(minute of day, impact, title)]}."""
    out = {pd.Timestamp(d): [] for d in days}
    if events is None or events.empty:
        return out
    ev = events[events["country"].astype(str).str.upper() == "USD"].reset_index(drop=True)
    t = pd.DatetimeIndex(pd.to_datetime(ev["time"], utc=True)).tz_convert(NY)
    td = (t.tz_localize(None) + pd.Timedelta(hours=6)).normalize()
    for k in range(len(ev)):
        if td[k] in out:
            out[td[k]].append((t[k].hour * 60 + t[k].minute, str(ev["impact"].iloc[k]), str(ev["title"].iloc[k])))
    return out


def generate_trades(bars: pd.DataFrame, cfg: LabConfig | None = None, events: pd.DataFrame | None = None, days=None,
                    prior_high: float = -np.inf, journal: list | None = None) -> pd.DataFrame:
    """His whole day on every trading day of `bars` (or only `days`) that has a previous 09:30 bar for its structure
    and the evening's references. `events` is the USD calendar (columns time, country, impact, title); without it no
    news session runs. `prior_high` is the all-time high before the first bar (the bars loaded may start late). Bars
    exist only for minutes with trades: a session opens on its first bar within 5 minutes of its time, an order fills
    at the next bar's open, and anything due at a time happens at the close of the last bar before it. One row per
    closed position."""
    cfg = cfg or LabConfig()
    rev_br = {s_: (float(a_), float(b_)) for s_, a_, b_ in cfg.rev_bracket}
    cont_br = {s_: (float(a_), float(b_)) for s_, a_, b_ in cfg.cont_bracket}

    def jot(event: str, **kw) -> None:
        if journal is not None:
            journal.append({"event": event, **kw})
    bars = bars.sort_index()
    if bars.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    ny = bars.index.tz_convert(NY)
    o, h, l, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(bars)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    mins = (bars.index.as_unit("ns").asi8 // 60_000_000_000).astype(np.int64)  # epoch minutes
    td = trading_days(bars.index)
    # swing pivots: a wick beyond the one candle before and the one after (strict), known when the next bar closes
    sh = np.zeros(n, dtype=bool)
    sl = np.zeros(n, dtype=bool)
    if n >= 3:
        sh[1:-1] = (h[1:-1] > h[:-2]) & (h[1:-1] > h[2:])
        sl[1:-1] = (l[1:-1] < l[:-2]) & (l[1:-1] < l[2:])
    run_high = np.maximum(np.maximum.accumulate(h), prior_high)
    all_days = [pd.Timestamp(d) for d in pd.unique(td)]
    want = set(pd.DatetimeIndex(days)) if days is not None else None
    ev_days = events_by_day(events, all_days)
    opens_0930 = np.flatnonzero(mod == 570)
    firm_close = _m(cfg.firm_close)
    grace = 5  # a session opens on its first bar within this many minutes of its time
    trades: list[dict] = []

    def epoch(date: pd.Timestamp, minute: int) -> int:
        """Epoch minute of a New York wall time on a calendar date."""
        return int((date + pd.Timedelta(minutes=minute)).tz_localize(NY).value // 60_000_000_000)

    def htf_day(t: int) -> int:
        """Daytime higher-time-frame bias: the previous 6 and 12 hours' net move, inverted; 0 when they disagree."""
        signs = []
        for hrs in cfg.htf_hours:
            j = np.searchsorted(mins, mins[t] - hrs * 60, side="right") - 1
            if j < 0:
                return 0
            signs.append(int(np.sign(c[t] - c[j])))
        return -signs[0] if signs[0] != 0 and all(x == signs[0] for x in signs) else 0

    for day in all_days:
        if want is not None and day not in want:
            continue
        idx = np.flatnonzero(td == day.to_datetime64())
        s, e = int(idx[0]), int(idx[-1]) + 1
        prev930 = opens_0930[opens_0930 < s]
        if not len(prev930):
            continue
        w0 = int(prev930[-1])  # the previous 09:30 open: "all the way back down to 9:30"
        today930 = opens_0930[(opens_0930 >= s) & (opens_0930 < e)]
        w_today = int(today930[0]) if len(today930) else w0
        am_prev = o[w0]  # "9:30 of that morning"
        prev_close = c[s - 1]
        eve = day - pd.Timedelta(days=1)
        evs = ev_days.get(day, [])
        is_speech = [any(w in title for w in SPEECH_WORDS) for _, _, title in evs]
        news_min = [mm for (mm, imp, _), sp in zip(evs, is_speech) if imp in NEWS_IMPACT and not sp and mm in (_m("08:15"), _m("08:30"))]
        release_t = {epoch(day, mm) for (mm, imp, _), sp in zip(evs, is_speech)
                     if imp in NEWS_IMPACT and not sp and mm in (_m("08:15"), _m("08:30"), _m("09:45"), _m("10:00"), _m("14:00"))}
        ten_switch = any(mm == _m("10:00") and imp in NEWS_IMPACT and not sp for (mm, imp, _), sp in zip(evs, is_speech))
        fomc = any(mm == _m("14:00") and imp == "High" and any(w in title for w in FOMC_WORDS) for mm, imp, title in evs)
        speeches = sorted(epoch(day, mm) for (mm, imp, _), sp in zip(evs, is_speech) if imp == "High" and sp)
        holiday = day.strftime("%Y-%m-%d") in BANK_HOLIDAYS

        # ---- the day's sessions ----
        sess: dict[str, Session] = {}
        nominal: dict[str, int] = {}

        def add(name: str, when: int, length: int, kind: str, cont: bool, ws: int, **kw) -> None:
            i = int(np.searchsorted(mins, when, side="left"))
            if not (s <= i < e and mins[i] < when + grace):
                return
            end = int(min(e, np.searchsorted(mins, when + length - 1, side="right")) - 1)
            ce = int(min(e, np.searchsorted(mins, when + cfg.continuation_minutes - 1, side="right")) - 1) if cont else -1
            sess[name] = Session(name, i, end, ce, o[i], kind, holiday=holiday, ws=ws, ath=run_high[i - 1], **kw)
            nominal[name] = when

        add("18:00", epoch(eve, _m("18:00")), 120, "evening", True, w0, cont_max=cfg.evening_continuations, rev_max=cfg.evening_reversions)
        add("20:00", epoch(eve, _m("20:00")), cfg.session_minutes, "evening", True, w0, cont_max=cfg.evening_continuations,
            rev_max=cfg.evening_reversions, a5_from="18:00", a5_done=False)
        if news_min:
            mm = min(news_min)
            add("news", epoch(day, mm), _m("09:30") - mm, "news", cfg.news_cont_body is not None, w0)  # reversions to the pre-news price only
        add("09:30", epoch(day, _m("09:30")), cfg.session_minutes, "day", True, w0)
        # FOMC is news: no continuation of the news candle ("I don't really do continuation of news anymore")
        add("14:00", epoch(day, _m("14:00")), cfg.pm_minutes or cfg.session_minutes, "day", not fomc, w_today, a5_from=None if fomc else "09:30", a5_done=fomc)
        if day.dayofweek == 4:
            add("fri", epoch(day, _m("15:00")), 60, "friday", False, w_today, rev_max=1, aplus_only=True)
        for sp in speeches:
            b = int(np.searchsorted(mins, sp, side="left"))
            for ss in sess.values():
                if ss.start <= b <= ss.end:
                    ss.blocked_from = min(ss.blocked_from, b)
        be_open_t = {nominal[k] for k, ss in sess.items() if ss.kind != "friday"}
        be_times = (set() if "be_open" in cfg.mgmt_off else be_open_t) | (set() if "be_release" in cfg.mgmt_off else release_t)
        t2130, t0930, t1000 = epoch(eve, _m("21:30")), epoch(day, _m("09:30")), epoch(day, _m("10:00"))

        # ---- structure since the previous 09:30 open ----
        piv_hi: list[list] = []  # [index, level, alive]
        piv_lo: list[list] = []
        bos_max = {1: np.full(e - w0, -1), -1: np.full(e - w0, -1)}  # the latest swing a bar's close broke (-1: none)
        wick_max = {1: np.full(e - w0, -1), -1: np.full(e - w0, -1)}  # the latest swing a bar's wick passed without a close

        def structure(t: int) -> None:
            j = t - 1
            if j - 1 >= w0:
                if sh[j]:
                    piv_hi.append([j, h[j], True])
                if sl[j]:
                    piv_lo.append([j, l[j], True])
            for d, pivs in ((1, piv_hi), (-1, piv_lo)):
                for p in pivs:
                    if p[2]:
                        if (c[t] - p[1]) * d > 0:
                            p[2] = False
                            bos_max[d][t - w0] = max(bos_max[d][t - w0], p[0])
                        elif (h[t] if d > 0 else l[t]) * d > p[1] * d:
                            wick_max[d][t - w0] = max(wick_max[d][t - w0], p[0])

        def bos(d: int, t: int, ws: int) -> bool:
            return t >= w0 and bos_max[d][t - w0] >= ws

        for t in range(w0, s):
            structure(t)

        def disp(t: int, d: int, ws: int) -> bool:
            """A displacement in direction d: a body larger than the previous, opposite-colour candle's and a close beyond
            its wick; two or three same-colour candles may count together against the one before them. Not when the
            displaced candle broke structure the other way, and not a candle that reached structure and failed to close
            through it."""
            if t - 1 < w0 or bos(-d, t - 1, ws):
                return False
            if wick_max[d][t - w0] >= ws and not bos(d, t, ws):
                return False
            for k in (1, 2, 3):
                f = t - k + 1  # the group's first candle
                pv = f - 1
                if pv < w0 or any(np.sign(c[x] - o[x]) != d for x in range(f, t + 1)):
                    break
                if np.sign(c[pv] - o[pv]) != -d:
                    continue
                if bos(-d, pv, ws):
                    return False
                if (c[t] - o[f]) * d > abs(c[pv] - o[pv]) and (c[t] > h[pv] if d > 0 else c[t] < l[pv]):
                    return True
            return False

        open_pos: list[Pos] = []
        pending: list[Pos] = []
        book: list[dict] = []
        first_of: dict[tuple, Pos] = {}  # (session, attempt) -> the attempt's first position
        counter = [0]

        def new_attempt() -> int:
            counter[0] += 1
            return counter[0]

        def set_anchor(ss: Session, value: float, why: str = "", t: int = -1) -> None:
            if journal is not None and value != ss.anchor:
                jot("anchor", day=day, session=ss.name, time=ny[t] if t >= 0 else None, old=float(ss.anchor), new=float(value), why=why)
            ss.anchor = value
            ss.exc_up = ss.exc_dn = 0.0

        def close(p: Pos, px: float, reason: str, t: int, amb: bool = False) -> None:
            trades.append(_record(cfg, p, px, reason, t, ny, amb, day))
            open_pos.remove(p)
            ss = sess.get(p.session)
            if ss is None or p.setup != "reversion" or first_of.get((p.session, p.attempt)) is not p:
                return
            if reason == "stop":
                ss.losses_in_row += 1
                if ss.losses_in_row >= cfg.reanchor_after_losses:
                    lo = max(w0, t - cfg.reanchor_minutes + 1)
                    set_anchor(ss, (h[lo:t + 1].max() + l[lo:t + 1].min()) / 2, "after losses", t)  # "adjusting fair price to this consolidation now"
                if ss.losses_in_row >= cfg.max_reversion_losses:
                    ss.stopped = True
            elif reason == "target":
                ss.losses_in_row = 0

        def bracket(room: float, moved: float, ss: Session):
            half_ok = cfg.half_in_ny or ss.kind == "evening"
            if cfg.evening_force_half and ss.kind == "evening":
                return (cfg.half_stop, cfg.half_target) if room >= cfg.room_half and moved > cfg.room_half else None
            if room >= cfg.room_full and moved > cfg.target:
                return cfg.stop, cfg.target
            if half_ok and room >= cfg.room_half and moved > cfg.room_half:
                return cfg.half_stop, cfg.half_target
            return None

        def in_profit(p: Pos, t: int) -> bool:
            return (c[t] - p.entry) * p.d > 0 and (p.stop - p.entry) * p.d < 0

        for t in range(s, e):
            can_fill = t + 1 < e and not (firm_close <= mod[t + 1] < _m("18:00"))
            # ---- 1. fills and exits at this bar's open ----
            for p in pending:
                p.entry_i, p.entry = t, o[t] + p.d * cfg.slippage
                p.stop, p.target = p.entry - p.d * p.stop_pts, p.entry + p.d * p.target_pts
                open_pos.append(p)
            pending = []
            for p in [q for q in open_pos if q.exit_next]:
                close(p, o[t] - p.d * cfg.slippage, "exit_signal", t)
            filled_now = []
            for b in [x for x in book if x["active"]]:
                d = b["d"]
                if (d < 0 and l[t] < b["level"]) or (d > 0 and h[t] > b["level"]):
                    px = (min(o[t], b["level"]) if d < 0 else max(o[t], b["level"])) + d * cfg.slippage
                    p = Pos("book", "overnight", "A+", d, t, t, px, px - d * b["stop"], px + d * b["target"], b["stop"], b["target"],
                            _contracts(cfg, b["stop"]), new_attempt(), False, "stop", b["anchor"])
                    b["active"] = False
                    open_pos.append(p)
                    filled_now.append(p)
            # ---- 2. stops and targets inside the bar (the stop first when both are touched) ----
            for p in list(open_pos):
                d = p.d
                if p in filled_now:  # filled inside this bar: only its stop can still be reached here
                    if (h[t] >= p.stop) if d < 0 else (l[t] <= p.stop):
                        close(p, p.stop - d * cfg.slippage, "stop", t)
                    continue
                hit_s = (l[t] <= p.stop) if d > 0 else (h[t] >= p.stop)
                hit_t = (h[t] >= p.target) if d > 0 else (l[t] <= p.target)
                if hit_s:
                    px = (min(o[t], p.stop) if d > 0 else max(o[t], p.stop)) - d * cfg.slippage
                    close(p, px, "breakeven" if (p.stop - p.entry) * d >= 0 else "stop", t, bool(hit_t))
                elif hit_t:
                    close(p, p.target, "target", t)
            # ---- 3. structure at the close ----
            structure(t)
            # ---- 4. the sessions at this bar ----
            for ss in sess.values():
                if t == ss.start:
                    ss.open_dir = int(np.sign(c[t] - o[t]))
                    ss.open_body = abs(c[t] - o[t])
                    jot("session", day=day, session=ss.name, kind=ss.kind, time=ny[t], end=ny[ss.end], anchor=float(ss.anchor),
                        open_dir=ss.open_dir, open_body=float(ss.open_body), gap=float(o[t] - prev_close) if ss.name == "18:00" else None,
                        news=bool(news_min), release_day=bool(release_t) or bool(fomc), holiday=bool(ss.holiday))
                    if ss.name == "09:30" and ss.holiday:  # a bank holiday is traded only on an influx at the open
                        prior = (mins >= nominal["09:30"] - 60) & (mins < nominal["09:30"])
                        rng = (h - l)[prior]
                        ss.disabled = not (len(rng) and h[t] - l[t] > np.median(rng))
                    if not ss.a5_done:
                        ref = sess.get(ss.a5_from)
                        if ref is None:
                            ss.a5_done = True
                        else:
                            ss.a5_old = ref.anchor
                if ss.cont_end >= 0 and ss.start < t <= ss.cont_end and not ss.stalled and ss.open_dir != 0:
                    ss.against = ss.against + 1 if np.sign(c[t] - o[t]) == -ss.open_dir else 0
                    if ss.against >= cfg.stall_candles:
                        ss.stalled = True
                if not ss.a5_done and ss.start <= t <= ss.cont_end:
                    away = int(np.sign(o[ss.start] - ss.a5_old))
                    for dd in (1, -1):
                        if bos(dd, t, ss.ws):  # the first move: away from the earlier anchor makes the new open fair
                            set_anchor(ss, o[ss.start] if away in (0, dd) else ss.a5_old, "first move", t)
                            ss.a5_done = True
                            break
                    if not ss.a5_done and t == ss.cont_end:
                        set_anchor(ss, ss.a5_old, "no move away", t)  # no move away: the earlier anchor stays fair
                        ss.a5_done = True
            am = sess.get("09:30")
            if am is not None and "news" in sess and t == am.cont_end:
                pre = o[sess["news"].start]  # a news day: the pre-news price stays fair if the opening move heads back to it
                set_anchor(am, pre if abs(c[t] - pre) < abs(o[am.start] - pre) else o[am.start], "news day open", t)
            if am is not None and ten_switch and am.start < t <= am.end and mins[t - 1] < t1000 <= mins[t]:
                set_anchor(am, o[t], "10:00 release", t)  # news at 10: the pre-10:00 price is fair
            for ss in sess.values():
                if ss.start <= t <= ss.end:
                    if abs(c[t] - ss.anchor) < cfg.room_half:
                        ss.exc_up = ss.exc_dn = 0.0  # back near fair value: wait for another move away
                    else:
                        ss.exc_up = max(ss.exc_up, h[t] - ss.anchor)
                        ss.exc_dn = max(ss.exc_dn, ss.anchor - l[t])
            # ---- 5. management at the close ----
            if t + 1 < e and any(mins[t] < x <= mins[t + 1] for x in be_times):
                why = "be_open" if any(mins[t] < x <= mins[t + 1] for x in be_open_t) else "be_release"
                for p in open_pos:
                    if in_profit(p, t):
                        p.stop = p.entry  # break-even into a new session or a release, when in profit
                        jot("manage", day=day, session=p.session, setup=p.setup, signal_time=ny[p.signal_i], time=ny[t], what=why)
            for p in open_pos:
                ss = sess.get(p.session)
                if p.setup == "continuation" and ss is not None:
                    if "flip_exit" not in cfg.mgmt_off and (bos(-p.d, t, ss.ws) or disp(t, -p.d, ss.ws)):
                        if not p.exit_next:
                            jot("manage", day=day, session=p.session, setup=p.setup, signal_time=ny[p.signal_i], time=ny[t], what="flip_exit")
                        p.exit_next = True  # the bias flipped: out at the next open
                    elif ss.cont_end >= 0 and t <= ss.cont_end and (t == ss.cont_end or ss.stalled):
                        best = (h[ss.start:t + 1].max() - o[ss.start]) if p.d > 0 else (o[ss.start] - l[ss.start:t + 1].min())
                        if "be_cont_unfair" not in cfg.mgmt_off and best < cfg.unfair_move and in_profit(p, t):
                            p.stop = p.entry  # the unfair move never made 38 points
                            jot("manage", day=day, session=p.session, setup=p.setup, signal_time=ny[p.signal_i], time=ny[t], what="be_cont_unfair")
                if "be_evening38" not in cfg.mgmt_off and p.evening38 and ss is not None and bos(-p.d, t, ss.ws) and in_profit(p, t):
                    p.stop = p.entry
                    jot("manage", day=day, session=p.session, setup=p.setup, signal_time=ny[p.signal_i], time=ny[t], what="be_evening38")
            # ---- 6. the firm's end of day ----
            if mod[t] < firm_close and (t == e - 1 or mod[t + 1] >= firm_close):
                for p in list(open_pos):
                    close(p, c[t] - p.d * cfg.slippage, "firm_close", t)
                for b in book:
                    b["active"] = False
                continue
            if t == e - 1:
                for p in list(open_pos):
                    close(p, c[t] - p.d * cfg.slippage, "day_end", t)
                continue
            # ---- 7. the overnight book: placed at 21:30 toward 9:30 of that morning, cancelled at 09:30 ----
            if cfg.book and "book" not in cfg.sessions_off and mins[t] < t2130 <= mins[t + 1]:
                d = int(np.sign(am_prev - c[t]))
                if d != 0:
                    levels = sorted({p[1] for p in (piv_lo if d < 0 else piv_hi) if p[2] and min(am_prev, c[t]) < p[1] < max(am_prev, c[t])})
                    if cfg.book_max_levels is not None:
                        levels = sorted(levels, key=lambda x: abs(c[t] - x))[:cfg.book_max_levels]
                    for lv in levels:
                        room = abs(am_prev - lv)
                        br = (cfg.stop, cfg.target) if room >= cfg.room_full else ((cfg.half_stop, cfg.half_target) if room >= cfg.room_half else None)
                        if br:
                            book.append({"level": lv, "d": d, "stop": br[0], "target": br[1], "anchor": am_prev, "active": True})
                            jot("order", day=day, session="book", time=ny[t], level=float(lv), d=d, stop=br[0], target=br[1], anchor=float(am_prev))
            if mins[t] < t0930 <= mins[t + 1]:
                for b in book:
                    b["active"] = False
            # ---- 8. signals at the close, filled at the next bar's open ----
            # Every rule a signal fails is recorded; the first, in the live system's order, is the reason it was passed.
            for ss in sess.values():
                if not ss.start <= t <= ss.end:
                    continue
                gate = ("no next bar" if not can_fill else "speech" if t >= ss.blocked_from else "holiday, no influx" if ss.disabled
                        else "session off" if ss.name in cfg.sessions_off else None)
                if ss.cont_end >= 0 and t <= ss.cont_end and not ss.stalled:  # the continuation phase
                    d = ss.open_dir
                    if d == 0 or not bos(d, t, ss.ws):
                        continue
                    htf = int(np.sign(am_prev - c[t])) if ss.kind == "evening" else htf_day(t)
                    mine = [p for p in open_pos if p.session == ss.name and p.setup == "continuation"]
                    gap = o[ss.start] - prev_close
                    checks = [
                        ("continuation limit", ss.cont_max is not None and ss.cont_entries >= ss.cont_max),
                        ("news candle not huge", ss.kind == "news" and cfg.news_cont_body is not None and ss.open_body <= cfg.news_cont_body),
                        ("against the bias", cfg.cont_needs_htf and htf == -d),
                        ("away from the gap", ss.name == "18:00" and "gap_rule" not in cfg.filters_off and abs(gap) >= TICK and int(np.sign(-gap)) != d),
                        ("gap too big", ss.name == "18:00" and cfg.evening_max_gap is not None and abs(gap) > cfg.evening_max_gap),
                        ("against the bias, not strong", ss.name != "18:00" and ss.kind == "day" and "cont_htf_strong" not in cfg.filters_off
                         and htf == -d and not disp(t, d, ss.ws)),
                        ("layering off", bool(mine) and not cfg.layering),
                        ("earlier one in drawdown", "cont_drawdown" not in cfg.filters_off and any((c[t] - p.entry) * p.d < 0 for p in mine)),
                    ]
                    fails = ([gate] if gate else []) + [name for name, bad in checks if bad]
                    wide = ss.open_body > cfg.big_open_body and not ss.holiday
                    st, tg = cont_br.get(ss.name, (cfg.wide_stop, cfg.wide_target) if wide else (cfg.stop, cfg.target))
                    jot("signal", day=day, session=ss.name, kind=ss.kind, setup="continuation", d=d, grade="A+", time=ny[t], index=int(t),
                        close=float(c[t]), anchor=float(ss.anchor), room=float(abs(ss.anchor - c[t])), moved=None, htf=htf,
                        ath=bool(h[ss.start:t + 1].max() >= ss.ath), losses=ss.losses_in_row, layer=bool(mine), stop=st, target=tg,
                        taken=not fails, reason=fails[0] if fails else "taken", fails=fails)
                    if fails:
                        continue
                    ss.cont_entries += 1
                    pending.append(Pos(ss.name, "continuation", "A+", d, t, -1, np.nan, np.nan, np.nan, st, tg, _contracts(cfg, st),
                                       new_attempt(), bool(mine), "market", ss.anchor, evening38=ss.kind == "evening" and tg == cfg.target))
                    continue
                d = int(np.sign(ss.anchor - c[t]))
                if d == 0:
                    continue
                raw = "A+" if bos(d, t, ss.ws) else ("A" if disp(t, d, ss.ws) else None)
                if raw is None:
                    continue
                room = abs(ss.anchor - c[t])
                moved = ss.exc_up if d < 0 else ss.exc_dn
                htf = int(np.sign(am_prev - c[t])) if ss.kind == "evening" else htf_day(t)
                ath = bool(h[ss.start:t + 1].max() >= ss.ath)
                mine = [p for p in open_pos if p.session == ss.name and p.setup == "reversion" and p.d == d]
                stopped = ss.stopped and "three_losses" not in cfg.filters_off
                fourth_ok = cfg.fourth_aplus and not ss.fourth_used
                grade = raw if raw == "A+" or cfg.allow_grade_a else None
                br0 = bracket(room, np.inf if "band" in cfg.filters_off else moved, ss)
                lastp = max(mine, key=lambda p: p.entry_i) if mine else None
                layer_off = bool(mine) and (not cfg.layering or stopped)
                checks = [
                    ("three losses in a row", stopped and not fourth_ok),
                    ("displacement entries off", grade is None),
                    ("fourth attempt needs A+", stopped and fourth_ok and grade != "A+"),
                    ("break of structure only", raw != "A+" and ss.aplus_only),
                    ("two losses: break of structure only", raw != "A+" and "after_two_losses" not in cfg.filters_off
                     and ss.losses_in_row >= cfg.bos_only_after_losses),
                    ("all-time high: break of structure only", d < 0 and raw != "A+" and "ath" not in cfg.filters_off and ath),
                    ("biases opposed (grade B)", "grade_b" not in cfg.filters_off and htf == -d),
                    ("under 15 points of room", br0 is None and room < cfg.room_half),
                    ("no move away first", br0 is None and room >= cfg.room_half),
                    ("layering off", layer_off),
                    ("last one not halfway", bool(mine) and not layer_off and (c[t] - lastp.entry) * d < cfg.layer_progress * lastp.target_pts),
                    ("same level", bool(mine) and not layer_off and any(abs(c[t] - p.entry) < TICK for p in mine)),
                    ("attempt limit", not mine and ss.rev_max is not None and ss.attempts >= ss.rev_max),
                ]
                fails = ([gate] if gate else []) + [name for name, bad in checks if bad]
                br = rev_br.get(ss.name, br0) if br0 is not None else None
                jot("signal", day=day, session=ss.name, kind=ss.kind, setup="reversion", d=d, grade=raw, time=ny[t], index=int(t),
                    close=float(c[t]), anchor=float(ss.anchor), room=float(room), moved=float(moved), htf=htf, ath=ath,
                    losses=ss.losses_in_row, layer=bool(mine), stop=br[0] if br else None, target=br[1] if br else None,
                    taken=not fails, reason=fails[0] if fails else "taken", fails=fails)
                if fails:
                    continue
                if mine:
                    att, layer = lastp.attempt, True
                else:
                    ss.attempts += 1
                    if ss.stopped:
                        ss.fourth_used = True
                    att, layer = new_attempt(), False
                p = Pos(ss.name, "reversion", grade, d, t, -1, np.nan, np.nan, np.nan, br[0], br[1], _contracts(cfg, br[0]), att, layer,
                        "market", ss.anchor, evening38=ss.kind == "evening" and br[1] == cfg.target)
                if not layer:
                    first_of[(ss.name, att)] = p
                pending.append(p)
    out = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    return out.sort_values(["entry_time", "session", "attempt"], kind="stable").reset_index(drop=True)
