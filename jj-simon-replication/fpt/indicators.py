"""Average True Range and swing (pivot) detection on 1-minute bars."""
from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.fillna(df["high"] - df["low"])


def atr(df: pd.DataFrame, period: int = 14, method: str = "wilder") -> pd.Series:
    """ATR in price points. 'wilder' (RMA, TradingView's default `ta.atr`) or 'sma'."""
    tr = true_range(df)
    if method == "sma":
        return tr.rolling(period, min_periods=1).mean()
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=1).mean()


def swing_points(df: pd.DataFrame, left: int = 3, right: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Pivot highs/lows (TradingView `ta.pivothigh/pivotlow` semantics).

    Returns two boolean arrays marking the pivot BAR. A pivot at bar i is only
    known once bar i+right has closed, so a backtester must not use pivot i
    before index i+right. Use `confirmed_at` for that bookkeeping.
    """
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    n = len(df)
    sh = np.zeros(n, dtype=bool)
    sl = np.zeros(n, dtype=bool)
    for i in range(left, n - right):
        hw = h[i - left : i + right + 1]
        lw = l[i - left : i + right + 1]
        if h[i] == hw.max() and (hw == h[i]).sum() == 1:
            sh[i] = True
        if l[i] == lw.min() and (lw == l[i]).sum() == 1:
            sl[i] = True
    return sh, sl


def confirmed_at(pivot_index: int, right: int) -> int:
    """Index of the first bar at which a pivot at `pivot_index` is confirmed."""
    return pivot_index + right
