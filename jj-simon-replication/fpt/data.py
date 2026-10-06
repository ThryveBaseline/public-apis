"""Loading and generating 1-minute NQ bars.

The strategy is defined on the 1-minute chart of the E-mini Nasdaq-100 (NQ)
in New York time. Every function here returns a DataFrame indexed by a
tz-aware DatetimeIndex in America/New_York with columns
open, high, low, close, volume, where each row is the bar that OPENS at the
index timestamp (the 09:30 row is the first regular-session bar).
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

NY = "America/New_York"
COLUMNS = ["open", "high", "low", "close", "volume"]

_TIME_CANDIDATES = ["timestamp", "ts_event", "ts_recv", "datetime", "date_time", "time", "date", "ts", "dt"]


def _parse_timestamps(raw: pd.Series) -> pd.Series:
    """Parse a timestamp column. Strings that carry a UTC offset (e.g. a CSV
    written from a tz-aware index, which changes from -05:00 to -04:00 at the
    March DST switch) are parsed as UTC so mixed offsets do not fail; naive
    strings stay naive and are localised by the caller."""
    sample = str(raw.dropna().iloc[0]).strip() if len(raw.dropna()) else ""
    if re.search(r"([+-]\d{2}:?\d{2}|Z)$", sample):
        return pd.to_datetime(raw, utc=True)
    return pd.to_datetime(raw)


def load_minute_bars(path: str, source_tz: str = NY, time_col: str | None = None) -> pd.DataFrame:
    """Load a CSV of 1-minute bars.

    Accepts the common export layouts (TradingView, Databento, FirstRate,
    Kibot, Tradovate, NinjaTrader): any column order, any capitalisation, a
    single timestamp column or separate date + time columns.

    source_tz: timezone of naive timestamps in the file (Databento exports are
    UTC; TradingView exports follow the chart timezone). tz-aware timestamps
    are converted as-is.
    """
    df = pd.read_csv(path)
    lower = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=lower)

    if time_col is not None:
        tcol = time_col.lower()
        ts = _parse_timestamps(df[tcol])
    elif "date" in df.columns and "time" in df.columns and "timestamp" not in df.columns:
        ts = pd.to_datetime(df["date"].astype(str) + " " + df["time"].astype(str))
    else:
        tcol = next((c for c in _TIME_CANDIDATES if c in df.columns), None)
        if tcol is None:
            raise ValueError(f"no timestamp column found in {list(df.columns)}")
        raw = df[tcol]
        if pd.api.types.is_numeric_dtype(raw) and raw.max() > 10_000_000_000:  # epoch ms
            ts = pd.to_datetime(raw, unit="ms", utc=True)
        elif pd.api.types.is_numeric_dtype(raw):  # epoch s
            ts = pd.to_datetime(raw, unit="s", utc=True)
        else:
            ts = _parse_timestamps(raw)

    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(source_tz, ambiguous="infer", nonexistent="shift_forward")
    ts = ts.dt.tz_convert(NY)

    out = pd.DataFrame(index=pd.DatetimeIndex(ts, name="ts"))
    for c in ["open", "high", "low", "close"]:
        if c not in df.columns:
            raise ValueError(f"missing column {c!r}")
        out[c] = df[c].astype(float).values
    out["volume"] = df["volume"].astype(float).values if "volume" in df.columns else 0.0
    if "symbol" in df.columns:  # Databento continuous contracts carry the underlying contract per bar
        out["symbol"] = df["symbol"].astype(str).values
    if "rtype" in df.columns and out["close"].abs().max() > 1e7:  # Databento fixed-point prices (1e-9 units)
        for c in ["open", "high", "low", "close"]:
            out[c] = out[c] / 1e9
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out


def roll_days(df: pd.DataFrame) -> list:
    """New York dates on which the underlying contract changed from the previous
    bar (needs a `symbol` column, as Databento continuous data provides). A
    roll day's open is a different contract's price from the previous close,
    so its 'unfair move' is an artefact; the evaluator excludes these dates."""
    if "symbol" not in df.columns or df.empty:
        return []
    sym = df["symbol"].astype(str)
    changed = sym.ne(sym.shift()).to_numpy().copy()
    changed[0] = False
    days = df.index[changed].tz_convert(NY).normalize().unique() if df.index.tz is not None else df.index[changed].normalize().unique()
    return sorted({d.date() for d in days})


def rth_mask(index: pd.DatetimeIndex, start: str = "09:30", end: str = "16:00") -> np.ndarray:
    """Boolean mask for bars whose open time is within [start, end) New York time."""
    t = index.tz_convert(NY)
    minutes = t.hour * 60 + t.minute
    s = _hhmm(start)
    e = _hhmm(end)
    return (minutes >= s) & (minutes < e)


def _hhmm(s: str) -> int:
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def synthetic_minute_bars(
    days: int = 60,
    start: str = "2025-01-06",
    seed: int = 7,
    base_price: float = 21000.0,
    sigma_points_per_min: float = 6.0,
    open_shock_points: float = 25.0,
    reversion_strength: float = 0.02,
) -> pd.DataFrame:
    """Generate regular-session (09:30-16:00) 1-minute bars with an opening
    shock followed by mean reversion toward the open, so that the strategy
    has something to chew on in tests and demos.

    This is NOT market data. Use it only to exercise the code path; every
    performance number from synthetic data is meaningless.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=days, tz=NY)
    rows = []
    price = base_price
    for d in dates:
        session_open = price
        fair = session_open
        direction = rng.choice([-1.0, 1.0])
        t0 = d.replace(hour=9, minute=30)
        n = 390
        # intraday volatility shape: high at the open, decays, bumps at 14:00
        for i in range(n):
            ts = t0 + pd.Timedelta(minutes=i)
            vol = sigma_points_per_min * (1.0 + 2.0 * np.exp(-i / 25.0) + 0.6 * np.exp(-((i - 270) ** 2) / 800.0))
            drift = 0.0
            if i < 12:
                drift = direction * open_shock_points / 12.0
            else:
                drift = -reversion_strength * (price - fair)
            o = price
            steps = rng.normal(drift / 4.0, vol / 2.0, size=4)
            path = o + np.cumsum(steps)
            h = max(o, path.max())
            l = min(o, path.min())
            c = path[-1]
            v = float(rng.integers(200, 2000))
            rows.append((ts, round(o, 2), round(h, 2), round(l, 2), round(c, 2), v))
            price = c
        # overnight gap
        price = price + rng.normal(0.0, 40.0)
    df = pd.DataFrame(rows, columns=["ts", *COLUMNS]).set_index("ts")
    df.index = pd.DatetimeIndex(df.index, name="ts")
    return df
