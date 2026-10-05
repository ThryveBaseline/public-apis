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
from .portfolio import PortfolioConfig, optimal_risk_scan, simulate_portfolio
from .propfirm import FIRM_PRESETS
from .strategy import StrategyConfig


def _cfg_from_args(a) -> StrategyConfig:
    cfg = StrategyConfig()
    for name in ("rr", "risk_dollars", "max_trades_per_day", "daily_loss_stop_r", "max_consecutive_losses", "min_body_atr", "wick_pct", "anchor", "size_mode", "continuation_end", "window_end", "slippage_points", "commission_per_contract_side"):
        v = getattr(a, name, None)
        if v is not None:
            setattr(cfg, name, v)
    if getattr(a, "pm_session", False):
        cfg.pm_session = True
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
    b.add_argument("--min-body-atr", type=float, dest="min_body_atr")
    b.add_argument("--wick-pct", type=float, dest="wick_pct")
    b.add_argument("--anchor", choices=["open_0930", "close_0929", "vwap_0929_0930"])
    b.add_argument("--continuation-end", dest="continuation_end")
    b.add_argument("--window-end", dest="window_end")
    b.add_argument("--slippage-points", type=float, dest="slippage_points")
    b.add_argument("--commission", type=float, dest="commission_per_contract_side")
    b.add_argument("--pm-session", action="store_true", dest="pm_session")
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

    sub.add_parser("firms", help="list firm presets and their verification status")

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
        rows = R.optimal_fixed_risk(a.p, a.rr, rules.max_drawdown, rules.profit_target, a.trades_per_day, a.max_days, sims=a.sims)
        print(f"{rules.firm} {rules.plan}: target {rules.profit_target:,.0f}, drawdown {rules.max_drawdown:,.0f} (verified={rules.verified})")
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

    if a.cmd == "implied":
        out = R.implied_daily_r(a.payout, a.accounts, a.days, a.risk)
        out["trades_per_day_needed_at_p_rr"] = R.trades_per_day_for_daily_r(out["r_per_account_day"], a.p, a.rr)
        print(json.dumps(out, indent=2))
        return 0

    if a.cmd == "firms":
        for k, r in FIRM_PRESETS.items():
            print(f"{k:24s} {r.firm:18s} {r.plan:22s} size {r.account_size:>9,.0f} target {r.profit_target:>7,.0f} dd {r.max_drawdown:>7,.0f} {r.drawdown_type:18s} verified={r.verified}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
