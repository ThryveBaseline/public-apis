"""Command line interface.

    python -m fpt.cli synthetic --days 60 --out data/synthetic.csv
    python -m fpt.cli backtest --csv data/NQ_1m.csv --source-tz UTC --report out/report.md
    python -m fpt.cli sizing --atr 12.4
    python -m fpt.cli edge --p 0.54 --rr 1.5 --trades-per-day 1.5 --risk 1000
    python -m fpt.cli evaluation --firm topstep_100k --p 0.54 --rr 1.5
    python -m fpt.cli portfolio --account topstep_100k:20 --account tradeify_100k_select:25 --months 6
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import risk as R
from .backtest import run_backtest
from .data import load_minute_bars, synthetic_minute_bars
from .bootstrap import DEFAULT_LADDER, GrowthConfig, growth_scan, simulate_growth
from .portfolio import PortfolioConfig, optimal_risk_scan, simulate_portfolio
from .propfirm import FIRM_PRESETS
from .strategy import StrategyConfig


def _cfg_from_args(a) -> StrategyConfig:
    cfg = StrategyConfig()
    for name in ("rr", "risk_dollars", "max_trades_per_day", "daily_loss_stop_r", "max_consecutive_losses", "stop_scope", "target_points", "min_body_atr", "wick_pct", "anchor", "size_mode", "continuation_end", "window_end", "slippage_points", "commission_per_contract_side", "skip_first_minutes", "reversion_end", "big_open_candle_points"):
        v = getattr(a, name, None)
        if v is not None:
            setattr(cfg, name, v)
    if getattr(a, "pm_session", False):
        cfg.pm_session = True
    if getattr(a, "all_sessions", False):
        cfg.pm_session = True
        cfg.extra_sessions = (("08:30", "08:35", "09:29"), ("18:00", "18:05", "19:30"), ("20:00", "20:05", "21:30"))
    if getattr(a, "rolling_fair_value", False):
        cfg.rolling_fair_value = True
    if getattr(a, "require_band_touch", False):
        cfg.require_band_touch = True
    if getattr(a, "no_grade_a", False):
        cfg.allow_grade_a = False
    return cfg


def main(argv=None):
    p = argparse.ArgumentParser(prog="fpt", description="Fair Pricing Theory replication toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("synthetic", help="write synthetic 1-minute bars (for exercising the code only)")
    s.add_argument("--days", type=int, default=60)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--out", required=True)

    b = sub.add_parser("backtest", help="backtest the rules on a 1-minute NQ CSV")
    b.add_argument("--csv", required=True)
    b.add_argument("--source-tz", default="America/New_York", help="timezone of naive timestamps in the file (Databento: UTC)")
    b.add_argument("--report")
    b.add_argument("--trades")
    b.add_argument("--rr", type=float)
    b.add_argument("--risk-dollars", type=float, dest="risk_dollars")
    b.add_argument("--size-mode", choices=["tier", "risk"], dest="size_mode")
    b.add_argument("--max-trades-per-day", type=int, dest="max_trades_per_day")
    b.add_argument("--daily-loss-stop-r", type=float, dest="daily_loss_stop_r")
    b.add_argument("--max-consecutive-losses", type=int, dest="max_consecutive_losses")
    b.add_argument("--stop-scope", choices=["day", "session"], dest="stop_scope", help="session = the loss stops reset at each session start (reported: three losses in a row end the session)")
    b.add_argument("--target-points", type=float, dest="target_points", help="fixed target in points instead of rr x stop (reported: 100-point targets on funded accounts without a consistency rule)")
    b.add_argument("--min-body-atr", type=float, dest="min_body_atr")
    b.add_argument("--wick-pct", type=float, dest="wick_pct")
    b.add_argument("--anchor", choices=["open_0930", "close_0929", "vwap_0929_0930"])
    b.add_argument("--continuation-end", dest="continuation_end")
    b.add_argument("--window-end", dest="window_end")
    b.add_argument("--skip-first-minutes", type=int, dest="skip_first_minutes")
    b.add_argument("--reversion-end", dest="reversion_end", help="e.g. 10:00 (fxreplay's filtered variant)")
    b.add_argument("--big-open-candle-points", type=float, dest="big_open_candle_points")
    b.add_argument("--slippage-points", type=float, dest="slippage_points")
    b.add_argument("--commission", type=float, dest="commission_per_contract_side")
    b.add_argument("--pm-session", action="store_true", dest="pm_session")
    b.add_argument("--all-sessions", action="store_true", help="JJ's full day: 08:30 news, 09:30, 14:00, 18:00 and 20:00 sessions")
    b.add_argument("--rolling-fair-value", action="store_true", dest="rolling_fair_value", help="re-anchor fair value to the most recent consolidation (JJ's stated practice)")
    b.add_argument("--require-band-touch", action="store_true", dest="require_band_touch")
    b.add_argument("--no-grade-a", action="store_true", dest="no_grade_a")

    z = sub.add_parser("sizing", help="stop and contracts for a 1-minute ATR reading")
    z.add_argument("--atr", type=float, required=True)
    z.add_argument("--risk", type=float, default=1000.0)
    z.add_argument("--point-value", type=float, default=20.0)

    e = sub.add_parser("edge", help="expectancy, Kelly, streaks and the statistical daily stop")
    e.add_argument("--p", type=float, default=0.54)
    e.add_argument("--rr", type=float, default=1.5)
    e.add_argument("--trades-per-day", type=float, default=1.5, help="qualifying trades per day; the public backtests imply 1-3 (see README calibration)")
    e.add_argument("--risk", type=float, default=1000.0)
    e.add_argument("--quantile", type=float, default=0.05)

    v = sub.add_parser("evaluation", help="probability of passing an evaluation vs fixed risk per trade")
    v.add_argument("--firm", default="topstep_100k", choices=sorted(FIRM_PRESETS))
    v.add_argument("--p", type=float, default=0.54)
    v.add_argument("--rr", type=float, default=1.5)
    v.add_argument("--trades-per-day", type=float, default=1.5)
    v.add_argument("--max-days", type=int, default=30)
    v.add_argument("--sims", type=int, default=4000)

    f = sub.add_parser("portfolio", help="multi-account Monte Carlo")
    f.add_argument("--account", action="append", default=[], help="preset:count, repeatable")
    f.add_argument("--risk", type=float, default=1000.0)
    f.add_argument("--p", type=float, default=0.54)
    f.add_argument("--rr", type=float, default=1.5)
    f.add_argument("--trades-per-day", type=float, default=1.5)
    f.add_argument("--months", type=int, default=6)
    f.add_argument("--sims", type=int, default=1000)
    f.add_argument("--daily-loss-stop-r", type=float)
    f.add_argument("--max-consecutive-losses", type=int)
    f.add_argument("--start-funded", action="store_true")
    f.add_argument("--routing", choices=["copy", "round_robin"], default="copy", help="round_robin = one trade per account per day, accounts in rotation (JJ's stated routine)")
    f.add_argument("--eval-risk-mode", choices=["fixed", "two_trade"], default="fixed", dest="eval_risk_mode", help="two_trade = evaluations risk target/(2*rr) per trade (JJ's max-risk eval posture)")
    f.add_argument("--scan-risk", action="store_true", help="scan several risk levels instead of one run")
    f.add_argument("--json", action="store_true")

    g = sub.add_parser("growth", help="bootstrap: grow from a small bankroll by reinvesting payouts in new evaluations")
    g.add_argument("--start-cash", type=float, default=500.0)
    g.add_argument("--monthly-contribution", type=float, default=0.0)
    g.add_argument("--months", type=int, default=12)
    g.add_argument("--sims", type=int, default=1000)
    g.add_argument("--p", type=float, default=0.54)
    g.add_argument("--rr", type=float, default=1.5)
    g.add_argument("--trades-per-day", type=float, default=1.5)
    g.add_argument("--eval-risk-mode", choices=["two_trade", "fixed"], default="two_trade", dest="eval_risk_mode")
    g.add_argument("--eval-risk", type=float, default=500.0, help="per-trade evaluation risk in fixed mode")
    g.add_argument("--funded-risk", type=float, default=1000.0)
    g.add_argument("--ladder", action="append", default=[], help="preset:max_accounts in purchase order, repeatable (default: his S/A-tier ladder, cheapest first)")
    g.add_argument("--income-after-funded", type=int, default=5)
    g.add_argument("--income-take", type=float, default=0.5)
    g.add_argument("--max-buys-per-day", type=int, default=1)
    g.add_argument("--scan", action="store_true", help="scan starting cash x evaluation posture")
    g.add_argument("--json", action="store_true")

    sub.add_parser("firms", help="list firm presets and their verification status")

    m = sub.add_parser("evalmath", help="JJ's prop-firm arithmetic: cost to funded, cost per drawdown dollar, eval EV, two-trade pass probability")
    m.add_argument("--fee", type=float, default=100.0)
    m.add_argument("--pass-rate", type=float, default=0.30)
    m.add_argument("--drawdown", type=float, default=2000.0)
    m.add_argument("--p-payout", type=float, default=0.10)
    m.add_argument("--payout", type=float, default=2000.0)
    m.add_argument("--p", type=float, default=0.5)

    c = sub.add_parser("implied", help="back out the per-account daily edge implied by a reported result")
    c.add_argument("--payout", type=float, required=True, help="dollars reported")
    c.add_argument("--accounts", type=int, required=True)
    c.add_argument("--days", type=int, required=True, help="trading days")
    c.add_argument("--risk", type=float, default=1000.0)
    c.add_argument("--p", type=float, default=0.54)
    c.add_argument("--rr", type=float, default=1.5)

    a = p.parse_args(argv)

    if a.cmd == "synthetic":
        df = synthetic_minute_bars(days=a.days, seed=a.seed)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        df.to_csv(a.out)
        print(f"wrote {len(df)} bars to {a.out}")
        return 0

    if a.cmd == "backtest":
        df = load_minute_bars(a.csv, source_tz=a.source_tz)
        cfg = _cfg_from_args(a)
        res = run_backtest(df, cfg)
        text = res.report()
        print(text)
        if a.report:
            os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
            with open(a.report, "w") as fh:
                fh.write(text)
        if a.trades:
            res.trades.to_csv(a.trades, index=False)
        return 0

    if a.cmd == "sizing":
        tier = R.atr_tier(a.atr)
        n_risk = R.contracts_for_risk(a.risk, tier.stop_points, a.point_value)
        print(json.dumps({
            "atr": a.atr, "tier": tier.name, "stop_points": tier.stop_points,
            "contracts_by_tier": tier.contracts, "risk_by_tier": R.dollar_risk(tier.stop_points, tier.contracts, a.point_value),
            "contracts_for_risk": n_risk, "target_points": 1.5 * tier.stop_points,
        }, indent=2))
        return 0

    if a.cmd == "edge":
        out = {
            "expectancy_r": R.expectancy_r(a.p, a.rr),
            "breakeven_winrate": R.breakeven_winrate(a.rr),
            "kelly_fraction_of_bankroll": R.kelly_fraction(a.p, a.rr),
            "expected_daily_r": R.expectancy_r(a.p, a.rr) * a.trades_per_day,
            "expected_daily_dollars": R.expectancy_r(a.p, a.rr) * a.trades_per_day * a.risk,
            "expected_max_losing_streak_per_100": R.expected_max_losing_streak(a.p, 100),
            "losing_streak_quantiles_per_200": {str(k): v for k, v in R.losing_streak_quantiles(a.p, 200).items()},
            "daily_stop": R.daily_stop_from_stats(a.p, a.rr, a.trades_per_day, a.risk, a.quantile),
        }
        print(json.dumps(out, indent=2))
        return 0

    if a.cmd == "evaluation":
        rules = FIRM_PRESETS[a.firm]
        dll = rules.daily_loss_limit if (rules.daily_loss_limit is not None and not rules.daily_loss_fails_account) else None
        rows = R.optimal_fixed_risk(a.p, a.rr, rules.max_drawdown, rules.profit_target, a.trades_per_day, a.max_days, sims=a.sims,
                                    drawdown_type=rules.drawdown_type, lock_profit=rules.drawdown_lock_profit, daily_loss_limit=dll)
        lock = f", locks at start+{rules.drawdown_lock_profit:,.0f}" if rules.drawdown_lock_profit is not None else ""
        print(f"{rules.firm} {rules.plan}: target {rules.profit_target:,.0f}, drawdown {rules.max_drawdown:,.0f} {rules.drawdown_type}{lock}, "
              f"soft daily loss limit {dll if dll is None else format(dll, ',.0f')} (verified={rules.verified}); consistency and minimum-day rules not applied")
        print(f"{'risk/trade':>12} {'% of DD':>8} {'P(pass)':>8} {'P(fail)':>8} {'median days':>12}")
        for r in rows:
            print(f"{r['risk_per_trade']:>12,.0f} {r['risk_pct_of_drawdown']:>8.0%} {r['p_pass']:>8.1%} {r['p_fail']:>8.1%} {r['median_days_to_pass']:>12.1f}")
        return 0

    if a.cmd == "portfolio":
        accounts = []
        for spec in a.account or ["topstep_100k:10"]:
            key, _, cnt = spec.partition(":")
            accounts.append((key, int(cnt or 1)))
        cfg = PortfolioConfig(accounts=accounts, risk_per_trade=a.risk, p_win=a.p, rr=a.rr, trades_per_day=a.trades_per_day, months=a.months, sims=a.sims, daily_loss_stop_r=a.daily_loss_stop_r, max_consecutive_losses=a.max_consecutive_losses, start_funded=a.start_funded, routing=a.routing, eval_risk_mode=a.eval_risk_mode)
        if a.scan_risk:
            rows = optimal_risk_scan(cfg)
            print(f"{'risk/trade':>10} {'net median':>12} {'net p5':>12} {'P(net>0)':>9} {'breaches':>9} {'payouts mean':>13}")
            for r in rows:
                print(f"{r['risk_per_trade']:>10,.0f} {r['net_median']:>12,.0f} {r['net_p5']:>12,.0f} {r['p_net_positive']:>9.1%} {r['breaches_mean']:>9.1f} {r['payouts_mean']:>13,.0f}")
            return 0
        res = simulate_portfolio(cfg)
        res.pop("_arrays", None)
        if a.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"accounts={res['accounts']} months={res['months']} risk/trade={a.risk:,.0f} p={a.p} rr={a.rr} trades/day={a.trades_per_day}")
            nt = res["net_total"]
            print(f"net cash after costs: p5 {nt['p5']:,.0f} | p25 {nt['p25']:,.0f} | median {nt['median']:,.0f} | p75 {nt['p75']:,.0f} | p95 {nt['p95']:,.0f}")
            print(f"payouts median {res['payouts_total']['median']:,.0f}, costs median {res['costs_total']['median']:,.0f}, P(net>0) {res['p_net_positive']:.1%}, breaches/sim {res['breaches_per_sim']['mean']:.1f}")
            print("monthly net median: " + ", ".join(f"{x:,.0f}" for x in res["monthly_net_median"]))
            print("funded accounts (median) by month: " + ", ".join(f"{x:.0f}" for x in res["funded_accounts_median_by_month"]))
        return 0

    if a.cmd == "evalmath":
        print(json.dumps({
            "cost_to_funded": R.cost_to_funded(a.fee, a.pass_rate),
            "cost_per_drawdown_dollar": R.cost_per_drawdown_dollar(a.fee, a.drawdown),
            "eval_expected_value": R.eval_expected_value(a.p_payout, a.payout, a.fee),
            "two_trade_pass_probability_strict": R.two_trade_pass_probability(a.p, True),
            "two_trade_pass_probability_two_wins_before_two_losses": R.two_trade_pass_probability(a.p, False),
        }, indent=2))
        return 0

    if a.cmd == "implied":
        out = R.implied_daily_r(a.payout, a.accounts, a.days, a.risk)
        out["trades_per_day_needed_at_p_rr"] = R.trades_per_day_for_daily_r(out["r_per_account_day"], a.p, a.rr)
        print(json.dumps(out, indent=2))
        return 0

    if a.cmd == "growth":
        ladder = [(k, int(n or 1)) for k, _, n in (spec.partition(":") for spec in a.ladder)] or list(DEFAULT_LADDER)
        cfg = GrowthConfig(start_cash=a.start_cash, monthly_contribution=a.monthly_contribution, ladder=ladder, p_win=a.p, rr=a.rr, trades_per_day=a.trades_per_day,
                           eval_risk_mode=a.eval_risk_mode, eval_risk=a.eval_risk, funded_risk=a.funded_risk, months=a.months, sims=a.sims,
                           income_after_funded=a.income_after_funded, income_take=a.income_take, max_buys_per_day=a.max_buys_per_day)
        if a.scan:
            rows = growth_scan(cfg)
            print(f"{'posture':>10} {'start $':>8} {'P(bust)':>8} {'P(5 funded)':>12} {'months to 5':>12} {'funded m'+str(a.months):>10} {'payouts p25':>12} {'payouts med':>12}")
            for r in rows:
                print(f"{r['eval_risk_mode']:>10} {r['start_cash']:>8,.0f} {r['p_bust']:>8.1%} {r['p_5_funded']:>12.1%} {r['months_to_5_funded_median']:>12.1f} {r['funded_last_median']:>10.0f} {r['payouts_last_p25']:>12,.0f} {r['payouts_last_median']:>12,.0f}")
            return 0
        res = simulate_growth(cfg)
        res.pop("_arrays", None)
        if a.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"start ${a.start_cash:,.0f}, {a.months} months, {a.sims} paths, posture {a.eval_risk_mode}, ladder {ladder}")
            print(f"P(bust) {res['p_bust']:.1%}; first payout within 3 months {res['p_first_payout_within_3_months']:.1%}; never {res['first_payout_month']['p_never']:.1%}")
            print("months to N funded (median | P reached): " + ", ".join(f"{k}: {v['median']:.0f} | {v['p_reached']:.0%}" for k, v in res['months_to_funded'].items()))
            fl = res['funded_accounts_last_month']; pl = res['monthly_payouts_last_month']; it = res['income_total']
            print(f"last month: funded accounts p25/med/p75 {fl['p25']:.0f}/{fl['median']:.0f}/{fl['p75']:.0f}; payouts {pl['p25']:,.0f}/{pl['median']:,.0f}/{pl['p75']:,.0f}; income taken so far median {it['median']:,.0f}")
            print("funded accounts (median) by month: " + ", ".join(f"{x:.0f}" for x in res['funded_median_by_month']))
            print("payouts (median) by month: " + ", ".join(f"{x:,.0f}" for x in res['payouts_median_by_month']))
        return 0

    if a.cmd == "firms":
        for k, r in FIRM_PRESETS.items():
            print(f"{k:24s} {r.firm:18s} {r.plan:22s} size {r.account_size:>9,.0f} target {r.profit_target:>7,.0f} dd {r.max_drawdown:>7,.0f} {r.drawdown_type:18s} verified={r.verified}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
