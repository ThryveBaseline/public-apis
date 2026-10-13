"""The USD economic calendar the JJ system stream trades news from (docs/research/jj_system_v1.md).

Source: Forex Factory's weekly calendar feeds, the "red folder" (High) and "orange folder" (Medium) events JJ names,
fetched each night on the GB10 and kept as dated snapshots:
  <dir>/ff_thisweek_YYYYMMDDTHHMMSSZ.json and <dir>/ff_nextweek_YYYYMMDDTHHMMSSZ.json (the UTC fetch time),
each the feed's JSON list of {title, country, date, impact, forecast, previous}.

A trading day's events come from the latest snapshot fetched before that day began (18:00 ET the evening before)
whose week covers it, so a schedule is never read after the fact. A day no snapshot covers has no calendar, and the
runner does not score it.
"""
from __future__ import annotations

import glob
import json
import os
import re

import pandas as pd

NY = "America/New_York"
NAME = re.compile(r"ff_(thisweek|nextweek)_(\d{8}T\d{6}Z)\.json$")


def snapshots(folder: str) -> list[dict]:
    """Every snapshot in the folder: its fetch time (UTC), the Sunday-to-Saturday week it covers, and its events."""
    out = []
    for path in sorted(glob.glob(os.path.join(folder, "ff_*.json"))):
        m = NAME.search(os.path.basename(path))
        if not m:
            continue
        with open(path) as fh:
            raw = json.load(fh)
        ev = pd.DataFrame(raw)
        if ev.empty or "date" not in ev:
            continue
        t = pd.DatetimeIndex(pd.to_datetime(ev["date"], utc=True)).tz_convert(NY)
        ev = pd.DataFrame({"time": t, "country": ev.get("country", ""), "impact": ev.get("impact", ""), "title": ev.get("title", "")})
        mid = t.tz_localize(None).normalize().sort_values()[len(t) // 2]
        sunday = mid - pd.Timedelta(days=(mid.dayofweek + 1) % 7)
        fetched = pd.Timestamp(m.group(2))
        fetched = fetched.tz_localize("UTC") if fetched.tzinfo is None else fetched.tz_convert("UTC")
        out.append({"path": path, "fetched": fetched, "week": sunday, "events": ev})
    return out


def day_start(day: pd.Timestamp) -> pd.Timestamp:
    """When a trading day begins: 18:00 ET the evening before."""
    return (pd.Timestamp(day).normalize() - pd.Timedelta(hours=6)).tz_localize(NY)


def events_for(days, folder: str) -> tuple[pd.DataFrame, list]:
    """The calendar for each trading day (from the latest snapshot fetched before it began whose week covers it) and the
    days no snapshot covers."""
    snaps = snapshots(folder)
    rows, missing = [], []
    for d in sorted(pd.DatetimeIndex(days)):
        begin = day_start(d)
        sunday = d - pd.Timedelta(days=(d.dayofweek + 1) % 7)
        ok = [s for s in snaps if s["fetched"] < begin.tz_convert("UTC") and s["week"] == sunday]
        if not ok:
            missing.append(d)
            continue
        ev = max(ok, key=lambda s: s["fetched"])["events"]
        td = (ev["time"].dt.tz_localize(None) + pd.Timedelta(hours=6)).dt.normalize()
        rows.append(ev[td == d])
    cal = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["time", "country", "impact", "title"])
    return cal, missing
