# Replication plan

Goal: reproduce JJ Simon's published operation end to end and find out,
with your own data, which parts of it carry the edge.

## Phase 0: evidence (this repository)
- [x] Reconstruct the strategy rules, risk model and account operation from public sources (`docs/DOSSIER.md`).
- [x] Implement them as testable code with every unstated choice exposed as a parameter (`fpt/`, `docs/ASSUMPTIONS.md`).
- [ ] Fold in the primary transcripts (his videos, the Chart Fanatics episode) once fetched on a machine with YouTube access (`docs/research/`).

## Phase 1: data
- Buy or export at least 2 years of 1-minute NQ (continuous front-month, volume-rolled). Databento GLBX.MDP3 `ohlcv-1m` is the cleanest; TradingView export works for a few months.
- Keep the full session (overnight included) so the 09:29 pre-open candle and the 18:00/20:00 sessions can be studied.
- Load with `fpt.data.load_minute_bars(path, source_tz=...)` and check the first bar of a day is 09:30 ET.

## Phase 2: baseline backtest
- `python -m fpt.cli backtest --csv data/NQ_1m.csv --source-tz UTC --report out/baseline.md --trades out/baseline_trades.csv`
- Compare with the public third-party numbers (fxreplay 52-54% / PF 1.66-1.76; the 365-day test PF 1.7, 289 trades). Differences in trade count come first from `continuation_end`, `min_body_atr` and `allow_grade_a`.

## Phase 3: sensitivity
Sweep, one at a time, and keep the regions that are flat, not the peaks:
- `continuation_end` in {09:33, 09:35, 09:40, 09:45}
- `min_body_atr` in {0, 0.5, 1.0, 1.5}
- `allow_grade_a` in {True, False}
- `require_band_touch` in {False, True} with `band_points` in {25, 38, 50}
- reversion cut-off: fxreplay found reversions after 10:00 weak; test `window_end` in {10:00, 10:30, 11:00}
- `flat_at_window_end` in {True, False}
- slippage 0.25 vs 0.50 points: a 16.5-point stop with 3 contracts is sensitive to fills

## Phase 4: the operation
- Take the R distribution from the best stable region and run `fpt.portfolio.simulate_portfolio` with `bootstrap_r` set to it.
- Fill `fpt/propfirm.py` presets with the current rules of the firms you will use (set `verified=True` with the source URL and date).
- Scan risk per trade (`optimal_risk_scan`) and account mix; the output to watch is the 5th percentile of net cash after costs, not the median.
- Decide the daily stop from `risk.daily_stop_from_stats` for your measured p and trades/day, and the consecutive-loss stop from `risk.losing_streak_quantiles`.

## Phase 5: forward test
- Put `pine/fair_pricing_theory.pine` on NQ1! 1-minute, chart timezone America/New_York, and log signals for 20 sessions. Compare with `generate_trades` on the same days (they should agree on signal bars; differences come from pivot confirmation timing).
- Paper trade one evaluation-sized account for a month at the backtested parameters before copying to more accounts.

## Phase 6: scale
- Add accounts only as the forward-test statistics stay inside the backtest's confidence band (win rate within about 5 points, PF above 1.3 over 100+ trades).
- Stagger evaluations so a breached funded account has a replacement already past its minimum trading days.
