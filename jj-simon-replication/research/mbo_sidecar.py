"""The MBO sidecar of the forward paper test (docs/research/mbo_sidecar_pilot.md): annotate-only, it never changes
a trade, a checkpoint or a candidate.

For each day of GLBX.MDP3 MBO data (ESZ6 and NQZ6, 00:00-21:00 UTC), the NQ order book is rebuilt from the
midnight snapshot and read at every regular-session minute boundary, 09:30 to 16:00 ET: the best bid and offer,
the depth of the five best levels each side, and the signed aggressor flow of NQ and ES over the minute before.
The day is admitted only if the trades it rebuilds reproduce the 1-minute bars of the forward file and the book
is never crossed or locked at a boundary. Each S3 or S4 trade on an admitted day is then annotated with:

  E1  the market fill: the far touch at the entry minute's start, against the engine's assumed entry (the bar's
      open plus one tick of slippage), in ticks (positive: the real fill was better than the engine assumed);
  E2  a passive entry: a limit at the near touch at the entry minute's start, filled only if a trade prints
      through it within the minute (no queue assumed), else a market order at the far touch a minute later;
  S   book state at the signal: the five-level imbalance, the NQ flow and the ES flow, each signed in the trade's
      direction, flagged when below the reference sessions' 20th percentile (the round-1 sessions, bought before
      the forward test); a trade is skip-flagged when both NQ imbalance and NQ flow are flagged.

Raw MBO files are read where they are stored and never copied; everything derived is private.

usage (on the GB10):
  python research/mbo_sidecar.py day --mbo /path/glbx-mdp3-20261006.mbo.dbn.zst --bars data/forward/nq_1min_forward.csv \\
      --out research/private/mbo_sidecar
  python research/mbo_sidecar.py report --features research/private/mbo_sidecar --state research/private/forward_v1_state.json \\
      --reference-trades research/private/forward_v1_baseline_trades.csv --out research/private/mbo_sidecar_report.md
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
F_LAST, F_TOB = 0x80, 0x40


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
    ids = {}
    for sym, ivs in meta.mappings.items():
        found = {int(iv["symbol"]) for iv in ivs}
        if len(found) != 1:
            raise SystemExit(f"refusing: {sym} maps to {sorted(found)} within the file")
        ids[sym] = found.pop()
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
        self.unknown = 0

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
                self.unknown += 1
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
                self.unknown += 1
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


def day_features(rec: np.ndarray, ids: dict, day: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Per regular-session boundary T (state after every record received before T): NQ's best bid and offer and
    five-level depth, and the signed aggressor flow of NQ and ES over [T - 60 s, T); NQ's trade range over
    [T, T + 60 s). Also NQ's 1-minute bars rebuilt from its trades, by exchange time, and the book's counters."""
    nq, es = ids["NQZ6"], ids["ESZ6"]
    bnd = boundaries(day)
    bnd_ns = bnd.as_unit("ns").asi8
    order = np.argsort(rec["ts_recv"], kind="stable")
    if not (order == np.arange(len(rec))).all():
        rec = rec[order]
    q = rec[rec["instrument_id"] == nq]
    if (q["flags"] & F_TOB).any():
        raise SystemExit("refusing: top-of-book records in an MBO file")
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
    trades = {}
    for name, iid in (("nq", nq), ("es", es)):
        t = rec[(rec["instrument_id"] == iid) & (rec["action"] == b"T")]
        trades[name] = pd.DataFrame({"ts_recv": t["ts_recv"].astype("int64"), "ts_event": t["ts_event"].astype("int64"), "price": t["price"] / PRICE_SCALE,
                                     "size": t["size"].astype(float), "sign": np.where(t["side"] == b"B", 1.0, np.where(t["side"] == b"A", -1.0, 0.0))})
    for name, tr in trades.items():
        k = np.searchsorted(bnd_ns, tr["ts_recv"].to_numpy(), side="right")  # trade in [bnd[k-1], bnd[k])
        g = pd.DataFrame({"k": k, "signed": tr["sign"] * tr["size"], "size": tr["size"], "price": tr["price"]})
        g = g[(g["k"] >= 1) & (g["k"] <= len(bnd))]
        agg = g.groupby("k").agg(signed=("signed", "sum"), vol=("size", "sum"), lo=("price", "min"), hi=("price", "max"))
        # flow over [T - 60 s, T) belongs to boundary T = bnd[k]; the range over [T, T + 60 s) to boundary bnd[k - 1]
        flow = (agg["signed"] / agg["vol"]).reindex(range(1, len(bnd) + 1))
        f[f"{name}_flow"] = np.r_[np.nan, flow.to_numpy()[:-1]]
        if name == "nq":
            f["next_lo"] = agg["lo"].reindex(range(1, len(bnd) + 1)).to_numpy()
            f["next_hi"] = agg["hi"].reindex(range(1, len(bnd) + 1)).to_numpy()
    f["spread_ticks"] = (f["ask"] - f["bid"]) / TICK
    f["imbalance"] = (f["bid_depth"] - f["ask_depth"]) / (f["bid_depth"] + f["ask_depth"])
    tq = trades["nq"]
    minute = pd.to_datetime(tq["ts_event"], utc=True).dt.floor("1min")
    bars = tq.assign(minute=minute).groupby("minute").agg(open=("price", "first"), high=("price", "max"), low=("price", "min"),
                                                          close=("price", "last"), volume=("size", "sum"))
    counters = {"nq_records": int(len(q)), "unknown_order_events": int(book.unknown), "mid_event_boundaries": int(mid_event),
                "crossed_or_locked_boundaries": int((f["bid"] >= f["ask"]).sum()), "empty_side_boundaries": int(f[["bid", "ask"]].isna().any(axis=1).sum())}
    return f, bars, counters


def bar_match(rebuilt: pd.DataFrame, bars: pd.DataFrame, day: pd.Timestamp, nq_id: int) -> dict:
    """Rebuilt NQ bars against the forward file's bars for the same contract, over the date's regular session."""
    b = bars[bars["symbol"].astype(str) == str(nq_id)]
    b = b[(b.index >= boundaries(day)[0]) & (b.index < boundaries(day)[-1])]
    if b.empty:
        return {"minutes": 0, "matched": 0, "share": 0.0}
    r = rebuilt.reindex(b.index.tz_convert("UTC"))
    same = np.ones(len(b), dtype=bool)
    for c in ("open", "high", "low", "close", "volume"):
        same &= np.isclose(r[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float), atol=1e-9, rtol=0)
    return {"minutes": int(len(b)), "matched": int(same.sum()), "share": float(same.mean())}


def day_mode(a) -> int:
    info, rec = read_dbn(a.mbo)
    if sorted(info["ids"]) != sorted(SYMBOLS):
        raise SystemExit(f"refusing: the file maps {sorted(info['ids'])}, not {list(SYMBOLS)}")
    start = pd.Timestamp(info["start"], unit="ns", tz="UTC")
    day = pd.Timestamp(start.date())
    f, rebuilt, counters = day_features(rec, info["ids"], day)
    bars = load_minute_bars(a.bars, source_tz="UTC")
    match = bar_match(rebuilt, bars, day, info["ids"]["NQZ6"])
    admitted = match["share"] >= BAR_MATCH and counters["crossed_or_locked_boundaries"] == 0 and counters["empty_side_boundaries"] == 0
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.join(a.out, day.strftime("%Y-%m-%d"))
    f.to_csv(stem + ".features.csv", index_label="boundary")
    check = {"date": day.strftime("%Y-%m-%d"), "mbo_sha256": sha256(a.mbo), "bars_sha256": sha256(a.bars), "ids": info["ids"], "bar_match": match,
             **counters, "admitted": bool(admitted)}
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


def annotate(trades: pd.DataFrame, feats: dict, cuts: dict) -> pd.DataFrame:
    """E1, E2 and the skip flags for each trade whose date has admitted features."""
    out = []
    for _, t in trades.iterrows():
        f = feats.get(t["date"])
        if f is None:
            continue
        T = pd.Timestamp(t["entry_time"]).tz_convert("UTC")
        if T not in f.index:
            continue
        i = f.index.get_loc(T)
        row = f.iloc[i]
        d = 1.0 if str(t["direction"]).lower() in ("long", "1") else -1.0
        engine = float(t["entry"])
        far = row["ask"] if d > 0 else row["bid"]
        near = row["bid"] if d > 0 else row["ask"]
        through = (row["next_lo"] < near) if d > 0 else (row["next_hi"] > near)
        later = f.iloc[i + 1] if i + 1 < len(f) else row
        fill = near if through else (later["ask"] if d > 0 else later["bid"])
        sig = {k: d * row[k] for k in ("imbalance", "nq_flow", "es_flow")}
        flags = {f"flag_{k}": bool(v < cuts[k]) for k, v in sig.items()}
        out.append({"candidate": t["candidate"], "date": t["date"], "entry_time": str(T), "direction": "long" if d > 0 else "short", "r": float(t["r"]),
                    "exit_reason": t["exit_reason"], "stop_points": abs(engine - float(t["stop"])), "e1_ticks": d * (engine - far) / TICK,
                    "e2_filled": bool(through), "e2_ticks": d * (engine - fill) / TICK, "spread_ticks": row["spread_ticks"],
                    **{f"signed_{k}": v for k, v in sig.items()}, **flags, "skip_flag": flags["flag_imbalance"] and flags["flag_nq_flow"]})
    return pd.DataFrame(out)


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
    feats, checks = load_features(a.features)
    ref = {d: f for d, f in feats.items() if pd.Timestamp(d) < FIRST_UNSEEN}
    fwd = {d: f for d, f in feats.items() if pd.Timestamp(d) >= FIRST_UNSEEN}
    cuts = reference_cuts(ref)
    with open(a.state) as fh:
        state = json.load(fh)
    trades = pd.DataFrame(state["trades"])
    if a.reference_trades:
        old = pd.read_csv(a.reference_trades)
        old["date"] = pd.to_datetime(old["date"]).dt.strftime("%Y-%m-%d")
        trades = pd.concat([old[old["date"].isin(ref)], trades], ignore_index=True)
    ann = annotate(trades, feats, cuts)
    s = ["# MBO sidecar pilot: annotations (private)\n",
         f"Reference sessions (before the forward test): {len(ref)} admitted; forward: {len(fwd)} admitted. Flags at the reference "
         f"{FLAG_PCT}th percentile of each signed feature: " + ", ".join(f"{k} {v:+.3f}" for k, v in cuts.items()) + ".\n",
         "| date | admitted | bars matched | crossed or locked | unknown order events |", "|---|---|---|---|---|"]
    for c in checks:
        s.append(f"| {c['date']} | {c['admitted']} | {c['bar_match']['matched']}/{c['bar_match']['minutes']} | {c['crossed_or_locked_boundaries']} | "
                 f"{c['unknown_order_events']} |")
    s += ["", "| set | candidate | trades | E1 ticks | E2 ticks | E2 filled | skip-flagged | R flagged | R not flagged |", "|---|---|---|---|---|---|---|---|---|"]
    for label, part in (("reference", ann[ann["date"].map(lambda d: pd.Timestamp(d) < FIRST_UNSEEN)] if len(ann) else ann),
                        ("forward", ann[ann["date"].map(lambda d: pd.Timestamp(d) >= FIRST_UNSEEN)] if len(ann) else ann)):
        for name in ("S3", "S4"):
            p = part[part["candidate"] == name] if len(part) else part
            if not len(p):
                s.append(f"| {label} | {name} | 0 | | | | | | |")
                continue
            fl = p[p["skip_flag"]]
            s.append(f"| {label} | {name} | {len(p)} | {p['e1_ticks'].mean():+.2f} | {p['e2_ticks'].mean():+.2f} | {p['e2_filled'].mean():.0%} | {len(fl)} | "
                     f"{fl['r'].mean() if len(fl) else float('nan'):+.2f} | {p[~p['skip_flag']]['r'].mean():+.2f} |")
    s += ["", "Ticks are against the engine's assumed entry (positive: better). Each trade is listed in the CSV beside this report."]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        fh.write("\n".join(s) + "\n")
    ann.to_csv(os.path.splitext(a.out)[0] + ".csv", index=False)
    print("\n".join(s))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("day")
    d.add_argument("--mbo", required=True)
    d.add_argument("--bars", required=True, help="1-minute bars covering the day, prepared as the sealed file (symbol = instrument_id)")
    d.add_argument("--out", required=True)
    r = sub.add_parser("report")
    r.add_argument("--features", required=True)
    r.add_argument("--state", required=True)
    r.add_argument("--reference-trades")
    r.add_argument("--out", required=True)
    a = ap.parse_args()
    return day_mode(a) if a.mode == "day" else report_mode(a)


if __name__ == "__main__":
    raise SystemExit(main())
