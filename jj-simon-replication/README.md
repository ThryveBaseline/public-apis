# JJ Simon replication: Fair Pricing Theory, ATR-tier risk, multi-account prop firm operation

A from-scratch, testable reconstruction of the method JJ Simon (YouTube
`@itsjjsimon`) says produced his prop-firm payouts: mean reversion to the
09:30 ET "fair price" on 1-minute NQ, break-of-structure plus displacement
entries, ATR-tier stops with a fixed 1.5R target, roughly ten trades per
session, copied across dozens of prop-firm accounts, with statistical rules
for when to stop.

Nothing here is endorsed by or affiliated with JJ Simon. Every rule is
reconstructed from public material (his videos and landing pages, podcast
appearances, third-party backtests and indicators). `docs/DOSSIER.md` holds
the evidence with sources; `docs/ASSUMPTIONS.md` lists every place the
public record is silent and what the code assumes instead.

Futures trading can lose more than the drawdown of a prop account costs
you; nothing in this repository is advice.

## Layout

```
fpt/            the library
  data.py       CSV loading (any common 1-minute export), synthetic bars for tests
  fair_value.py 09:30 / 14:00 fair-value anchors and bands
  indicators.py ATR (Wilder), confirmed pivot highs/lows
  structure.py  displacement-candle and structure-break tests
  strategy.py   the rules: windows, continuation vs reversion, A+/A grades, ATR tiers, 1.5R, daily limits
  backtest.py   bar-by-bar backtest with slippage and commission; statistics tables
  risk.py       expectancy, Kelly, losing-streak quantiles, risk of ruin, statistical daily stop, optimal fixed risk
  propfirm.py   firm rule presets and a vectorised evaluation/funded/payout account simulator
  portfolio.py  N-account copy-trading Monte Carlo with fees, resets, breaches and payouts
  cli.py        command line
pine/           TradingView port of the signal logic
tests/          pytest suite (18 tests)
docs/           dossier, assumptions, replication plan, raw research
data/           where your NQ 1-minute CSV goes (see data/README.md)
```

## Quick start

```bash
cd jj-simon-replication
pip install -r requirements.txt
python -m pytest -q

# exercise the pipeline on synthetic bars (NOT market data; numbers are meaningless)
python -m fpt.cli synthetic --days 60 --out data/synthetic.csv
python -m fpt.cli backtest --csv data/synthetic.csv --min-body-atr 0.5

# real data: a 1-minute NQ CSV (Databento exports are UTC)
python -m fpt.cli backtest --csv data/NQ_1m.csv --source-tz UTC --report out/report.md --trades out/trades.csv

# the risk model
python -m fpt.cli sizing --atr 12.4            # tier, stop, contracts, risk, target
python -m fpt.cli edge --p 0.54 --rr 1.5 --trades-per-day 10 --risk 1000
python -m fpt.cli evaluation --firm topstep_100k --p 0.54 --rr 1.5

# the account operation
python -m fpt.cli firms
python -m fpt.cli portfolio --account topstep_100k:20 --account tradeify_100k_select:15 --account mffu_100k_starter:10 --months 6
python -m fpt.cli portfolio --account topstep_100k:10 --months 3 --scan-risk
```

## The rules as implemented (defaults)

| Component | Rule | Source class |
|---|---|---|
| Instrument | NQ, 1-minute bars, New York time, $20/point | JJ |
| Fair value | open of the 09:30 bar (the pre-open candle price); optional 14:00 anchor | JJ; codified by fxreplay, joetroyer, AndrewFXTD |
| Window | 09:30-11:00 | JJ |
| Continuation phase | first 5 minutes (JJ's own words; fxreplay says 10-15): trade away from fair value in the direction of the opening push | JJ / fxreplay |
| Reversion phase | rest of the window: trade back toward fair value | JJ |
| Trigger | break of structure (with the move) or market structure break (against the prior swing) confirmed by a displacement candle: counter-wick under 20% of open-to-extreme; grade A+ = structure break + displacement, A = displacement only, B = skip | JJ / fxreplay |
| Stop | 1-minute ATR above 20: 50 points, 1 contract; 7-20: 25 points, 2 contracts; below 7: 16.5 points, 3 contracts (about $1,000 risk) | fxreplay codification of JJ |
| Target | 1.5R, fixed, no management, no partials | JJ / fxreplay |
| Cadence | up to 10 trades per day, one position at a time, flat at 11:00 | JJ (10/day); assumption (one at a time) |
| Costs | 0.25-point slippage per side, $2.50 per contract per side | assumption |

Change any of it through `StrategyConfig` (see `fpt/strategy.py`) or the CLI flags.

## What the risk tools answer

* `edge`: expectancy per trade and per day, breakeven win rate, Kelly fraction of the drawdown allowance, expected and tail losing streaks, and the **statistical daily stop**: the loss at which today's result has fallen outside the 5th percentile of what the edge produces, which is the reconstruction of "knowing exactly when to stop trading".
* `evaluation`: for a firm preset, the probability of hitting the profit target before the drawdown as a function of fixed risk per trade: the "optimal risk" curve for passing evaluations.
* `portfolio`: the 20-45 account operation under copy trading: evaluation fees, resets, activation fees, breaches, passes, consistency rules, payout caps and cadence, with the distribution of net cash flow per month. `--scan-risk` repeats it across risk levels.
* `risk.risk_of_ruin`, `risk.losing_streak_quantiles`: sanity checks for a 54% / 1.5R edge at ten trades a day.

Firm presets in `fpt/propfirm.py` are templates; each carries `verified` and `source`. Confirm the numbers on the firm's site before trusting a simulation.

## Reproducing his numbers

1. Get real 1-minute NQ data (see `data/README.md`). Include the full session so the 09:29 candle exists.
2. Run the default backtest and compare with the public third-party backtests (fxreplay: 150-158 trades, 52-54% win rate, PF 1.66-1.76; the 365-day custom-indicator test: 289 trades, PF 1.7). Expect differences: those studies used different continuation windows and filters (see `docs/DOSSIER.md`).
3. Sweep the assumptions in `docs/ASSUMPTIONS.md` (`continuation_end`, `min_body_atr`, `allow_grade_a`, `require_band_touch`, `flat_at_window_end`) and look for parameter regions that are stable rather than a single best setting.
4. Feed the resulting trade R distribution into `portfolio` (`PortfolioConfig.bootstrap_r`) instead of the parametric 54% / 1.5R.
5. Paper trade the signals from `pine/fair_pricing_theory.pine` on TradingView, or wire `generate_trades` to a live 1-minute feed, before any funded account sees them.

## Running on the GB10

The toolkit is plain numpy/pandas; it needs no GPU. On the DGX Spark run it
in a venv as above. The one place local models help is the research side:
point a local LLM at the transcripts in `docs/research/` to extract rule
statements, then confirm against the dossier. `docs/REPLICATION_PLAN.md`
has the step-by-step plan.
