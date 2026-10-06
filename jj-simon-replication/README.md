# JJ Simon replication: Fair Pricing Theory, fixed-bracket risk, multi-account prop firm operation

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
  strategy.py   the rules: windows, continuation vs reversion, his displacement and swing definitions, A+/A grades, the 25/38 bracket, the room rule, session stops
  backtest.py   bar-by-bar backtest with slippage and commission; statistics tables
  risk.py       expectancy, Kelly, losing-streak quantiles, risk of ruin, statistical daily stop, optimal fixed risk
  propfirm.py   firm rule presets and a vectorised evaluation/funded/payout account simulator
  portfolio.py  N-account copy-trading Monte Carlo with fees, resets, breaches and payouts
  cli.py        command line
pine/           TradingView port of the signal logic
tests/          pytest suite
docs/           dossier, mechanism, bootstrap path, assumptions, replication plan, raw research
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
python -m fpt.cli edge --p 0.42 --rr 1.5 --trades-per-day 1.5 --risk 1000   # 0.42 = his own figure (the default); 0.54 = third-party variant, not transferable
python -m fpt.cli evaluation --firm topstep_100k --p 0.42 --rr 1.5

# the account operation
python -m fpt.cli firms
python -m fpt.cli portfolio --account topstep_100k:5 --account tradeify_100k_growth:5 --account mffu_100k_pro:3 --account lucid_100k_flex:5 --account alpha_100k_standard:5 --account apex_100k_intraday:20 --months 6
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
| Trigger | break of structure (with the move) or market structure break (against the prior swing) confirmed by a displacement candle: body larger than the previous candle's and a close beyond it (his definition; fxreplay's counter-wick-under-20% test is `displacement_mode="wick"`); grade A+ = structure break + displacement, A = displacement only, B = skip | JJ / fxreplay |
| Stop and size | 25-point stop, one NQ contract per $500 of risk; 50 points at half size on a wide opening candle; 50 / 75 on 150k accounts (fxreplay's ATR ladder 50 / 25 / 16.5 with 1 / 2 / 3 contracts is `stop_mode="atr_tier"`) | JJ (primary corpus) |
| Target | 38 points on the 25-point stop ("3825"), fixed, no management, no partials; break-even only at a new session open or before scheduled news; 100-point targets on funded accounts without a consistency rule | JJ (primary corpus) |
| Reversion room | only when fair value is at least 0.8 x the target away (at most 20% of the target beyond fair value) | JJ (primary corpus) |
| Stop trading | three consecutive losses end the session; no maximum when winning; an open position after 11:00 runs to its stop or target | JJ (primary corpus) |
| Cadence | up to 10 trades per day, one position at a time, flat at 11:00 | JJ (10/day); assumption (one at a time) |
| Costs | 0.25-point slippage per side, $2.50 per contract per side | assumption |

Change any of it through `StrategyConfig` (see `fpt/strategy.py`) or the CLI flags.

## Calibration: how many trades a day really carry the edge

JJ says "about 10 trades a day" (up to 20-30 in later videos). The
independent backtests of his written rules find far fewer qualifying
signals: fxreplay's study logged 150-158 trades, the 365-day
custom-indicator test 289 trades in a year (about 1.2 a day), both at
roughly 52-54% win rate and 1.5R. His own reported results agree with the
backtests, not with the headline cadence: "$105,700 in 3 weeks" across
about 40 accounts is 105,700 / (40 x 15) = $176 of payout per account per
day, about 0.18R at $1,000 risk. At 54% / 1.5R (the third-party figure; at
his own 42% a trade is worth 0.05R and the same payout would need about 3.5
trades a day) one trade is worth 0.35R, so that is what about 0.5
R-producing trades per account per day would yield if
payouts equalled P&L; payouts are net of splits, caps, breaches and
evaluation-phase accounts, so the gross cadence is higher but nowhere near
ten trades a day at 54%, which would be +3.5R (+$3,500) per account per day
and would blow through every prop firm's payout cap within a week.

The portfolio simulator defaults to **his operation**: round-robin routing of
about 20 signals a day across all accounts, one trade per account per day,
22 trading days a month, payouts after five winning days at 50% of profit.
The win rate is the assumption that decides everything and it is not
settled: `p_win` defaults to **0.42**, his own latest explicit figure at
1.5R; the 54% of the third-party fxreplay backtest belongs to a different
variant of the rules and cannot be transferred to this implementation. Run
`python -m fpt.cli scenarios` to see the 45-account operation across 40, 41,
42, 46, 50 and 54% (positive from about 46% up; about -$94k over six months
at 42%). Agreement between a simulated income and his reported income at any
win rate is a calibration target, not validation. The number that settles
it is measured, not assumed: `python -m fpt.cli evaluate --csv <nq_1min.csv>`
reports the pass probability of these rules on real data under each firm's
exact rules, in sample and on an untouched out-of-sample tail.

## What the risk tools answer

* `edge`: expectancy per trade and per day, breakeven win rate, Kelly fraction of the drawdown allowance, expected and tail losing streaks, and the **statistical daily stop**: the running loss at which today has fallen outside the 5th percentile of what the edge produces (the closing-P&L quantile is reported alongside), which is the reconstruction of "knowing exactly when to stop trading".
* `evaluation`: for a firm preset, the probability of hitting the profit target before the drawdown as a function of fixed risk per trade, under the preset's drawdown type, lock level and soft daily loss limit (consistency and minimum-day rules are not applied): the "optimal risk" curve for passing evaluations.
* `portfolio`: the 20-45 account operation under copy trading: evaluation fees, resets, activation fees, breaches, passes, consistency rules, payout caps and cadence, with the distribution of net cash flow per month. `--scan-risk` repeats it across risk levels.
* `risk.risk_of_ruin`, `risk.losing_streak_quantiles`: sanity checks for a given win rate, R and cadence (his own 42% / 1.5R by default; 54% is the third-party variant).
* `evaluate`: the primary measurement. On real 1-minute data it produces the R distribution by year, quarter, volatility regime, session and setup; the pass probability under each firm's exact rules by starting one evaluation on every trading day and following the real sequence; the funded payout probability and the days to payout; and the bootstrap survival tables rebuilt from the measured inputs. The last `--oos-months` are reported separately and never used for tuning.
* `scenarios`: the portfolio (and, with `--growth`, the bootstrap) across win rates, with 54% labelled as the third-party variant.
* `growth`: the bootstrap question. Start with a few hundred dollars, buy the cheapest evaluations on his S/A-tier ladder, reinvest every payout in new evaluations up to each firm's funded cap, and see how often the bankroll dies before the first payout, how long it takes to reach 5, 10 or 20 funded accounts, and when income can be taken. `--scan` repeats it across starting bankrolls and evaluation postures (his two-trade posture vs a fixed smaller risk). `--his-stats` prints his calculator exactly as he states it ($100 x 33% x 33% x $2,000 = $217.80 back, +$117.80 per evaluation, no split, one payout per funded account) and runs the same inputs as a state process in trading days (purchase, pass/fail after `--eval-days`, a qualifying period of `--qualifying-days`, payout); `--funded-mode repeat` is the separate lifetime model. Scans vary the pass rate and the payout rate independently. `docs/BOOTSTRAP.md` reads the results against his own statements about starting small; `docs/MECHANISM.md` explains, in his words, what each layer of the method is for. The pass and payout mechanics are the same `PropAccount` rules as `portfolio`; treat the payout dollars as an upper bound (see calibration) and the bust probability and time-to-funded as the robust outputs.

Firm presets in `fpt/propfirm.py` carry `verified` (True = the number comes from the firm's own help center; seven of twelve presets) and `source`; the rest are third-party placeholders. Evaluation and funded consistency rules are separate fields. Confirm every number on the firm's site before trusting a simulation.

## Reproducing his numbers

1. Get real 1-minute NQ data (see `data/README.md`). Include the full session so the 09:29 candle exists.
2. Run the default backtest and compare with the public third-party backtests (fxreplay: 150-158 trades, 52-54% win rate, PF 1.66-1.76; the 365-day custom-indicator test: 289 trades, PF 1.7). Expect differences: those studies used different continuation windows and filters (see `docs/DOSSIER.md`).
3. Sweep the assumptions in `docs/ASSUMPTIONS.md` (`continuation_end`, `min_body_atr`, `allow_grade_a`, `require_band_touch`, `flat_at_window_end`) and look for parameter regions that are stable rather than a single best setting.
4. Feed the resulting trade R distribution into `portfolio` (`PortfolioConfig.bootstrap_r`) instead of the parametric win rate (0.42 / 1.5R by default; 54% is the third-party variant).
5. Paper trade the signals from `pine/fair_pricing_theory.pine` on TradingView, or wire `generate_trades` to a live 1-minute feed, before any funded account sees them.

## Running on the GB10

The toolkit is plain numpy/pandas; it needs no GPU. On the DGX Spark run it
in a venv as above. The one place local models help is the research side:
point a local LLM at the transcripts in `docs/research/` to extract rule
statements, then confirm against the dossier. `docs/REPLICATION_PLAN.md`
has the step-by-step plan.
