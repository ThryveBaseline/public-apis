import json

import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.evaluate import trading_days_of, walk_forward_payout_probability
from fpt.propfirm import FUNDED, PropAccount
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.candidates import PRESETS, fees_per_eval, firm_rows
from research.ledger_filters import sequential_pass
from research.lifetime import (HORIZONS, LifetimeAccount, check_first_payout, first_payout_outcomes, lifetime_rows,
                               walk_forward_lifetime)


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    bars = synthetic_minute_bars(days=200, seed=9)
    p = tmp_path_factory.mktemp("lt") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    return bars, sequential_pass(load_trades(str(p)))


def test_without_the_rule_the_account_is_the_frozen_one():
    rng = np.random.default_rng(3)
    for firm in ("topstep_50k", "topstep_50k_x", "fundednext_50k_flex", "tradeify_100k_growth"):
        a = PropAccount(PRESETS[firm], sims=40, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False)
        b = LifetimeAccount(PRESETS[firm], sims=40, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False)
        for _ in range(120):
            r = rng.choice([-1.02, 1.51, 0.3, -0.4], size=(40, 2), p=[0.45, 0.4, 0.1, 0.05])
            mask = rng.random((40, 2)) < 0.7
            a.apply_day(r.copy(), mask.copy())
            b.apply_day(r.copy(), mask.copy())
            assert np.array_equal(a.payout_now(), b.payout_now())
            assert np.array_equal(a.phase, b.phase) and np.allclose(a.balance, b.balance) and np.allclose(a.threshold, b.threshold)


def test_topstep_rule_moves_the_limit_to_the_starting_balance_with_a_payout():
    """Five $300 winning days, a payout, then a $800 loss: the frozen account survives on its trailing limit, the
    Express Funded rule (limit at the starting balance after a payout) breaches."""
    rules = PRESETS["topstep_50k_x"]
    outcome = {}
    for rule in (False, True):
        acct = LifetimeAccount(rules, sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, mll_to_start_on_payout=rule)
        paid = []
        for r in [0.6] * 5 + [-1.6]:
            acct.apply_day(np.array([[r]]), np.array([[True]]))
            paid.append(float(acct.payout_now()[0]))
        assert paid[4] == pytest.approx(0.5 * 1500 * 0.9) and sum(paid) == pytest.approx(paid[4])  # one payout, after the fifth winning day
        outcome[rule] = int(acct.phase[0])
    assert outcome[False] == FUNDED and outcome[True] != FUNDED


def test_first_payouts_equal_the_frozen_walk_forward_and_lifetimes_add_up(engine):
    bars, st = engine
    cal = trading_days_of(bars)
    for firm in ("topstep_50k", "topstep_50k_x", "fundednext_50k_flex"):
        for rule in (False, True):
            lt = walk_forward_lifetime(st, PRESETS[firm], 500.0, HORIZONS, cal, rule)
            check_first_payout(st, PRESETS[firm], 500.0, cal, lt)  # raises if the first payouts differ
            frozen = walk_forward_payout_probability(st, PRESETS[firm], 500.0, 60, trading_days=cal)
            assert list(first_payout_outcomes(lt)["outcome"]) == list(frozen["outcome"])
            for a, b in zip(HORIZONS, HORIZONS[1:]):
                assert (lt[f"paid_{a}"] <= lt[f"paid_{b}"] + 1e-9).all() and (lt[f"payouts_{a}"] <= lt[f"payouts_{b}"]).all()
            got = lt["first_payout_amount"].fillna(0.0)
            assert (lt[f"paid_{HORIZONS[-1]}"] >= got - 1e-9).all()  # a lifetime is never worth less than its first payout
            n = len(lt)
            avail = n - np.arange(n)
            assert (lt["censored_250"] == ((avail < 250) & ~(lt["bust_day"] <= avail))).all()
    # the rule only takes payouts away after the first one
    a = walk_forward_lifetime(st, PRESETS["topstep_50k_x"], 500.0, HORIZONS, cal, False)
    b = walk_forward_lifetime(st, PRESETS["topstep_50k_x"], 500.0, HORIZONS, cal, True)
    assert (b["paid_250"] <= a["paid_250"] + 1e-9).all() and (a["first_payout_day"].equals(b["first_payout_day"]))
    lt = a.copy()
    lt.loc[lt["first_payout_day"].notna().idxmax(), "first_payout_amount"] += 1.0
    with pytest.raises(ValueError, match="first payouts differ"):
        check_first_payout(st, PRESETS["topstep_50k_x"], 500.0, cal, lt)


def test_lifetime_rows_ev_arithmetic(engine):
    bars, st = engine
    cal = trading_days_of(bars)
    last = st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None).max()
    cut = (last - pd.DateOffset(months=2)).normalize()
    rows = lifetime_rows(st, cal, cut, "topstep_50k_x", 0.95)
    assert {(r["period"], r["horizon"]) for r in rows} == {(p, h) for p in ("development", "benchmark") for h in HORIZONS}
    dev = [r for r in rows if r["period"] == "development"]
    part = st[st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut].assign(r=lambda x: x["r"] * 0.95)
    ev_row = firm_rows(part, cal[cal <= cut], firms=("topstep_50k_x",)).iloc[0].to_dict()
    lt = walk_forward_lifetime(part, PRESETS["topstep_50k_x"], 500.0, HORIZONS, cal[cal <= cut], True)
    for r in dev:
        kept = lt[~lt[f"censored_{r['horizon']}"]]
        assert r["paid_mean"] == pytest.approx(kept[f"paid_{r['horizon']}"].mean())
        assert r["ev"] == pytest.approx(ev_row["pass_rate"] * kept[f"paid_{r['horizon']}"].mean() - fees_per_eval(ev_row))
        assert r["fees"] == pytest.approx(fees_per_eval(ev_row)) and r["first_payout_rate"] == pytest.approx(ev_row["payout_rate"])
    for r in rows:  # a horizon longer than the period's data leaves no uncensored start: the mean is undefined, not zero
        assert (r["funded_starts"] == 0 and np.isnan(r["paid_mean"])) or (r["funded_starts"] > 0 and r["paid_mean"] >= 0)
    assert any(r["funded_starts"] == 0 for r in rows if r["period"] == "benchmark" and r["horizon"] == 250)


def test_cli_runs_through_b3s_gates(tmp_path, monkeypatch):
    from fpt.data import load_minute_bars, roll_days
    from fpt.evaluate import evaluate_trades
    from research import bracket_replay, candidates, lifetime
    from research.anatomy import exclude_roll_trades
    bars = synthetic_minute_bars(days=130, seed=5)
    bars["symbol"] = np.where(bars.index < bars.index[len(bars) // 2], 1000, 1001)
    out = bars.copy()
    out.index = out.index.tz_convert("UTC")
    out.index.name = "ts_event"
    csv = tmp_path / "bars.csv"
    out.to_csv(csv)
    loaded = load_minute_bars(str(csv), source_tz="UTC")
    rolls = sorted(roll_days(loaded))
    led = tmp_path / "trades.csv"
    generate_trades(loaded, StrategyConfig()).to_csv(led, index=False)
    trades = load_trades(str(led))
    rep = evaluate_trades(trades, loaded, exclude_dates=rolls, oos_months=2)
    (tmp_path / "report.md").write_text(rep.text)
    kept, n_excl = exclude_roll_trades(trades, rolls)
    man = {"data": {"roll_dates_excluded": [str(d) for d in rolls], "sha256": candidates.sha256(str(csv))},
           "outputs": {"n_trades": len(trades), "trades_sha256": candidates.sha256(str(led)), "report_sha256": candidates.sha256(str(tmp_path / "report.md"))},
           "hygiene": {"trades_excluded": n_excl}}
    (tmp_path / "manifest.json").write_text(json.dumps(man))
    day = kept["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    oos = ((day.max() - pd.DateOffset(months=2)).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    common = ["--trades", str(led), "--csv", str(csv), "--source-tz", "UTC", "--oos-start", oos, "--manifest", str(tmp_path / "manifest.json")]
    monkeypatch.setattr("sys.argv", ["bracket_replay.py", *common, "--out", str(tmp_path / "b1.md"), "--private-out", str(tmp_path / "replay.csv")])
    assert bracket_replay.main() in (0, None)
    monkeypatch.setattr("sys.argv", ["lifetime.py", *common, "--report", str(tmp_path / "report.md"), "--replay-csv", str(tmp_path / "replay.csv"), "--out", str(tmp_path / "b4.md")])
    assert lifetime.main() == 0
    text = (tmp_path / "b4.md").read_text()
    assert "reproduces all 8 firm rows" in text and "Gate, passed on every row" in text
    for head in ("## topstep_50k_x at 1.00 of the budget", "## topstep_50k_x at 0.95 of the budget", "## topstep_50k at 1.00 of the budget"):
        assert head in text
    assert text.count("| S4 S3 + A+ reversion, sealed bracket | development |") == 3 * len(HORIZONS)
