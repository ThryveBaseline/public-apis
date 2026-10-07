"""Gate for the research engine on real data: with every hook at its default, research.engine must rebuild the
sealed ledger byte for byte.

Checks, in order, refusing at the first failure: the bar file is the sealed run's (sha256 in the manifest); the
research engine's ledger, written exactly as scripts/seal_run.py writes trades.csv, has the manifest's trades sha256.
Prints the two hashes and PASS; writes nothing outside a temporary directory.

usage: python research/engine_check.py --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fpt.data import load_minute_bars  # noqa: E402
from research.engine import ResearchConfig, generate_trades  # noqa: E402


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--source-tz", default="UTC")
    ap.add_argument("--manifest", required=True)
    a = ap.parse_args()
    with open(a.manifest) as fh:
        m = json.load(fh)
    data_sha = sha256(a.csv)
    if data_sha != m["data"]["sha256"]:
        raise SystemExit(f"refusing: the bar file is not the sealed run's ({data_sha} != {m['data']['sha256']})")
    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    trades = generate_trades(bars, ResearchConfig())
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "trades.csv")
        trades.to_csv(p, index=False)
        got = sha256(p)
    want = m["outputs"]["trades_sha256"]
    print(f"bar file sha256 {data_sha} (sealed)\nresearch engine ledger sha256 {got}\nsealed ledger sha256 {want}\ntrades {len(trades)} (sealed {m['outputs']['n_trades']})")
    if got != want:
        raise SystemExit("FAIL: the research engine at its defaults does not rebuild the sealed ledger")
    print("PASS: the research engine at its defaults rebuilds the sealed ledger byte for byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
