# Conditional edge: the pre-registered tests (research step 4)

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades and the bar file have the manifest's sha256. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time). Entries: 8647 replayed, of which 3536 continuation and 992 reversion A+; 142 sit on a session holding a contract switch (or opening a contract the previous session did not trade), where gap, the prior-session comparison and the overnight range are undefined (clarification 1).

Implements docs/research/preregistration_conditional_edge.md as registered in commit c0c7a15 and clarified in 26cb07a, both before any run on real data (sha256 of the file read: d32040ce4f453e52cfcefba92ceb9012d2121522c414fdc8f5a9548a2d5399a3, the pinned value). Development: New York days through 2025-10-05; benchmark: from 2025-10-06. Outcome: R of the sealed bracket replayed, flat at 16:00. Each test is the development difference in mean R, favoured minus other side, with day-clustered standard errors combined across the two sides as registered, a one-sided normal p-value and Holm's step-down across all nine at 0.05; a condition passes only if Holm-significant and positive in at least 60% of the development years with at least 10 trades on each side. The benchmark year is reported beside and never used. Days with both sides counts the development days on which both sides trade, where the registered standard error ignores their covariance.

## Tests

| id | population | condition (favoured side) | development: favoured n, R | other n, R | difference (se) | p | Holm p | years positive | days with both sides | passes | benchmark: favoured n, R | other n, R | difference (se) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | continuation | trend (with the 20-session trend) | 1604, +0.030 | 1655, -0.007 | +0.037 (0.038) | 0.1630 | 1.0000 | 10 of 16 | 0 | no | 128, +0.067 | 143, +0.151 | -0.084 (0.151) |
| H2 | continuation | overnight move (continuing the overnight move) | 1573, +0.027 | 1624, +0.006 | +0.021 (0.038) | 0.2936 | 1.0000 | 9 of 16 | 0 | no | 136, +0.226 | 131, -0.011 | +0.237 (0.151) |
| H3 | continuation | opening candle (body / ATR at or above its walk-forward median) | 1887, +0.053 | 1274, -0.047 | +0.101 (0.039) | 0.0052 | 0.0468 | 11 of 15 | 0 | yes | 172, +0.053 | 99, +0.213 | -0.160 (0.154) |
| H4 | continuation | overnight compression (overnight range / ATR at or below its walk-forward median) | 1555, -0.004 | 1552, +0.034 | -0.038 (0.039) | 0.8359 | 1.0000 | 4 of 15 | 0 | no | 95, +0.237 | 172, +0.039 | +0.198 (0.161) |
| H5 | continuation | open outside the prior session (open beyond the prior session's extreme in the trade's direction) | 495, +0.070 | 2714, +0.005 | +0.066 (0.054) | 0.1105 | 0.8838 | 11 of 16 | 0 | no | 56, +0.245 | 211, +0.074 | +0.171 (0.180) |
| H6 | continuation | extension at the signal (distance from fair value / ATR at or below its walk-forward median) | 1616, -0.025 | 1545, +0.053 | -0.078 (0.039) | 0.9782 | 1.0000 | 3 of 15 | 70 | no | 101, +0.113 | 170, +0.111 | +0.003 (0.158) |
| H7 | reversion A+ | room to fair value (distance from fair value / ATR at or above its walk-forward median) | 251, -0.041 | 526, -0.057 | +0.016 (0.095) | 0.4335 | 1.0000 | 4 of 5 | 41 | no | 77, +0.097 | 136, -0.053 | +0.150 (0.188) |
| H8 | reversion A+ | trend (with the 20-session trend) | 410, -0.136 | 369, +0.043 | -0.179 (0.089) | 0.9777 | 1.0000 | 1 of 8 | 21 | no | 88, +0.015 | 125, -0.008 | +0.023 (0.174) |
| H9 | reversion A+ | gap fill (trading back across the overnight move) | 357, -0.052 | 405, -0.066 | +0.013 (0.091) | 0.4413 | 1.0000 | 5 of 8 | 18 | no | 113, +0.010 | 97, -0.003 | +0.013 (0.176) |

Passing conditions: H3. Per the registration, a passing condition becomes a candidate filter (B3 firm scoring on its favoured side, then re-simulation); a failing one is dropped and not re-cut on these data.

## Secondary outcome, continuation: hold to 16:00 minus the drift, per daily ATR (reported, not tested)

| id | development: favoured | other | benchmark: favoured | other |
|---|---|---|---|---|
| H1 | +0.0330 | +0.0364 | +0.0268 | +0.0806 |
| H2 | +0.0399 | +0.0321 | +0.0655 | +0.0468 |
| H3 | +0.0518 | +0.0112 | +0.0732 | +0.0239 |
| H4 | +0.0126 | +0.0594 | +0.0189 | +0.0770 |
| H5 | +0.0425 | +0.0343 | +0.1904 | +0.0207 |
| H6 | +0.0117 | +0.0602 | +0.0549 | +0.0554 |

## Thresholds used (walk-forward medians from earlier development years; the benchmark uses all development years)

| label | body / ATR (H3) | overnight range / ATR (H4) | extension / ATR, continuation (H6) | room / ATR, reversion A+ (H7) |
|---|---|---|---|---|
| 2010 | n/a | n/a | n/a | n/a |
| 2011 | 0.038 | 0.515 | 0.050 | n/a |
| 2012 | 0.035 | 0.523 | 0.056 | n/a |
| 2013 | 0.035 | 0.528 | 0.059 | n/a |
| 2014 | 0.035 | 0.503 | 0.060 | n/a |
| 2015 | 0.033 | 0.489 | 0.059 | 0.772 |
| 2016 | 0.033 | 0.487 | 0.058 | 0.772 |
| 2017 | 0.033 | 0.488 | 0.056 | 0.717 |
| 2018 | 0.034 | 0.486 | 0.057 | 0.717 |
| 2019 | 0.034 | 0.488 | 0.056 | 0.406 |
| 2020 | 0.034 | 0.490 | 0.055 | 0.418 |
| 2021 | 0.034 | 0.497 | 0.055 | 0.283 |
| 2022 | 0.034 | 0.499 | 0.055 | 0.273 |
| 2023 | 0.034 | 0.497 | 0.055 | 0.237 |
| 2024 | 0.035 | 0.495 | 0.055 | 0.233 |
| 2025 | 0.035 | 0.496 | 0.055 | 0.231 |
| benchmark | 0.035 | 0.496 | 0.055 | 0.222 |

## Volatility regime, descriptive only (seen in the anatomy, not tested)

Daily ATR as a share of the previous session's close (as the anatomy computes it), terciles fitted on every development trading day with a 09:30 bar; outcome the replayed bracket R flat at 16:00 on replayed entries. The anatomy's figures (ledger R on every development entry, terciles on every development day) therefore differ slightly.

| population | period | low: n, R | mid: n, R | high: n, R |
|---|---|---|---|---|
| continuation | development | 1031, +0.016 | 1078, +0.020 | 1156, +0.004 |
| continuation | benchmark | 21, +0.065 | 115, +0.211 | 135, +0.035 |
| reversion A+ | development | 90, -0.064 | 215, -0.137 | 474, -0.010 |
| reversion A+ | benchmark | 9, +0.104 | 87, +0.056 | 117, -0.047 |
