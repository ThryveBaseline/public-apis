# Trend exit for continuation: the pre-registered test

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

Implements docs/research/preregistration_trend_exit.md as registered in commit 66a400a (sha256 of the file read: 77816edcad0a40a265f095eba02202ae20f89b1c969cebda9839db60f1963e12, the pinned value). Development: New York days through 2025-10-05; benchmark from 2025-10-06. Family: stop k x the previous session's daily ATR, k in {0.2, 0.3, 0.4, 0.5, 0.7, 1}, no target, flat at 16:00; replayed on the 8647 entries the B2 replay covers (consistency: on the 37753 entry-variant pairs where B2's same-k bracket with a 2:1 target, k in 0.2 to 0.7, never filled its target, the two replays agree in R and exit time; k = 1.0 has no B2 counterpart).

Walk-forward k, chosen on earlier development years only: 2013: trend_0.5; 2014: trend_0.5; 2015: trend_1; 2016: trend_1; 2017: trend_1; 2018: trend_1; 2019: trend_0.3; 2020: trend_0.3; 2021: trend_0.3; 2022: trend_0.3; 2023: trend_0.5; 2024: trend_0.5; 2025: trend_0.3; benchmark: trend_0.3; before 2013 (the fourth development year), no trend trade. S3's chain for comparison: 2013: atr_0.4_rr2.00; 2014: atr_0.5_rr1.52; 2015: atr_0.4_rr1.52; 2016: atr_0.7_rr1.00; 2017: atr_0.5_rr1.52; 2018: atr_0.5_rr1.52; 2019: atr_0.3_rr2.00; 2020: atr_0.3_rr2.00; 2021: atr_0.4_rr2.00; 2022: atr_0.4_rr2.00; 2023: atr_0.4_rr2.00; 2024: atr_0.4_rr2.00; 2025: atr_0.4_rr2.00; benchmark: atr_0.4_rr2.00.

## The test

Paired difference per development continuation entry from 2013, trend-exit R minus S3's R: +0.0002 (standard error 0.0138, clustered by day), one-sided p 0.4929; trend exit +0.0471 R against S3 +0.0468 R on 2803 entries; positive in 7 of 13 chain years. **Fails** (registered rule: p < 0.05 and positive in at least 60% of chain years).

| year | mean difference |
|---|---|
| 2013 | -0.0106 |
| 2014 | -0.0405 |
| 2015 | +0.0369 |
| 2016 | +0.0352 |
| 2017 | +0.0036 |
| 2018 | -0.0577 |
| 2019 | +0.0076 |
| 2020 | +0.0444 |
| 2021 | -0.0127 |
| 2022 | -0.0562 |
| 2023 | -0.0062 |
| 2024 | +0.0147 |
| 2025 | +0.0534 |

## R per trade by direction, same entries (from 2013)

| outcome | period | long | short | both |
|---|---|---|---|---|
| trend exit (chain) | development | 1426, +0.070 (0.033) | 1377, +0.024 (0.033) | 2803, +0.047 (0.023) |
| trend exit (chain) | benchmark | 125, +0.226 (0.138) | 146, -0.001 (0.156) | 271, +0.104 (0.106) |
| S3 (chain) | development | 1426, +0.058 (0.028) | 1377, +0.036 (0.030) | 2803, +0.047 (0.021) |
| S3 (chain) | benchmark | 125, +0.180 (0.104) | 146, +0.026 (0.105) | 271, +0.097 (0.075) |
| S1 (sealed bracket) | development | 1426, +0.022 (0.030) | 1377, +0.005 (0.030) | 2803, +0.014 (0.021) |
| S1 (sealed bracket) | benchmark | 125, +0.099 (0.121) | 146, +0.123 (0.096) | 271, +0.112 (0.076) |

Exit mix of the trend exit: development 31.6% stopped, 68.4% flat at 16:00; benchmark 48.7% stopped, 51.3% flat at 16:00.

## Streams under the firm rules (B3 and B4), each on its own span

The exit failed its test; per the registration these are reported once for the record and dropped. Every stream takes its first trade in 2013, so each is scored on a calendar from 2013-01-01 (research/stream_report: on a wider calendar, evaluations started more than a horizon earlier see no trade and count as failures, and the later early ones replay the first days on a shortened window). S4 and S6 keep the reversion A+ entries of the same span.

### B3 summary: the frozen topstep_50k at the sealed sizing

| stream | period | span from | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S3 from 2013 | development | 2013-01-01 | 2677 | +0.048 | +129.5 | 31.8% | 2.4% | 62.9% | 3.2% | 552 | +61 | +13 |
| S3 from 2013 | benchmark | 2013-01-01 | 227 | +0.084 | +19.1 | 22.8% | 6.5% | 70.1% | 3.4% | 528 | +36 | -0 |
| S5 continuation, walk-forward trend exit | development | 2013-01-01 | 2677 | +0.049 | +132.4 | 24.0% | 2.3% | 60.1% | 3.5% | 512 | +25 | -19 |
| S5 continuation, walk-forward trend exit | benchmark | 2013-01-01 | 227 | +0.075 | +17.0 | 15.1% | 5.9% | 44.4% | 7.9% | 1,017 | +19 | -6 |
| S4 from 2013 | development | 2013-01-01 | 2927 | +0.049 | +144.9 | 31.5% | 2.4% | 61.2% | 3.1% | 599 | +66 | +18 |
| S4 from 2013 | benchmark | 2013-01-01 | 272 | +0.106 | +28.8 | 25.5% | 8.4% | 74.4% | 5.9% | 646 | +74 | +33 |
| S6 S5 + A+ reversion, from 2013 | development | 2013-01-01 | 2917 | +0.051 | +149.4 | 24.9% | 2.3% | 60.0% | 3.4% | 523 | +29 | -16 |
| S6 S5 + A+ reversion, from 2013 | benchmark | 2013-01-01 | 293 | +0.061 | +17.9 | 15.1% | 5.9% | 40.7% | 7.3% | 924 | +8 | -17 |

### Size sensitivity, topstep_50k_x

| stream | period | P(pass) at 1.00 / 0.98 / 0.95 | P(payout) at 1.00 / 0.98 / 0.95 | EV net of all fees at 1.00 / 0.98 / 0.95 |
|---|---|---|---|---|
| S3 from 2013 | development | 31.5% / 34.2% / 35.3% | 62.9% / 64.7% / 65.3% | +12 / +16 / +17 |
| S3 from 2013 | benchmark | 22.8% / 26.2% / 28.5% | 70.1% / 69.4% / 69.8% | -0 / +8 / +11 |
| S5 continuation, walk-forward trend exit | development | 23.7% / 24.4% / 24.5% | 60.1% / 61.7% / 62.8% | -20 / -19 / -20 |
| S5 continuation, walk-forward trend exit | benchmark | 15.1% / 16.9% / 16.9% | 44.4% / 50.7% / 52.0% | -6 / -1 / +0 |
| S4 from 2013 | development | 32.1% / 35.3% / 36.4% | 60.4% / 61.7% / 63.1% | +20 / +28 / +30 |
| S4 from 2013 | benchmark | 27.5% / 30.5% / 30.5% | 73.4% / 74.1% / 74.4% | +40 / +47 / +43 |
| S6 S5 + A+ reversion, from 2013 | development | 25.4% / 26.7% / 26.9% | 59.8% / 61.1% / 62.6% | -14 / -12 / -13 |
| S6 S5 + A+ reversion, from 2013 | benchmark | 12.4% / 13.3% / 13.3% | 40.4% / 45.0% / 44.7% | -25 / -21 / -22 |

### Whole micro contracts, topstep_50k_x

| stream | period | evaluation: trades, mean size | P(pass) | +/- | funded: trades, mean size | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees | P(bust) from $2,000 (frozen bootstrap) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S3 from 2013 | development | 2677, 0.92 | 35.3% | 2.7% | 2661, 0.85 | 69.1% | 3.3% | 459 | +63 | +8 | 0% |
| S3 from 2013 | benchmark | 227, 0.79 | 23.5% | 7.8% | 185, 0.75 | 72.1% | 10.5% | 369 | +13 | -30 | 3% |
| S5 continuation, walk-forward trend exit | development | 2677, 0.91 | 24.3% | 2.4% | 2655, 0.83 | 64.7% | 3.4% | 464 | +24 | -23 | 1% |
| S5 continuation, walk-forward trend exit | benchmark | 227, 0.86 | 16.7% | 6.4% | 223, 0.72 | 57.1% | 7.8% | 543 | +3 | -25 | 40% |
| S4 from 2013 | development | 2927, 0.92 | 36.4% | 2.6% | 2923, 0.85 | 65.4% | 3.2% | 501 | +70 | +14 | 0% |
| S4 from 2013 | benchmark | 272, 0.81 | 28.9% | 8.9% | 271, 0.80 | 71.8% | 5.4% | 540 | +63 | +15 | 0% |
| S6 S5 + A+ reversion, from 2013 | development | 2917, 0.91 | 26.2% | 2.5% | 2911, 0.84 | 63.6% | 3.5% | 480 | +31 | -18 | 1% |
| S6 S5 + A+ reversion, from 2013 | benchmark | 293, 0.88 | 13.0% | 4.0% | 300, 0.77 | 58.1% | 6.8% | 551 | -7 | -29 | 87% |

### Lifetime (B4): EV per evaluation with every payout and every fee

Payout policies: ask, ask whenever eligible (the frozen walk-forward's policy; gated); wait, wait until the loss limit has reached the starting balance (Topstep's advice). The first-payout gate is checked on the first policy.

topstep_50k_x at 1.00 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S3 from 2013 | development | ask | 31.5% | 97 | 62.9% | +191 | +264 | +293 | 62.9% | 99.9% |
| S3 from 2013 | development | wait | 31.5% | 97 | 62.9% | +208 | +295 | +340 | 47.7% | 99.9% |
| S3 from 2013 | benchmark | ask | 22.8% | 85 | 70.1% | +66 | +66 | +66 | 70.9% | 92.6% |
| S3 from 2013 | benchmark | wait | 22.8% | 85 | 70.1% | +42 | +42 | +42 | 31.5% | 95.2% |
| S5 continuation, walk-forward trend exit | development | ask | 23.7% | 93 | 60.1% | +87 | +146 | +173 | 61.6% | 100.0% |
| S5 continuation, walk-forward trend exit | development | wait | 23.7% | 93 | 60.1% | +93 | +171 | +217 | 48.3% | 100.0% |
| S5 continuation, walk-forward trend exit | benchmark | ask | 15.1% | 74 | 44.4% | +24 | +33 | +33 | 44.7% | 98.6% |
| S5 continuation, walk-forward trend exit | benchmark | wait | 15.1% | 74 | 44.4% | +18 | +28 | +28 | 30.3% | 99.5% |
| S4 from 2013 | development | ask | 32.1% | 98 | 60.4% | +202 | +264 | +270 | 60.5% | 99.9% |
| S4 from 2013 | development | wait | 32.1% | 98 | 60.4% | +219 | +303 | +310 | 45.5% | 100.0% |
| S4 from 2013 | benchmark | ask | 27.5% | 91 | 73.4% | +143 | +143 | +143 | 73.9% | 90.5% |
| S4 from 2013 | benchmark | wait | 27.5% | 91 | 73.4% | +225 | +238 | +238 | 58.2% | 92.9% |
| S6 S5 + A+ reversion, from 2013 | development | ask | 25.4% | 94 | 59.8% | +102 | +152 | +182 | 60.7% | 100.0% |
| S6 S5 + A+ reversion, from 2013 | development | wait | 25.4% | 94 | 59.8% | +112 | +187 | +237 | 48.4% | 100.0% |
| S6 S5 + A+ reversion, from 2013 | benchmark | ask | 12.4% | 69 | 40.4% | -5 | -5 | -5 | 40.5% | 95.1% |
| S6 S5 + A+ reversion, from 2013 | benchmark | wait | 12.4% | 69 | 40.4% | -11 | -11 | -11 | 27.2% | 95.2% |

topstep_50k_x at 0.95 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S3 from 2013 | development | ask | 35.3% | 104 | 65.3% | +211 | +288 | +319 | 65.4% | 100.0% |
| S3 from 2013 | development | wait | 35.3% | 104 | 65.3% | +237 | +346 | +388 | 50.0% | 100.0% |
| S3 from 2013 | benchmark | ask | 28.5% | 93 | 69.8% | +85 | +85 | +85 | 70.6% | 92.7% |
| S3 from 2013 | benchmark | wait | 28.5% | 93 | 69.8% | +53 | +53 | +53 | 29.1% | 95.9% |
| S5 continuation, walk-forward trend exit | development | ask | 24.5% | 96 | 62.8% | +86 | +144 | +170 | 64.4% | 100.0% |
| S5 continuation, walk-forward trend exit | development | wait | 24.5% | 96 | 62.8% | +90 | +169 | +214 | 48.7% | 100.0% |
| S5 continuation, walk-forward trend exit | benchmark | ask | 16.9% | 78 | 52.0% | +37 | +46 | +46 | 52.5% | 97.9% |
| S5 continuation, walk-forward trend exit | benchmark | wait | 16.9% | 78 | 52.0% | +28 | +40 | +40 | 32.0% | 99.3% |
| S4 from 2013 | development | ask | 36.4% | 105 | 63.1% | +233 | +299 | +306 | 63.1% | 99.9% |
| S4 from 2013 | development | wait | 36.4% | 105 | 63.1% | +257 | +354 | +363 | 47.3% | 100.0% |
| S4 from 2013 | benchmark | ask | 30.5% | 96 | 74.4% | +147 | +147 | +147 | 75.0% | 89.9% |
| S4 from 2013 | benchmark | wait | 30.5% | 96 | 74.4% | +249 | +268 | +268 | 59.9% | 91.6% |
| S6 S5 + A+ reversion, from 2013 | development | ask | 26.9% | 98 | 62.6% | +108 | +159 | +191 | 63.7% | 100.0% |
| S6 S5 + A+ reversion, from 2013 | development | wait | 26.9% | 98 | 62.6% | +119 | +199 | +251 | 49.4% | 100.0% |
| S6 S5 + A+ reversion, from 2013 | benchmark | ask | 13.3% | 71 | 44.7% | +7 | +7 | +7 | 44.8% | 95.9% |
| S6 S5 + A+ reversion, from 2013 | benchmark | wait | 13.3% | 71 | 44.7% | +3 | +3 | +3 | 30.9% | 96.2% |

topstep_50k at 1.00 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S3 from 2013 | development | ask | 31.8% | 98 | 62.9% | +193 | +267 | +296 | 62.9% | 99.9% |
| S3 from 2013 | development | wait | 31.8% | 98 | 62.9% | +210 | +298 | +343 | 47.7% | 99.9% |
| S3 from 2013 | benchmark | ask | 22.8% | 85 | 70.1% | +66 | +66 | +66 | 70.9% | 92.6% |
| S3 from 2013 | benchmark | wait | 22.8% | 85 | 70.1% | +42 | +42 | +42 | 31.5% | 95.2% |
| S5 continuation, walk-forward trend exit | development | ask | 24.0% | 93 | 60.1% | +89 | +148 | +175 | 61.6% | 100.0% |
| S5 continuation, walk-forward trend exit | development | wait | 24.0% | 93 | 60.1% | +95 | +174 | +220 | 48.3% | 100.0% |
| S5 continuation, walk-forward trend exit | benchmark | ask | 15.1% | 74 | 44.4% | +24 | +33 | +33 | 44.7% | 98.6% |
| S5 continuation, walk-forward trend exit | benchmark | wait | 15.1% | 74 | 44.4% | +18 | +28 | +28 | 30.3% | 99.5% |
| S4 from 2013 | development | ask | 31.5% | 97 | 61.2% | +202 | +261 | +265 | 61.2% | 99.9% |
| S4 from 2013 | development | wait | 31.5% | 97 | 61.2% | +222 | +302 | +309 | 46.3% | 100.0% |
| S4 from 2013 | benchmark | ask | 25.5% | 90 | 74.4% | +157 | +157 | +157 | 74.9% | 91.1% |
| S4 from 2013 | benchmark | wait | 25.5% | 90 | 74.4% | +226 | +238 | +238 | 58.5% | 93.6% |
| S6 S5 + A+ reversion, from 2013 | development | ask | 24.9% | 94 | 60.0% | +100 | +150 | +181 | 61.0% | 99.9% |
| S6 S5 + A+ reversion, from 2013 | development | wait | 24.9% | 94 | 60.0% | +111 | +187 | +237 | 48.6% | 100.0% |
| S6 S5 + A+ reversion, from 2013 | benchmark | ask | 15.1% | 74 | 40.7% | +15 | +15 | +15 | 40.8% | 95.7% |
| S6 S5 + A+ reversion, from 2013 | benchmark | wait | 15.1% | 74 | 40.7% | +11 | +11 | +11 | 29.5% | 96.0% |
