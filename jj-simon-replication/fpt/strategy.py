"""Signal generation for the Fair Pricing Theory NQ method.

Reconstructed rules (sources in docs/DOSSIER.md):
  * Instrument NQ, 1-minute chart, New York time.
  * Fair value = the 09:30 open price (pre-open candle). Afternoon anchor at
    14:00 is optional.
  * Window: 09:30-11:00 ("the 90-minute window"). First minutes (JJ: ~5,
    fxreplay's codification: 10-15): CONTINUATION trades in the direction of
    the opening push away from fair value. Remainder of the window:
    REVERSION trades back toward fair value. Optional 14:00-15:00 session.
  * Entry trigger for both: a break of structure (BOS, with the move) or
    market structure break (MSB, against the prior swing) CONFIRMED by a
    displacement candle (counter-wick < 20% of open-to-extreme). Grades:
    A+ = structure break + displacement, A = displacement alone, B = skip.
  * His bracket: 25-point stop, 38-point target ("3825"), one NQ contract per
    $500 of risk; 50 / 75 on a wide opening candle or a 150k account. The
    fxreplay ATR ladder (50/25/16.5 with 1/2/3 contracts) is kept as
    stop_mode="atr_tier". No management, no partials; break-even only at a
    new session open or before scheduled news.
  * No maximum trades when winning; three losing attempts end the session.
    One position at a time (he layers accounts, the backtester trades one).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fair_value import FairValueConfig, day_keys, fair_value_series, hhmm, minute_of_day
from .indicators import atr as atr_fn
from .indicators import swing_points
from .risk import DEFAULT_ATR_TIERS, NQ_POINT_VALUE, atr_tier, contracts_for_risk
from .structure import is_displacement, is_displacement_jj

TRADE_COLUMNS = [
    "signal_time", "entry_time", "exit_time", "session", "setup", "grade", "direction",
    "fair_value", "atr", "tier", "stop_points", "contracts", "entry", "stop", "target",
    "exit", "exit_reason", "pnl_points", "pnl_dollars", "risk_dollars", "r", "bars_held",
    "distance_from_fv",
]


@dataclass
class StrategyConfig:
    # sessions (New York time, HH:MM)
    session_start: str = "09:30"
    continuation_end: str = "09:35"  # JJ: continuation only in the first ~5 minutes; fxreplay codifies 10-15 (set "09:45")
    window_end: str = "11:00"
    skip_first_minutes: int = 0  # fxreplay's filtered test skips the first 3 minutes for continuations
    reversion_end: str | None = None  # fxreplay's filtered test: reversions only until ~10:00; None = window_end
    big_open_candle_points: float | None = 25.0  # JJ: if the opening candle is larger than this, cut size in half and use the 50-point stop
    big_open_measure: str = "body"  # "body": open-to-close of the opening candle (his wording: "The candle body is 33 points") | "range": high-low
    big_open_scope: str = "continuation"  # "continuation": the continuation trade off each session's own opening candle (his use) | "session": every trade of that session | "am": every 09:30 session trade (legacy)
    pm_session: bool = False
    pm_start: str = "14:00"
    pm_continuation_end: str = "14:05"
    pm_end: str = "15:00"  # JJ's earlier videos: 14:00-15:00 afternoon session
    extra_sessions: tuple = ()  # more (start, continuation_end, end) windows anchored at their start bar's open, e.g. (("08:30", "08:35", "09:29"), ("18:00", "18:05", "19:30"), ("20:00", "20:05", "21:30")) for his 8:30 news, 6 PM and 8 PM sessions
    rolling_fair_value: bool = True  # JJ (standing rule, Apr-Oct 2026): "I change fair price throughout the day based on most recent consolidation"
    consolidation_bars: int = 8  # a consolidation = the last N bars' range below consolidation_atr_mult x ATR
    consolidation_atr_mult: float = 1.5
    # fair value
    anchor: str = "open_0930"
    band_points: float = 38.0
    require_band_touch: bool = False  # reversion only after price reached fv +/- band
    min_distance_from_fv: float = 0.0  # reversion only when at least this far from fair value
    # entry mechanics
    atr_period: int = 14
    displacement_mode: str = "jj"  # "jj": his definition (body larger than the previous candle's body and close beyond it) | "wick": fxreplay's 20% counter-wick test plus min_body_atr
    wick_pct: float = 0.20  # "wick" mode only
    min_body_atr: float = 0.5  # "wick" mode only: displacement body must be >= this x ATR
    swing_left: int = 1  # JJ: structure is a wick lower/higher than the one candle before and the one after (KHEQ5g55dQ4 ~6:54 L283); fxreplay-style pivots: 3/3
    swing_right: int = 1
    continuation_direction: str = "open_candle"  # "open_candle": colour of the session's opening 1-minute candle (3L8xdh3oPm4 L412, PN1UKQMPb5M L51) | "side_of_fv": sign(close - fair value)
    continuation_stall_candles: int | None = 2  # continuation phase also ends once this many consecutive candles close against the opening direction (the unfair move stalled)
    structure_lookback: int = 60  # bars; a swing older than this is not "recent structure"
    allow_grade_a: bool = True  # take displacement-only (grade A) entries
    # risk
    stop_mode: str = "fixed"  # "fixed": his bracket, stop_points / target_points (25 / 38, "3825") | "atr_tier": fxreplay's ATR ladder
    stop_points: float = 25.0  # his New York floor: "never less than 25 points"; 50 on a 150k account or a wide open
    atr_tiers: tuple = DEFAULT_ATR_TIERS  # "atr_tier" mode only
    size_mode: str = "risk"  # "risk" (contracts from risk_dollars) | "tier" (1/2/3 contracts by ATR tier, "atr_tier" mode)
    risk_dollars: float = 500.0  # his evaluation demonstrations: one NQ contract on the 25-point stop = $500 (KHEQ5g55dQ4 ~1:07:52 L2147)
    point_value: float = NQ_POINT_VALUE
    max_contracts: int = 3
    rr: float = 1.5
    # daily discipline
    max_trades_per_day: int = 100  # JJ: "no maximum" when winning; the stops below count losing attempts (KN7j6NXXAio ~1:45 L101)
    daily_loss_stop_r: float | None = None
    daily_profit_stop_r: float | None = None
    max_consecutive_losses: int | None = 3  # JJ: "if I'm trying to trade reversion and I lose three in a row, then I'm done" (KHEQ5g55dQ4 ~34:24 L1124)
    stop_scope: str = "session"  # the three-loss stop is per session (KHEQ5g55dQ4 ~34:24 L1124, ~1:10:50 L2238); "day" = once per day
    flat_at_window_end: bool = False  # JJ: "After 11:00 a.m., I am done trading as well, but I'll let a position play out if I'm still in one" (UVKVSWKFlvo ~7:49 L288); True = flatten at the window end
    target_points: float | None = 38.0  # his bracket "3825": 38-point target on the 25-point stop; None = rr x stop; funded accounts without a consistency rule: 100
    max_target_overshoot_pct: float | None = 0.2  # reversion room rule: at most 20% of the target may lie beyond fair value, i.e. distance to fair value >= 0.8 x target (KhooqEQK9bA ~11:04 L471, KHEQ5g55dQ4 ~1:22:33 L2596)
    # costs (per contract per side)
    commission_per_contract_side: float = 2.50
    slippage_points: float = 0.25


def generate_trades(df: pd.DataFrame, cfg: StrategyConfig | None = None) -> pd.DataFrame:
    """Run the rules bar by bar and return one row per completed trade."""
    cfg = cfg or StrategyConfig()
    df = df.sort_index()
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    n = len(df)
    if n == 0:
        return pd.DataFrame(columns=TRADE_COLUMNS)

    a = atr_fn(df, cfg.atr_period).to_numpy(float)
    fv = fair_value_series(
        df,
        FairValueConfig(anchor=cfg.anchor, band_points=cfg.band_points, pm_anchor=cfg.pm_session, pm_time=cfg.pm_start,
                        extra_anchor_times=tuple(x[0] for x in cfg.extra_sessions)),
    ).to_numpy(float)
    sh, sl = swing_points(df, cfg.swing_left, cfg.swing_right)
    keys = day_keys(df.index)
    mod = minute_of_day(df.index)
    times = df.index

    windows = [("am", hhmm(cfg.session_start), hhmm(cfg.continuation_end), hhmm(cfg.window_end))]
    if cfg.pm_session:
        windows.append(("pm", hhmm(cfg.pm_start), hhmm(cfg.pm_continuation_end), hhmm(cfg.pm_end)))
    for start, cont_end, end in cfg.extra_sessions:
        windows.append((f"s{start.replace(':', '')}", hhmm(start), hhmm(cont_end), hhmm(end)))
    windows.sort(key=lambda w: w[1])
    window_starts = {w[1] for w in windows}
    am_start = hhmm(cfg.session_start)

    rev_end_min = hhmm(cfg.reversion_end) if cfg.reversion_end else None
    trades: list[dict] = []
    for k in np.unique(keys):
        pos = np.where(keys == k)[0]
        day_bars = pos.tolist()
        last_bar = day_bars[-1]
        # per-day state
        trades_today = 0
        daily_r = 0.0
        consec_losses = 0
        stopped = False
        position: dict | None = None
        day_high = -np.inf
        day_low = np.inf
        rolling_fv = np.nan  # most recent consolidation's price, once one has formed after a push (JJ's rolling fair price)
        last_window = None
        piv_high: list[list] = []  # [index, price, broken, broken_at_bar]
        piv_low: list[list] = []
        first = np.where(mod[pos] == am_start)[0]  # the 09:30 candle, whatever other sessions are enabled
        open_range = float(h[pos[first[0]]] - l[pos[first[0]]]) if len(first) else 0.0  # legacy "range" / "am" measure
        sess_open: dict[str, dict] = {}  # per session: opening candle direction, size, stall counter, stall flag

        for t in day_bars:
            # ---- manage an open position on this bar ----
            if position is not None and t >= position["entry_index"]:
                d = position["direction"]
                exit_price = None
                reason = None
                if cfg.flat_at_window_end and mod[t] >= position["window_end"]:
                    # flatten at this bar's open: nothing that happens later in the bar counts
                    exit_price, reason = o[t] - d * cfg.slippage_points, "window_end"
                elif d > 0:
                    if l[t] <= position["stop"]:
                        exit_price, reason = position["stop"] - cfg.slippage_points, "stop"
                    elif h[t] >= position["target"]:
                        exit_price, reason = position["target"], "target"
                else:
                    if h[t] >= position["stop"]:
                        exit_price, reason = position["stop"] + cfg.slippage_points, "stop"
                    elif l[t] <= position["target"]:
                        exit_price, reason = position["target"], "target"
                if exit_price is None and t == last_bar:
                    exit_price, reason = c[t] - d * cfg.slippage_points, "session_end"
                if exit_price is not None:
                    rec = _close(position, exit_price, reason, times[t], t, cfg)
                    trades.append(rec)
                    daily_r += rec["r"]
                    consec_losses = consec_losses + 1 if rec["pnl_dollars"] < 0 else 0
                    position = None
                    if cfg.daily_loss_stop_r is not None and daily_r <= -abs(cfg.daily_loss_stop_r):
                        stopped = True
                    if cfg.daily_profit_stop_r is not None and daily_r >= cfg.daily_profit_stop_r:
                        stopped = True
                    if cfg.max_consecutive_losses is not None and consec_losses >= cfg.max_consecutive_losses:
                        stopped = True

            # ---- session extremes, measured from each session's own start ----
            if mod[t] in window_starts:
                day_high, day_low = -np.inf, np.inf
                if cfg.stop_scope == "session":
                    daily_r, consec_losses, stopped = 0.0, 0, False
            if mod[t] >= windows[0][1]:
                day_high = max(day_high, h[t])
                day_low = min(day_low, l[t])

            # ---- confirm pivots that became known on this bar ----
            j = t - cfg.swing_right
            if j >= day_bars[0]:
                if sh[j]:
                    piv_high.append([j, h[j], False, -1])
                if sl[j]:
                    piv_low.append([j, l[j], False, -1])
            # ---- any close through a swing level consumes it (same on every bar, as in the Pine port) ----
            for p in piv_high:
                if not p[2] and c[t] > p[1]:
                    p[2], p[3] = True, t
            for p in piv_low:
                if not p[2] and c[t] < p[1]:
                    p[2], p[3] = True, t

            win_now = _window_for(mod[t], windows)
            if win_now is not None:
                sname = win_now[0]
                if sname not in sess_open:  # first bar of this session = its opening candle
                    body = abs(c[t] - o[t])
                    size = body if cfg.big_open_measure == "body" else (h[t] - l[t])
                    sess_open[sname] = {"dir": int(np.sign(c[t] - o[t])), "size": float(size), "against": 0, "stalled": False}
                else:
                    so = sess_open[sname]
                    if cfg.continuation_stall_candles is not None and so["dir"] != 0:
                        so["against"] = so["against"] + 1 if np.sign(c[t] - o[t]) == -so["dir"] else 0
                        if so["against"] >= cfg.continuation_stall_candles:
                            so["stalled"] = True

            if position is not None or stopped or trades_today >= cfg.max_trades_per_day:
                continue
            if t == last_bar or t + 1 > last_bar:
                continue
            fvt = fv[t]
            if np.isnan(fvt) or np.isnan(a[t]):
                continue

            win = _window_for(mod[t], windows)
            if win is None:
                continue
            session, w_start, w_cont_end, w_end = win
            if cfg.flat_at_window_end and mod[t + 1] >= w_end:
                continue  # the fill bar would be flattened at its own open
            if session != last_window:
                rolling_fv = np.nan  # each session starts from its own anchor
                last_window = session
            if cfg.rolling_fair_value and mod[t] >= w_cont_end:
                j0 = t - cfg.consolidation_bars + 1
                if j0 >= day_bars[0]:
                    rng = h[j0 : t + 1].max() - l[j0 : t + 1].min()
                    if rng <= cfg.consolidation_atr_mult * a[t] and abs(c[t] - fvt) > rng:
                        rolling_fv = float(c[j0 : t + 1].mean())
                if not np.isnan(rolling_fv):
                    fvt = rolling_fv
            so = sess_open.get(session, {"dir": 0, "size": 0.0, "stalled": False})
            setup = "continuation" if (mod[t] < w_cont_end and not so["stalled"]) else "reversion"
            if setup == "continuation" and mod[t] < w_start + cfg.skip_first_minutes:
                continue
            if setup == "reversion" and rev_end_min is not None and mod[t] >= rev_end_min:
                continue
            if c[t] == fvt:
                continue
            above = c[t] > fvt
            # the bracket for this trade (needed by the reversion room rule)
            if cfg.stop_mode == "atr_tier":
                tier = atr_tier(a[t], cfg.atr_tiers)
                stop_pts = tier.stop_points
                tier_name = tier.name
                tier_contracts = tier.contracts
            else:
                stop_pts = cfg.stop_points
                tier_name = f"fixed{cfg.stop_points:g}"
                tier_contracts = max(1, int(cfg.risk_dollars // (stop_pts * cfg.point_value)))
            target_pts = cfg.target_points if cfg.target_points is not None else cfg.rr * stop_pts
            if setup == "continuation":
                if cfg.continuation_direction == "open_candle":
                    if so["dir"] == 0:
                        continue
                    direction = so["dir"]
                else:
                    direction = 1 if above else -1
            else:
                direction = -1 if above else 1
                if cfg.require_band_touch:
                    if direction < 0 and day_high < fvt + cfg.band_points:
                        continue
                    if direction > 0 and day_low > fvt - cfg.band_points:
                        continue
                if abs(c[t] - fvt) < cfg.min_distance_from_fv:
                    continue
                if cfg.max_target_overshoot_pct is not None and abs(c[t] - fvt) < (1.0 - cfg.max_target_overshoot_pct) * target_pts:
                    continue  # not enough room: more than the allowed share of the target would lie beyond fair value

            if cfg.displacement_mode == "jj":
                if t - 1 < day_bars[0]:
                    continue
                if not is_displacement_jj(o[t], h[t], l[t], c[t], o[t - 1], h[t - 1], l[t - 1], c[t - 1], direction):
                    continue
            elif not is_displacement(o[t], h[t], l[t], c[t], direction, cfg.wick_pct, cfg.min_body_atr * a[t]):
                continue

            # structure break against the most recent unbroken swing in the trade direction
            grade = None
            pivots = piv_high if direction > 0 else piv_low
            level = None
            for p in reversed(pivots):
                if p[0] < t - cfg.structure_lookback:
                    break
                if not p[2] or p[3] == t:  # still live before this bar's close
                    level = p
                    break
            if level is not None and level[3] == t:
                grade = "A+"  # this displacement candle is the first close through the most recent live swing
            elif cfg.allow_grade_a:
                grade = "A"
            else:
                continue

            if cfg.size_mode == "tier":
                contracts = min(tier_contracts, cfg.max_contracts)
            else:
                contracts = contracts_for_risk(cfg.risk_dollars, stop_pts, cfg.point_value, cfg.max_contracts)
            if cfg.big_open_candle_points is not None:
                if cfg.big_open_scope == "am":
                    big = open_range > cfg.big_open_candle_points and session == "am"
                elif cfg.big_open_scope == "session":
                    big = so["size"] > cfg.big_open_candle_points
                else:  # "continuation": the trade off this session's own opening candle
                    big = so["size"] > cfg.big_open_candle_points and setup == "continuation"
                if big:
                    wide = max(cfg.atr_tiers, key=lambda x: x[1])  # the wide stop (50 points)
                    stop_pts = wide[1]
                    target_pts = cfg.rr * stop_pts  # 50 / 75 (he quotes 50 / 76)
                    contracts = max(1, contracts // 2)
                    tier_name = "big_open"
            if contracts <= 0:
                continue

            entry = o[t + 1] + direction * cfg.slippage_points
            position = {
                "signal_index": t,
                "signal_time": times[t],
                "entry_index": t + 1,
                "entry_time": times[t + 1],
                "session": session,
                "setup": setup,
                "grade": grade,
                "direction": direction,
                "fair_value": fvt,
                "atr": a[t],
                "tier": tier_name,
                "stop_points": stop_pts,
                "contracts": contracts,
                "entry": entry,
                "stop": entry - direction * stop_pts,
                "target": entry + direction * target_pts,
                "window_end": w_end,
                "distance_from_fv": c[t] - fvt,
            }
            trades_today += 1

        if position is not None:  # should have been flattened on the last bar
            rec = _close(position, c[last_bar], "session_end", times[last_bar], last_bar, cfg)
            trades.append(rec)

    out = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    return out


def _window_for(m: int, windows: list[tuple]) -> tuple | None:
    for session, start, cont_end, end in windows:
        if start <= m < end:
            return session, start, cont_end, end
    return None


def _close(position: dict, exit_price: float, reason: str, exit_time, exit_index: int, cfg: StrategyConfig) -> dict:
    d = position["direction"]
    pnl_points = (exit_price - position["entry"]) * d
    contracts = position["contracts"]
    gross = pnl_points * contracts * cfg.point_value
    commission = 2.0 * contracts * cfg.commission_per_contract_side
    pnl_dollars = gross - commission
    risk_dollars = position["stop_points"] * contracts * cfg.point_value
    return {
        "signal_time": position["signal_time"],
        "entry_time": position["entry_time"],
        "exit_time": exit_time,
        "session": position["session"],
        "setup": position["setup"],
        "grade": position["grade"],
        "direction": "long" if d > 0 else "short",
        "fair_value": position["fair_value"],
        "atr": position["atr"],
        "tier": position["tier"],
        "stop_points": position["stop_points"],
        "contracts": contracts,
        "entry": position["entry"],
        "stop": position["stop"],
        "target": position["target"],
        "exit": exit_price,
        "exit_reason": reason,
        "pnl_points": pnl_points,
        "pnl_dollars": pnl_dollars,
        "risk_dollars": risk_dollars,
        "r": pnl_dollars / risk_dollars if risk_dollars else 0.0,
        "bars_held": exit_index - position["entry_index"] + 1,
        "distance_from_fv": position["distance_from_fv"],
    }
