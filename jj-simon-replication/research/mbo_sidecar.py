"""The MBO sidecar of the forward paper test (docs/research/mbo_sidecar_pilot.md): annotate-only, it never changes
a trade, a checkpoint or a candidate.

For each day of GLBX.MDP3 MBO data (ESZ6 and NQZ6, 00:00-21:00 UTC), the NQ order book is rebuilt from the day's
clear and snapshot and read at every regular-session minute boundary, 09:30 to 16:00 ET: the best bid and offer,
the depth of the five best levels each side, and the signed aggressor flow of NQ and ES over the minute before.
The day is admitted only if the trades it rebuilds reproduce the 1-minute bars of the bar file (by exchange or
receive time), and the book starts whole, never meets an unknown cancel or a possibly-bad-book flag, and is
never crossed, locked or one-sided at a boundary. Each S3 or S4 trade on an admitted day is then annotated with:

  E1  the market fill: the far touch at the entry minute's start;
  E2  a passive entry: a limit at the near touch, filled only if a trade prints through it within the minute (no
      queue assumed), else a market order at the far touch a minute later;
  S   book state at the signal: the five-level imbalance, the NQ flow and the ES flow, each signed in the trade's
      direction, flagged below the 20th percentile of the admitted forward sessions' boundaries; a trade is
      skip-flagged when both NQ imbalance and NQ flow are flagged. Forward sessions and trades only.

E1 and E2 are measured in ticks against the engine's entry and in R, replaying the trade's bracket from each entry
with the engine's exits; the engine's own entry must replay to its recorded R first. Raw MBO files are read where
they are stored and never copied; everything derived is private.

usage (on the GB10):
  python research/mbo_sidecar.py check --mbo /path/glbx-mdp3-20261006.mbo.dbn.zst      (integrity only; no feature is read)
  python research/mbo_sidecar.py day --mbo /path/glbx-mdp3-20261006.mbo.dbn.zst --bars data/forward/nq_1min_forward.csv \\
      --out research/private/mbo_sidecar
  python research/mbo_sidecar.py report --features research/private/mbo_sidecar --state research/private/forward_v1_state.json \\
      --bars data/forward/nq_1min_forward.csv --out research/private/mbo_sidecar_report.md
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import heapq
import json
import os
import struct
import sys
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import NY, load_minute_bars  # noqa: E402

PRICE_SCALE = 1_000_000_000
TICK = 0.25
LEVELS = 5
FLAG_PCT = 20  # a signed feature below this percentile of the reference sessions' distribution is flagged
BAR_MATCH = 0.99  # share of regular-session minutes whose rebuilt bar must equal the file's bar exactly
FIRST_UNSEEN = pd.Timestamp("2026-10-06")
SYMBOLS = ("NQZ6", "ESZ6")
MBO_DTYPE = np.dtype([("length", "u1"), ("rtype", "u1"), ("publisher_id", "<u2"), ("instrument_id", "<u4"), ("ts_event", "<u8"), ("order_id", "<u8"),
                      ("price", "<i8"), ("size", "<u4"), ("flags", "u1"), ("channel_id", "u1"), ("action", "S1"), ("side", "S1"), ("ts_recv", "<u8"),
                      ("ts_in_delta", "<i4"), ("sequence", "<u4")])
F_LAST, F_TOB, F_SNAPSHOT, F_BAD_TS_RECV, F_MAYBE_BAD_BOOK = 0x80, 0x40, 0x20, 0x08, 0x04
FLAT_MIN = 16 * 60  # the candidates' flat_time, 16:00 ET
SLIP, POINT_VALUE, COMMISSION_RT = 0.25, 20.0, 5.0  # the engine's per-contract conventions (fpt/strategy.StrategyConfig)
DIRECTION = {"long": 1.0, "short": -1.0}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_dbn(path: str) -> tuple[dict, np.ndarray]:
    """The metadata and the MBO records of a DBN version 3 file (zstd-compressed or not). Refuses anything else:
    another version, schema or record type, or a body that is not whole MBO records."""
    import databento_dbn

    raw = open(path, "rb").read()
    if raw[:4] == b"\x28\xb5\x2f\xfd":
        import zstandard

        raw = zstandard.ZstdDecompressor().stream_reader(raw).read()
    if raw[:3] != b"DBN" or raw[3] != 3:
        raise SystemExit(f"refusing: {path} is not DBN version 3")
    mlen = struct.unpack("<I", raw[4:8])[0]
    meta = databento_dbn.Metadata.decode(raw[:8 + mlen])
    if str(meta.schema).lower().split(".")[-1] != "mbo" or meta.dataset != "GLBX.MDP3":
        raise SystemExit(f"refusing: {path} is {meta.dataset} {meta.schema}, not GLBX.MDP3 mbo")
    body = raw[8 + mlen:]
    if len(body) % MBO_DTYPE.itemsize:
        raise SystemExit(f"refusing: {path} does not hold whole MBO records")
    rec = np.frombuffer(body, dtype=MBO_DTYPE)
    if len(rec) == 0 or (rec["length"] != MBO_DTYPE.itemsize // 4).any() or (rec["rtype"] != 0xA0).any():
        raise SystemExit(f"refusing: {path} holds records other than MBO")
    if list(meta.partial) or list(meta.not_found):
        raise SystemExit(f"refusing: {path} has partial {list(meta.partial)} or missing {list(meta.not_found)} symbols")
    ids = {}
    for sym, ivs in meta.mappings.items():
        found = {str(iv["symbol"]).strip() for iv in ivs}
        if len(found) != 1 or not next(iter(found)).isdigit():
            raise SystemExit(f"refusing: {sym} maps to {sorted(found)} within the file")
        ids[sym] = int(found.pop())
    info = {"start": int(meta.start), "end": int(meta.end), "symbols": list(meta.symbols), "ids": ids}
    return info, rec


def boundaries(day: pd.Timestamp) -> pd.DatetimeIndex:
    """The regular-session minute boundaries of a New York date, 09:30 to 16:00 ET inclusive, as UTC."""
    t0 = pd.Timestamp(day.date(), tz=NY) + pd.Timedelta(hours=9, minutes=30)
    return pd.date_range(t0, t0 + pd.Timedelta(hours=6, minutes=30), freq="1min").tz_convert("UTC")


class Book:
    """One instrument's order book by order (Databento MBO semantics: trades and fills leave the book alone; the
    resting side is reduced by the cancel or modify that follows)."""

    def __init__(self) -> None:
        self.orders: dict = {}
        self.levels = {b"B": defaultdict(int), b"A": defaultdict(int)}
        self.unknown_cancels = 0
        self.unknown_modifies = 0  # treated as adds, as in Databento's book example

    def clear(self) -> None:
        self.orders.clear()
        self.levels = {b"B": defaultdict(int), b"A": defaultdict(int)}

    def _take(self, side, price, size) -> None:
        lv = self.levels[side]
        lv[price] -= size
        if lv[price] <= 0:
            del lv[price]

    def apply(self, action, side, price, size, oid) -> None:
        if action == b"R":
            self.clear()
        elif action == b"A":
            if side in self.levels:
                self.orders[oid] = (side, price, size)
                self.levels[side][price] += size
        elif action == b"C":
            o = self.orders.get(oid)
            if o is None:
                self.unknown_cancels += 1
                return
            s, p, q = o
            cut = min(size, q)
            self._take(s, p, cut)
            if q - cut > 0:
                self.orders[oid] = (s, p, q - cut)
            else:
                del self.orders[oid]
        elif action == b"M":
            o = self.orders.pop(oid, None)
            if o is None:
                self.unknown_modifies += 1
            else:
                self._take(*o)
            if side in self.levels:
                self.orders[oid] = (side, price, size)
                self.levels[side][price] += size

    def top(self) -> dict:
        bid, ask = self.levels[b"B"], self.levels[b"A"]
        bp = heapq.nlargest(LEVELS, bid)
        ap = heapq.nsmallest(LEVELS, ask)
        return {"bid": bp[0] / PRICE_SCALE if bp else np.nan, "ask": ap[0] / PRICE_SCALE if ap else np.nan,
                "bid_depth": float(sum(bid[p] for p in bp)), "ask_depth": float(sum(ask[p] for p in ap))}


def day_features(rec: np.ndarray, ids: dict, day: pd.Timestamp) -> tuple[pd.DataFrame, dict, dict]:
    """Per regular-session boundary T (state after every NQ record received before T): NQ's best bid and offer and
    five-level depth; the signed aggressor flow of NQ and ES over [T - 60 s, T); NQ's aggressor trade range over
    [T, T + 60 s). Prints without an aggressor side are left out of flow and range. Also NQ's 1-minute bars rebuilt
    from its trades, by exchange time and by receive time, and the book's integrity counters."""
    nq, es = ids["NQZ6"], ids["ESZ6"]
    bnd = boundaries(day)
    bnd_ns = bnd.as_unit("ns").asi8
    q = rec[rec["instrument_id"] == nq]
    if len(q) == 0:
        raise SystemExit("refusing: no NQ records")
    if (np.diff(q["ts_recv"].astype(np.int64)) < 0).any():
        raise SystemExit("refusing: NQ records are not in receive-time order")
    if (q["flags"] & F_TOB).any():
        raise SystemExit("refusing: top-of-book records in an MBO file")
    clear = bool(q["action"][0] == b"R")
    snap = (q["flags"] & F_SNAPSHOT != 0)[1 if clear else 0:]
    n_snap = int(np.argmin(snap)) if not snap.all() else len(snap)  # the snapshot records leading the day, after the clear
    counters = {"nq_records": int(len(q)), "starts_with_clear": clear,
                "snapshot_records": n_snap,
                "maybe_bad_book_records": int(((q["flags"] & F_MAYBE_BAD_BOOK != 0) & (q["ts_recv"].astype(np.int64) < bnd_ns[-1] + 60 * PRICE_SCALE)).sum()),
                "maybe_bad_book_records_all_day": int((q["flags"] & F_MAYBE_BAD_BOOK != 0).sum()),
                "bad_ts_recv_records": int((q["flags"] & F_BAD_TS_RECV != 0).sum())}
    book = Book()
    rows, mid_event = [], 0
    ts, act, side, price, size, oid, flags = (q[k].tolist() for k in ("ts_recv", "action", "side", "price", "size", "order_id", "flags"))
    j, n = 0, len(ts)
    for t in bnd_ns.tolist():
        while j < n and ts[j] < t:
            book.apply(act[j], side[j], price[j], size[j], oid[j])
            j += 1
        if j and not flags[j - 1] & F_LAST:
            mid_event += 1
        rows.append(book.top())
    f = pd.DataFrame(rows, index=bnd)
    edges = np.r_[bnd_ns[0] - 60 * PRICE_SCALE, bnd_ns, bnd_ns[-1] + 60 * PRICE_SCALE]  # [09:29, 09:30, ..., 16:00, 16:01]
    trades = {}
    for name, iid in (("nq", nq), ("es", es)):
        t = rec[(rec["instrument_id"] == iid) & (rec["action"] == b"T")]
        trades[name] = pd.DataFrame({"ts_recv": t["ts_recv"].astype("int64"), "ts_event": t["ts_event"].astype("int64"), "price": t["price"] / PRICE_SCALE,
                                     "size": t["size"].astype(float), "sign": np.where(t["side"] == b"B", 1.0, np.where(t["side"] == b"A", -1.0, 0.0))})
    for name, tr in trades.items():
        sided = tr[tr["sign"] != 0]
        k = np.searchsorted(edges, sided["ts_recv"].to_numpy(), side="right") - 1  # bucket k: [edges[k], edges[k + 1])
        g = pd.DataFrame({"k": k, "signed": sided["sign"] * sided["size"], "size": sided["size"], "price": sided["price"]})
        g = g[(g["k"] >= 0) & (g["k"] < len(edges) - 1)]
        agg = g.groupby("k").agg(signed=("signed", "sum"), vol=("size", "sum"), lo=("price", "min"), hi=("price", "max"))
        flow = (agg["signed"] / agg["vol"]).reindex(range(len(edges) - 1))
        f[f"{name}_flow"] = flow.to_numpy()[:len(bnd)]  # boundary i: bucket i, [T - 60 s, T)
        if name == "nq":
            f["next_lo"] = agg["lo"].reindex(range(len(edges) - 1)).to_numpy()[1:]  # boundary i: bucket i + 1, [T, T + 60 s)
            f["next_hi"] = agg["hi"].reindex(range(len(edges) - 1)).to_numpy()[1:]
    f["spread_ticks"] = (f["ask"] - f["bid"]) / TICK
    f["imbalance"] = (f["bid_depth"] - f["ask_depth"]) / (f["bid_depth"] + f["ask_depth"])
    tq = trades["nq"]
    rebuilt = {}
    for clock in ("ts_event", "ts_recv"):
        minute = pd.to_datetime(tq[clock], utc=True).dt.floor("1min")
        rebuilt[clock] = tq.assign(minute=minute).groupby("minute").agg(open=("price", "first"), high=("price", "max"), low=("price", "min"),
                                                                        close=("price", "last"), volume=("size", "sum"))
    counters.update({"unknown_cancels": int(book.unknown_cancels), "unknown_modifies": int(book.unknown_modifies), "mid_event_boundaries": int(mid_event),
                     "crossed_or_locked_boundaries": int((f["bid"] >= f["ask"]).sum()), "empty_side_boundaries": int(f[["bid", "ask"]].isna().any(axis=1).sum())})
    return f, rebuilt, counters


def bar_match(rebuilt: pd.DataFrame, bars: pd.DataFrame, day: pd.Timestamp, nq_id: int) -> dict:
    """Rebuilt NQ bars against the forward file's bars for the same contract, over the date's regular session."""
    b = bars[bars["symbol"].astype(str) == str(nq_id)]
    b = b[(b.index >= boundaries(day)[0]) & (b.index < boundaries(day)[-1])]
    if b.empty:
        return {"minutes": 0, "matched": 0, "share": 0.0, "note": f"the bar file holds no bar of instrument {nq_id} in this session"}
    r = rebuilt.reindex(b.index.tz_convert("UTC"))
    same = np.ones(len(b), dtype=bool)
    for c in ("open", "high", "low", "close", "volume"):
        same &= np.isclose(r[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float), atol=1e-9, rtol=0)
    return {"minutes": int(len(b)), "matched": int(same.sum()), "share": float(same.mean())}


def admitted(match: dict, c: dict) -> bool:
    """The admission rule, fixed before any book was read: the rebuilt bars reproduce the bar file's on at least 99%
    of the regular session's minutes, by exchange time or by receive time (which Databento's bars use is not
    documented beyond doubt; both are recorded); the book starts from a clear and a snapshot, never meets a
    cancel of an unknown order or a record flagged as a possibly bad book, and is never crossed, locked or empty
    on a side at a boundary."""
    bars_ok = max(m["share"] for m in match.values()) >= BAR_MATCH
    book_ok = (c["starts_with_clear"] and c["snapshot_records"] > 0 and c["unknown_cancels"] == 0 and c["maybe_bad_book_records"] == 0
               and c["crossed_or_locked_boundaries"] == 0 and c["empty_side_boundaries"] == 0)
    return bool(bars_ok and book_ok)


def check_mode(a) -> int:
    """Integrity only, before any book is read: the file's metadata, NQ's first records (action, side, flags, receive
    and exchange times), whether receive times are in order, the clear and snapshot run, the possibly-bad-book flags,
    and a pass of the book that counts cancels and modifies of unknown orders. No feature is computed."""
    info, rec = read_dbn(a.mbo)
    q = rec[rec["instrument_id"] == info["ids"].get("NQZ6", -1)]
    snap = q["flags"] & F_SNAPSHOT != 0
    book = Book()
    for act, side, price, size, oid in zip(*(q[k].tolist() for k in ("action", "side", "price", "size", "order_id"))):
        book.apply(act, side, price, size, oid)
    ts = q["ts_recv"].astype(np.int64)
    out = {"file": os.path.basename(a.mbo), "mbo_sha256": sha256(a.mbo), "start": str(pd.Timestamp(info["start"], unit="ns", tz="UTC")),
           "end": str(pd.Timestamp(info["end"], unit="ns", tz="UTC")), "symbols": info["symbols"], "ids": info["ids"], "records": int(len(rec)),
           "nq_records": int(len(q)), "nq_ts_recv_decreases": int((np.diff(ts) < 0).sum()), "first_is_clear": bool(len(q) and q["action"][0] == b"R"),
           "snapshot_flagged": int(snap.sum()), "snapshot_flagged_in_first_run_after_clear": int(np.argmin(snap[1:])) if len(q) > 1 and not snap[1:].all() else int(snap[1:].sum()),
           "maybe_bad_book": int((q["flags"] & F_MAYBE_BAD_BOOK != 0).sum()), "bad_ts_recv": int((q["flags"] & F_BAD_TS_RECV != 0).sum()),
           "unknown_cancels": book.unknown_cancels, "unknown_modifies": book.unknown_modifies,
           "first_records": [{"action": r["action"].decode(), "side": r["side"].decode(), "flags": hex(int(r["flags"])),
                              "ts_recv": str(pd.Timestamp(int(r["ts_recv"]), unit="ns", tz="UTC")), "ts_event": str(pd.Timestamp(int(r["ts_event"]), unit="ns", tz="UTC"))}
                             for r in q[:20]]}
    print(json.dumps(out, indent=1))
    return 0


def day_mode(a) -> int:
    info, rec = read_dbn(a.mbo)
    if sorted(info["ids"]) != sorted(SYMBOLS):
        raise SystemExit(f"refusing: the file maps {sorted(info['ids'])}, not {list(SYMBOLS)}")
    start = pd.Timestamp(info["start"], unit="ns", tz="UTC")
    day = pd.Timestamp(start.date())
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, day.strftime("%Y-%m-%d"))
    try:
        f, rebuilt, counters = day_features(rec, info["ids"], day)
    except SystemExit as e:  # a refused day still leaves its record, not admitted
        with open(stem + ".check.json", "w") as fh:
            json.dump({"date": day.strftime("%Y-%m-%d"), "mbo_sha256": sha256(a.mbo), "refused": str(e), "admitted": False}, fh, indent=1, sort_keys=True)
        raise
    bars = load_minute_bars(a.bars, source_tz="UTC")
    match = {clock: bar_match(rb, bars, day, info["ids"]["NQZ6"]) for clock, rb in rebuilt.items()}
    f.to_csv(stem + ".features.csv", index_label="boundary")
    check = {"date": day.strftime("%Y-%m-%d"), "mbo_sha256": sha256(a.mbo), "bars_sha256": sha256(a.bars), "ids": info["ids"], "bar_match": match,
             **counters, "admitted": admitted(match, counters)}
    with open(stem + ".check.json", "w") as fh:
        json.dump(check, fh, indent=1, sort_keys=True)
    print(json.dumps(check, indent=1, sort_keys=True))
    return 0


def reference_cuts(feats: dict) -> dict:
    """The 20th percentile of each signed feature over every boundary of the reference sessions, both directions
    counted (a long's adverse value is a short's favourable one)."""
    cuts = {}
    for k in ("imbalance", "nq_flow", "es_flow"):
        x = pd.concat([f[k] for f in feats.values()]).dropna().to_numpy()
        cuts[k] = float(np.percentile(np.r_[x, -x], FLAG_PCT)) if len(x) else float("nan")
    return cuts


def replay(day_bars: pd.DataFrame, i0: int, d: float, entry: float, stop_pts: float, target_pts: float, stop_only_first: bool) -> tuple[float, str]:
    """The engine's exits from bar i0 of the day's bars before 16:00 (research/engine.py): the stop first (filled a
    tick through), then the target, else flat at the close of the last bar before 16:00 a tick through. With
    stop_only_first the target is not checked on the first bar (a fill inside it: what printed before is unknown).
    R per contract, the engine's commission included."""
    o, h, l, c = (day_bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    stop, target = entry - d * stop_pts, entry + d * target_pts
    for t in range(i0, len(c)):
        ex = None
        if d > 0:
            if l[t] <= stop:
                ex, why = stop - SLIP, "stop"
            elif not (stop_only_first and t == i0) and h[t] >= target:
                ex, why = target, "target"
        else:
            if h[t] >= stop:
                ex, why = stop + SLIP, "stop"
            elif not (stop_only_first and t == i0) and l[t] <= target:
                ex, why = target, "target"
        if ex is None and t == len(c) - 1:
            ex, why = c[t] - d * SLIP, "flat"
        if ex is not None:
            return ((ex - entry) * d * POINT_VALUE - COMMISSION_RT) / (stop_pts * POINT_VALUE), why
    return float("nan"), "no bar"


def annotate(trades: pd.DataFrame, feats: dict, cuts: dict, bars: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """E1, E2, their R and the skip flags for each trade whose date has admitted features. The engine's own entry is
    replayed first and must give the recorded R and exit, or the trade is set aside as a replay mismatch. Returns
    the annotations and the trades set aside, with the reason."""
    out, aside = [], []
    ny_day = bars.index.tz_convert(NY).normalize()
    for _, t in trades.iterrows():
        key = str(t["direction"]).strip().lower()
        if key not in DIRECTION:
            raise SystemExit(f"refusing: unknown trade direction {t['direction']!r}")
        d = DIRECTION[key]
        T = pd.Timestamp(t["entry_time"]).tz_convert("UTC")
        f = feats.get(t["date"])
        if f is None or T not in f.index:
            aside.append((t["candidate"], t["date"], "no admitted book for the day" if f is None else "entry not at a boundary"))
            continue
        day = bars[(ny_day == T.tz_convert(NY).normalize())]
        mod = day.index.tz_convert(NY).hour * 60 + day.index.tz_convert(NY).minute
        day = day[mod < FLAT_MIN]
        if T not in day.index:
            aside.append((t["candidate"], t["date"], "no bar at the entry"))
            continue
        i0 = day.index.get_loc(T)
        engine, sp, tp = float(t["entry"]), abs(float(t["entry"]) - float(t["stop"])), abs(float(t["target"]) - float(t["entry"]))
        r0, why0 = replay(day, i0, d, engine, sp, tp, False)
        if not (abs(r0 - float(t["r"])) < 1e-6 and why0 == str(t["exit_reason"])):
            aside.append((t["candidate"], t["date"], "replay mismatch"))
            continue
        i = f.index.get_loc(T)
        row = f.iloc[i]
        far = row["ask"] if d > 0 else row["bid"]
        near = row["bid"] if d > 0 else row["ask"]
        r1, _ = replay(day, i0, d, far, sp, tp, False)
        through = bool((row["next_lo"] < near) if d > 0 else (row["next_hi"] > near))
        later = T + pd.Timedelta(minutes=1)
        if not through and i0 + 1 < len(day) and day.index[i0 + 1] != later:
            aside.append((t["candidate"], t["date"], "no bar a minute after the entry"))
            continue
        if through:
            fill = near
            r2, _ = replay(day, i0, d, near, sp, tp, True)
        elif i + 1 < len(f) and i0 + 1 < len(day) and day.index[i0 + 1] == f.index[i + 1]:
            fill = f.iloc[i + 1]["ask"] if d > 0 else f.iloc[i + 1]["bid"]
            r2, _ = replay(day, i0 + 1, d, fill, sp, tp, False)
        else:
            fill, r2 = float("nan"), 0.0  # no later bar before 16:00: the passive order never trades
        sig = {k: d * row[k] for k in ("imbalance", "nq_flow", "es_flow")}
        flags = {f"flag_{k}": bool(v < cuts[k]) for k, v in sig.items()}
        out.append({"candidate": t["candidate"], "date": t["date"], "entry_time": str(T), "direction": key, "r": float(t["r"]), "exit_reason": t["exit_reason"],
                    "e1_ticks": d * (engine - far) / TICK, "e2_filled": through, "e2_ticks": d * (engine - fill) / TICK if np.isfinite(fill) else np.nan,
                    "r_e1": r1, "r_e2": r2, "dr_e1": r1 - r0, "dr_e2": r2 - r0, "spread_ticks": row["spread_ticks"],
                    **{f"signed_{k}": v for k, v in sig.items()}, **flags, "skip_flag": flags["flag_imbalance"] and flags["flag_nq_flow"]})
    return pd.DataFrame(out), aside


def load_features(folder: str) -> tuple[dict, list]:
    feats, checks = {}, []
    for path in sorted(glob.glob(os.path.join(folder, "*.check.json"))):
        with open(path) as fh:
            c = json.load(fh)
        checks.append(c)
        if c["admitted"]:
            feats[c["date"]] = pd.read_csv(path.replace(".check.json", ".features.csv"), index_col="boundary", parse_dates=["boundary"])
    return feats, checks


def report_mode(a) -> int:
    """Forward sessions only (the forward-only policy, docs/research/FORWARD_POLICY.md): the flags' reference is the
    admitted forward sessions' own boundaries, both directions (context, not trades), and only forward trades are
    annotated."""
    feats, checks = load_features(a.features)
    fwd = {d: f for d, f in feats.items() if pd.Timestamp(d) >= FIRST_UNSEEN}
    if not fwd:
        raise SystemExit("refusing: no admitted forward session")
    cuts = reference_cuts(fwd)
    with open(a.state) as fh:
        state = json.load(fh)
    trades = pd.DataFrame(state["trades"])
    bars = load_minute_bars(a.bars, source_tz="UTC")
    ann, aside = annotate(trades, fwd, cuts, bars)
    s = ["# MBO sidecar pilot: annotations (private)\n",
         f"Forward sessions admitted: {len(fwd)}. Flags at the {FLAG_PCT}th percentile of each signed feature over the admitted forward sessions' "
         "boundaries: " + ", ".join(f"{k} {v:+.3f}" for k, v in cuts.items()) + ".\n",
         "| date | admitted | bars matched (exchange time / receive time) | clear + snapshot | unknown cancels / modifies | possibly bad book | crossed or locked |",
         "|---|---|---|---|---|---|---|"]
    for c in checks:
        if "refused" in c:
            s.append(f"| {c['date']} | False ({c['refused']}) | | | | | |")
            continue
        m = c["bar_match"]
        s.append(f"| {c['date']} | {c['admitted']} | {m['ts_event']['matched']}/{m['ts_event']['minutes']} / {m['ts_recv']['matched']}/{m['ts_recv']['minutes']} | "
                 f"{c['starts_with_clear']} + {c['snapshot_records']} | {c['unknown_cancels']} / {c['unknown_modifies']} | {c['maybe_bad_book_records']} | "
                 f"{c['crossed_or_locked_boundaries']} |")
    s += ["", "Trades set aside: " + (", ".join(f"{k}: {v}" for k, v in pd.Series([x[2] for x in aside]).value_counts().items()) if aside else "none") + ".\n",
          "| candidate | trades | E1 ticks | E2 ticks | E2 filled | R change, market fill | R change, passive | passive better in R | "
          "filled: passive - market, R | unfilled: passive - market, R | skip-flagged | R flagged | R not flagged |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name in ("S3", "S4"):
        p = ann[ann["candidate"] == name] if len(ann) else ann
        if not len(p):
            s.append(f"| {name} | 0 |" + " |" * 11)
            continue
        gain = p["dr_e2"] - p["dr_e1"]
        fl, filled = p[p["skip_flag"]], p["e2_filled"]
        s.append(f"| {name} | {len(p)} | {p['e1_ticks'].mean():+.2f} | {p['e2_ticks'].mean():+.2f} | {filled.mean():.0%} | {p['dr_e1'].mean():+.3f} | "
                 f"{p['dr_e2'].mean():+.3f} | {(gain > 0).sum()} of {len(p)} | {gain[filled].mean() if filled.any() else float('nan'):+.3f} ({int(filled.sum())}) | "
                 f"{gain[~filled].mean() if (~filled).any() else float('nan'):+.3f} ({int((~filled).sum())}) | {len(fl)} | "
                 f"{fl['r'].mean() if len(fl) else float('nan'):+.2f} | {p[~p['skip_flag']]['r'].mean():+.2f} |")
    s += ["", "Ticks are against the engine's assumed entry (positive: better). R changes replay each trade's bracket from that entry against the engine's own "
          "R. 'Obvious' (fixed before day 10): the passive entry beats the market fill in R on average and on a majority of the forward trades. "
          "Observations only: any change they suggest is a new, frozen version judged on later forward data."]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write("\n".join(s) + "\n")
    ann.to_csv(os.path.splitext(a.out)[0] + ".csv", index=False)
    print("\n".join(s))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    k = sub.add_parser("check")
    k.add_argument("--mbo", required=True)
    d = sub.add_parser("day")
    d.add_argument("--mbo", required=True)
    d.add_argument("--bars", required=True, help="1-minute bars covering the day, prepared as the sealed file (symbol = instrument_id)")
    d.add_argument("--out", required=True)
    r = sub.add_parser("report")
    r.add_argument("--features", required=True)
    r.add_argument("--state", required=True)
    r.add_argument("--bars", required=True, help="the forward bar file")
    r.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"check": check_mode, "day": day_mode, "report": report_mode}[a.mode](a)


if __name__ == "__main__":
    raise SystemExit(main())
