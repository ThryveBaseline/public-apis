# run1 second read: Claude (cloud session), 2026-10-06, from the full sealed report

Written from `sealed/run1/report.md` (sha256 884fe702…) after the push, before reading any other reviewer. The first read stands unchanged in `run1_claude_cloud_first_read.md`; this file adds what the full tables show. Reminder: the 2025-10-06 to 2026-10-05 year is the inspected Baseline 0 benchmark; everything below that uses it is description, not selection. Candidate choices are made on development data.

## 1. The split that matters: continuation carries edge, reversion taxes it

| period | setup | trades | win rate | expectancy R | profit factor | trades/day |
|---|---|---|---|---|---|---|
| development | continuation | 3,281 | 44.1% | +0.020 | 1.04 | 0.69 |
| development | reversion | 4,150 | 37.2% | −0.082 | 0.87 | 0.87 |
| benchmark | continuation | 272 | 44.9% | +0.114 | 1.20 | 0.87 |
| benchmark | reversion | 986 | 35.5% | −0.122 | 0.81 | 3.15 |

Continuation is non-negative in both halves; reversion is negative in both halves, and in the benchmark year it is 78% of all trades at 3.15 a day. The combined −0.071 R is mostly the reversion leg. Standard errors: development continuation about ±0.02 R (so "around zero to slightly positive"), benchmark continuation about ±0.07 R (so "positive, loosely"). Grade tells the same story: A+ (first close through a live swing) is at breakeven in both halves (+0.014, +0.016); A is negative in both (−0.068, −0.111).

Reading: the reversion leg over-triggers. Three reversion entries a day in the opening 90 minutes is not how he describes trading it (one or two trades a session, often one per account). That makes the reversion leg the most likely home of the interpretation gap (class C) rather than evidence that reversion "does not work".

## 2. The geometry drift is real and large

| years | win rate | expectancy R | trades/day | Topstep 50K pass rate (start year) |
|---|---|---|---|---|
| 2010-2016 | 43-52% | −0.02 to +0.06 | 0.6-0.8 | 11-39% |
| 2017-2019 | 39-44% | −0.03 to −0.05 | 0.7-1.3 | 20-26% |
| 2020-2025 | 34-40% | −0.01 to −0.17 | 2.4-3.6 | 5-15% |
| benchmark 2025-26 | 37.5% | −0.071 | 4.0 | 8.7% |

NQ went from about 2,000 to above 30,000 over the sample while the bracket stayed at 25 and 38 points. Early on, 25 points was more than a percent of price, so the rules fired rarely and the fixed target was hard to reach but the stop was rarely hit by noise; now 25 points is under a tenth of a percent, the rules fire four times a day, and most of those are noise. The evaluation pass rate decays with price level in the same way: his 33% assumption matches what this reconstruction produced at 2011-2016 price levels, not today's. This is the strongest support yet for the bracket-normalization hypothesis, and it says the direction to test is "make today's bracket relatively larger", not smaller.

## 3. A methodological defect in the regime split

The volatility terciles are fitted on development days in points. Because points scale with price, the benchmark year lands almost entirely in "high" (1,252 of 1,258 trades), which makes the regime table uninformative out of sample and confounds regime with era in sample. Research-phase regime labels must be price-relative (ATR as a share of price, or a rolling percentile), fitted on development days. The anatomy tool is being extended to carry a relative regime beside the point-based one.

## 4. What the firm tables add

* Development-era pass rates were materially higher (Topstep 50K 20.1% ± 1.8%, payout before breach 45.8%), and the development bootstrap is marginally positive (EV +$8 per evaluation; $2,000 bankroll busts 27% of the time in 12 months, median 18 funded accounts by month 12). That is the era-dependence again, not evidence for today.
* Benchmark bootstrap: EV −$28 per evaluation, bust probability 100% at every bankroll up to $5,000. This is the number that would have to move before any real-money pilot.
* Tradeify growth passes fastest (median 2 days, 27.7%) but pays out least (5.2%): its evaluation is easy to attack with two-trade sizing and its funded stage is not. Firm choice is a lever for the evaluation stage only.

## 5. Quarterly noise

Benchmark quarters swing from −0.14 R to +0.04 R with about 300 trades each; a quarter's standard error is roughly 0.07 R, so no quarter is distinguishable from the year. Development quarters show the same dispersion (2017Q1 −0.25, 2017Q4 +0.06). Nothing should be selected at quarter granularity.

## Revised answers to the four questions

**What is wrong.** Added to the first read: the point-based regime classifier (fix in research tooling, not in the frozen code); and the trade count itself as evidence that the reversion leg is read too loosely.

**Justified.** Continuation as implemented is at or slightly above breakeven in development and positive in the benchmark; reversion as implemented is negative everywhere and dominates the trade count; the fixed bracket's meaning drifted by more than an order of magnitude across the sample; the evaluation economics at today's price level are negative.

**Not justified.** That reversion, as he trades it, loses: the implemented leg fires three times a day, which is not his cadence. That the development-era pass rates (20-39%) mean anything for today. Any quarter-level read.

**Test next, in this order on development data with walk-forward.**
1. Anatomy by year and setup, by setup and grade, by setup and entry time, with excursions and the geometry table (tool ready, run on the GB10).
2. B1: bracket normalization (ATR multiple, price percentage, opening-range multiple), judged on continuation and reversion separately, with the trades-per-day drift as a diagnostic.
3. B2: reversion tightened toward his cadence (A+ only, distance-from-fair-value minimum, one reversion per session, band touch required) as pre-registered variants, classified C.
4. B3: continuation-only and continuation-plus-conditioned-reversion as portfolios, then the evaluation and funded policy per firm.
5. Only then the other sessions and the broader signal stack.

**The target restated.** Continuation alone is about +0.02 R in development; the goal of +0.05 to +0.15 R per trade is within the range the setup split and geometry fix could plausibly deliver without inventing anything he does not already do.
