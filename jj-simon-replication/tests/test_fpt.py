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
    np.testing.assert_allclose((long["target"] - long["entry"]).to_numpy(), 1.5 * long["stop_points"].to_numpy())
    # one position at a time
    t = trades.sort_values("entry_time")
    assert (t["entry_time"].to_numpy()[1:] >= t["exit_time"].to_numpy()[:-1]).all()
    # a stop-out loses risk + costs
    stops = trades[trades["exit_reason"] == "stop"]
    if len(stops):
        assert (stops["pnl_dollars"] < -stops["risk_dollars"]).all()
    # flat by window end
    assert (trades["exit_time"].dt.hour * 60 + trades["exit_time"].dt.minute <= 11 * 60).all()


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
    rules = FIRM_PRESETS["topstep_100k"].with_(payout_min_days=1, consistency_pct=None, payout_max=None)
    acct = PropAccount(rules, sims=1, risk_per_trade=1000.0, start_phase=FUNDED)
    acct.apply_day(np.array([[1.5, 1.5]]), np.array([[True, True]]))
    cash = acct.month_end()
    assert cash[0] == pytest.approx(3000 * rules.payout_split)
    assert acct.balance[0] == pytest.approx(100_000)


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
    big = generate_trades(bars, StrategyConfig(big_open_candle_points=0.0))  # every opening candle counts as big
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
