"""Causal JJ V1 decision adapter, version jj-v1-stream-1.

Reads the frozen configuration and data classes, never calls generate_trades.
Virtual JJ positions determine the frozen multi-account signal rules; actual
broker positions and money exist ONLY in the brokerage ledger. See PARITY.md.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import asdict
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from research.jj_system import JJConfig, Session, Pos, BANK_HOLIDAYS, NEWS_IMPACT, SPEECH_WORDS, FOMC_WORDS
from .models import Bar, Blocked, Intent, NY, stable_id, trading_day, utc

VERSION = "jj-v1-stream-1"
SPEC_HASH = "928fb99da33f67c4b6e4aae26d5bc35c406b0ec871fdacda32d8fcf7f3ede456"
CODE_HASH = "5bf01d24ec9f5e2c6a677786168ab0dda341920243e20a4b28767ec35633f40d"


def verify_frozen(root):
    root = Path(root)
    for file, expected in (("research/jj_system.py", CODE_HASH), ("docs/research/jj_system_v1.md", SPEC_HASH)):
        if hashlib.sha256((root / file).read_bytes()).hexdigest() != expected:
            raise Blocked("FROZEN_JJ_HASH_MISMATCH")
    pin = json.loads((root / "research/jj_system_v1_init.json").read_text())
    for file, expected in pin["code"].items():
        if hashlib.sha256((root / file).read_bytes()).hexdigest() != expected:
            raise Blocked("FROZEN_DEPENDENCY_HASH_MISMATCH")
    if json.loads(json.dumps(asdict(JJConfig()))) != pin["config"] or pin["spec_sha256"] != SPEC_HASH:
        raise Blocked("FROZEN_JJ_CONFIG_MISMATCH")


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


class StreamingJJ:
    def __init__(self, *, calendar=None, prior_high=-math.inf):
        self.cfg = JJConfig()
        self.calendar = calendar or {}
        self.prior_high = prior_high
        self.bars, self.mins, self.run_high = [], [], []
        self.day = None
        self.active = False
        self.actions = []
        self.positions, self.pending, self.book = [], [], []
        self.ids = {}
        self.model_closes = []  # diagnostic model outcomes, never broker fills/P&L

    def epoch(self, date, minute):
        wall = datetime.fromisoformat(date).replace(tzinfo=NY) + timedelta(minutes=minute)
        return int(wall.timestamp() // 60)

    def emit(self, action, t, *, p=None, level=None, reference=""):
        # Decision time is the close of the completed candle, never its open.
        when = (utc(self.bars[t].time) + timedelta(minutes=1)).isoformat()
        payload = [VERSION, self.day, when, action, p.session if p else "", p.setup if p else "",
                   p.d if p else 0, p.attempt if p else 0, level, reference]
        intent = Intent(stable_id(payload), when, action, p.session if p else "", p.setup if p else "", p.d if p else 0,
                        p.stop_pts if p else 0, p.target_pts if p else 0, level, p.grade if p else "", reference)
        self.actions.append(intent)
        if action in ("ENTRY", "BOOK"):
            self.ids[id(p)] = intent.id
        return intent

    def _begin(self, day, t):
        self.day, self.active = day, False
        previous = [i for i, b in enumerate(self.bars[:t]) if b.time.astimezone(NY).hour == 9 and b.time.astimezone(NY).minute == 30]
        self.positions, self.pending, self.book, self.ids = [], [], [], {}
        self.sessions, self.nominal, self.first = {}, {}, {}
        self.piv_hi, self.piv_lo, self.bos_max, self.wick_max = [], [], {}, {}
        self.counter = 0
        if not previous:
            return
        self.w0 = previous[-1]
        self.am_prev = self.bars[self.w0].open
        self.prev_close = self.bars[t - 1].close
        self.active = True
        eve = (datetime.fromisoformat(day) - timedelta(days=1)).date().isoformat()
        self.events = self.calendar.get(day, [])
        releases = [(minute, impact, title) for minute, impact, title in self.events if not any(w in title for w in SPEECH_WORDS)]
        news = [m for m, impact, _ in releases if impact in NEWS_IMPACT and m in (495, 510)]
        self.fomc = any(m == 840 and impact == "High" and any(w in title for w in FOMC_WORDS) for m, impact, title in self.events)
        self.ten_switch = any(m == 600 and impact in NEWS_IMPACT for m, impact, _ in releases)
        self.speeches = [self.epoch(day, m) for m, impact, title in self.events if impact == "High" and any(w in title for w in SPEECH_WORDS)]
        self.definitions = [
            ("18:00", self.epoch(eve, 1080), 120, "evening", True),
            ("20:00", self.epoch(eve, 1200), 90, "evening", True),
            *(([("news", self.epoch(day, min(news)), 570 - min(news), "news", False)]) if news else []),
            ("09:30", self.epoch(day, 570), 90, "day", True),
            ("14:00", self.epoch(day, 840), 90, "day", not self.fomc),
            *(([("fri", self.epoch(day, 900), 60, "friday", False)]) if datetime.fromisoformat(day).weekday() == 4 else []),
        ]
        self.be_times = {when for name, when, _, kind, _ in self.definitions if kind != "friday"}
        self.be_times |= {self.epoch(day, m) for m, impact, _ in releases if impact in NEWS_IMPACT and m in (495, 510, 585, 600, 840)}
        self.t2130, self.t0930, self.t1000 = self.epoch(eve, 1290), self.epoch(day, 570), self.epoch(day, 600)
        self.close_time = self.epoch(day, 970)
        for i in range(self.w0, t):
            self.structure(i)

    def structure(self, t):
        self.bos_max[t] = {1: -1, -1: -1}
        self.wick_max[t] = {1: -1, -1: -1}
        j = t - 1
        if j - 1 >= self.w0:
            before, pivot, after = self.bars[j - 1:j + 2]
            if pivot.high > before.high and pivot.high > after.high:
                self.piv_hi.append([j, pivot.high, True])
            if pivot.low < before.low and pivot.low < after.low:
                self.piv_lo.append([j, pivot.low, True])
        bar = self.bars[t]
        for d, pivots in ((1, self.piv_hi), (-1, self.piv_lo)):
            for p in pivots:
                if not p[2]:
                    continue
                if (bar.close - p[1]) * d > 0:
                    p[2] = False
                    self.bos_max[t][d] = max(self.bos_max[t][d], p[0])
                elif (bar.high if d > 0 else bar.low) * d > p[1] * d:
                    self.wick_max[t][d] = max(self.wick_max[t][d], p[0])

    def bos(self, d, t, ws):
        return self.bos_max.get(t, {}).get(d, -1) >= ws

    def disp(self, t, d, ws):
        if t - 1 < self.w0 or self.bos(-d, t - 1, ws):
            return False
        if self.wick_max[t][d] >= ws and not self.bos(d, t, ws):
            return False
        for k in (1, 2, 3):
            f, pv = t - k + 1, t - k
            if pv < self.w0 or any(sign(self.bars[x].close - self.bars[x].open) != d for x in range(f, t + 1)):
                break
            before = self.bars[pv]
            if sign(before.close - before.open) != -d:
                continue
            if self.bos(-d, pv, ws):
                return False
            bar = self.bars[t]
            if (bar.close - self.bars[f].open) * d > abs(before.close - before.open) and (bar.close > before.high if d > 0 else bar.close < before.low):
                return True
        return False

    def htf(self, t):
        signs = []
        for hours in self.cfg.htf_hours:
            j = bisect_right(self.mins, self.mins[t] - hours * 60) - 1
            if j < 0:
                return 0
            signs.append(sign(self.bars[t].close - self.bars[j].close))
        return -signs[0] if signs[0] != 0 and all(s == signs[0] for s in signs) else 0

    def attempt(self):
        self.counter += 1
        return self.counter

    def new_pos(self, session, setup, grade, d, t, stop, target, attempt, layer=False, kind="market", anchor=0):
        return Pos(session, setup, grade, d, t, -1, math.nan, math.nan, math.nan, stop, target, 0, attempt, layer, kind, anchor,
                   evening38=session in ("18:00", "20:00") and target == self.cfg.target)

    def anchor(self, session, value):
        session.anchor = value
        session.exc_up = session.exc_dn = 0

    def profit(self, p, t):
        return (self.bars[t].close - p.entry) * p.d > 0 and (p.stop - p.entry) * p.d < 0

    def model_close(self, p, reason, t):
        self.positions.remove(p)
        self.model_closes.append({"signal": self.ids.get(id(p)), "reason": reason, "time": self.bars[t].time.isoformat()})
        ss = self.sessions.get(p.session)
        if ss is None or p.setup != "reversion" or self.first.get((p.session, p.attempt)) is not p:
            return
        if reason == "stop":
            ss.losses_in_row += 1
            if ss.losses_in_row >= self.cfg.reanchor_after_losses:
                recent = self.bars[max(self.w0, t - self.cfg.reanchor_minutes + 1):t + 1]
                self.anchor(ss, (max(b.high for b in recent) + min(b.low for b in recent)) / 2)
            if ss.losses_in_row >= self.cfg.max_reversion_losses:
                ss.stopped = True
        elif reason == "target":
            ss.losses_in_row = 0

    def move_be(self, p, t):
        if self.profit(p, t):
            p.stop = p.entry
            self.emit("BREAKEVEN", t, p=p, reference=self.ids[id(p)])

    def on_bar(self, bar: Bar):
        self.actions = []
        timestamp = utc(bar.time)
        if self.bars and timestamp <= utc(self.bars[-1].time):
            if timestamp == utc(self.bars[-1].time) and bar == self.bars[-1]:
                return []
            raise Blocked("STRATEGY_BAR_ORDER_OR_REVISION")
        self.bars.append(bar)
        self.mins.append(int(timestamp.timestamp() // 60))
        self.run_high.append(max(self.run_high[-1] if self.run_high else self.prior_high, bar.high))
        t, minute = len(self.bars) - 1, self.mins[-1]
        day = trading_day(timestamp)
        if day != self.day:
            self._begin(day, t)
        if not self.active:
            return []
        cfg = self.cfg
        # Virtual fills maintain the frozen full signal stream. Never used as money.
        for p in self.pending:
            p.entry_i, p.entry = t, bar.open + p.d * cfg.slippage
            p.stop, p.target = p.entry - p.d * p.stop_pts, p.entry + p.d * p.target_pts
            self.positions.append(p)
        self.pending = []
        for p in [p for p in self.positions if p.exit_next]:
            self.model_close(p, "exit_signal", t)
        filled_now = []
        for b in self.book:
            if b["active"] and ((b["d"] < 0 and bar.low < b["level"]) or (b["d"] > 0 and bar.high > b["level"])):
                p, d = b["position"], b["d"]
                p.attempt = self.attempt()
                p.entry_i, p.entry = t, (min(bar.open, b["level"]) if d < 0 else max(bar.open, b["level"])) + d * cfg.slippage
                p.stop, p.target = p.entry - d * p.stop_pts, p.entry + d * p.target_pts
                b["active"] = False
                self.positions.append(p)
                filled_now.append(p)
        for p in list(self.positions):
            hit_stop = bar.low <= p.stop if p.d > 0 else bar.high >= p.stop
            hit_target = bar.high >= p.target if p.d > 0 else bar.low <= p.target
            if hit_stop:
                self.model_close(p, "breakeven" if (p.stop - p.entry) * p.d >= 0 else "stop", t)
            elif p not in filled_now and hit_target:
                self.model_close(p, "target", t)
        self.structure(t)
        # Sessions are created only after their opening candle actually closes.
        for name, start, length, kind, cont in self.definitions:
            if name in self.sessions or not start <= minute < start + 5:
                continue
            today930 = [i for i in range(self.w0 + 1, t + 1) if self.bars[i].time.astimezone(NY).strftime("%H:%M") == "09:30"]
            ws = today930[-1] if name in ("14:00", "fri") and today930 else self.w0
            ss = Session(name, t, start + length - 1, start + 4 if cont else -1, bar.open, kind,
                         holiday=day in BANK_HOLIDAYS, ws=ws, ath=self.run_high[t - 1],
                         cont_max=1 if kind == "evening" else None, rev_max=1 if kind in ("evening", "friday") else None,
                         aplus_only=kind == "friday")
            ss.a5_from = "18:00" if name == "20:00" else "09:30" if name == "14:00" and not self.fomc else None
            ss.a5_done = ss.a5_from is None
            for sp in self.speeches:
                if start <= sp <= ss.end:
                    ss.blocked_from = min(ss.blocked_from, sp)
            self.sessions[name], self.nominal[name] = ss, start
        for ss in self.sessions.values():
            if t == ss.start:
                ss.open_dir, ss.open_body = sign(bar.close - bar.open), abs(bar.close - bar.open)
                if ss.name == "09:30" and ss.holiday:
                    ranges = [self.bars[i].high - self.bars[i].low for i, mm in enumerate(self.mins) if self.nominal["09:30"] - 60 <= mm < self.nominal["09:30"]]
                    ss.disabled = not (ranges and bar.high - bar.low > median(ranges))
                if not ss.a5_done:
                    ref = self.sessions.get(ss.a5_from)
                    if ref is None:
                        ss.a5_done = True
                    else:
                        ss.a5_old = ref.anchor
            if ss.cont_end >= 0 and ss.start < t and minute <= ss.cont_end and not ss.stalled and ss.open_dir:
                ss.against = ss.against + 1 if sign(bar.close - bar.open) == -ss.open_dir else 0
                ss.stalled = ss.against >= cfg.stall_candles
            if not ss.a5_done and ss.start <= t and minute <= ss.cont_end:
                away = sign(self.bars[ss.start].open - ss.a5_old)
                for dd in (1, -1):
                    if self.bos(dd, t, ss.ws):
                        self.anchor(ss, self.bars[ss.start].open if away in (0, dd) else ss.a5_old)
                        ss.a5_done = True
                        break
                if not ss.a5_done and minute == ss.cont_end:
                    self.anchor(ss, ss.a5_old)
                    ss.a5_done = True
        am = self.sessions.get("09:30")
        if am and "news" in self.sessions and minute == am.cont_end:
            pre = self.bars[self.sessions["news"].start].open
            self.anchor(am, pre if abs(bar.close - pre) < abs(self.bars[am.start].open - pre) else self.bars[am.start].open)
        if am and self.ten_switch and am.start < t and minute <= am.end and self.mins[t - 1] < self.t1000 <= minute:
            self.anchor(am, bar.open)
        for ss in self.sessions.values():
            if ss.start <= t and minute <= ss.end:
                if abs(bar.close - ss.anchor) < cfg.room_half:
                    ss.exc_up = ss.exc_dn = 0
                else:
                    ss.exc_up = max(ss.exc_up, bar.high - ss.anchor)
                    ss.exc_dn = max(ss.exc_dn, ss.anchor - bar.low)
        # Wall-clock boundary of this final minute, without looking at a next bar.
        if minute + 1 in self.be_times:
            for p in self.positions:
                self.move_be(p, t)
        for p in self.positions:
            ss = self.sessions.get(p.session)
            if p.setup == "continuation" and ss:
                if self.bos(-p.d, t, ss.ws) or self.disp(t, -p.d, ss.ws):
                    p.exit_next = True
                    self.emit("EXIT", t, p=p, reference=self.ids[id(p)])
                elif ss.cont_end >= 0 and minute <= ss.cont_end and (minute == ss.cont_end or ss.stalled):
                    window = self.bars[ss.start:t + 1]
                    best = max(b.high for b in window) - window[0].open if p.d > 0 else window[0].open - min(b.low for b in window)
                    if best < cfg.unfair_move:
                        self.move_be(p, t)
            if p.evening38 and ss and self.bos(-p.d, t, ss.ws):
                self.move_be(p, t)
        if minute + 1 == self.close_time:
            self.emit("FLATTEN", t)
            for p in list(self.positions):
                self.model_close(p, "firm_close", t)
            for b in self.book:
                b["active"] = False
            return self.actions
        if minute + 1 == self.t2130:
            d = sign(self.am_prev - bar.close)
            levels = sorted({p[1] for p in (self.piv_lo if d < 0 else self.piv_hi) if p[2] and min(self.am_prev, bar.close) < p[1] < max(self.am_prev, bar.close)}) if d else []
            for level in levels:
                room = abs(self.am_prev - level)
                br = (cfg.stop, cfg.target) if room >= cfg.room_full else (cfg.half_stop, cfg.half_target) if room >= cfg.room_half else None
                if br:
                    p = self.new_pos("book", "overnight", "A+", d, t, *br, -len(self.book) - 1, kind="stop", anchor=self.am_prev)
                    self.book.append({"level": level, "d": d, "active": True, "position": p})
                    # Strict trade-through at a live swing requires one tick beyond.
                    self.emit("BOOK", t, p=p, level=level + d * 0.25)
        if minute + 1 == self.t0930:
            for b in self.book:
                b["active"] = False
            self.emit("CANCEL_BOOK", t)
        if minute + 1 >= self.close_time:
            return self.actions
        for ss in self.sessions.values():
            if not ss.start <= t or minute > ss.end or minute >= ss.blocked_from or ss.disabled:
                continue
            if ss.cont_end >= 0 and minute <= ss.cont_end and not ss.stalled:
                d = ss.open_dir
                if not d or not self.bos(d, t, ss.ws) or (ss.cont_max is not None and ss.cont_entries >= ss.cont_max):
                    continue
                if ss.name == "18:00":
                    gap = self.bars[ss.start].open - self.prev_close
                    if abs(gap) >= 0.25 and sign(-gap) != d:
                        continue
                elif ss.kind == "day" and self.htf(t) == -d and not self.disp(t, d, ss.ws):
                    continue
                mine = [p for p in self.positions if p.session == ss.name and p.setup == "continuation"]
                if any((bar.close - p.entry) * p.d < 0 for p in mine):
                    continue
                wide = ss.open_body > cfg.big_open_body and not ss.holiday
                st, tg = (cfg.wide_stop, cfg.wide_target) if wide else (cfg.stop, cfg.target)
                ss.cont_entries += 1
                p = self.new_pos(ss.name, "continuation", "A+", d, t, st, tg, self.attempt(), bool(mine), anchor=ss.anchor)
                self.pending.append(p)
                self.emit("ENTRY", t, p=p)
                continue
            if ss.stopped:
                continue
            d = sign(ss.anchor - bar.close)
            if not d:
                continue
            grade = "A+" if self.bos(d, t, ss.ws) else "A" if self.disp(t, d, ss.ws) else None
            if grade is None or (grade != "A+" and (ss.aplus_only or ss.losses_in_row >= cfg.bos_only_after_losses)):
                continue
            if d < 0 and grade != "A+" and max(b.high for b in self.bars[ss.start:t + 1]) >= ss.ath:
                continue
            bias = sign(self.am_prev - bar.close) if ss.kind == "evening" else self.htf(t)
            if bias == -d:
                continue
            room, moved = abs(ss.anchor - bar.close), ss.exc_up if d < 0 else ss.exc_dn
            br = (cfg.stop, cfg.target) if room >= cfg.room_full and moved > cfg.target else (cfg.half_stop, cfg.half_target) if room >= cfg.room_half and moved > cfg.room_half else None
            if br is None:
                continue
            mine = [p for p in self.positions if p.session == ss.name and p.setup == "reversion" and p.d == d]
            if mine:
                last = max(mine, key=lambda p: p.entry_i)
                if (bar.close - last.entry) * d < cfg.layer_progress * last.target_pts or any(abs(bar.close - p.entry) < 0.25 for p in mine):
                    continue
                attempt, layer = last.attempt, True
            else:
                if ss.rev_max is not None and ss.attempts >= ss.rev_max:
                    continue
                ss.attempts += 1
                attempt, layer = self.attempt(), False
            p = self.new_pos(ss.name, "reversion", grade, d, t, *br, attempt, layer, anchor=ss.anchor)
            if not layer:
                self.first[(ss.name, attempt)] = p
            self.pending.append(p)
            self.emit("ENTRY", t, p=p)
        return self.actions
