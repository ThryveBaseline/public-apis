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
  * Stop by 1-minute ATR tier (>20 -> 50 pts / 1 ct, 7-20 -> 25 pts / 2 ct,
    <7 -> 16.5 pts / 3 ct, about $1,000 risk). Target fixed 1.5R. No
    management, no partials.
  * About 10 trades per day; one position at a time (assumption).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fair_value import FairValueConfig, day_keys, fair_value_series, hhmm, minute_of_day
from .indicators import atr as atr_fn
from .indicators import swing_points
from .risk import DEFAULT_ATR_TIERS, NQ_POINT_VALUE, atr_tier, contracts_for_risk
from .structure import is_displacement

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
    pm_session: bool = False
    pm_start: str = "14:00"
    pm_continuation_end: str = "14:05"
    pm_end: str = "15:00"  # JJ's earlier videos: 14:00-15:00 afternoon session
    # fair value
    anchor: str = "open_0930"
    band_points: float = 38.0
    require_band_touch: bool = False  # reversion only after price reached fv +/- band
    min_distance_from_fv: float = 0.0  # reversion only when at least this far from fair value
    # entry mechanics
    atr_period: int = 14
    wick_pct: float = 0.20
    min_body_atr: float = 0.5  # displacement body must be >= this x ATR; the codifications call candle size a discretionary, optional filter (see docs/ASSUMPTIONS.md)
    swing_left: int = 3
    swing_right: int = 3
    structure_lookback: int = 60  # bars; a swing older than this is not "recent structure"
    allow_grade_a: bool = True  # take displacement-only (grade A) entries
    # risk
    atr_tiers: tuple = DEFAULT_ATR_TIERS
    size_mode: str = "tier"  # "tier" (1/2/3 contracts by ATR tier) | "risk" (contracts from risk_dollars)
    risk_dollars: float = 1000.0
    point_value: float = NQ_POINT_VALUE
    max_contracts: int = 3
    rr: float = 1.5
    # daily discipline
    max_trades_per_day: int = 10
    daily_loss_stop_r: float | None = None
    daily_profit_stop_r: float | None = None
    max_consecutive_losses: int | None = None
    flat_at_window_end: bool = True
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
        FairValueConfig(anchor=cfg.anchor, band_points=cfg.band_points, pm_anchor=cfg.pm_session, pm_time=cfg.pm_start),
    ).to_numpy(float)
    sh, sl = swing_points(df, cfg.swing_left, cfg.swing_right)
    keys = day_keys(df.index)
    mod = minute_of_day(df.index)
    times = df.index

    windows = [("am", hhmm(cfg.session_start), hhmm(cfg.continuation_end), hhmm(cfg.window_end))]
    if cfg.pm_session:
        windows.append(("pm", hhmm(cfg.pm_start), hhmm(cfg.pm_continuation_end), hhmm(cfg.pm_end)))

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
        piv_high: list[list] = []  # [index, price, broken]
        piv_low: list[list] = []
        first = np.where(mod[pos] == windows[0][1])[0]
        open_range = float(h[pos[first[0]]] - l[pos[first[0]]]) if len(first) else 0.0

        for t in day_bars:
            # ---- manage an open position on this bar ----
            if position is not None and t >= position["entry_index"]:
                d = position["direction"]
                exit_price = None
                reason = None
                if d > 0:
                    if l[t] <= position["stop"]:
                        exit_price, reason = position["stop"] - cfg.slippage_points, "stop"
                    elif h[t] >= position["target"]:
                        exit_price, reason = position["target"], "target"
                else:
                    if h[t] >= position["stop"]:
                        exit_price, reason = position["stop"] + cfg.slippage_points, "stop"
                    elif l[t] <= position["target"]:
                        exit_price, reason = position["target"], "target"
                if exit_price is None and cfg.flat_at_window_end and mod[t] >= position["window_end"]:
                    exit_price, reason = o[t] - d * cfg.slippage_points, "window_end"
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

            # ---- session extremes (from the first window open) ----
            if mod[t] >= windows[0][1]:
                day_high = max(day_high, h[t])
                day_low = min(day_low, l[t])

            # ---- confirm pivots that became known on this bar ----
            j = t - cfg.swing_right
            if j >= day_bars[0]:
                if sh[j]:
                    piv_high.append([j, h[j], False])
                if sl[j]:
                    piv_low.append([j, l[j], False])

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
            setup = "continuation" if mod[t] < w_cont_end else "reversion"
            if setup == "continuation" and mod[t] < w_start + cfg.skip_first_minutes:
                continue
            if setup == "reversion" and rev_end_min is not None and mod[t] >= rev_end_min:
                continue
            if c[t] == fvt:
                continue
            above = c[t] > fvt
            if setup == "continuation":
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

            if not is_displacement(o[t], h[t], l[t], c[t], direction, cfg.wick_pct, cfg.min_body_atr * a[t]):
                continue

            # structure break against the most recent unbroken swing in the trade direction
            grade = None
            pivots = piv_high if direction > 0 else piv_low
            level = None
            for p in reversed(pivots):
                if p[0] < t - cfg.structure_lookback:
                    break
                if not p[2]:
                    level = p
                    break
            if level is not None and ((direction > 0 and c[t] > level[1]) or (direction < 0 and c[t] < level[1])):
                grade = "A+"
                for p in pivots:  # every level crossed by this close is now broken
                    if (direction > 0 and c[t] > p[1]) or (direction < 0 and c[t] < p[1]):
                        p[2] = True
            elif cfg.allow_grade_a:
                grade = "A"
            else:
                continue

            tier = atr_tier(a[t], cfg.atr_tiers)
            stop_pts = tier.stop_points
            if cfg.size_mode == "tier":
                contracts = min(tier.contracts, cfg.max_contracts)
            else:
                contracts = contracts_for_risk(cfg.risk_dollars, stop_pts, cfg.point_value, cfg.max_contracts)
            if cfg.big_open_candle_points is not None and open_range > cfg.big_open_candle_points and session == "am":
                wide = max(cfg.atr_tiers, key=lambda x: x[1])  # the widest stop tier (50 points)
                stop_pts = wide[1]
                contracts = max(1, contracts // 2)
                tier = tier.__class__(name="big_open", min_atr=wide[0], stop_points=stop_pts, contracts=contracts)
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
                "tier": tier.name,
                "stop_points": stop_pts,
                "contracts": contracts,
                "entry": entry,
                "stop": entry - direction * stop_pts,
                "target": entry + direction * cfg.rr * stop_pts,
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
