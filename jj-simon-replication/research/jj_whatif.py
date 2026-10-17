"""What the JJ system could have done (docs/research/jj_lab.md): every signal its rules saw, taken or passed, replayed
on the real bars with other exits.

For a signal at bar t in direction d, the entry is the next bar's open plus 0.25 points of slippage (as the engine's).
From there to the firm's end of that trading day (the last bar before 16:10 ET, or the day's last bar):
  grid    every stop in STOPS against every target in TARGETS: R of the first touched, the stop first when one bar
          touches both, or of the close at the end of the day if neither
  hold    each stop with no target, closed at the end of the day
  mfe     the most the trade went in its favour (points), and when
  mae     the most it went against it
R is the engine's: (points less 0.25 of commission per contract) over the stop, the same for any contract count
($2.50 a side on a $20 point), with 0.25 points of slippage on the stop and the closing exit.

Nothing here is used by the live system or chosen on history; it describes forward days already scored.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SLIP = 0.25
COMMISSION_POINTS = 0.25  # $5 a round trip per contract over $20 a point
STOPS = (12.5, 25.0, 50.0)
TARGETS = (19.0, 38.0, 76.0, 100.0)


def r_of(points: float, stop: float) -> float:
    return (points - COMMISSION_POINTS) / stop


def day_end_index(mod: np.ndarray, td: np.ndarray, t: int, firm_close: int = 970) -> int:
    """The last bar of t's trading day before the firm's close (16:10 ET)."""
    same = np.flatnonzero(td == td[t])
    last = int(same[-1])
    early = same[(same >= t) & (mod[same] < firm_close) & (mod[same] < 1080)]
    return int(early[-1]) if len(early) else last


def replay(o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray, t: int, d: int, end: int) -> dict | None:
    """Every exit in the grid for a signal at bar t in direction d (entry at bar t + 1's open), to bar `end`."""
    if t + 1 > end:
        return None
    e = o[t + 1] + d * SLIP
    hh, ll = h[t + 1:end + 1], l[t + 1:end + 1]
    fav = (hh - e) if d > 0 else (e - ll)
    adv = (e - ll) if d > 0 else (hh - e)
    out = {"entry": float(e), "mfe": float(fav.max()), "mae": float(adv.max()), "mfe_bar": int(np.argmax(fav)) + 1, "bars": int(end - t)}
    close_pts = (c[end] - d * SLIP - e) * d
    for s in STOPS:
        hit_s = np.flatnonzero(adv >= s)
        first_s = hit_s[0] if len(hit_s) else None
        out[f"hold_{s:g}"] = r_of(-s - SLIP, s) if first_s is not None else r_of(close_pts, s)
        for tg in TARGETS:
            hit_t = np.flatnonzero(fav >= tg)
            first_t = hit_t[0] if len(hit_t) else None
            if first_s is not None and (first_t is None or first_s <= first_t):
                r = r_of(-s - SLIP, s)
            elif first_t is not None:
                r = r_of(tg, s)
            else:
                r = r_of(close_pts, s)
            out[f"{s:g}/{tg:g}"] = r
    return out


def replay_signals(bars: pd.DataFrame, signals: pd.DataFrame, td: np.ndarray, firm_close: int = 970) -> pd.DataFrame:
    """The grid for each signal row (columns index, d), on the bars the engine ran on."""
    o, h, l, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ny = bars.index.tz_convert("America/New_York")
    mod = (ny.hour * 60 + ny.minute).to_numpy()
    rows = []
    for _, s in signals.iterrows():
        t = int(s["index"])
        rep = replay(o, h, l, c, t, int(s["d"]), day_end_index(mod, td, t, firm_close))
        rows.append(rep or {})
    return pd.DataFrame(rows, index=signals.index)
