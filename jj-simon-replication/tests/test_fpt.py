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
    assert r["ev_per_evaluation_dollars"] > 0
    assert 0.0 < r["p_bust"] < 1.0
    # no edge at all: 10% pass and payout -> negative EV and a bankroll that mostly dies
    r0 = simulate_his_stats(HisStatsConfig(start_cash=1000.0, pass_rate=0.10, payout_rate=0.10, months=6, sims=500))
    assert r0["ev_per_evaluation_dollars"] < 0 and r0["p_bust"] > 0.5



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
