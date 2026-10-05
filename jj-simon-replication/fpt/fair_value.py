"""Fair value anchors.

JJ Simon's premise: when no new information has arrived, price tends to
revert to a reference "fair price". For NQ he anchors that reference to the
price at the 09:30 ET cash open (the single candle right before the open,
before institutional volume hits) and, for the afternoon, the 14:00 ET price.
Third-party codifications draw a +/- band (38 points in joetroyer's
TradingView indicator) around the line to label premium / discount.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import NY


@dataclass(frozen=True)
class FairValueConfig:
    anchor: str = "open_0930"  # "open_0930" | "close_0929" | "vwap_0929_0930"
    band_points: float = 38.0
    pm_anchor: bool = False  # anchor a second fair value at pm_time
    pm_time: str = "14:00"


def minute_of_day(index: pd.DatetimeIndex) -> np.ndarray:
    t = index.tz_convert(NY)
    return (t.hour * 60 + t.minute).to_numpy()


def day_keys(index: pd.DatetimeIndex) -> np.ndarray:
    """int64 key per bar identifying its New York calendar day."""
    return index.tz_convert(NY).normalize().asi8


def hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _anchor_price(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, v: np.ndarray, dmod: np.ndarray, minute: int, how: str) -> float:
    at = np.where(dmod == minute)[0]
    prev = np.where(dmod == minute - 1)[0]
    if how == "open_0930":
        return float(o[at[0]]) if len(at) else np.nan
    if how == "close_0929":
        if len(prev):
            return float(c[prev[0]])
        return float(o[at[0]]) if len(at) else np.nan
    if how == "vwap_0929_0930":
        sel = np.concatenate([prev, at])
        if len(sel) == 0:
            return np.nan
        vv = v[sel]
        p = (h[sel] + l[sel] + c[sel]) / 3.0
        return float(p.mean()) if vv.sum() <= 0 else float((p * vv).sum() / vv.sum())
    raise ValueError(f"unknown anchor {how!r}")


def session_anchor_prices(df: pd.DataFrame, cfg: FairValueConfig = FairValueConfig()) -> pd.DataFrame:
    """One row per New York session date with fv_am (and fv_pm if enabled)."""
    keys = day_keys(df.index)
    mod = minute_of_day(df.index)
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    v = df["volume"].to_numpy(float) if "volume" in df.columns else np.zeros(len(df))
    rows = []
    for k in np.unique(keys):
        m = keys == k
        am = _anchor_price(o[m], h[m], l[m], c[m], v[m], mod[m], 9 * 60 + 30, cfg.anchor)
        pm = _anchor_price(o[m], h[m], l[m], c[m], v[m], mod[m], hhmm(cfg.pm_time), "open_0930") if cfg.pm_anchor else np.nan
        rows.append((k, am, pm))
    res = pd.DataFrame(rows, columns=["day_key", "fv_am", "fv_pm"]).set_index("day_key")
    res["date"] = pd.to_datetime(res.index, utc=True).tz_convert(NY).date
    return res


def fair_value_series(df: pd.DataFrame, cfg: FairValueConfig = FairValueConfig()) -> pd.Series:
    """Fair value aligned to every bar: the AM anchor from 09:30 on, replaced
    by the PM anchor from pm_time on when enabled. NaN before the open."""
    anchors = session_anchor_prices(df, cfg)
    keys = day_keys(df.index)
    mod = minute_of_day(df.index)
    fv = np.full(len(df), np.nan)
    pm_minute = hhmm(cfg.pm_time)
    am_map = anchors["fv_am"].to_dict()
    pm_map = anchors["fv_pm"].to_dict()
    for k in np.unique(keys):
        m = keys == k
        am = am_map.get(k, np.nan)
        if not np.isnan(am):
            fv[m & (mod >= 9 * 60 + 30)] = am
        if cfg.pm_anchor:
            pm = pm_map.get(k, np.nan)
            if not np.isnan(pm):
                fv[m & (mod >= pm_minute)] = pm
    return pd.Series(fv, index=df.index, name="fair_value")
