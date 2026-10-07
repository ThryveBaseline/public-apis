# H3 through firm scoring: continuation after a large opening candle

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

H3 as registered in commit c0c7a15 and clarified in 26cb07a (sha256 of the file read: d32040ce4f453e52cfcefba92ceb9012d2121522c414fdc8f5a9548a2d5399a3, the pinned value), at the registered cut: development through 2025-10-05, benchmark from 2025-10-06. On these inputs its registered test gives a development difference of +0.101 R (standard error 0.039), Holm p 0.0468 across the nine, positive in 11 of 15 years: it **passes**. Each stream is shown on the continuation entries where H3 is defined (the comparator) and on H3's favoured side only; S4's reversion A+ entries are the same in both, and the filter is applied before the sequential pass. H3 is first defined in 2011, so both sides of every pair are scored on a calendar from 2011-01-01.

### B3 summary: the frozen topstep_50k at the sealed sizing

| stream | period | span from | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 where H3 is defined | development | 2011-01-01 | 3161 | +0.013 | +40.8 | 30.0% | 1.9% | 54.1% | 3.1% | 551 | +41 | -7 |
| S1 where H3 is defined | benchmark | 2011-01-01 | 271 | +0.112 | +30.2 | 25.6% | 5.5% | 63.6% | 10.2% | 803 | +82 | +43 |
| S1 on H3's favoured side | development | 2011-01-01 | 1887 | +0.053 | +100.8 | 28.4% | 2.3% | 61.5% | 3.6% | 562 | +49 | -2 |
| S1 on H3's favoured side | benchmark | 2011-01-01 | 172 | +0.053 | +9.2 | 25.2% | 6.3% | 62.8% | 13.9% | 772 | +73 | +35 |
| S3 where H3 is defined | development | 2011-01-01 | 3035 | +0.043 | +131.7 | 29.8% | 2.2% | 63.3% | 3.0% | 513 | +48 | +1 |
| S3 where H3 is defined | benchmark | 2011-01-01 | 227 | +0.084 | +19.1 | 22.8% | 6.5% | 70.1% | 3.4% | 528 | +36 | -0 |
| S3 on H3's favoured side | development | 2011-01-01 | 1814 | +0.088 | +159.4 | 29.8% | 2.5% | 67.0% | 3.6% | 673 | +85 | +31 |
| S3 on H3's favoured side | benchmark | 2011-01-01 | 152 | +0.124 | +18.8 | 23.2% | 7.1% | 73.1% | 11.2% | 437 | +25 | -17 |
| S4 where H3 is defined | development | 2011-01-01 | 3285 | +0.045 | +147.0 | 29.5% | 2.2% | 61.8% | 2.9% | 545 | +50 | +4 |
| S4 where H3 is defined | benchmark | 2011-01-01 | 272 | +0.106 | +28.8 | 25.5% | 8.4% | 74.4% | 5.9% | 646 | +74 | +33 |
| S4 on H3's favoured side | development | 2011-01-01 | 2295 | +0.068 | +156.4 | 31.1% | 2.4% | 62.2% | 3.5% | 698 | +86 | +32 |
| S4 on H3's favoured side | benchmark | 2011-01-01 | 246 | +0.119 | +29.2 | 30.5% | 8.1% | 60.6% | 8.2% | 733 | +86 | +39 |

### Size sensitivity, topstep_50k_x

| stream | period | P(pass) at 1.00 / 0.98 / 0.95 | P(payout) at 1.00 / 0.98 / 0.95 | EV net of all fees at 1.00 / 0.98 / 0.95 |
|---|---|---|---|---|
| S1 where H3 is defined | development | 28.7% / 31.2% / 30.9% | 54.1% / 57.3% / 58.5% | -9 / -2 / -4 |
| S1 where H3 is defined | benchmark | 26.5% / 36.5% / 38.9% | 63.6% / 65.6% / 66.6% | +46 / +83 / +82 |
| S1 on H3's favoured side | development | 26.9% / 28.0% / 27.6% | 61.5% / 64.6% / 65.9% | -4 / -5 / -7 |
| S1 on H3's favoured side | benchmark | 26.2% / 34.1% / 34.1% | 62.8% / 66.8% / 67.1% | +38 / +68 / +63 |
| S3 where H3 is defined | development | 29.5% / 32.0% / 32.9% | 63.3% / 65.0% / 65.6% | +0 / +2 / +3 |
| S3 where H3 is defined | benchmark | 22.8% / 26.2% / 28.5% | 70.1% / 69.4% / 69.8% | -0 / +8 / +11 |
| S3 on H3's favoured side | development | 29.6% / 30.9% / 31.3% | 67.0% / 68.0% / 68.7% | +30 / +29 / +28 |
| S3 on H3's favoured side | benchmark | 23.2% / 24.5% / 24.5% | 73.1% / 73.1% / 72.4% | -17 / -17 / -21 |
| S4 where H3 is defined | development | 30.0% / 32.9% / 33.8% | 61.2% / 62.4% / 63.6% | +5 / +11 / +11 |
| S4 where H3 is defined | benchmark | 27.5% / 30.5% / 30.5% | 73.4% / 74.1% / 74.4% | +40 / +47 / +43 |
| S4 on H3's favoured side | development | 30.6% / 32.5% / 32.8% | 62.3% / 63.8% / 64.6% | +30 / +31 / +27 |
| S4 on H3's favoured side | benchmark | 27.8% / 31.8% / 31.8% | 62.6% / 66.6% / 69.2% | +40 / +54 / +51 |

### Whole micro contracts, topstep_50k_x

| stream | period | evaluation: trades, mean size | P(pass) | +/- | funded: trades, mean size | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees | P(bust) from $2,000 (frozen bootstrap) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 where H3 is defined | development | 3161, 0.95 | 30.9% | 2.1% | 3161, 0.89 | 59.6% | 3.2% | 484 | +40 | -10 | 0% |
| S1 where H3 is defined | benchmark | 271, 0.93 | 36.5% | 7.8% | 271, 0.85 | 70.9% | 10.9% | 660 | +122 | +65 | 0% |
| S1 on H3's favoured side | development | 1887, 0.94 | 27.6% | 2.4% | 1887, 0.89 | 66.2% | 3.5% | 496 | +42 | -12 | 0% |
| S1 on H3's favoured side | benchmark | 172, 0.91 | 34.1% | 8.5% | 172, 0.83 | 70.1% | 14.2% | 524 | +76 | +23 | 0% |
| S3 where H3 is defined | development | 3035, 0.92 | 32.9% | 2.5% | 3019, 0.86 | 68.8% | 3.0% | 428 | +48 | -5 | 0% |
| S3 where H3 is defined | benchmark | 227, 0.79 | 23.5% | 7.8% | 185, 0.75 | 72.1% | 10.5% | 369 | +13 | -30 | 3% |
| S3 on H3's favoured side | development | 1814, 0.92 | 31.8% | 2.6% | 1809, 0.86 | 71.5% | 3.6% | 556 | +77 | +16 | 0% |
| S3 on H3's favoured side | benchmark | 152, 0.79 | 19.9% | 7.9% | 130, 0.74 | 67.1% | 12.4% | 355 | -2 | -46 | 29% |
| S4 where H3 is defined | development | 3285, 0.92 | 33.8% | 2.4% | 3281, 0.86 | 65.7% | 2.9% | 461 | +53 | -1 | 0% |
| S4 where H3 is defined | benchmark | 272, 0.81 | 28.9% | 8.9% | 271, 0.80 | 71.8% | 5.4% | 540 | +63 | +15 | 0% |
| S4 on H3's favoured side | development | 2295, 0.93 | 32.4% | 2.6% | 2290, 0.87 | 66.4% | 3.5% | 579 | +76 | +18 | 0% |
| S4 on H3's favoured side | benchmark | 246, 0.85 | 35.8% | 8.2% | 248, 0.81 | 70.9% | 7.3% | 547 | +90 | +34 | 0% |

### Lifetime (B4): EV per evaluation with every payout and every fee

Payout policies: ask, ask whenever eligible (the frozen walk-forward's policy; gated); wait, wait until the loss limit has reached the starting balance (Topstep's advice). The first-payout gate is checked on the first policy.

topstep_50k_x at 1.00 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 where H3 is defined | development | ask | 28.7% | 95 | 54.1% | +120 | +141 | +142 | 54.7% | 99.9% |
| S1 where H3 is defined | development | wait | 28.7% | 95 | 54.1% | +123 | +160 | +165 | 37.2% | 100.0% |
| S1 where H3 is defined | benchmark | ask | 26.5% | 89 | 63.6% | +232 | +299 | +299 | 63.6% | 100.0% |
| S1 where H3 is defined | benchmark | wait | 26.5% | 89 | 63.6% | +274 | +375 | +375 | 55.1% | 100.0% |
| S1 on H3's favoured side | development | ask | 26.9% | 97 | 61.5% | +87 | +159 | +180 | 63.5% | 100.0% |
| S1 on H3's favoured side | development | wait | 26.9% | 97 | 61.5% | +72 | +185 | +246 | 52.0% | 97.7% |
| S1 on H3's favoured side | benchmark | ask | 26.2% | 89 | 62.8% | +132 | +162 | +162 | 64.7% | 100.0% |
| S1 on H3's favoured side | benchmark | wait | 26.2% | 89 | 62.8% | +131 | +208 | +208 | 55.5% | 100.0% |
| S3 where H3 is defined | development | ask | 29.5% | 96 | 63.3% | +158 | +219 | +243 | 63.8% | 100.0% |
| S3 where H3 is defined | development | wait | 29.5% | 96 | 63.3% | +167 | +240 | +276 | 44.0% | 100.0% |
| S3 where H3 is defined | benchmark | ask | 22.8% | 85 | 70.1% | +66 | +66 | +66 | 70.9% | 92.6% |
| S3 where H3 is defined | benchmark | wait | 22.8% | 85 | 70.1% | +42 | +42 | +42 | 31.5% | 95.2% |
| S3 on H3's favoured side | development | ask | 29.6% | 103 | 67.0% | +131 | +269 | +323 | 68.9% | 99.9% |
| S3 on H3's favoured side | development | wait | 29.6% | 103 | 67.0% | +127 | +316 | +422 | 61.1% | 97.4% |
| S3 on H3's favoured side | benchmark | ask | 23.2% | 91 | 73.1% | +82 | +107 | +107 | 72.0% | 94.4% |
| S3 on H3's favoured side | benchmark | wait | 23.2% | 91 | 73.1% | +63 | +111 | +111 | 44.2% | 87.4% |
| S4 where H3 is defined | development | ask | 30.0% | 96 | 61.2% | +167 | +219 | +224 | 61.7% | 99.9% |
| S4 where H3 is defined | development | wait | 30.0% | 96 | 61.2% | +176 | +247 | +252 | 42.0% | 100.0% |
| S4 where H3 is defined | benchmark | ask | 27.5% | 91 | 73.4% | +143 | +143 | +143 | 73.9% | 90.5% |
| S4 where H3 is defined | benchmark | wait | 27.5% | 91 | 73.4% | +225 | +238 | +238 | 58.2% | 92.9% |
| S4 on H3's favoured side | development | ask | 30.6% | 102 | 62.3% | +162 | +287 | +324 | 64.1% | 100.0% |
| S4 on H3's favoured side | development | wait | 30.6% | 102 | 62.3% | +148 | +322 | +411 | 53.9% | 97.8% |
| S4 on H3's favoured side | benchmark | ask | 27.8% | 92 | 62.6% | +170 | +173 | +173 | 63.3% | 90.4% |
| S4 on H3's favoured side | benchmark | wait | 27.8% | 92 | 62.6% | +176 | +186 | +186 | 54.0% | 90.8% |

topstep_50k_x at 0.95 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 where H3 is defined | development | ask | 30.9% | 99 | 58.5% | +134 | +159 | +159 | 59.2% | 99.9% |
| S1 where H3 is defined | development | wait | 30.9% | 99 | 58.5% | +147 | +191 | +197 | 41.4% | 100.0% |
| S1 where H3 is defined | benchmark | ask | 38.9% | 109 | 66.6% | +348 | +441 | +441 | 66.7% | 100.0% |
| S1 where H3 is defined | benchmark | wait | 38.9% | 109 | 66.6% | +454 | +693 | +707 | 61.9% | 100.0% |
| S1 on H3's favoured side | development | ask | 27.6% | 102 | 65.9% | +87 | +161 | +183 | 68.5% | 100.0% |
| S1 on H3's favoured side | development | wait | 27.6% | 102 | 65.9% | +69 | +196 | +270 | 56.4% | 97.1% |
| S1 on H3's favoured side | benchmark | ask | 34.1% | 102 | 67.1% | +199 | +236 | +236 | 69.1% | 100.0% |
| S1 on H3's favoured side | benchmark | wait | 34.1% | 102 | 67.1% | +188 | +284 | +284 | 58.9% | 100.0% |
| S3 where H3 is defined | development | ask | 32.9% | 102 | 65.6% | +174 | +238 | +263 | 66.1% | 100.0% |
| S3 where H3 is defined | development | wait | 32.9% | 102 | 65.6% | +191 | +281 | +315 | 46.4% | 100.0% |
| S3 where H3 is defined | benchmark | ask | 28.5% | 93 | 69.8% | +85 | +85 | +85 | 70.6% | 92.7% |
| S3 where H3 is defined | benchmark | wait | 28.5% | 93 | 69.8% | +53 | +53 | +53 | 29.1% | 95.9% |
| S3 on H3's favoured side | development | ask | 31.3% | 109 | 68.7% | +127 | +271 | +335 | 70.7% | 99.9% |
| S3 on H3's favoured side | development | wait | 31.3% | 109 | 68.7% | +122 | +326 | +438 | 62.2% | 96.5% |
| S3 on H3's favoured side | benchmark | ask | 24.5% | 94 | 72.4% | +80 | +106 | +106 | 72.2% | 94.8% |
| S3 on H3's favoured side | benchmark | wait | 24.5% | 94 | 72.4% | +57 | +109 | +109 | 43.4% | 86.1% |
| S4 where H3 is defined | development | ask | 33.8% | 103 | 63.6% | +192 | +247 | +252 | 64.2% | 100.0% |
| S4 where H3 is defined | development | wait | 33.8% | 103 | 63.6% | +206 | +287 | +295 | 44.1% | 100.0% |
| S4 where H3 is defined | benchmark | ask | 30.5% | 96 | 74.4% | +147 | +147 | +147 | 75.0% | 89.9% |
| S4 where H3 is defined | benchmark | wait | 30.5% | 96 | 74.4% | +249 | +268 | +268 | 59.9% | 91.6% |
| S4 on H3's favoured side | development | ask | 32.8% | 107 | 64.6% | +171 | +311 | +354 | 66.3% | 100.0% |
| S4 on H3's favoured side | development | wait | 32.8% | 107 | 64.6% | +152 | +341 | +435 | 54.9% | 97.1% |
| S4 on H3's favoured side | benchmark | ask | 31.8% | 98 | 69.2% | +198 | +202 | +202 | 70.2% | 91.2% |
| S4 on H3's favoured side | benchmark | wait | 31.8% | 98 | 69.2% | +218 | +230 | +230 | 61.5% | 91.8% |

topstep_50k at 1.00 of the budget:

| stream | period | policy | P(pass) | fees per evaluation | B3 P(payout) | EV, H 60 | EV, H 120 | EV, H 250 | P(any payout by 250) | P(breach by 250) |
|---|---|---|---|---|---|---|---|---|---|---|
| S1 where H3 is defined | development | ask | 30.0% | 97 | 54.1% | +127 | +150 | +150 | 54.7% | 99.9% |
| S1 where H3 is defined | development | wait | 30.0% | 97 | 54.1% | +131 | +171 | +176 | 37.2% | 100.0% |
| S1 where H3 is defined | benchmark | ask | 25.6% | 88 | 63.6% | +222 | +287 | +287 | 63.6% | 100.0% |
| S1 where H3 is defined | benchmark | wait | 25.6% | 88 | 63.6% | +263 | +361 | +361 | 55.1% | 100.0% |
| S1 on H3's favoured side | development | ask | 28.4% | 100 | 61.5% | +95 | +171 | +193 | 63.5% | 100.0% |
| S1 on H3's favoured side | development | wait | 28.4% | 100 | 61.5% | +80 | +198 | +263 | 52.1% | 97.7% |
| S1 on H3's favoured side | benchmark | ask | 25.2% | 88 | 62.8% | +125 | +153 | +153 | 64.7% | 100.0% |
| S1 on H3's favoured side | benchmark | wait | 25.2% | 88 | 62.8% | +124 | +198 | +198 | 55.5% | 100.0% |
| S3 where H3 is defined | development | ask | 29.8% | 96 | 63.3% | +160 | +221 | +245 | 63.8% | 100.0% |
| S3 where H3 is defined | development | wait | 29.8% | 96 | 63.3% | +169 | +243 | +279 | 44.0% | 100.0% |
| S3 where H3 is defined | benchmark | ask | 22.8% | 85 | 70.1% | +66 | +66 | +66 | 70.9% | 92.6% |
| S3 where H3 is defined | benchmark | wait | 22.8% | 85 | 70.1% | +42 | +42 | +42 | 31.5% | 95.2% |
| S3 on H3's favoured side | development | ask | 29.8% | 104 | 67.0% | +131 | +270 | +324 | 68.9% | 99.9% |
| S3 on H3's favoured side | development | wait | 29.8% | 104 | 67.0% | +128 | +318 | +424 | 61.1% | 97.4% |
| S3 on H3's favoured side | benchmark | ask | 23.2% | 91 | 73.1% | +82 | +107 | +107 | 72.0% | 94.4% |
| S3 on H3's favoured side | benchmark | wait | 23.2% | 91 | 73.1% | +63 | +111 | +111 | 44.2% | 87.4% |
| S4 where H3 is defined | development | ask | 29.5% | 96 | 61.8% | +167 | +217 | +220 | 62.3% | 99.9% |
| S4 where H3 is defined | development | wait | 29.5% | 96 | 61.8% | +178 | +246 | +251 | 42.7% | 100.0% |
| S4 where H3 is defined | benchmark | ask | 25.5% | 90 | 74.4% | +157 | +157 | +157 | 74.9% | 91.1% |
| S4 where H3 is defined | benchmark | wait | 25.5% | 90 | 74.4% | +226 | +238 | +238 | 58.5% | 93.6% |
| S4 on H3's favoured side | development | ask | 31.1% | 103 | 62.2% | +168 | +289 | +322 | 63.9% | 100.0% |
| S4 on H3's favoured side | development | wait | 31.1% | 103 | 62.2% | +152 | +315 | +404 | 53.8% | 97.8% |
| S4 on H3's favoured side | benchmark | ask | 30.5% | 96 | 60.6% | +155 | +158 | +158 | 61.3% | 89.8% |
| S4 on H3's favoured side | benchmark | wait | 30.5% | 96 | 60.6% | +143 | +144 | +144 | 52.0% | 89.8% |
