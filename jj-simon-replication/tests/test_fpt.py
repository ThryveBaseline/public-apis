import numpy as np
import pandas as pd
import pytest

from fpt import risk as R
from fpt.backtest import run_backtest, streaks, max_drawdown
from fpt.data import synthetic_minute_bars, load_minute_bars
from fpt.fair_value import FairValueConfig, fair_value_series, session_anchor_prices
from fpt.indicators import atr, swing_points
from fpt.portfolio import PortfolioConfig, simulate_portfolio, optimal_risk_scan
from fpt.propfirm import FIRM_PRESETS, PropAccount, EVAL, FUNDED, FAILED
from fpt.strategy import StrategyConfig, generate_trades
from fpt.structure import is_displacement


@pytest.fixture(scope="module")
def bars():
    return synthetic_minute_bars(days=15, seed=3)


def test_synthetic_shape(bars):
    assert list(bars.columns) == ["open", "high", "low", "close", "volume"]
    assert str(bars.index.tz) == "America/New_York"
    first = bars.index[0]
    assert (first.hour, first.minute) == (9, 30)
    assert len(bars) == 15 * 390
    assert (bars["high"] >= bars[["open", "close"]].max(axis=1)).all()
    assert (bars["low"] <= bars[["open", "close"]].min(axis=1)).all()


def test_csv_roundtrip(tmp_path, bars):
    path = tmp_path / "bars.csv"
    bars.to_csv(path)
    back = load_minute_bars(str(path))
    assert len(back) == len(bars)
    assert back.index[0] == bars.index[0]
    np.testing.assert_allclose(back["close"].to_numpy(), bars["close"].to_numpy())


def test_fair_value_anchor_is_open_of_0930(bars):
    fv = fair_value_series(bars)
    day0 = bars.iloc[:390]
    assert fv.iloc[0] == day0["open"].iloc[0]
    assert fv.iloc[100] == day0["open"].iloc[0]
    assert fv.iloc[389] == day0["open"].iloc[0]
    anchors = session_anchor_prices(bars)
    assert len(anchors) == 15


def test_pre_open_close_anchor(bars):
    fv = fair_value_series(bars, FairValueConfig(anchor="close_0929"))
    # no 09:29 bar in RTH-only data: falls back to the 09:30 open
    assert fv.iloc[0] == bars["open"].iloc[0]


def test_pm_anchor(bars):
    fv = fair_value_series(bars, FairValueConfig(pm_anchor=True))
    pm_bar = bars.iloc[270]  # 09:30 + 270 min = 14:00
    assert (pm_bar.name.hour, pm_bar.name.minute) == (14, 0)
    assert fv.iloc[270] == pm_bar["open"]
    assert fv.iloc[269] == bars["open"].iloc[0]


def test_displacement_rule():
    # bullish candle open 100 high 110 close 109: counter-wick 1 <= 20% of 10
    assert is_displacement(100, 110, 99, 109, +1)
    # counter-wick 3 > 20% of 10 -> not displacement
    assert not is_displacement(100, 110, 99, 107, +1)
    # bearish
    assert is_displacement(100, 101, 90, 91, -1)
    assert not is_displacement(100, 101, 90, 94, -1)
    # body filter
    assert not is_displacement(100, 110, 99, 109, +1, min_body=12)
    # wrong colour
    assert not is_displacement(100, 110, 99, 99.5, +1)


def test_atr_and_swings(bars):
    a = atr(bars, 14)
    assert (a.dropna() > 0).all()
    sh, sl = swing_points(bars, 3, 3)
    assert sh.sum() > 0 and sl.sum() > 0
    i = np.where(sh)[0][0]
    h = bars["high"].to_numpy()
    assert h[i] == h[i - 3 : i + 4].max()


def test_atr_tiers():
    assert R.atr_tier(25.0).stop_points == 50.0 and R.atr_tier(25.0).contracts == 1
    assert R.atr_tier(20.0).stop_points == 50.0
    assert R.atr_tier(12.0).stop_points == 25.0 and R.atr_tier(12.0).contracts == 2
    assert R.atr_tier(7.0).stop_points == 25.0
    assert R.atr_tier(5.0).stop_points == 16.5 and R.atr_tier(5.0).contracts == 3
    for v in (25.0, 12.0, 5.0):
        t = R.atr_tier(v)
        assert 980 <= R.dollar_risk(t.stop_points, t.contracts) <= 1000


def test_contracts_for_risk():
    assert R.contracts_for_risk(1000, 50) == 1
    assert R.contracts_for_risk(1000, 25) == 2
    assert R.contracts_for_risk(1000, 16.5) == 3
    assert R.contracts_for_risk(1000, 16.5, point_value=2.0) == 30
    assert R.contracts_for_risk(1000, 16.5, max_contracts=2) == 2


def test_edge_math():
    assert R.expectancy_r(0.54, 1.5) == pytest.approx(0.35)
    assert R.breakeven_winrate(1.5) == pytest.approx(0.4)
    assert R.kelly_fraction(0.54, 1.5) == pytest.approx(0.54 - 0.46 / 1.5)
    assert R.kelly_fraction(0.3, 1.5) == 0.0
    q = R.losing_streak_quantiles(0.54, 200, sims=3000)
    assert q[0.5] >= 3 and q[0.99] >= q[0.5]
    ds = R.daily_stop_from_stats(0.54, 1.5, 10, 1000, sims=5000)
    assert ds["stop_r"] < 0 and ds["expected_daily_r"] > 0
    assert 0 < ds["p_negative_day"] < 0.5
    rr = R.risk_of_ruin(0.54, 1.5, risk_fraction=0.33, n_trades=200, sims=3000)
    assert 0 <= rr <= 1
    rows = R.optimal_fixed_risk(0.54, 1.5, 3000, 6000, 10, 20, candidates=[300, 1000], sims=500)
    assert len(rows) == 2 and all(0 <= r["p_pass"] <= 1 for r in rows)


def test_strategy_generates_trades(bars):
    cfg = StrategyConfig(min_body_atr=0.5)
    trades = generate_trades(bars, cfg)
    assert len(trades) > 0
    assert set(trades["setup"]) <= {"continuation", "reversion"}
    assert set(trades["grade"]) <= {"A+", "A"}
    assert (trades["entry_time"] > trades["signal_time"]).all()
    assert (trades["exit_time"] >= trades["entry_time"]).all()
    # entries only inside the 09:30-11:00 window
    sig_min = trades["signal_time"].dt.hour * 60 + trades["signal_time"].dt.minute
    assert (sig_min >= 9 * 60 + 30).all() and (sig_min < 11 * 60).all()
    # continuation only in the first 15 minutes
    cont = trades[trades["setup"] == "continuation"]
    assert (sig_min[cont.index] < 9 * 60 + 45).all()
    # at most max_trades_per_day per day
    per_day = trades.groupby(trades["signal_time"].dt.normalize()).size()
    assert per_day.max() <= cfg.max_trades_per_day
    # stop/target geometry
    long = trades[trades["direction"] == "long"]
    short = trades[trades["direction"] == "short"]
    assert (long["stop"] < long["entry"]).all() and (long["target"] > long["entry"]).all()
    assert (short["stop"] > short["entry"]).all() and (short["target"] < short["entry"]).all()
    expected = np.where(long["tier"].to_numpy() == "big_open", 1.5 * long["stop_points"].to_numpy(), 38.0)  # his 25 / 38 bracket; 50 / 75 on a wide open
    np.testing.assert_allclose((long["target"] - long["entry"]).to_numpy(), expected)
    # one position at a time
    t = trades.sort_values("entry_time")
    assert (t["entry_time"].to_numpy()[1:] >= t["exit_time"].to_numpy()[:-1]).all()
    # a stop-out loses risk + costs
    stops = trades[trades["exit_reason"] == "stop"]
    if len(stops):
        assert (stops["pnl_dollars"] < -stops["risk_dollars"]).all()
    # his default lets a position run past 11:00; with flat_at_window_end the exits stop at 11:00
    flat = generate_trades(bars, StrategyConfig(flat_at_window_end=True))
    assert (flat["exit_time"].dt.hour * 60 + flat["exit_time"].dt.minute <= 11 * 60).all()


def test_daily_stop_rules(bars):
    cfg = StrategyConfig(min_body_atr=0.5, max_consecutive_losses=2)
    trades = generate_trades(bars, cfg)
    for _, day in trades.groupby(trades["signal_time"].dt.normalize()):
        losses = (day.sort_values("entry_time")["pnl_dollars"] < 0).to_numpy()
        run = 0
        for i, lo in enumerate(losses):
            run = run + 1 if lo else 0
            if run >= 2:
                assert i == len(losses) - 1  # trading stopped after the second consecutive loss
                break
    cfg2 = StrategyConfig(min_body_atr=0.5, max_trades_per_day=2)
    t2 = generate_trades(bars, cfg2)
    assert t2.groupby(t2["signal_time"].dt.normalize()).size().max() <= 2


def test_backtest_result(bars):
    res = run_backtest(bars, StrategyConfig(min_body_atr=0.5))
    s = res.summary
    assert s["trades"] == len(res.trades)
    assert 0 <= s["win_rate"] <= 1
    assert s["max_drawdown_dollars"] >= 0
    assert "A+" in res.by_grade.index or "A" in res.by_grade.index
    assert isinstance(res.report(), str) and "Backtest report" in res.report()
    assert streaks(np.array([1, 1, 0, 0, 0, 1])) == (2, 3)
    assert max_drawdown(np.array([100, -50, -100, 200])) == 150


def test_prop_account_trailing_eod_pass_and_fail():
    rules = FIRM_PRESETS["topstep_100k"].with_(min_trading_days=1, consistency_pct=None, daily_loss_limit=None)
    acct = PropAccount(rules, sims=3, risk_per_trade=1000.0)
    # sim0: +6R, sim1: -3R, sim2: +1R
    r = np.array([[1.5, 1.5, 1.5, 1.5], [-1, -1, -1, 0], [1, 0, 0, 0]], float)
    mask = np.array([[1, 1, 1, 1], [1, 1, 1, 0], [1, 0, 0, 0]], bool)
    acct.apply_day(r, mask)
    assert acct.phase[0] == FUNDED  # 6,000 target hit in one day
    assert acct.phase[1] == FAILED  # 3,000 drawdown breached
    assert acct.phase[2] == EVAL
    assert acct.balance[2] == pytest.approx(101_000)
    # trailing threshold moved up with the EOD peak for sim2
    assert acct.threshold[2] == pytest.approx(101_000 - 3_000)


def test_prop_account_payout():
    rules = FIRM_PRESETS["topstep_100k"].with_(payout_min_days=1, consistency_pct=None, payout_max=None, payout_fraction=1.0)
    acct = PropAccount(rules, sims=1, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.apply_day(np.array([[1.5, 1.5]]), np.array([[True, True]]))
    cash = acct.month_end()
    assert cash[0] == pytest.approx(3000 * rules.payout_split)
    assert acct.balance[0] == pytest.approx(100_000)
    # his default: 50% of profit per request, and only days of $150+ count toward the payout
    half = FIRM_PRESETS["topstep_100k"].with_(payout_min_days=1, consistency_pct=None, payout_max=None)
    acct = PropAccount(half, sims=1, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.apply_day(np.array([[1.5, 1.5]]), np.array([[True, True]]))
    assert acct.month_end()[0] == pytest.approx(1500 * half.payout_split)
    acct = PropAccount(half, sims=1, risk_per_trade=50.0, start_phase=FUNDED)
    acct.apply_day(np.array([[1.5]]), np.array([[True]]))  # +$75: not a winning day
    assert acct.days_since_payout[0] == 0


def test_payout_buffer_fraction_cap_min_days_and_month_end_fee():
    tr = FIRM_PRESETS["tradeify_100k_growth"]  # buffer 4,500, 50% of profit above it, cap 4,000, 90/10, 5 winning days of $150+
    acct = PropAccount(tr, sims=3, risk_per_trade=1000.0, start_phase=FUNDED)
    for _ in range(4):
        acct.apply_day(np.array([[1.0], [2.0], [4.0]]), np.ones((3, 1), bool))
    assert (acct.payout_now() == 0).all()  # four winning days: nothing yet
    acct.apply_day(np.array([[1.0], [2.0], [4.0]]), np.ones((3, 1), bool))
    paid = acct.payout_now()
    # profit 5,000 / 10,000 / 20,000 -> above the buffer 500 / 5,500 / 15,500 -> 50% = 250 / 2,750 / 7,750 -> cap 4,000 -> x0.9
    assert np.allclose(paid, [225.0, 2475.0, 3600.0])
    assert np.allclose(acct.balance, [104_750.0, 107_250.0, 116_000.0])
    assert (acct.balance >= tr.account_size + tr.payout_buffer).all() and (acct.days_since_payout == 0).all()
    # month_end charges the monthly subscription to evaluations before paying, and the fee is not netted from the cash
    ts = FIRM_PRESETS["topstep_100k"].with_(consistency_pct=None)
    acct = PropAccount(ts, sims=2, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.phase[1] = EVAL
    acct.costs_total[:] = 0.0
    for _ in range(5):
        acct.apply_day(np.array([[1.5], [0.0]]), np.array([[True], [False]]))
    cash = acct.month_end()
    assert acct.costs_total.tolist() == [0.0, 99.0]
    assert cash.tolist() == [2700.0, 0.0]  # 7,500 profit -> 50% = 3,750 -> cap 3,000 -> 90%


def test_portfolio_runs():
    cfg = PortfolioConfig(accounts=[("topstep_100k", 3), ("tradeify_100k_select", 2)], sims=50, months=2, trades_per_day=8)
    res = simulate_portfolio(cfg)
    assert res["accounts"] == 5
    assert len(res["monthly_net_median"]) == 2
    assert 0 <= res["p_net_positive"] <= 1
    rows = optimal_risk_scan(PortfolioConfig(accounts=[("topstep_100k", 2)], sims=30, months=1), risks=(500, 1000))
    assert len(rows) == 2


def test_portfolio_daily_discipline_limits_trades():
    cfg = PortfolioConfig(accounts=[("topstep_100k", 1)], sims=20, months=1, max_consecutive_losses=1, daily_loss_stop_r=1.0)
    res = simulate_portfolio(cfg)
    assert res["accounts"] == 1


def test_no_lookahead_in_structure(bars):
    """Shifting future bars must not change signals already produced."""
    cfg = StrategyConfig(min_body_atr=0.5)
    full = generate_trades(bars, cfg)
    cut = bars.iloc[: 390 * 10]
    part = generate_trades(cut, cfg)
    full_first = full[full["signal_time"] < cut.index[-1]]
    assert len(part) == len(full_first)
    pd.testing.assert_frame_equal(part.reset_index(drop=True), full_first.reset_index(drop=True))


def test_implied_edge():
    out = R.implied_daily_r(105_700, 40, 15, 1000)
    assert out["r_per_account_day"] == pytest.approx(0.1762, abs=1e-3)
    assert R.trades_per_day_for_daily_r(0.35, 0.54, 1.5) == pytest.approx(1.0)
    assert R.trades_per_day_for_daily_r(1.0, 0.3, 1.5) == float("inf")


def test_two_trade_eval_posture():
    rules = FIRM_PRESETS["topstep_100k"].with_(min_trading_days=1, consistency_pct=None, daily_loss_limit=None)
    acct = PropAccount(rules, sims=2, risk_per_trade=1000.0, eval_risk=rules.profit_target / 3.0)
    r = np.array([[1.5, 1.5], [-1.0, -1.0]])
    acct.apply_day(r, np.ones((2, 2), bool))
    assert acct.phase[0] == FUNDED  # two 1.5R wins at target/3 risk clear the $6,000 target
    assert acct.phase[1] == FAILED  # two $2,000 losses breach the $3,000 drawdown
    # funded phase uses the lower risk
    acct.apply_day(np.array([[-1.0], [0.0]]), np.array([[True], [False]]))
    assert acct.balance[0] == pytest.approx(99_000)


def test_round_robin_routing_one_trade_per_account_per_day():
    from fpt.portfolio import route_round_robin
    # 20 signals a day over 45 funded accounts: signal k is worth $100+k at $1 risk, so each balance says which signal the account took
    rules = FIRM_PRESETS["topstep_100k"].with_(consistency_pct=None, daily_loss_limit=None, winning_day_min=0.0)
    accts = [PropAccount(rules, sims=1, risk_per_trade=1.0, start_phase=FUNDED, restart_failed=False) for _ in range(45)]
    r, mask, offset = np.array([[100.0 + k for k in range(20)]]), np.ones((1, 20), bool), np.zeros(1, dtype=int)
    expected = [list(range(20)), list(range(20, 40)), list(range(40, 45)) + list(range(15))]  # the rotation continues where it left off
    for day in range(3):
        before = np.array([a.balance[0] for a in accts])
        offset = route_round_robin(accts, r, mask, offset)
        took = np.array([a.balance[0] for a in accts]) - before
        traded = np.flatnonzero(took)
        assert sorted(traded.tolist()) == sorted(expected[day])
        assert sorted(int(x) - 100 for x in took[traded]) == list(range(20))  # every signal consumed exactly once
        assert max(int(a.trading_days[0]) for a in accts) <= day + 1  # at most one trade per account per day
    assert [int(took[k]) - 100 for k in range(40, 45)] == [0, 1, 2, 3, 4] and int(took[0]) - 100 == 5  # day 3: signals 0-4 to accounts 40-44, then 5.. to account 0
    for _ in range(6):
        offset = route_round_robin(accts, r, mask, offset)
    assert all(int(a.trading_days[0]) == 4 for a in accts)  # 9 days x 20 signals = 180 trades spread evenly over 45 accounts
    cfg = PortfolioConfig(accounts=[("topstep_100k", 4)], sims=30, months=1, trades_per_day=3.0, routing="round_robin", eval_risk_mode="two_trade")
    res = simulate_portfolio(cfg)
    assert res["accounts"] == 4
    assert 0 <= res["p_net_positive"] <= 1


def test_jj_prop_firm_math():
    assert R.cost_to_funded(100, 0.30) == pytest.approx(333.33, abs=0.01)
    assert R.cost_per_drawdown_dollar(750, 4500) == pytest.approx(0.1667, abs=1e-3)
    assert R.eval_expected_value(0.10, 2000, 100) == pytest.approx(110.0)
    assert R.two_trade_pass_probability(0.5) == 0.25
    assert R.two_trade_pass_probability(0.5, strict=False) == 0.5


def test_time_filters_and_big_open_candle(bars):
    cfg = StrategyConfig(skip_first_minutes=3, reversion_end="10:00", continuation_end="09:45")
    t = generate_trades(bars, cfg)
    m = t["signal_time"].dt.hour * 60 + t["signal_time"].dt.minute
    cont = t[t["setup"] == "continuation"]
    rev = t[t["setup"] == "reversion"]
    assert (m[cont.index] >= 9 * 60 + 33).all()
    assert (m[rev.index] < 10 * 60).all()
    big = generate_trades(bars, StrategyConfig(big_open_candle_points=0.0, big_open_scope="session"))  # every opening candle counts as big
    assert (big["stop_points"] == 50.0).all()
    assert (big["contracts"] == 1).all()
    none = generate_trades(bars, StrategyConfig(big_open_candle_points=None))
    assert len(none) >= len(big) * 0 + 1


def test_topstep_daily_loss_limit_is_a_soft_stop():
    rules = FIRM_PRESETS["topstep_100k"].with_(min_trading_days=1, consistency_pct=None)
    acct = PropAccount(rules, sims=1, risk_per_trade=1000.0)
    acct.apply_day(np.array([[-1.0, -1.0, -1.0, -1.0]]), np.ones((1, 4), bool))
    assert acct.balance[0] == pytest.approx(98_000)  # trading stopped at the -$2,000 daily loss limit
    assert acct.phase[0] == EVAL


def test_extra_sessions_and_rolling_fair_value(bars):
    cfg = StrategyConfig(pm_session=True, extra_sessions=(("10:00", "10:05", "10:30"),), rolling_fair_value=True)
    t = generate_trades(bars, cfg)
    assert set(t["session"]) <= {"am", "pm", "s1000"}
    fv = fair_value_series(bars, FairValueConfig(pm_anchor=True, extra_anchor_times=("10:00",)))
    assert fv.iloc[30] == bars["open"].iloc[30]  # 10:00 anchor re-sets fair value
    assert fv.iloc[29] == bars["open"].iloc[0]
    assert fv.iloc[270] == bars["open"].iloc[270]  # 14:00 anchor


# ---------------------------------------------------------------------------
# Audit fixes (2026-10-06): hand-built bar sequences for the rule edge cases
# ---------------------------------------------------------------------------

# the fxreplay-style mechanics the hand-built sequences below were written for
LEGACY = dict(displacement_mode="wick", swing_left=3, swing_right=3, continuation_direction="side_of_fv", continuation_stall_candles=None,
              stop_mode="atr_tier", size_mode="tier", risk_dollars=1000.0, target_points=None, max_target_overshoot_pct=None,
              max_consecutive_losses=None, stop_scope="day", flat_at_window_end=True, max_trades_per_day=10, rolling_fair_value=False,
              big_open_measure="range", big_open_scope="am")


def _day_frame(day: str, bars: dict, start="09:30", end="11:05", default=(99.5, 100.0, 99.0, 99.4)):
    """One NY-session day of 1-minute dojis (no displacement) with overrides {"HH:MM": (o, h, l, c)}."""
    idx = pd.date_range(f"{day} {start}", f"{day} {end}", freq="1min", tz="America/New_York")
    rows = []
    for ts in idx:
        key = ts.strftime("%H:%M")
        o, h, l, c = bars.get(key, default)
        rows.append((o, h, l, c, 100))
    return pd.DataFrame(rows, index=idx, columns=["open", "high", "low", "close", "volume"])


def _seed_day(day="2026-01-05"):
    return _day_frame(day, {}, start="09:30", end="16:00", default=(100.0, 100.5, 99.5, 100.0))


def test_structure_already_broken_by_a_plain_close_is_not_a_plus():
    # pivot high 99.9 at 09:36 (confirmed 09:39); 09:40 closes above it with a 35% counter-wick (no signal);
    # the 09:41 displacement candle is therefore NOT the first close through the level -> grade A, not A+
    day = _day_frame("2026-01-06", {
        "09:30": (100.0, 100.5, 99.5, 100.0),
        "09:33": (99.3, 99.6, 99.0, 99.35), "09:34": (99.3, 99.5, 99.0, 99.35), "09:35": (99.3, 99.6, 99.0, 99.35),
        "09:36": (99.3, 99.9, 99.0, 99.4),
        "09:37": (99.3, 99.5, 99.0, 99.35), "09:38": (99.3, 99.4, 99.0, 99.35), "09:39": (99.3, 99.3, 99.0, 99.25),
        "09:40": (99.3, 100.3, 99.2, 99.95),
        "09:41": (99.3, 99.95, 99.25, 99.95),
    })
    df = pd.concat([_seed_day(), day])
    trades = generate_trades(df, StrategyConfig(**LEGACY))
    assert len(trades) >= 1
    first = trades.iloc[0]
    assert first["signal_time"].strftime("%H:%M") == "09:41"
    assert first["grade"] == "A"
    assert first["direction"] == "long" and first["setup"] == "reversion"


def test_first_close_through_a_live_swing_is_a_plus():
    day = _day_frame("2026-01-06", {
        "09:30": (100.0, 100.5, 99.5, 100.0),
        "09:33": (99.3, 99.6, 99.0, 99.35), "09:34": (99.3, 99.5, 99.0, 99.35), "09:35": (99.3, 99.6, 99.0, 99.35),
        "09:36": (99.3, 99.9, 99.0, 99.4),
        "09:37": (99.3, 99.5, 99.0, 99.35), "09:38": (99.3, 99.4, 99.0, 99.35), "09:39": (99.3, 99.3, 99.0, 99.25),
        "09:41": (99.3, 99.95, 99.25, 99.95),
    })
    trades = generate_trades(pd.concat([_seed_day(), day]), StrategyConfig(**LEGACY))
    assert trades.iloc[0]["grade"] == "A+"


def test_window_end_flattens_at_the_open_before_the_bar_range_counts():
    day = _day_frame("2026-01-06", {
        "09:30": (100.0, 100.5, 99.5, 100.0),
        "10:58": (95.0, 95.7, 94.95, 95.7),      # bullish displacement below fair value -> long reversion
        "10:59": (95.8, 96.0, 95.5, 95.9),       # fill bar
        "11:00": (95.6, 125.0, 95.5, 120.0),     # would hit the target after the open
    }, default=(95.5, 95.9, 95.1, 95.4))
    trades = generate_trades(pd.concat([_seed_day(), day]), StrategyConfig(**LEGACY))
    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["entry_time"].strftime("%H:%M") == "10:59"
    assert t["exit_reason"] == "window_end"
    assert t["exit"] == pytest.approx(95.6 - 0.25)


def test_signal_whose_fill_would_be_flattened_is_skipped():
    day = _day_frame("2026-01-06", {
        "09:30": (100.0, 100.5, 99.5, 100.0),
        "10:59": (95.0, 95.7, 94.95, 95.7),      # displacement on the last bar of the window
        "11:00": (95.8, 125.0, 95.5, 120.0),
    }, default=(95.5, 95.9, 95.1, 95.4))
    trades = generate_trades(pd.concat([_seed_day(), day]), StrategyConfig(**LEGACY))
    assert len(trades) == 0


def test_big_open_rule_reads_the_0930_candle_even_with_an_0830_session():
    cfg = StrategyConfig(**{**LEGACY, "big_open_scope": "session"}, extra_sessions=(("08:30", "08:35", "09:29"),))
    base = {"09:30": (100.0, 101.0, 99.0, 100.0), "09:41": (94.3, 95.95, 94.25, 95.95)}  # body large enough for the post-spike ATR
    small_open = _day_frame("2026-01-06", {**base, "08:30": (100.0, 115.0, 85.0, 100.0)}, start="08:30", default=(95.5, 95.9, 95.1, 95.4))
    t = generate_trades(pd.concat([_seed_day(), small_open]), cfg)
    am = t[t["session"] == "am"]
    assert len(am) >= 1 and (am["tier"] != "big_open").all()
    big_open = _day_frame("2026-01-06", {**base, "09:30": (100.0, 115.0, 85.0, 100.0)}, start="08:30", default=(95.5, 95.9, 95.1, 95.4))
    t2 = generate_trades(pd.concat([_seed_day(), big_open]), cfg)
    am2 = t2[t2["session"] == "am"]
    assert len(am2) >= 1 and (am2["tier"] == "big_open").all()


def test_fixed_target_points_override():
    day = _day_frame("2026-01-06", {"09:30": (100.0, 100.5, 99.5, 100.0), "09:41": (95.3, 95.95, 95.25, 95.95)}, default=(95.5, 95.9, 95.1, 95.4))
    t = generate_trades(pd.concat([_seed_day(), day]), StrategyConfig(**{**LEGACY, "target_points": 100.0})).iloc[0]
    assert t["target"] - t["entry"] == pytest.approx(100.0)


def test_soft_daily_loss_limit_liquidates_exactly_at_the_limit():
    rules = FIRM_PRESETS["topstep_100k"].with_(min_trading_days=1, consistency_pct=None)
    acct = PropAccount(rules, sims=1, risk_per_trade=1500.0)
    pnl = acct.apply_day(np.array([[-1.0, -1.0, -1.0]]), np.ones((1, 3), bool))
    assert pnl[0] == pytest.approx(-2_000)  # not -3,000: the breaching trade is cut at the limit
    assert acct.balance[0] == pytest.approx(98_000) and acct.phase[0] == EVAL


def test_consistency_rule_is_phase_specific():
    # E8: no rule in the evaluation, 35% once funded -> two 1.5R wins at target/3 risk pass
    e8 = FIRM_PRESETS["e8_100k_signature"].with_(min_trading_days=1)
    acct = PropAccount(e8, sims=1, risk_per_trade=1000.0, eval_risk=e8.profit_target / 3.0)
    acct.apply_day(np.array([[1.5]]), np.ones((1, 1), bool))
    acct.apply_day(np.array([[1.5]]), np.ones((1, 1), bool))
    assert acct.phase[0] == FUNDED
    assert e8.funded_consistency_pct == 0.35
    # Topstep: 55% rule in the Combine only -> a funded account with one big day still gets paid
    ts = FIRM_PRESETS["topstep_100k"].with_(payout_min_days=1)
    acct = PropAccount(ts, sims=1, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.apply_day(np.array([[3.0]]), np.ones((1, 1), bool))
    assert acct.month_end()[0] > 0


def test_failed_account_is_rebought_next_day_at_the_right_price():
    ts = FIRM_PRESETS["topstep_100k"].with_(min_trading_days=1, consistency_pct=None, daily_loss_limit=None)
    acct = PropAccount(ts, sims=1, risk_per_trade=3000.0)
    acct.apply_day(np.array([[-1.0]]), np.ones((1, 1), bool))
    assert acct.phase[0] == FAILED
    acct.apply_day(np.zeros((1, 1)), np.zeros((1, 1), bool))  # next day: re-bought before trading
    assert acct.phase[0] == EVAL and acct.costs_total[0] == pytest.approx(99.0 + 99.0)
    tr = FIRM_PRESETS["tradeify_100k_growth"].with_(daily_loss_limit=None)
    acct = PropAccount(tr, sims=1, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.apply_day(np.array([[-3.5]]), np.ones((1, 1), bool))
    acct.apply_day(np.zeros((1, 1)), np.zeros((1, 1), bool))
    assert acct.costs_total[0] == pytest.approx(255.0)  # a funded breach needs a new evaluation, not a $169 reset


def test_round_robin_skips_dead_accounts():
    from fpt.portfolio import route_round_robin
    rules = FIRM_PRESETS["topstep_100k"].with_(consistency_pct=None, daily_loss_limit=None)
    accts = [PropAccount(rules, sims=1, risk_per_trade=1000.0, restart_failed=False) for _ in range(4)]
    for k in (0, 2):
        accts[k].phase[:] = FAILED
    offset = route_round_robin(accts, np.array([[1.5, 1.5]]), np.ones((1, 2), bool), np.zeros(1, dtype=int))
    assert [int(a.trading_days[0]) for a in accts] == [0, 1, 0, 1]
    assert int(offset[0]) == 0  # two signals over two live accounts -> back to the start


def test_risk_math_audit_fixes():
    assert R.expected_max_losing_streak(0.54, 100) == pytest.approx(5.38, abs=0.02)  # full Schilling, not the leading term
    d = R.daily_stop_from_stats(0.54, 1.5, 10, 1000.0)
    assert d["stop_r"] <= d["close_quantile_r"]  # the running loss is at least as bad as the close
    static = R.optimal_fixed_risk(0.54, 1.5, 3000, 6000, 1.5, 30, candidates=[750.0], sims=1500)[0]["p_pass"]
    trailing = R.optimal_fixed_risk(0.54, 1.5, 3000, 6000, 1.5, 30, candidates=[750.0], sims=1500, drawdown_type="trailing_eod", lock_profit=3000, daily_loss_limit=2000)[0]["p_pass"]
    assert trailing < static


def test_bootstrap_growth_buys_only_with_cash_and_frees_failed_slots():
    from fpt.bootstrap import GrowthConfig, simulate_growth
    from fpt.propfirm import INACTIVE
    rules = FIRM_PRESETS["fundednext_50k_flex"]
    acct = PropAccount(rules, sims=2, risk_per_trade=1000.0, start_phase=INACTIVE, restart_failed=False)
    assert acct.costs_total.sum() == 0 and (acct.phase == INACTIVE).all()
    acct.purchase(np.array([True, False]))
    assert acct.phase[0] == EVAL and acct.phase[1] == INACTIVE and acct.costs_total[0] == rules.eval_cost
    acct.apply_day(np.array([[-3.0], [0.0]]), np.array([[True], [False]]))  # breach the $1,500 drawdown
    assert acct.phase[0] == FAILED
    acct.release_failed()
    assert acct.phase[0] == INACTIVE
    res = simulate_growth(GrowthConfig(start_cash=60.0, months=2, sims=50, ladder=[("fundednext_50k_flex", 2)]))
    assert res["p_bust"] == 1.0  # $60 cannot buy a $70 evaluation
    res = simulate_growth(GrowthConfig(start_cash=5000.0, months=3, sims=100, ladder=[("fundednext_50k_flex", 2), ("topstep_50k", 2)]))
    assert 0.0 <= res["p_bust"] < 1.0 and res["invested_total"]["mean"] > 0


def test_his_stats_calculator_matches_his_arithmetic():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    # his base case: $100 eval, 33% pass, 33% payout rate, $2,000 payout -> positive EV per evaluation
    r = simulate_his_stats(HisStatsConfig(start_cash=1000.0, months=3, sims=500))
    assert r["calculator"]["ev_per_eval"] == pytest.approx(117.80)
    assert 0.0 < r["p_bust"] < 1.0
    # no edge at all: 10% pass and payout -> negative EV and a bankroll that mostly dies
    r0 = simulate_his_stats(HisStatsConfig(start_cash=1000.0, pass_rate=0.10, payout_rate=0.10, months=6, sims=500))
    assert r0["calculator"]["ev_per_eval"] < 0 and r0["p_bust"] > 0.5



# ---------------------------------------------------------------------------
# His own rules from the primary corpus (defaults since the corpus integration)
# ---------------------------------------------------------------------------

def test_jj_displacement_definition():
    from fpt.structure import is_displacement_jj
    # body larger than the previous candle's body and a close beyond the previous candle
    assert is_displacement_jj(100.0, 101.5, 99.9, 101.4, 100.2, 100.8, 99.8, 100.6, +1)
    assert not is_displacement_jj(100.0, 101.5, 99.9, 100.7, 100.2, 100.8, 99.8, 100.6, +1)  # closes inside the previous candle
    assert not is_displacement_jj(100.0, 100.3, 99.9, 100.2, 99.0, 100.1, 98.0, 100.0, +1)  # smaller body than the previous candle
    assert is_displacement_jj(100.5, 100.55, 99.4, 99.5, 100.6, 100.8, 100.4, 100.5, -1)


def test_continuation_follows_the_opening_candle_colour():
    day = _day_frame("2026-01-06", {
        "09:30": (100.0, 100.7, 99.9, 100.6),      # bullish opening candle -> continuation direction long
        "09:31": (100.6, 100.8, 100.4, 100.5),
        "09:32": (100.5, 100.55, 99.4, 99.5),      # bearish displacement closing below fair value
    })
    df = pd.concat([_seed_day(), day])
    jj = generate_trades(df, StrategyConfig())
    assert not ((jj["setup"] == "continuation") & (jj["direction"] == "short")).any()
    legacy_dir = generate_trades(df, StrategyConfig(continuation_direction="side_of_fv", continuation_stall_candles=None))
    assert ((legacy_dir["setup"] == "continuation") & (legacy_dir["direction"] == "short")).any()


def test_reversion_room_rule_and_fixed_bracket():
    def day_at(level):
        return _day_frame("2026-01-06", {
            "09:30": (100.0, 100.5, 99.5, 100.0),
            "09:39": (level - 0.2, level + 0.1, level - 0.5, level - 0.1),
            "09:40": (level - 0.1, level + 1.5, level - 0.2, level + 1.4),   # his displacement: bigger body, close above the previous high
        }, default=(level, level, level, level))
    cfg = StrategyConfig(rolling_fair_value=False)  # keep the 09:30 anchor so the room rule is tested on its own
    near = generate_trades(pd.concat([_seed_day(), day_at(80.0)]), cfg)   # 18.6 points of room < 0.8 x 38
    assert len(near) == 0
    far = generate_trades(pd.concat([_seed_day(), day_at(60.0)]), cfg)    # 38.6 points of room
    assert len(far) == 1
    t = far.iloc[0]
    assert t["setup"] == "reversion" and t["direction"] == "long"
    assert t["stop_points"] == 25.0 and t["target"] - t["entry"] == pytest.approx(38.0) and t["contracts"] == 1


def test_three_losses_end_the_session(bars):
    trades = generate_trades(bars, StrategyConfig())
    for _, day in trades.groupby(trades["signal_time"].dt.date):
        losses = 0
        for i, r in enumerate(day["r"].to_numpy()):
            losses = losses + 1 if r < 0 else 0
            if losses >= 3:
                assert i == len(day) - 1, "a fourth attempt after three consecutive losses"
                break


# ---------------------------------------------------------------------------
# Correction pass: the calculator reproduces his arithmetic exactly; scans vary
# one input at a time; timing is an explicit state process; walk-forward
# evaluation on a real trade sequence
# ---------------------------------------------------------------------------

def test_his_calculator_reproduces_his_numbers():
    from fpt.bootstrap import his_calculator
    # his base case: $100 x 33% pass x 33% payout x $2,000 = $217.80 back, +$117.80, one payout per funded account, no split
    c = his_calculator(100.0, 0.33, 0.33, 2000.0)
    assert c["gross_return_per_eval"] == pytest.approx(217.80)
    assert c["ev_per_eval"] == pytest.approx(117.80)
    assert c["return_multiple"] == pytest.approx(2.178)
    assert c["p_payout_per_eval"] == pytest.approx(0.1089)
    assert c["cost_per_funded_account"] == pytest.approx(100.0 / 0.33)  # 303.03
    assert c["expected_payout_per_funded_account"] == pytest.approx(660.0)
    assert c["breakeven_payouts_per_100_evals"] == pytest.approx(5.0)
    for n in (5, 10, 20, 50, 100):
        assert c["p_zero_payouts"][n] == pytest.approx((1 - 0.1089) ** n)
    # other inputs follow the same arithmetic
    c = his_calculator(150.0, 0.25, 0.5, 3000.0)
    assert c["gross_return_per_eval"] == pytest.approx(375.0) and c["ev_per_eval"] == pytest.approx(225.0)
    assert c["return_multiple"] == pytest.approx(2.5) and c["p_payout_per_eval"] == pytest.approx(0.125)
    assert c["cost_per_funded_account"] == pytest.approx(600.0) and c["expected_payout_per_funded_account"] == pytest.approx(1500.0)
    assert c["breakeven_payouts_per_100_evals"] == pytest.approx(5.0)
    assert his_calculator(100.0, 0.10, 0.10, 2000.0)["ev_per_eval"] == pytest.approx(-80.0)
    # a monthly figure is evaluations per month x EV per evaluation, with no cycle-length divisor
    c = his_calculator(100.0, 0.33, 0.33, 2000.0, evals_per_month=10)
    assert c["monthly_profit"] == pytest.approx(1178.0) and c["annual_profit"] == pytest.approx(14136.0)
    assert "monthly_profit" not in his_calculator(100.0, 0.33, 0.33, 2000.0)
    # a zero pass rate is a legal scan value: no funded accounts, an infinite cost per funded account, not a crash
    c = his_calculator(100.0, 0.0, 0.33, 2000.0)
    assert c["cost_per_funded_account"] == float("inf") and c["ev_per_eval"] == pytest.approx(-100.0) and c["p_zero_payouts"][5] == 1.0
    with pytest.raises(ValueError):
        his_calculator(0.0, 0.33, 0.33, 2000.0)
    with pytest.raises(ValueError):
        his_calculator(100.0, 1.2, 0.33, 2000.0)


def test_state_process_timing_and_first_batch_check():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    # a certain pass and a certain payout, one account at a time: funded exactly eval_days after the purchase, the first
    # payout exactly eval_days + qualifying_days after the start, and a payout every eval_days + qualifying_days after that
    for E, Q, months in ((4, 10, 2), (1, 1, 1), (2, 5, 3), (7, 3, 2), (10, 20, 4)):
        T = months * 22
        r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=E, qualifying_days=Q, months=months, sims=20, max_live_accounts=1, buys_per_day=1))
        assert r["first_funded"]["median_trading_days"] == E
        assert r["first_payout"]["median_trading_days"] == E + Q and r["p_bust"] == 0.0
        n_pay = (T - 1) // (E + Q)
        assert r["payouts_count"]["median"] == n_pay
        days = [k * (E + Q) for k in range(1, n_pay + 1)]
        assert r["payouts_median_by_month"] == [2000.0 * sum(1 for d in days if d // 22 == m) for m in range(months)]
    # E=4, Q=10: 44 days give 3 payouts in single mode
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=4, qualifying_days=10, months=2, sims=50, max_live_accounts=1, buys_per_day=1))
    assert r["payouts_count"]["median"] == 3 and r["invested_total"]["median"] == 400.0  # the 4th evaluation is in flight at the cut-off
    # payout processing delays the cash, not the account
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=4, qualifying_days=10, payout_processing_days=3, months=2, sims=10, max_live_accounts=1, buys_per_day=1))
    assert r["first_payout"]["median_trading_days"] == 17
    # the day counts are the process, not a clamp: zero days is an error, not a silent one-day step
    with pytest.raises(ValueError):
        simulate_his_stats(HisStatsConfig(eval_days=0, sims=5, months=1))
    with pytest.raises(ValueError):
        simulate_his_stats(HisStatsConfig(qualifying_days=0, sims=5, months=1))
    with pytest.raises(ValueError):
        simulate_his_stats(HisStatsConfig(funded_mode="monthly", sims=5, months=1))
    # the closed form for the first batch: P(no payout from 5 evaluations) = (1 - 0.1089)^5 = 56.2%; the paths that never pay match it
    r = simulate_his_stats(HisStatsConfig(start_cash=500.0, months=12, sims=8000, seed=1))
    p0 = (1 - 0.1089) ** 5
    assert abs(r["first_payout"]["p_never"] - p0) < 3 * (p0 * (1 - p0) / 8000) ** 0.5
    assert abs(r["first_funded"]["p_never"] - (1 - 0.33) ** 5) < 0.02
    assert p0 - 0.01 < r["p_bust"] < p0 + 0.08  # bust includes the survivors that paid once and then lost everything
    # "within 3 months" means inside the first 3 x 22 trading days, the same months the payouts are booked to
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=56, qualifying_days=10, months=4, sims=5, max_live_accounts=1, buys_per_day=1))
    assert r["first_payout"]["median_trading_days"] == 66 and r["first_payout"]["p_within_3_months"] == 0.0 and r["payouts_median_by_month"] == [0.0, 0.0, 0.0, 2000.0]
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=55, qualifying_days=10, months=4, sims=5, max_live_accounts=1, buys_per_day=1))
    assert r["first_payout"]["median_trading_days"] == 65 and r["first_payout"]["p_within_3_months"] == 1.0 and r["payouts_median_by_month"] == [0.0, 0.0, 2000.0, 0.0]


def test_state_process_single_pays_once_repeat_pays_geometrically():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    # every evaluation funds (pass = 1); one account at a time; a bankroll that cannot bust
    base = dict(start_cash=1e9, pass_rate=1.0, payout_rate=0.33, eval_days=1, qualifying_days=1, months=40, sims=1000, max_live_accounts=1, buys_per_day=1, income_after_cash=1e12)
    r = simulate_his_stats(HisStatsConfig(funded_mode="single", **base))
    funded = r["invested_total"]["mean"] / 100.0
    assert abs(r["payouts_count"]["mean"] / funded - 0.33) < 0.01  # at most one payout per funded account: payout_rate on average
    assert r["expected_payouts_per_funded_account"] == pytest.approx(0.33)
    r = simulate_his_stats(HisStatsConfig(funded_mode="repeat", **base))
    funded = r["invested_total"]["mean"] / 100.0
    assert abs(r["payouts_count"]["mean"] / funded - 0.33 / 0.67) < 0.015  # the lifetime model: payout_rate / (1 - payout_rate)
    assert r["expected_payouts_per_funded_account"] == pytest.approx(0.33 / 0.67)
    # hard bound in single mode: pass = payout = 1, one account, 22 days of 2-day cycles -> 10 payouts from 11 evaluations (one in flight)
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=1, qualifying_days=1, funded_mode="single", months=1, sims=5, max_live_accounts=1, buys_per_day=1))
    assert r["payouts_count"]["median"] == 10 and r["invested_total"]["median"] == 1100.0
    # the same in repeat mode: the one evaluation pays every day from day 2
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=1.0, eval_days=1, qualifying_days=1, funded_mode="repeat", months=1, sims=5, max_live_accounts=1, buys_per_day=1))
    assert r["payouts_count"]["median"] == 20 and r["invested_total"]["median"] == 100.0


def test_state_process_bust_only_when_nothing_is_live_and_cash_is_short():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    one = dict(eval_days=4, qualifying_days=10, sims=10, max_live_accounts=1, buys_per_day=1)
    # the funded account is lost at its decision on day 14 with $0 cash: bust
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=0.0, months=1, **one))
    assert r["p_bust"] == 1.0 and r["first_funded"]["median_trading_days"] == 4 and r["first_payout"]["p_never"] == 1.0
    # $0 cash with a live account whose decision falls after the horizon is NOT bust
    r = simulate_his_stats(HisStatsConfig(start_cash=100.0, pass_rate=1.0, payout_rate=0.0, eval_days=10, qualifying_days=20, months=1, sims=10, max_live_accounts=1, buys_per_day=1))
    assert r["p_bust"] == 0.0
    # less than one evaluation of cash and nothing live: bust on day one, nothing invested
    r = simulate_his_stats(HisStatsConfig(start_cash=99.99, months=1, sims=10))
    assert r["p_bust"] == 1.0 and r["invested_total"]["mean"] == 0.0
    # $200 buys a second attempt after the first is lost, then busts: both evaluations are paid for
    r = simulate_his_stats(HisStatsConfig(start_cash=200.0, pass_rate=1.0, payout_rate=0.0, months=2, **one))
    assert r["p_bust"] == 1.0 and r["invested_total"]["median"] == 200.0
    # a zero pass rate: the first batch fails on day 4 and the path is bust
    r = simulate_his_stats(HisStatsConfig(start_cash=500.0, pass_rate=0.0, months=1, sims=10))
    assert r["p_bust"] == 1.0 and r["invested_total"]["median"] == 500.0 and r["calculator"]["cost_per_funded_account"] == float("inf")


def test_state_process_realised_return_matches_the_calculator_when_nothing_busts():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    big = dict(start_cash=1e9, max_live_accounts=10**6, buys_per_day=100, months=12, sims=100, income_after_cash=1e12, seed=7)
    r = simulate_his_stats(HisStatsConfig(**big))
    assert r["p_bust"] == 0.0 and r["benchmark_return_per_eval"] == pytest.approx(1.178)
    assert abs(r["realised_return_per_eval"] - 1.178) < 0.02  # (income + cash + in-flight value - start) / invested -> ev / cost
    # a 90/10 split and the lifetime model move the no-bust benchmark with them
    r = simulate_his_stats(HisStatsConfig(profit_split=0.9, **big))
    assert r["benchmark_return_per_eval"] == pytest.approx(0.9 * 2.178 - 1) and abs(r["realised_return_per_eval"] - (0.9 * 2.178 - 1)) < 0.02
    r = simulate_his_stats(HisStatsConfig(funded_mode="repeat", **big))
    lifetime = 0.33 * 2000.0 * (0.33 / 0.67) / 100.0 - 1
    assert r["benchmark_return_per_eval"] == pytest.approx(lifetime) and abs(r["realised_return_per_eval"] - lifetime) < 0.03


def test_realised_return_per_eval_is_pooled_and_unchanged_by_bust():
    from fpt.bootstrap import HisStatsConfig, simulate_his_stats
    # $500 buys five evaluations and 61% of paths bust: the return PER EVALUATION is still the calculator's +1.178x (pooled
    # over every dollar invested), while the average path's multiple is negative because most paths lose their $500
    r = simulate_his_stats(HisStatsConfig(start_cash=500.0, months=12, sims=4000))
    assert r["p_bust"] > 0.5
    assert abs(r["realised_return_per_eval"] - 1.178) < 0.05
    assert r["mean_path_return_multiple"] < 0.0


def test_his_stats_json_output_is_a_single_json_document(capsys):
    import json
    from fpt.cli import main
    main(["growth", "--his-stats", "--start-cash", "500", "--sims", "2000", "--json"])
    out = capsys.readouterr().out
    d = json.loads(out)  # nothing printed ahead of the document
    assert d["calculator"]["ev_per_eval"] == pytest.approx(117.80)
    assert "realised_return_per_eval" in d and "mean_path_return_multiple" in d


def test_scan_varies_pass_and_payout_independently():
    from fpt.bootstrap import HisStatsConfig, his_stats_scan
    rows = his_stats_scan(HisStatsConfig(sims=300, months=3), start_cash=(1000.0,), pass_rates=(0.33, 0.40), payout_rates=(0.33,))
    assert [(r["pass_rate"], r["payout_rate"]) for r in rows] == [(0.33, 0.33), (0.40, 0.33)]
    rows = his_stats_scan(HisStatsConfig(sims=300, months=3), start_cash=(1000.0,), pass_rates=(0.33,), payout_rates=(0.33, 0.50))
    assert [(r["pass_rate"], r["payout_rate"]) for r in rows] == [(0.33, 0.33), (0.33, 0.50)]


def _trade_rows(day_rs, start="2025-01-06"):
    rows = []
    d0 = pd.Timestamp(start, tz="America/New_York")
    for i, rs in enumerate(day_rs):
        day = d0 + pd.offsets.BDay(i)
        for j, r in enumerate(rs):
            t = day + pd.Timedelta(hours=9, minutes=31 + j)
            rows.append({"entry_time": t, "r": r, "session": "am", "setup": "reversion", "grade": "A", "direction": "long"})
    return pd.DataFrame(rows)


def test_walk_forward_pass_probability_on_a_known_sequence():
    from fpt.evaluate import walk_forward_pass_probability, walk_forward_payout_probability
    rules = FIRM_PRESETS["fundednext_50k_flex"].with_(min_trading_days=1, consistency_pct=None, daily_loss_limit=None, payout_min_days=1)
    # two winning days of +1.5R at target / 3 risk pass on day 2; then two -1R days (-$2,000 total) fail a fresh start on day 2
    seq = [[1.5], [1.5], [-1.0], [-1.0], [1.5], [1.5], [1.5], [1.5]]
    pp = walk_forward_pass_probability(_trade_rows(seq), rules, eval_risk=1000.0, max_days=4)
    assert list(pp["outcome"][:3]) == ["pass", "fail", "fail"]
    assert pp["days"][0] == 2
    # a funded start on the first day pays after its first winning day (one qualifying day, $150+)
    pr = walk_forward_payout_probability(_trade_rows(seq), rules, funded_risk=1000.0, max_days=4)
    assert pr["outcome"][0] == "payout" and pr["days"][0] == 1 and pr["amount"][0] > 0
    # a funded start on day 3 breaches (-$2,000 over two days) before any winning day
    assert pr["outcome"][2] == "bust"


def test_evaluate_pipeline_runs_with_an_out_of_sample_tail(bars):
    from fpt.evaluate import evaluate_trades
    trades = generate_trades(bars, StrategyConfig())
    rep = evaluate_trades(trades, bars, firms=("topstep_50k",), oos_months=0)
    assert "P(pass)" in rep.text and "firms_in_sample" in rep.tables
    assert not np.isnan(rep.tables["firms_in_sample"]["pass_rate"].iloc[0])


def test_walk_forward_calendar_counts_no_trade_days_and_starts_on_them():
    from fpt.evaluate import walk_forward_pass_probability, _daily_r
    rules = FIRM_PRESETS["fundednext_50k_flex"].with_(min_trading_days=1, consistency_pct=None, daily_loss_limit=None)
    cal = pd.bdate_range("2025-01-06", periods=3)  # Mon, Tue, Wed have bars
    trades = _trade_rows([[1.5], [], [1.5]])  # Tuesday has bars but no trade
    # without the calendar the function can only see the two traded days
    pp = walk_forward_pass_probability(trades, rules, eval_risk=1000.0, max_days=10)
    assert len(pp) == 2 and pp["days"][0] == 2
    # with it, Tuesday is a day of the path on which nothing happens, and a start of its own
    pp = walk_forward_pass_probability(trades, rules, eval_risk=1000.0, max_days=10, trading_days=cal)
    assert [str(d.date()) for d in pp["start"]] == ["2025-01-06", "2025-01-07", "2025-01-08"]
    assert pp["outcome"][0] == "pass" and pp["days"][0] == 3
    assert pp["outcome"][1] == "censored"
    # a no-trade day does not count toward the firm's minimum trading days: target hit on the third day, pass on the fourth
    pp = walk_forward_pass_probability(_trade_rows([[1.5], [], [1.5], [0.1]]), rules.with_(min_trading_days=3), 1000.0, 10, trading_days=pd.bdate_range("2025-01-06", periods=4))
    assert pp["outcome"][0] == "pass" and pp["days"][0] == 4
    # calendar days before the first trade are starts too (empty days, then the trades)
    pp = walk_forward_pass_probability(_trade_rows([[1.5], [1.5]], start="2025-01-08"), rules, 1000.0, 3, trading_days=pd.bdate_range("2025-01-06", periods=4))
    assert list(pp["outcome"]) == ["open", "pass", "pass", "censored"] and list(pp["days"][1:3]) == [3, 2]
    # the calendar is in New York dates whatever the zone of the timestamps
    utc = trades.assign(entry_time=trades["entry_time"].dt.tz_convert("UTC"))
    assert [len(r) for r in _daily_r(utc, trading_days=cal.tz_localize("America/New_York"))[1]] == [1, 0, 1]


def test_walk_forward_feeds_consecutive_calendar_days_in_order(monkeypatch):
    from fpt.evaluate import walk_forward_pass_probability
    seq = [[0.01, 0.02], [0.11], [0.21, 0.22, 0.23], [0.31], [], [0.51]]  # distinct R per (day, trade); day 5 has no trade
    cal = pd.bdate_range("2025-01-06", periods=6)
    never = FIRM_PRESETS["topstep_50k"].with_(profit_target=1e9, max_drawdown=1e9, daily_loss_limit=None, consistency_pct=None)
    calls = []
    orig = PropAccount.apply_day
    monkeypatch.setattr(PropAccount, "apply_day", lambda self, r, m: (calls.append((r.copy(), m.copy())), orig(self, r, m))[1])
    pp = walk_forward_pass_probability(_trade_rows(seq), never, 100.0, max_days=6, trading_days=cal)
    assert len(pp) == 6 and len(calls) == 6
    for k, (r, m) in enumerate(calls):  # sim i on step k gets exactly the trades of calendar day i + k, nothing skipped or repeated
        for i in range(6):
            assert list(np.round(r[i][m[i]], 2)) == (list(np.round(seq[i + k], 2)) if i + k < 6 else [])
    assert list(pp["outcome"]) == ["open"] + ["censored"] * 5


def test_walk_forward_applies_the_firm_rules_exactly():
    from fpt.evaluate import walk_forward_pass_probability as wf
    ts = FIRM_PRESETS["topstep_50k"]  # 50k: target 3,000, EOD-trailing 2,000 locking at +2,000, soft daily loss limit 1,000, consistency 55%
    plain = ts.with_(daily_loss_limit=None, consistency_pct=None)
    out = lambda pp, i=0: (pp["outcome"][i], pp["days"][i])
    # two-trade risk: two 1.5R winners at target / 3 pass on day 2
    assert out(wf(_trade_rows([[1.5], [1.5]]), plain, ts.profit_target / 3, 5)) == ("pass", 2)
    # EOD trailing: +1,500 lifts the threshold to 49,500; -1,500 leaves 50,000 (alive); -600 -> 49,400 fails on day 3. Static drawdown would not.
    assert out(wf(_trade_rows([[1.5], [-1.5], [-0.6]]), plain, 1000.0, 5)) == ("fail", 3)
    assert wf(_trade_rows([[1.5], [-1.5], [-0.6]]), plain.with_(drawdown_type="static"), 1000.0, 5)["outcome"][0] == "censored"
    # the lock: +2,500 would trail to 50,500 but locks at the start balance; -2,400 -> 50,100 survives (fails without the lock)
    assert wf(_trade_rows([[2.5], [-2.4]]), plain, 1000.0, 5)["outcome"][0] == "censored"
    assert out(wf(_trade_rows([[2.5], [-2.4]]), plain.with_(drawdown_lock_profit=None), 1000.0, 5)) == ("fail", 2)
    # an intraday dip through yesterday's threshold fails even if the day would close well above it
    assert out(wf(_trade_rows([[1.5], [-2.1, 3.0]]), plain, 1000.0, 5)) == ("fail", 2)
    # soft daily loss limit: -500, -500 stop the day (the three winners after them never trade); without it the day makes +3,500 and passes at once
    soft = ts.with_(consistency_pct=None)
    assert out(wf(_trade_rows([[-0.5, -0.5, 1.5, 1.5, 1.5], [1.5, 1.5], [1.0]]), soft, 1000.0, 5)) == ("pass", 3)
    assert out(wf(_trade_rows([[-0.5, -0.5, 1.5, 1.5, 1.5], [1.5, 1.5], [1.0]]), plain, 1000.0, 5)) == ("pass", 1)
    # the firm liquidates at the limit: -800 then -500 is clipped to -1,000 for the day, so +4,000 next day passes (unclipped: 52,700, not yet)
    assert out(wf(_trade_rows([[-0.8, -0.5], [1.5, 1.5, 1.0]]), soft, 1000.0, 5)) == ("pass", 2)
    assert wf(_trade_rows([[-0.8, -0.5], [1.5, 1.5, 1.0]]), plain, 1000.0, 5)["outcome"][0] == "censored"
    # consistency: +3,000, +2,000, +1,500: the best day (3,000) is within 55% of the profit only on day 3
    assert out(wf(_trade_rows([[3.0], [2.0], [1.5]]), ts.with_(daily_loss_limit=None), 1000.0, 5)) == ("pass", 3)
    # minimum trading days: target on day 1, pass on the third traded day
    assert out(wf(_trade_rows([[3.0], [0.1], [0.1]]), plain.with_(min_trading_days=3), 1000.0, 5)) == ("pass", 3)
    # no lookahead: what happens after a path resolves cannot change it
    a = wf(_trade_rows([[1.5], [1.5], [0.1]]), plain, 1000.0, 5)
    b = wf(_trade_rows([[1.5], [1.5], [-9.0]]), plain, 1000.0, 5)
    assert out(a) == out(b) == ("pass", 2) and list(b["outcome"][1:]) == ["fail", "fail"]


def test_walk_forward_payout_asks_daily_and_retires_after_the_first_payout(monkeypatch):
    from fpt.evaluate import walk_forward_payout_probability
    ts = FIRM_PRESETS["topstep_50k"]  # XFA: five winning days of $150+, 50% of profit up to $2,000, 90/10
    calls = []
    orig = PropAccount.payout_now
    monkeypatch.setattr(PropAccount, "payout_now", lambda self: (calls.append(orig(self)), calls[-1])[1])
    pr = walk_forward_payout_probability(_trade_rows([[1.5]] * 8), ts, funded_risk=500.0, max_days=8)
    assert len(calls) == 8  # asked every day
    # +$750 a day: the fifth winning day pays 50% of $3,750 at the 90% split
    assert pr["outcome"][0] == "payout" and pr["days"][0] == 5 and pr["amount"][0] == pytest.approx(1687.5)
    assert not any(c[0] > 0 for c in calls[5:])  # the path is retired: no second payout
    assert list(pr["outcome"][4:]) == ["censored"] * 4
    # a +$100 day is not a winning day
    pr = walk_forward_payout_probability(_trade_rows([[1.5]] * 4 + [[0.2], [1.5]]), ts, 500.0, 8)
    assert pr["outcome"][0] == "payout" and pr["days"][0] == 6
    # a breach while funded is a bust
    pr = walk_forward_payout_probability(_trade_rows([[-1.0, -1.0], [-1.0, -1.0, -1.0]]), ts.with_(daily_loss_limit=None), 500.0, 8)
    assert pr["outcome"][0] == "bust" and pr["days"][0] == 2


def test_rate_counts_open_starts_and_allows_for_overlapping_paths():
    from fpt.evaluate import _rate, walk_forward_pass_probability
    plain = FIRM_PRESETS["topstep_50k"].with_(daily_loss_limit=None, consistency_pct=None)
    # five +0.1R days on a three-day horizon: three starts use the whole horizon (open), two are cut off by the end of the data
    pp = walk_forward_pass_probability(_trade_rows([[0.1]] * 5), plain, 1000.0, max_days=3)
    assert list(pp["outcome"]) == ["open"] * 3 + ["censored"] * 2
    s = _rate(pp, "pass", "fail", horizon=3)
    assert s["n_seen"] == 3 and s["n_open"] == 3 and s["n_resolved"] == 0 and s["n_censored"] == 2
    assert s["rate"] == 0.0 and np.isnan(s["rate_resolved"])  # nothing passed within the horizon
    # two passes and two open starts: 50% within the horizon, 100% of those that resolved
    df = pd.DataFrame({"start": pd.bdate_range("2025-01-06", periods=5), "outcome": ["pass", "open", "pass", "open", "censored"], "days": [2.0, np.nan, 3.0, np.nan, np.nan]})
    s = _rate(df, "pass", "fail", horizon=10)
    assert s["rate"] == 0.5 and s["rate_resolved"] == 1.0 and s["days_median"] == 2.5
    # every start passes: a standard error of zero, not nan
    s = _rate(walk_forward_pass_probability(_trade_rows([[1.5]] * 4), plain, 1000.0, 30), "pass", "fail", horizon=30)
    assert s["rate"] == 1.0 and s["stderr"] == 0.0
    # neighbouring starts share their days, so runs of equal outcomes widen the error beyond the binomial p(1-p)/n
    runs = pd.DataFrame({"start": pd.bdate_range("2025-01-06", periods=40), "outcome": (["pass"] * 10 + ["fail"] * 10) * 2, "days": 5.0})
    assert _rate(runs, "pass", "fail")["stderr"] > np.sqrt(0.25 / 40)


def test_day_keys_are_new_york_dates_whatever_the_timestamp_zone():
    from fpt.evaluate import _daily_r, r_distribution_breakdown, volatility_regime
    cols = {"session": "pm", "setup": "reversion", "grade": "A", "direction": "long"}
    rows = pd.DataFrame([{"entry_time": pd.Timestamp("2025-01-06 20:05", tz="America/New_York"), "r": 1.5, **cols},  # his 8 PM session: 01:05 UTC the next day
                         {"entry_time": pd.Timestamp("2025-01-07 09:45", tz="America/New_York"), "r": 1.5, **cols}])
    utc = rows.assign(entry_time=rows["entry_time"].dt.tz_convert("UTC"))
    assert [str(d.date()) for d in _daily_r(utc)[0]] == ["2025-01-06", "2025-01-07"]
    bd = r_distribution_breakdown(utc)
    assert bd.loc[bd["dimension"] == "all", "trades_per_day"].iloc[0] == 1.0
    bars = synthetic_minute_bars(days=20, seed=3)
    reg = volatility_regime(bars)
    assert reg.index.tz is None and len(reg) == 20 and reg.equals(volatility_regime(bars.tz_convert("UTC")))


def test_trades_per_day_divides_by_the_trading_days_of_the_bucket():
    from fpt.evaluate import r_distribution_breakdown, volatility_regime, trading_days_of
    bars = synthetic_minute_bars(days=30, seed=11)
    trades = generate_trades(bars, StrategyConfig(allow_grade_a=False))  # A+ only: some days carry no trade
    cal = trading_days_of(bars)
    assert len(cal) == 30 and trades["entry_time"].dt.normalize().nunique() < 30
    bd = r_distribution_breakdown(trades, volatility_regime(bars), trading_days=cal)
    row = lambda dim, key: bd[(bd["dimension"] == dim) & (bd["bucket"] == key)].iloc[0]
    assert row("all", "all")["trades_per_day"] == pytest.approx(len(trades) / 30)
    assert row("setup", "reversion")["trades_per_day"] == pytest.approx(row("setup", "reversion")["trades"] / 30)
    reg = volatility_regime(bars)
    assert row("regime", "high")["trades_per_day"] == pytest.approx(row("regime", "high")["trades"] / (reg == "high").sum())


def test_evaluate_in_sample_numbers_do_not_depend_on_the_out_of_sample_tail(tmp_path):
    from fpt.evaluate import evaluate_trades, _ny_naive
    from fpt.cli import main
    bars = synthetic_minute_bars(days=60, seed=5)
    trades = generate_trades(bars, StrategyConfig())
    full = evaluate_trades(trades, bars, firms=("topstep_50k",), oos_months=1)
    assert "firms_out_of_sample" in full.tables and full.tables["firms_out_of_sample"]["n_eval_starts"].iloc[0] > 0
    # the same data cut at the in-sample boundary, with nothing after it: every in-sample table must be identical
    day = _ny_naive(trades["entry_time"]).dt.normalize()
    cut = (day.max() - pd.DateOffset(months=1)).normalize()
    head_bars = bars[bars.index.tz_localize(None).normalize() <= cut]
    head = evaluate_trades(trades[day <= cut], head_bars, firms=("topstep_50k",), oos_months=0)
    for key in ("r_in_sample", "firms_in_sample", "pass_breakdown_in_sample_topstep_50k", "pass_in_sample_topstep_50k", "payout_in_sample_topstep_50k"):
        pd.testing.assert_frame_equal(full.tables[key].reset_index(drop=True), head.tables[key].reset_index(drop=True))
    # the regime rows are in both (the terciles are fitted on the in-sample bars only)
    assert (full.tables["r_in_sample"]["dimension"] == "regime").sum() == 3
    # end to end through the CLI: the out-of-sample section is populated and the in-sample section is the same with or without the tail
    bars.tz_localize(None).to_csv(tmp_path / "full.csv")
    head_bars.tz_localize(None).to_csv(tmp_path / "head.csv")
    assert main(["evaluate", "--csv", str(tmp_path / "full.csv"), "--firms", "topstep_50k", "--oos-months", "1", "--report", str(tmp_path / "full.md")]) == 0
    assert main(["evaluate", "--csv", str(tmp_path / "head.csv"), "--firms", "topstep_50k", "--oos-months", "0", "--report", str(tmp_path / "head.md")]) == 0
    section = lambda text: text.split("## R distribution, in sample")[1].split("## R distribution, out of sample")[0].strip()
    full_md, head_md = open(tmp_path / "full.md").read(), open(tmp_path / "head.md").read()
    assert "## R distribution, out of sample" in full_md and "## Pass and payout probability under exact firm rules, out of sample" in full_md
    assert section(full_md) == section(head_md)


def test_csv_roundtrip_across_the_dst_change(tmp_path):
    bars = synthetic_minute_bars(days=70, seed=2)  # Jan 6 -> mid April: crosses the March DST switch, so offsets change -05:00 -> -04:00
    path = tmp_path / "dst.csv"
    bars.to_csv(path)
    back = load_minute_bars(str(path))
    assert len(back) == len(bars)
    assert (back.index == bars.index).all()
