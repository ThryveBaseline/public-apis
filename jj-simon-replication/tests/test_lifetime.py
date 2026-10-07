import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.evaluate import _daily_r, trading_days_of, walk_forward_payout_probability
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


def _run(acct, rs):
    paid = []
    for r in rs:
        acct.apply_day(np.array([[r]]), np.array([[True]]))
        paid.append(float(acct.payout_now()[0]))
    return paid


def test_without_the_rules_the_account_is_the_frozen_one():
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


def test_the_limit_moves_to_the_starting_balance_with_a_payout():
    """Five $300 winning days, a payout, then a $800 loss: the frozen account survives on its trailing limit, the
    Express Funded rules (limit at the starting balance after a payout) breach."""
    outcome = {}
    for rule in (False, True):
        acct = LifetimeAccount(PRESETS["topstep_50k_x"], sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, topstep_xfa=rule)
        paid = _run(acct, [0.6] * 5 + [-1.6])
        assert paid[4] == pytest.approx(0.5 * 1500 * 0.9) and sum(paid) == pytest.approx(paid[4])
        outcome[rule] = int(acct.phase[0])
    assert outcome[False] == FUNDED and outcome[True] != FUNDED


def test_a_later_payout_needs_net_profit_since_the_last():
    """$5,000 in five days and a $1,800 payout, a $1,500 loss, then five $155 winning days: still $725 down since the
    payout, so the Express Funded rules pay nothing more; the frozen account pays again."""
    path = [2.0] * 5 + [-3.0] + [0.31] * 5
    frozen = PropAccount(PRESETS["topstep_50k_x"], sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False)
    xfa = LifetimeAccount(PRESETS["topstep_50k_x"], sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, topstep_xfa=True)
    pf, px = _run(frozen, path), _run(xfa, path)
    assert pf[4] == px[4] == pytest.approx(2000 * 0.9)  # the first payout: half the profit, capped at $2,000, 90% to the trader
    assert pf[-1] > 0 and px[-1] == 0 and xfa.phase[0] == FUNDED


def test_waiting_for_the_lock_delays_the_first_payout():
    """At $300 a day the first payout is due after five winning days; waiting for the limit to reach the starting
    balance (profit of $2,000 at a close) moves it to the seventh day, at a larger amount."""
    ask = LifetimeAccount(PRESETS["topstep_50k_x"], sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, topstep_xfa=True)
    wait = LifetimeAccount(PRESETS["topstep_50k_x"], sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, topstep_xfa=True, wait_for_lock=True)
    pa, pw = _run(ask, [0.6] * 7), _run(wait, [0.6] * 7)
    assert [i for i, x in enumerate(pa) if x > 0] == [4] and [i for i, x in enumerate(pw) if x > 0] == [6]
    assert pw[6] == pytest.approx(0.5 * 2100 * 0.9)


def _scalar_reference(st, rules, cal, horizon, topstep_xfa, wait):
    """Every start on its own one-account run, day by day: the payouts per day, the first payout and the breach."""
    dates, rs = _daily_r(st, cal)
    n = len(dates)
    rows = []
    for i in range(n):
        acct = LifetimeAccount(rules, sims=1, risk_per_trade=500.0, start_phase=FUNDED, restart_failed=False, topstep_xfa=topstep_xfa, wait_for_lock=wait)
        per_day, bust = [], np.nan
        for k in range(min(horizon, n - i)):
            day = rs[i + k]
            r = np.zeros((1, max(1, len(day))))
            m = np.zeros((1, max(1, len(day))), dtype=bool)
            r[0, :len(day)], m[0, :len(day)] = day, True
            live = acct.phase[0] == FUNDED
            acct.apply_day(r, m)
            per_day.append(float(acct.payout_now()[0]))
            if live and acct.phase[0] != FUNDED:
                bust = k + 1
        rows.append((per_day, bust))
    return rows


@pytest.mark.parametrize("firm,xfa,wait", [("topstep_50k_x", True, False), ("topstep_50k_x", True, True), ("fundednext_50k_flex", False, False)])
def test_the_vectorised_run_equals_a_scalar_reference_and_its_daily_estimates(engine, firm, xfa, wait):
    bars, st = engine
    cal = trading_days_of(bars)
    lt, summary = walk_forward_lifetime(st, PRESETS[firm], 500.0, HORIZONS, cal, xfa, wait_for_lock=wait)
    ref = _scalar_reference(st, PRESETS[firm], cal, max(HORIZONS), xfa, wait)
    n = len(ref)
    for h in HORIZONS:
        assert np.allclose(lt[f"paid_{h}"], [sum(p[:h]) for p, _ in ref])
        assert list(lt[f"payouts_{h}"]) == [sum(1 for x in p[:h] if x > 0) for p, _ in ref]
    assert np.allclose(lt["bust_day"].to_numpy(float), [b for _, b in ref], equal_nan=True)
    for h in HORIZONS:  # every summary: the sum over days of that day's mean over the starts that have it
        if h > n:
            assert np.isnan(summary[h]["paid"]) and np.isnan(summary[h]["p_any"])
            continue
        seen = [[x for x in ref if len(x[0]) > k] for k in range(h)]
        first = [next((k for k, x in enumerate(p) if x > 0), None) for p, _ in ref]  # each start's first payout day (0-based)
        firsts = {id(x): f for x, f in zip(ref, first)}
        want = {"paid": sum(np.mean([p[k] for p, _ in s]) for k, s in enumerate(seen)),
                "payouts": sum(np.mean([p[k] > 0 for p, _ in s]) for k, s in enumerate(seen)),
                "p_breach": sum(np.mean([b == k + 1 for _, b in s]) for k, s in enumerate(seen)),
                "p_any": sum(np.mean([firsts[id(x)] == k for x in s]) for k, s in enumerate(seen)),
                "first_amount": sum(np.mean([x[0][k] if firsts[id(x)] == k else 0.0 for x in s]) for k, s in enumerate(seen))}
        for key, v in want.items():
            assert summary[h][key] == pytest.approx(v), (h, key)
        assert summary[h]["n_full"] == sum(1 for p, _ in ref if len(p) >= h)
    if not wait:
        check_first_payout(st, PRESETS[firm], 500.0, cal, lt)


def test_first_payouts_equal_the_frozen_walk_forward(engine):
    bars, st = engine
    cal = trading_days_of(bars)
    for firm, xfa in (("topstep_50k", True), ("topstep_50k_x", True), ("topstep_50k_x", False), ("fundednext_50k_flex", False)):
        lt, _ = walk_forward_lifetime(st, PRESETS[firm], 500.0, HORIZONS, cal, xfa)
        check_first_payout(st, PRESETS[firm], 500.0, cal, lt)
        frozen = walk_forward_payout_probability(st, PRESETS[firm], 500.0, 60, trading_days=cal)
        assert list(first_payout_outcomes(lt)["outcome"]) == list(frozen["outcome"])
        assert (lt[f"paid_{HORIZONS[-1]}"] >= lt["first_payout_amount"].fillna(0.0) - 1e-9).all()
    lt, _ = walk_forward_lifetime(st, PRESETS["topstep_50k_x"], 500.0, HORIZONS, cal, True)
    lt.loc[lt["first_payout_day"].notna().idxmax(), "first_payout_amount"] += 1.0
    with pytest.raises(ValueError, match="first payouts differ"):
        check_first_payout(st, PRESETS["topstep_50k_x"], 500.0, cal, lt)


def test_lifetime_rows_ev_arithmetic(engine):
    bars, st = engine
    cal = trading_days_of(bars)
    last = st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None).max()
    cut = (last - pd.DateOffset(months=2)).normalize()
    rows = lifetime_rows(st, cal, cut, "topstep_50k_x", 0.95, policies=("ask", "wait"))
    assert {(r["period"], r["policy"], r["horizon"]) for r in rows} == {(p, q, h) for p in ("development", "benchmark") for q in ("ask", "wait") for h in HORIZONS}
    assert {r["policy"] for r in lifetime_rows(st, cal, cut, "topstep_50k_x", 0.95)} == {"ask"}  # the default is the gated policy alone
    part = st[st["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None) <= cut].assign(r=lambda x: x["r"] * 0.95)
    ev_row = firm_rows(part, cal[cal <= cut], firms=("topstep_50k_x",)).iloc[0].to_dict()
    for policy, wait in (("ask", False), ("wait", True)):
        _, summary = walk_forward_lifetime(part, PRESETS["topstep_50k_x"], 500.0, HORIZONS, cal[cal <= cut], True, wait_for_lock=wait)
        for r in (x for x in rows if x["period"] == "development" and x["policy"] == policy):
            assert r["paid_mean"] == pytest.approx(summary[r["horizon"]]["paid"], nan_ok=True)
            assert r["ev"] == pytest.approx(ev_row["pass_rate"] * summary[r["horizon"]]["paid"] - fees_per_eval(ev_row), nan_ok=True)
            assert r["ev_first_mean"] == pytest.approx(ev_row["pass_rate"] * summary[60]["first_amount"] - fees_per_eval(ev_row))
            assert r["b3_payout_rate"] == pytest.approx(ev_row["payout_rate"]) and r["fees"] == pytest.approx(fees_per_eval(ev_row))
    bm = [r for r in rows if r["period"] == "benchmark" and r["horizon"] == 250]
    assert all(np.isnan(r["paid_mean"]) for r in bm)  # a horizon longer than the benchmark's data: no estimate, not zero


def test_cli_runs_through_b3s_gates(sealed_4y, tmp_path, monkeypatch):
    from research import lifetime
    monkeypatch.setattr("sys.argv", ["lifetime.py", *sealed_4y["b3"], "--out", str(tmp_path / "b4.md")])
    assert lifetime.main() == 0
    text = (tmp_path / "b4.md").read_text()
    assert "reproduces all 8 firm rows" in text and "Gate, passed on every row of the first policy" in text
    for head in ("## topstep_50k_x at 1.00 of the budget", "## topstep_50k_x at 0.95 of the budget", "## topstep_50k at 1.00 of the budget"):
        assert head in text
    assert text.count("| S4 S3 + A+ reversion, sealed bracket | development | ask |") == 3 * len(HORIZONS)
    assert text.count("| S4 S3 + A+ reversion, sealed bracket | development | wait |") == 3 * len(HORIZONS)
