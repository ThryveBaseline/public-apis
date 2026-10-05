"""Candle and structure primitives: displacement candles and structure breaks."""
from __future__ import annotations


def is_displacement(o: float, h: float, l: float, c: float, direction: int, wick_pct: float = 0.20, min_body: float = 0.0) -> bool:
    """Displacement candle test.

    Public rule (fxreplay's codification of JJ Simon): the candle must close
    decisively, with the counter-wick measuring less than `wick_pct` (20%) of
    the distance from the candle's open to the extreme in the direction of
    the move. For a bullish candle that is (high - close) < 0.20 * (high - open).

    `min_body` (in points) is an additional size filter; the public sources
    say "strong" displacement but do not publish a size threshold, so the
    strategy exposes it as `min_body_atr` and defaults it conservatively.
    """
    if direction > 0:
        if c <= o:
            return False
        span = h - o
        if span <= 0:
            return False
        return (h - c) <= wick_pct * span and (c - o) >= min_body
    else:
        if c >= o:
            return False
        span = o - l
        if span <= 0:
            return False
        return (c - l) <= wick_pct * span and (o - c) >= min_body


def breaks_level(close: float, level: float, direction: int) -> bool:
    """Close beyond a swing level in the trade direction (BOS when with the
    trend, MSB/CHoCH when against it: same mechanical test)."""
    return close > level if direction > 0 else close < level
