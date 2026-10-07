"""Research copy of the frozen engine, with hooks for the candidates that survive the ledger-based screens.

fpt/ stays frozen (Baseline 0, commit f585bfb). This module imports the frozen StrategyConfig, _window_for and
_close unchanged and carries a copy of fpt.strategy.generate_trades with a few hooks, each of which leaves the frozen
behaviour unchanged at its default (tests/test_engine.py runs both engines on the same bars under many frozen
configurations and requires identical trade tables; the GB10 run must reproduce sealed/run1/trades.csv).

Why a re-simulation and not only the ledger replay: the replay changes each sealed trade's exit, but it cannot add
the entries the frozen engine skipped while a position was open; a bracket that exits sooner or later changes which
later signals are taken. Re-running the rules with the new bracket takes them, one position at a time.

Hooks (ResearchConfig):
  allow_grade_a_continuation / allow_grade_a_reversion   grade A per setup (None: follow allow_grade_a); his funded
                                                          reversion trigger is A+ only
  continuation_atr_k, continuation_rr                     continuation stop = k x the previous Globex session's daily
                                                          ATR (research.anatomy.daily_context), tick-rounded, at least
                                                          2 points; target = rr x stop, tick-rounded (np.inf: none),
                                                          as research/bracket_replay's ATR family; it replaces the
                                                          wide-open 50/75 switch for continuation
  flat_time                                               flat at the close of the last bar before this New York time,
                                                          less slippage, and no fills at or after it (the firms'
                                                          end-of-day rule; the frozen engine holds to the day's last bar)
  one_contract                                            one contract per trade, so a wide stop is not sized to zero
                                                          contracts by risk_dollars; R is per that contract
Continuation only, with the frozen fields: reversion_end equal to session_start.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY  # noqa: E402
from fpt.fair_value import FairValueConfig, day_keys, fair_value_series, hhmm, minute_of_day  # noqa: E402
from fpt.indicators import atr as atr_fn  # noqa: E402
from fpt.indicators import swing_points  # noqa: E402
from fpt.risk import atr_tier, contracts_for_risk  # noqa: E402
from fpt.strategy import TRADE_COLUMNS, StrategyConfig, _close, _window_for  # noqa: E402
from fpt.structure import is_displacement, is_displacement_jj  # noqa: E402
from research.anatomy import daily_context  # noqa: E402
from research.bracket_replay import _round_tick  # noqa: E402


@dataclass
class ResearchConfig(StrategyConfig):
    """StrategyConfig plus the research hooks; every default leaves the frozen behaviour unchanged."""
    allow_grade_a_continuation: bool | None = None
    allow_grade_a_reversion: bool | None = None
    continuation_atr_k: float | None = None
    continuation_rr: float | None = None
    flat_time: str | None = None
    one_contract: bool = False


def generate_trades(df: pd.DataFrame, cfg: ResearchConfig | None = None) -> pd.DataFrame:
    """fpt.strategy.generate_trades with the ResearchConfig hooks; at their defaults it is the frozen engine."""
    cfg = cfg or ResearchConfig()
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
    flat_min = hhmm(cfg.flat_time) if cfg.flat_time else None
    allow_a = {"continuation": cfg.allow_grade_a if cfg.allow_grade_a_continuation is None else cfg.allow_grade_a_continuation,
               "reversion": cfg.allow_grade_a if cfg.allow_grade_a_reversion is None else cfg.allow_grade_a_reversion}
    datr = np.full(n, np.nan)
    if cfg.continuation_atr_k is not None:
        if cfg.continuation_rr is None:
            raise ValueError("continuation_atr_k needs continuation_rr (np.inf for no target)")
        datr = pd.Series(df.index.tz_convert(NY).normalize().tz_localize(None)).map(daily_context(df)["daily_atr"]).to_numpy(float)

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
                # same-bar ambiguity: both the stop and the target lie inside this bar's range. The 1-minute
                # data cannot say which printed first; it is resolved as a STOP (worst case) and flagged.
                both = (l[t] <= position["stop"] and h[t] >= position["target"]) if d > 0 else (h[t] >= position["stop"] and l[t] <= position["target"])
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
                if exit_price is None and flat_min is not None and mod[t] < flat_min and (t == last_bar or mod[t + 1] >= flat_min):
                    exit_price, reason = c[t] - d * cfg.slippage_points, "flat"  # the close of the last bar before flat_time, as the replay
                if exit_price is None and t == last_bar:
                    exit_price, reason = c[t] - d * cfg.slippage_points, "session_end"
                if exit_price is not None:
                    rec = _close(position, exit_price, reason, times[t], t, cfg)
                    rec["ambiguous_bar"] = bool(both) and reason in ("stop", "target")
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
            if flat_min is not None and mod[t + 1] >= flat_min:
                continue  # no fills at or after flat_time
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
            atr_cont = setup == "continuation" and cfg.continuation_atr_k is not None
            if atr_cont:
                if not np.isfinite(datr[t]) or datr[t] <= 0:
                    continue  # no previous-session daily ATR yet: no bracket
                stop_pts = _round_tick(cfg.continuation_atr_k * datr[t])
                target_pts = _round_tick(stop_pts * cfg.continuation_rr) if np.isfinite(cfg.continuation_rr) else np.inf
                tier_name = f"atr{cfg.continuation_atr_k:g}"
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
            elif allow_a[setup]:
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
                if big and not atr_cont:  # an ATR-scaled continuation bracket replaces the wide-open switch
                    wide = max(cfg.atr_tiers, key=lambda x: x[1])  # the wide stop (50 points)
                    stop_pts = wide[1]
                    target_pts = cfg.rr * stop_pts  # 50 / 75 (he quotes 50 / 76)
                    contracts = max(1, contracts // 2)
                    tier_name = "big_open"
            if cfg.one_contract:
                contracts = 1  # R per one contract on the trade's own stop, as research/bracket_replay.r_of
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
