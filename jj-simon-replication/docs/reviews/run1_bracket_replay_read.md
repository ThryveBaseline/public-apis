# B1 bracket replay: read (Claude, cloud session, 2026-10-07)

Source: `research/run1_bracket_replay.md` (sha256 4cb5479c…), produced on the GB10 at tool commit d093765 against the sealed ledger; numbers below are the development tables and walk-forward chains as transcribed by the Surface session, plus era splits computed from the chain rows. The benchmark year appears only where marked, as comparison.

**Gates.** Reproduction: replaying each trade's own sealed stop and target matches the ledger on all 7,656 stop or target exits before 16:00 (100.00%, largest R difference 0.0000). Population: 8,647 entries scored identically for every variant (121 roll-date trades excluded as sealed; 42 entries without a previous-session ATR or opening range dropped for all variants: 34 development, 8 benchmark). Left outside the reproduction check by design: 103 stop or target fills after 16:00 and 888 `session_end` trades (ledger mean R +0.179 when held into the evening, +0.153 flat at 16:00).

## 1. Scaling the bracket to volatility does not fix the portfolio

Development, all 7,397 entries, selected rows:

| bracket | median stop (pts) | win rate | expectancy R | profit factor | ambiguous bars |
|---|---|---|---|---|---|
| sealed (control, flat 16:00) | 25 | 40.3% | −0.041 | 0.93 | 2 |
| fixed 25/38 on every entry | 25 | 40.1% | −0.047 | 0.92 | 3 |
| 0.03 × daily ATR, RR 1.52 | 7 | 34.9% | −0.211 | 0.71 | 352 |
| 0.10 × daily ATR, RR 1.52 | 24.5 | 37.7% | −0.084 | 0.87 | 1 |
| 0.30 × daily ATR, RR 1.52 | 73 | 42.1% | −0.021 | 0.96 | 0 |
| 0.30 × daily ATR, RR 2.0 | 73 | 39.5% | −0.019 | 0.96 | 0 |
| 1.5 × previous opening range, RR 1.52 | 59.5 | 41.2% | −0.021 | 0.96 | 0 |
| 0.30% of price, RR 1.52 | 37 | 38.7% | −0.061 | 0.90 | 0 |

Every family improves monotonically as the stop widens, and none crosses zero. Tight scaled stops are much worse than 25 points: inside the one-minute noise, many bars contain both levels and are resolved as stops.

## 2. The out-of-year chain picks the widest bracket every year, and its gain is one era

The sequential chain (each year, the variant best on all earlier development years, scored on that year only) chose `atr_0.3_rr2.00` in every year from 2013 to 2025: the largest stop and the largest reward-to-risk in the grid, so the grid did not bracket the optimum.

| era | chain expectancy R | sealed bracket | difference | years better | trades |
|---|---|---|---|---|---|
| 2013-2017 | +0.007 | +0.008 | −0.001 | 2/5 | 1,136 |
| 2018-2021 | −0.004 | −0.077 | +0.073 | 4/4 | 2,266 |
| 2022-2025 (to Oct 5) | −0.044 | −0.041 | −0.003 | 2/4 | 3,519 |
| 2013-2025 | −0.022 | −0.045 | +0.022 | 8/13 | 6,921 |

47% of the total gain comes from 2021 alone. In the era closest to today's prices, 2022-2025, the wide bracket is no better than the sealed one.

## 3. By setup: a modest continuation lever, no reversion lever

| chain (all families) | out-of-year expectancy R | sealed bracket |
|---|---|---|
| continuation | +0.043 | +0.014 |
| reversion | −0.073 | −0.084 |

Continuation under the widest ATR bracket gains about +0.03 R per trade out of year, +0.011 in 2022-2025; the paired difference is roughly one and a half standard errors and was chosen at the edge of a 34-variant grid, so it is weak evidence. Reversion stays negative under every family: the best reversion development row is −0.051 R (1.5 × previous opening range) against −0.084 sealed, and under the widest bracket reversion is worse than sealed in 2022-2025 (−0.076 against −0.068, inferred from the chains).

Benchmark, comparison only (Surface session's flag): continuation under the chosen bracket is +0.073 against +0.112 for the sealed bracket, with a median stop of 147.5 points and a mean hold of 186 bars against 7. The development preference does not show up in the inspected year.

## What this settles

* **The fixed-point bracket is not the main reason the baseline loses.** The anatomy's geometry drift is real (a 25-point stop went from 72% to 5% of the daily range), but restoring the old ratio by scaling the bracket does not restore the old results; the edge did not scale with the bracket.
* **Reversion's losses are not a stop-placement problem.** This converges with his own words (`docs/research/synthesis/reversion_rules.md`): on every prop account his reversion stop is a static 25 points. What he does differently is selectivity and targets: the move-away gate, break-of-structure entries on funded accounts, three or four attempts a session, and a target matched to the room to fair value. That is B2, and it is now the main test.
* **Continuation may like a wide stop.** This matches his funded continuation ("give myself the largest possible stop-loss", KHEQ5g55dQ4 ~16:27), but the evidence is weak and not visible in the latest year. It stays a candidate, not a finding.

## Pre-registered next for geometry (B1b, cheap, same tool)

Because the chain chose the edge, the grid is extended once, before looking at any result: stop = 0.4, 0.5 and 0.7 × daily ATR (the 2010-2016 ratio was 0.4-0.7) at RR 1.0, 1.52 and 2.0, plus a direction-to-close control with no stop or target, flat at 16:00, R measured in 25-point units. The control measures how much directional content the entry signal carries over the rest of the day, independent of any bracket. Same reproduction gate, same walk-forward, same rule that the benchmark is never selected on.

## Addendum after reading the full report (same day)

* **The reversion chain is not evidence of anything.** Reversion trades per development year are 1, 11, 2, 3, 23, 50, 51 and 27 for 2010 to 2017, then 146 to 848 from 2018. The chain's selection rule averages the earlier years' expectancies without weighting them by trades, so a single 2010 trade at +1.98 R steers the early choices (the chosen reversion bracket changes three times). Its out-of-year −0.073 against −0.084 should not be read as an improvement. The pooled development table carries the reversion conclusion: all 34 brackets negative, best −0.051.
* **The same flaw inflates the "mean" column** of the per-year matrices for reversion (for example +0.111 for the widest ATR bracket, from that one 2010 trade). For all setups and for continuation, early years hold 80 to 190 trades each and the chain is not distorted in the same way.
* **Reversion barely exists in this ledger before 2018.** The room rule needs 30.4 points between the signal close and fair value; at 2010-2016 prices and ranges that was rare. The development-era strength is almost entirely continuation, so the pre-2018 data says little about reversion either way.
* **Fix, applied to the B2 run, not to this file:** the chain selects on the pooled, trade-weighted expectancy of all earlier development years, and the per-year matrices show a pooled mean beside the yearly values. The B1 output stays exactly as run.

