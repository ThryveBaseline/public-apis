"""Seal a canonical evaluation run so the first real-data result is preserved
before any model sees it or any change is considered.

    python3 scripts/seal_run.py --csv data/nq_1min.csv --out sealed/run1 [--oos-months 12] [--source-tz UTC] [--firms ...]

Refuses to run if anything under fpt/ or pine/ differs from the committed
tree (the strategy and evaluator must be frozen), then writes into --out:

    report.md        the evaluate report
    trades.csv       every trade the frozen rules produced (with ambiguous_bar)
    manifest.json    sha256 of the data file, its row count and date range,
                     the git commit and tag, the fpt/ tree hash, the exact
                     options, the sha256 of report.md and trades.csv, and the
                     roll dates excluded
    SEALED           a one-line marker with the manifest's own sha256

Nothing in here tunes or chooses: the options are recorded, not optimised.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, PKG)

from fpt.data import load_minute_bars, roll_days  # noqa: E402
from fpt.evaluate import evaluate_trades  # noqa: E402
from fpt.strategy import StrategyConfig, generate_trades  # noqa: E402


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=PKG, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--source-tz", default="America/New_York")
    ap.add_argument("--firms", default="topstep_50k,fundednext_50k_flex,topstep_100k,tradeify_100k_growth")
    ap.add_argument("--oos-months", type=int, default=12)
    ap.add_argument("--eval-risk-mode", choices=["fixed", "two_trade"], default="two_trade")
    ap.add_argument("--eval-risk", type=float, default=500.0)
    ap.add_argument("--funded-risk", type=float, default=500.0)
    ap.add_argument("--allow-dirty", action="store_true", help="only for smoke tests on synthetic data")
    a = ap.parse_args()

    dirty = git("status", "--porcelain", "--", "fpt", "pine")
    if dirty and not a.allow_dirty:
        print("refusing to seal: uncommitted changes under fpt/ or pine/:\n" + dirty)
        return 2
    if os.path.exists(os.path.join(a.out, "SEALED")):
        print(f"refusing: {a.out} is already sealed")
        return 2
    os.makedirs(a.out, exist_ok=True)

    bars = load_minute_bars(a.csv, source_tz=a.source_tz)
    rolls = roll_days(bars)
    cfg = StrategyConfig()  # the frozen defaults, no overrides
    trades = generate_trades(bars, cfg)
    trades.to_csv(os.path.join(a.out, "trades.csv"), index=False)
    rep = evaluate_trades(trades, bars, exclude_dates=rolls, firms=tuple(x for x in a.firms.split(",") if x),
                          eval_risk_mode=a.eval_risk_mode, eval_risk=a.eval_risk, funded_risk=a.funded_risk, oos_months=a.oos_months)
    with open(os.path.join(a.out, "report.md"), "w") as fh:
        fh.write(rep.text)

    manifest = {
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": {"path": os.path.abspath(a.csv), "sha256": sha256(a.csv), "rows": int(len(bars)),
                 "first_bar": str(bars.index[0]), "last_bar": str(bars.index[-1]), "has_symbol_column": "symbol" in bars.columns,
                 "roll_dates_excluded": [str(d) for d in rolls]},
        "code": {"git_commit": git("rev-parse", "HEAD"), "git_tag": git("describe", "--tags", "--exact-match"), "fpt_tree": git("rev-parse", "HEAD:jj-simon-replication/fpt"),
                 "working_tree_dirty": bool(dirty)},
        "options": vars(a),
        "strategy_config": {k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.__dict__.items()},
        "outputs": {"report_sha256": sha256(os.path.join(a.out, "report.md")), "trades_sha256": sha256(os.path.join(a.out, "trades.csv")), "n_trades": int(len(trades))},
        "hygiene": rep.tables.get("hygiene", {}),
    }
    mpath = os.path.join(a.out, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, indent=1, default=str)
    with open(os.path.join(a.out, "SEALED"), "w") as fh:
        fh.write(sha256(mpath) + "\n")
    print(json.dumps({k: manifest[k] for k in ("data", "code", "outputs", "hygiene")}, indent=1, default=str))
    print(f"sealed: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
