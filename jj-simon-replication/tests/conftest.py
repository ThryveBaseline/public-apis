import json
import sys

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope="session")
def sealed_4y(tmp_path_factory):
    """Four years of synthetic regular-hours bars with one contract roll, sealed the way run1 was: the frozen engine's
    ledger, the frozen evaluator's report (three months out of sample), a manifest with every hash the gates check,
    and the bracket replay's per-trade file from its own CLI. Shared by the CLI tests of the tools built on B3."""
    from fpt.data import NY, load_minute_bars, roll_days, synthetic_minute_bars
    from fpt.evaluate import evaluate_trades
    from fpt.strategy import StrategyConfig, generate_trades
    from research import bracket_replay, candidates
    from research.anatomy import exclude_roll_trades, load_trades
    tmp = tmp_path_factory.mktemp("sealed_4y")
    bars = synthetic_minute_bars(days=1080, seed=5, start="2019-01-07")
    bars["symbol"] = np.where(bars.index < bars.index[len(bars) // 2], 1000, 1001)
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    csv = tmp / "bars.csv"
    out.to_csv(csv)
    loaded = load_minute_bars(str(csv), source_tz="UTC")
    rolls = sorted(roll_days(loaded))
    led = tmp / "trades.csv"
    generate_trades(loaded, StrategyConfig()).to_csv(led, index=False)
    trades = load_trades(str(led))
    rep = evaluate_trades(trades, loaded, exclude_dates=rolls, oos_months=3)
    (tmp / "report.md").write_text(rep.text)
    kept, n_excl = exclude_roll_trades(trades, rolls)
    man = {"data": {"roll_dates_excluded": [str(d) for d in rolls], "sha256": candidates.sha256(str(csv))},
           "outputs": {"n_trades": len(trades), "trades_sha256": candidates.sha256(str(led)), "report_sha256": candidates.sha256(str(tmp / "report.md"))},
           "hygiene": {"trades_excluded": n_excl}}
    (tmp / "manifest.json").write_text(json.dumps(man))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = ((day.max() - pd.DateOffset(months=3)).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp / "manifest.json")]
    saved = sys.argv
    try:
        sys.argv = ["bracket_replay.py", *common, "--out", str(tmp / "b1.md"), "--private-out", str(tmp / "replay.csv")]
        bracket_replay.main()
    finally:
        sys.argv = saved
    return {"dir": tmp, "common": common, "b3": [*common, "--report", str(tmp / "report.md"), "--replay-csv", str(tmp / "replay.csv")]}
