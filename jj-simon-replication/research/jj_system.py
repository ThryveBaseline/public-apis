"""JJ Simon's system, his whole trading day, as one forward paper stream (docs/research/jj_system_v1.md).

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
VERSION = "jj_system_v1"


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


def generate_trades(bars: pd.DataFrame, cfg: JJConfig | None = None, events: pd.DataFrame | None = None, days=None,
                    prior_high: float = -np.inf) -> pd.DataFrame:
    """His whole day on every trading day of `bars` (or only `days`) that has a previous 09:30 bar for its structure
    and the evening's references. `events` is the USD calendar (columns time, country, impact, title); without it no
    news session runs. `prior_high` is the all-time high before the first bar (the bars loaded may start late). One
    row per closed position."""
    cfg = cfg or JJConfig()
    bars = bars.sort_index()
    if bars.empty:
        return pd.DataFrame(columns=TRADE_COLUMNS)
    ny = bars.index.tz_convert(NY)
    o, h, l, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    n = len(bars)
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    mins = (bars.index.as_unit("ns").asi8 // 60_000_000_000).astype(np.int64)  # epoch minutes
    cal = ny.tz_localize(None).normalize()
    dow = ny.dayofweek.to_numpy()
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
    trades: list[dict] = []

    def htf_day(t: int) -> int:
        """Daytime higher-time-frame bias: the previous 6 and 12 hours' net move, inverted; 0 when they disagree."""
        signs = []
        for hrs in cfg.htf_hours:
            j = np.searchsorted(mins, mins[t] - hrs * 60, side="right") - 1
            if j < 0:
                return 0
            signs.append(int(np.sign(c[t] - c[j])))
        return -signs[0] if signs[0] != 0 and all(x == signs[0] for x in signs) else 0

    def last_within(i: int, minutes: int, e: int) -> int:
        """The last bar index at most `minutes` - 1 minutes after bar i (within the day)."""
        return int(min(e, np.searchsorted(mins, mins[i] + minutes - 1, side="right")) - 1)

    for day in all_days:
        if want is not None and day not in want:
            continue
        idx = np.flatnonzero(td == day.to_datetime64())
        s, e = int(idx[0]), int(idx[-1]) + 1
        prev930 = opens_0930[opens_0930 < s]
        if not len(prev930):
            continue
        w0 = int(prev930[-1])  # structure: from the previous 09:30 open ("all the way back down to 9:30")
        am_prev = o[w0]  # "9:30 of that morning"
        prev_close = c[s - 1]
        ath = run_high[s - 1]
        evs = ev_days.get(day, [])
        news_min = [mm for mm, imp, title in evs if imp in NEWS_IMPACT and mm in (_m("08:15"), _m("08:30"))
                    and not any(w in title for w in SPEECH_WORDS)]
        release_min = {mm for mm, imp, title in evs if imp in NEWS_IMPACT and mm in (_m("08:15"), _m("08:30"), _m("09:45"), _m("10:00"), _m("14:00"))}
        ten_switch = any(mm == _m("10:00") and imp in NEWS_IMPACT and not any(w in title for w in SPEECH_WORDS) for mm, imp, title in evs)
        fomc = any(mm == _m("14:00") and imp == "High" and any(w in title for w in FOMC_WORDS) for mm, imp, title in evs)
        speeches = sorted(mm for mm, imp, title in evs if imp == "High" and any(w in title for w in SPEECH_WORDS))
        holiday = day.strftime("%Y-%m-%d") in BANK_HOLIDAYS
        at = {int(mod[i]): i for i in range(s, e)}

        # ---- the day's sessions (a session runs only when its opening bar exists) ----
        sess: dict[str, Session] = {}

        def add(name: str, minute: int, length: int, kind: str, cont: bool, **kw) -> None:
            if minute not in at:
                return
            i = at[minute]
            ce = last_within(i, cfg.continuation_minutes, e) if cont else -1
            sess[name] = Session(name, i, last_within(i, length, e), ce, o[i], kind, holiday=holiday, **kw)

        if 1080 in at and cal[at[1080]] < day:
            add("18:00", 1080, 120, "evening", True, cont_max=cfg.evening_continuations, rev_max=cfg.evening_reversions)
        add("20:00", 1200, cfg.session_minutes, "evening", True, cont_max=cfg.evening_continuations, rev_max=cfg.evening_reversions,
            a5_from="18:00", a5_done=False)
        if news_min:
            mm = min(news_min)
            add("news", mm, _m("09:30") - mm, "news", False)  # reversions to the pre-news price only
        add("09:30", 570, cfg.session_minutes, "day", True)
        if "09:30" in sess and holiday:  # a bank holiday is traded only on an influx: the opening candle larger than most so far
            i = sess["09:30"].start
            rng = h[s:i] - l[s:i]
            if not len(rng) or not h[i] - l[i] > np.median(rng):
                del sess["09:30"]
        add("14:00", 840, cfg.session_minutes, "day", True, a5_from=None if fomc else "09:30", a5_done=fomc)
        if 900 in at and dow[at[900]] == 4:
            add("fri", 900, 60, "friday", False, rev_max=1, aplus_only=True)
        for sp in speeches:
            b = at.get(sp)
            for ss in sess.values():
                if b is not None and ss.start <= b <= ss.end:
                    ss.blocked_from = min(ss.blocked_from, b)
        opens = {int(mod[ss.start]) for ss in sess.values() if ss.kind != "friday"} | release_min

        # ---- structure since the previous 09:30 open ----
        piv_hi: list[list] = []  # [index, level, alive]
        piv_lo: list[list] = []
        bos = {1: np.zeros(e - w0, dtype=bool), -1: np.zeros(e - w0, dtype=bool)}
        wickfail = {1: np.zeros(e - w0, dtype=bool), -1: np.zeros(e - w0, dtype=bool)}

        def structure(t: int) -> None:
            j = t - 1
            if j - 1 >= w0:
                if sh[j]:
                    piv_hi.append([j, h[j], True])
                if sl[j]:
                    piv_lo.append([j, l[j], True])
            for p in piv_hi:
                if p[2]:
                    if c[t] > p[1]:
                        p[2] = False
                        bos[1][t - w0] = True
                    elif h[t] > p[1]:
                        wickfail[1][t - w0] = True
            for p in piv_lo:
                if p[2]:
                    if c[t] < p[1]:
                        p[2] = False
                        bos[-1][t - w0] = True
                    elif l[t] < p[1]:
                        wickfail[-1][t - w0] = True

        for t in range(w0, s):
            structure(t)

        def disp(t: int, d: int) -> bool:
            """A displacement in direction d: a body larger than the previous, opposite-colour candle's and a close beyond
            its wick; two or three same-colour candles may count together against the one before them. Not right after a
            break the other way, and not a candle that reached structure and failed to close through it."""
            if t - 1 < w0 or bos[-d][t - 1 - w0]:
                return False
            if wickfail[d][t - w0] and not bos[d][t - w0]:
                return False
            for k in (1, 2, 3):
                f = t - k + 1  # the group's first candle
                pv = f - 1
                if pv < w0 or any(np.sign(c[x] - o[x]) != d for x in range(f, t + 1)):
                    break
                if np.sign(c[pv] - o[pv]) != -d:
                    continue
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

        def set_anchor(ss: Session, value: float) -> None:
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
                lo = max(w0, t - cfg.reanchor_minutes + 1)
                set_anchor(ss, (h[lo:t + 1].max() + l[lo:t + 1].min()) / 2)  # "adjusting fair price to this consolidation now"
                if ss.losses_in_row >= cfg.max_reversion_losses:
                    ss.stopped = True
            elif reason == "target":
                ss.losses_in_row = 0

        def bracket(room: float, moved: float):
            if room >= cfg.room_full and moved > cfg.target:
                return cfg.stop, cfg.target
            if room >= cfg.room_half and moved > cfg.room_half:
                return cfg.half_stop, cfg.half_target
            return None

        def in_profit(p: Pos, t: int) -> bool:
            return (c[t] - p.entry) * p.d > 0 and (p.stop - p.entry) * p.d < 0

        for t in range(s, e):
            nxt_ok = t + 1 < e and mins[t + 1] - mins[t] == 1 and not (firm_close <= mod[t + 1] < 1080)
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
                        if bos[dd][t - w0]:  # the first move: away from the earlier anchor makes the new open fair
                            set_anchor(ss, o[ss.start] if away in (0, dd) else ss.a5_old)
                            ss.a5_done = True
                            break
                    if not ss.a5_done and t == ss.cont_end:
                        set_anchor(ss, ss.a5_old)  # no move away: the earlier anchor stays fair
                        ss.a5_done = True
            am = sess.get("09:30")
            if am is not None and "news" in sess and t == am.cont_end:
                pre = sess["news"].anchor  # a news day: the pre-news price stays fair if the opening move heads back to it
                set_anchor(am, pre if abs(c[t] - pre) < abs(o[am.start] - pre) else o[am.start])
            if am is not None and ten_switch and mod[t] == 600 and am.start <= t <= am.end:
                set_anchor(am, o[t])  # news at 10: the pre-10:00 price is fair
            for ss in sess.values():
                if ss.start <= t <= ss.end:
                    if abs(c[t] - ss.anchor) < cfg.room_half:
                        ss.exc_up = ss.exc_dn = 0.0  # back near fair value: wait for another move away
                    else:
                        ss.exc_up = max(ss.exc_up, h[t] - ss.anchor)
                        ss.exc_dn = max(ss.exc_dn, ss.anchor - l[t])
            # ---- 5. management at the close ----
            if nxt_ok and int(mod[t + 1]) in opens:
                for p in open_pos:
                    if in_profit(p, t):
                        p.stop = p.entry  # break-even into a new session or a release, when in profit
            for p in open_pos:
                ss = sess.get(p.session)
                if p.setup == "continuation" and ss is not None:
                    if bos[-p.d][t - w0] or disp(t, -p.d):
                        p.exit_next = True  # the bias flipped: out at the next open
                    elif ss.cont_end >= 0 and t <= ss.cont_end and (t == ss.cont_end or ss.stalled):
                        best = (h[ss.start:t + 1].max() - o[ss.start]) if p.d > 0 else (o[ss.start] - l[ss.start:t + 1].min())
                        if best < cfg.unfair_move and in_profit(p, t):
                            p.stop = p.entry  # the unfair move never made 38 points
                if p.evening38 and bos[-p.d][t - w0] and in_profit(p, t):
                    p.stop = p.entry
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
            # ---- 7. the overnight book: placed at 21:30 toward 9:30 of that morning, cancelled at 09:29 ----
            if mod[t] == _m("21:29") and cal[t] < day:
                d = int(np.sign(am_prev - c[t]))
                if d != 0:
                    levels = sorted({p[1] for p in (piv_lo if d < 0 else piv_hi) if p[2] and min(am_prev, c[t]) < p[1] < max(am_prev, c[t])})
                    for lv in levels:
                        room = abs(am_prev - lv)
                        br = (cfg.stop, cfg.target) if room >= cfg.room_full else ((cfg.half_stop, cfg.half_target) if room >= cfg.room_half else None)
                        if br:
                            book.append({"level": lv, "d": d, "stop": br[0], "target": br[1], "anchor": am_prev, "active": True})
            if mod[t] == _m("09:29"):
                for b in book:
                    b["active"] = False
            # ---- 8. signals at the close, filled at the next bar's open ----
            if not nxt_ok:
                continue
            for ss in sess.values():
                if not ss.start <= t <= ss.end or t >= ss.blocked_from:
                    continue
                if ss.cont_end >= 0 and t <= ss.cont_end and not ss.stalled:  # the continuation phase
                    d = ss.open_dir
                    if d == 0 or not bos[d][t - w0] or (ss.cont_max is not None and ss.cont_entries >= ss.cont_max):
                        continue
                    if ss.name == "18:00":
                        gap = o[ss.start] - prev_close
                        if abs(gap) >= TICK and int(np.sign(-gap)) != d:
                            continue  # never away from the gap
                    elif ss.kind == "day" and htf_day(t) == -d and not disp(t, d):
                        continue  # against the higher time frame only on a strong opening: a break and a displacement
                    mine = [p for p in open_pos if p.session == ss.name and p.setup == "continuation"]
                    if any((c[t] - p.entry) * p.d < 0 for p in mine):
                        continue  # no layering in drawdown
                    wide = ss.open_body > cfg.big_open_body and not ss.holiday
                    st, tg = (cfg.wide_stop, cfg.wide_target) if wide else (cfg.stop, cfg.target)
                    ss.cont_entries += 1
                    pending.append(Pos(ss.name, "continuation", "A+", d, t, -1, np.nan, np.nan, np.nan, st, tg, _contracts(cfg, st),
                                       new_attempt(), bool(mine), "market", ss.anchor, evening38=ss.kind == "evening" and tg == cfg.target))
                    continue
                if ss.stopped:
                    continue
                d = int(np.sign(ss.anchor - c[t]))
                if d == 0:
                    continue
                grade = "A+" if bos[d][t - w0] else ("A" if disp(t, d) else None)
                if grade is None or (grade != "A+" and (ss.aplus_only or ss.losses_in_row >= cfg.bos_only_after_losses)):
                    continue
                if d < 0 and grade != "A+" and h[s:t + 1].max() >= ath:
                    continue  # at all-time highs, shorts only on a break of structure
                bias = int(np.sign(am_prev - c[t])) if ss.kind == "evening" else htf_day(t)
                if bias == -d:
                    continue  # grade B: the biases are opposed
                br = bracket(abs(ss.anchor - c[t]), ss.exc_up if d < 0 else ss.exc_dn)
                if br is None:
                    continue
                mine = [p for p in open_pos if p.session == ss.name and p.setup == "reversion" and p.d == d]
                if mine:
                    lastp = max(mine, key=lambda p: p.entry_i)
                    if (c[t] - lastp.entry) * d < cfg.layer_progress * lastp.target_pts or any(abs(c[t] - p.entry) < TICK for p in mine):
                        continue  # layer only once the last one is halfway to its target, and not at the same level
                    att, layer = lastp.attempt, True
                else:
                    if ss.rev_max is not None and ss.attempts >= ss.rev_max:
                        continue
                    ss.attempts += 1
                    att, layer = new_attempt(), False
                p = Pos(ss.name, "reversion", grade, d, t, -1, np.nan, np.nan, np.nan, br[0], br[1], _contracts(cfg, br[0]), att, layer,
                        "market", ss.anchor, evening38=ss.kind == "evening" and br[1] == cfg.target)
                if not layer:
                    first_of[(ss.name, att)] = p
                pending.append(p)
    out = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    return out.sort_values(["entry_time", "session", "attempt"], kind="stable").reset_index(drop=True)
