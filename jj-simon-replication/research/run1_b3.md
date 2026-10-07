# B3: candidate streams under the frozen firm rules

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

Every stream goes through the sequential pass (one position at a time, three-loss session stop, each trade's own exit time) and is scored with the frozen evaluator's walk-forward pass and payout functions under each firm preset and the sealed cut. The benchmark year is reported beside and never used to choose. EV per evaluation is the frozen calculator: pass x payout x median payout - fee.

Read with: S0r, not S0, is the control for S1-S4 (same entries, same 16:00 flat); S0 differs from it by the entries the replay drops for lack of context and by the ledger's exits after 16:00. S1's entries are exactly those of a frozen-engine run with reversion off, less the entries the replay drops for lack of context. S2-S4 are built from the sealed entries: they cannot contain an A+ reversion that the sealed three-loss stop or open position suppressed, nor a continuation re-entry that an earlier ATR exit would have freed (research/engine.py re-simulates whatever survives). Sizing: these tables book every trade at R x its budget whatever the stop ($1,000 or $2,000 in the evaluation by firm, $500 funded), as the frozen evaluator does, which is fractional contracts; the whole-contract table below sizes in micro NQ.

Walk-forward bracket for continuation (S3, S4), chosen on earlier development years only: 2013: atr_0.4_rr2.00; 2014: atr_0.5_rr1.52; 2015: atr_0.4_rr1.52; 2016: atr_0.7_rr1.00; 2017: atr_0.5_rr1.52; 2018: atr_0.5_rr1.52; 2019: atr_0.3_rr2.00; 2020: atr_0.3_rr2.00; 2021: atr_0.4_rr2.00; 2022: atr_0.4_rr2.00; 2023: atr_0.4_rr2.00; 2024: atr_0.4_rr2.00; 2025: atr_0.4_rr2.00; benchmark: atr_0.4_rr2.00; before 2013, the sealed bracket.

## Summary, topstep_50k

EV per evaluation is the frozen calculator's (pass x payout x median payout - one evaluation fee), as in the sealed report. EV net of all fees also charges the evaluation fee for every billing month the evaluation runs (monthly at this firm; 22 trading days a month) and the activation fee on each pass, which the frozen calculator leaves out.

| stream | period | trades | R/trade | total R | P(pass) | +/- | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 sealed ledger | development | 7431 | -0.037 | -276.4 | 20.1% | 1.8% | 45.8% | 3.3% | 623 | +8 | -26 |
| S0 sealed ledger | benchmark | 1258 | -0.071 | -89.1 | 8.7% | 4.0% | 13.2% | 4.6% | 1,800 | -28 | -44 |
| S0r sealed brackets, flat 16:00 | development | 7397 | -0.041 | -303.4 | 18.0% | 1.7% | 44.4% | 3.1% | 590 | -2 | -33 |
| S0r sealed brackets, flat 16:00 | benchmark | 1250 | -0.072 | -90.4 | 7.7% | 3.9% | 13.2% | 4.6% | 1,800 | -31 | -45 |
| S1 continuation only, sealed bracket | development | 3265 | +0.013 | +42.3 | 29.6% | 1.9% | 54.6% | 3.0% | 551 | +40 | -7 |
| S1 continuation only, sealed bracket | benchmark | 271 | +0.112 | +30.2 | 25.6% | 5.5% | 63.6% | 10.2% | 803 | +82 | +43 |
| S2 continuation + A+ reversion, sealed bracket | development | 4038 | +0.001 | +3.4 | 26.4% | 1.8% | 52.4% | 2.9% | 560 | +28 | -15 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | 480 | +0.062 | +29.6 | 19.4% | 4.8% | 36.6% | 7.6% | 1,232 | +38 | +7 |
| S3 continuation only, walk-forward ATR bracket | development | 3139 | +0.042 | +133.2 | 29.3% | 2.1% | 63.4% | 2.9% | 502 | +44 | -2 |
| S3 continuation only, walk-forward ATR bracket | benchmark | 227 | +0.084 | +19.1 | 22.8% | 6.5% | 70.1% | 3.4% | 528 | +36 | -0 |
| S4 S3 + A+ reversion, sealed bracket | development | 3389 | +0.044 | +148.5 | 29.0% | 2.1% | 62.0% | 2.8% | 538 | +48 | +2 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | 272 | +0.106 | +28.8 | 25.5% | 8.4% | 74.4% | 5.9% | 646 | +74 | +33 |

## Position size at Topstep's drawdown, topstep_50k_x

At the sealed sizing a stop-out costs 1.02 R with slippage and commission ($1,020 in a Topstep 50K evaluation), so two stop-outs cost $2,040 and breach the $2,000 drawdown; on the frozen topstep_50k preset its $1,000 soft daily limit caps each at exactly $1,000 and the balance lands on the threshold, which fails too (the help centre: an account fails when its balance hits the limit). Sized 0.98 the account fails on the third stop-out instead of the second, and two wins (2 x 1.51 R x 0.98 = 2.96 R) no longer reach the $3,000 target; the funded phase has the same kind of edge at four stop-outs. 0.98 clears the edge only for stops of about 25 points or more (the edge is 1 / (1 + 0.5 / stop): 0.965 at 14 points). This table and the next use topstep_50k_x (TopstepX: no daily loss limit for accounts created or reset since 2024-08-25; everything else as topstep_50k), because below the sealed sizing (and, at it, after a day that started with a win) the frozen account's soft daily limit credits a later trade on a day that has nearly reached the limit with a full win but a loss cut to the room left, which no real account allows; the frozen topstep_50k preset is shown at the sealed sizing only, where this slightly favours the streams that trade more than once a day, so compare streams in this table's 1.00 column. Fractional sizes, both phases scaled alike.

| preset | stream | period | P(pass) at 1.00 / 0.98 / 0.95 | P(payout) at 1.00 / 0.98 / 0.95 | EV net of all fees at 1.00 / 0.98 / 0.95 |
|---|---|---|---|---|---|
| topstep_50k_x | S0 sealed ledger | development | 19.9% / 21.6% / 21.4% | 45.0% / 46.8% / 47.9% | -27 / -24 / -25 |
| topstep_50k_x | S0 sealed ledger | benchmark | 8.4% / 9.3% / 9.3% | 8.4% / 8.4% / 11.0% | -49 / -49 / -45 |
| topstep_50k_x | S0r sealed brackets, flat 16:00 | development | 18.5% / 19.6% / 19.6% | 43.6% / 45.1% / 46.0% | -34 / -33 / -33 |
| topstep_50k_x | S0r sealed brackets, flat 16:00 | benchmark | 8.4% / 9.3% / 9.3% | 8.4% / 8.4% / 11.0% | -49 / -49 / -45 |
| topstep_50k_x | S1 continuation only, sealed bracket | development | 28.2% / 30.6% / 30.2% | 54.6% / 57.6% / 58.7% | -9 / -3 / -6 |
| topstep_50k_x | S1 continuation only, sealed bracket | benchmark | 26.5% / 36.5% / 38.9% | 63.6% / 65.6% / 66.6% | +46 / +83 / +82 |
| topstep_50k_x | S2 continuation + A+ reversion, sealed bracket | development | 25.7% / 27.6% / 27.1% | 52.1% / 53.6% / 55.1% | -16 / -14 / -15 |
| topstep_50k_x | S2 continuation + A+ reversion, sealed bracket | benchmark | 17.2% / 18.3% / 19.2% | 35.6% / 37.6% / 38.9% | +3 / +6 / +8 |
| topstep_50k_x | S3 continuation only, walk-forward ATR bracket | development | 28.9% / 31.4% / 32.1% | 63.4% / 65.0% / 65.5% | -3 / +0 / +0 |
| topstep_50k_x | S3 continuation only, walk-forward ATR bracket | benchmark | 22.8% / 26.2% / 28.5% | 70.1% / 69.4% / 69.8% | -0 / +8 / +11 |
| topstep_50k_x | S4 S3 + A+ reversion, sealed bracket | development | 29.4% / 32.4% / 33.0% | 61.4% / 62.5% / 63.6% | +2 / +8 / +8 |
| topstep_50k_x | S4 S3 + A+ reversion, sealed bracket | benchmark | 27.5% / 30.5% / 30.5% | 73.4% / 74.1% / 74.4% | +40 / +47 / +43 |

## Whole contracts

Each candidate's entries sized in whole micro NQ contracts ($2 a point): the largest count whose full stop-out (the stop plus 0.25 point of exit slippage, plus $0.50 round-trip commission per micro, the replay's $5 per NQ scaled; real micro fees run higher, about 0.01 to 0.02 R per trade on a 25-point stop) stays within the budget ($1,000 in the evaluation, $500 funded), at most 50 (the preset's 5 NQ). An entry that rounds to zero contracts is not taken, the sequential pass runs on what is taken, and each R is scaled by the contracts' stop risk as a share of the budget (size). No stream sits on the drawdown edge here: the sealed 25-point stop takes 19 micros in the evaluation (size 0.95) and 9 funded (0.90), the 50-point stop 9 and 4 (0.90 and 0.80), so the sealed rows differ from the summary for that reason; the preset is topstep_50k_x, for the reason given above. Micro NQ began trading on 2019-05-06; this applies today's contract menu to every year, which is the question for an account opened now (before May 2019 only NQ existed, and a stop wider than 50 points could not be taken at $1,000 of risk, nor one wider than 25 at $500). The frozen bootstrap is run on these inputs.

| preset | stream | period | evaluation: trades, mean size | P(pass) | +/- | funded: trades, mean size | P(payout) | +/- | median payout | EV per evaluation | EV net of all fees | P(bust) from $2,000 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k_x | S0 sealed ledger | development | 7431, 0.95 | 21.3% | 1.8% | 7431, 0.90 | 47.9% | 3.3% | 549 | +7 | -29 | 26% |
| topstep_50k_x | S0 sealed ledger | benchmark | 1258, 0.94 | 9.6% | 4.1% | 1258, 0.89 | 11.0% | 4.3% | 1,800 | -30 | -45 | 100% |
| topstep_50k_x | S0r sealed brackets, flat 16:00 | development | 7397, 0.95 | 19.6% | 1.7% | 7397, 0.90 | 46.0% | 3.2% | 513 | -3 | -36 | 64% |
| topstep_50k_x | S0r sealed brackets, flat 16:00 | benchmark | 1250, 0.94 | 9.6% | 4.1% | 1250, 0.89 | 11.0% | 4.3% | 1,800 | -30 | -45 | 100% |
| topstep_50k_x | S1 continuation only, sealed bracket | development | 3265, 0.95 | 30.2% | 2.1% | 3265, 0.89 | 59.7% | 3.1% | 483 | +38 | -11 | 1% |
| topstep_50k_x | S1 continuation only, sealed bracket | benchmark | 271, 0.93 | 36.5% | 7.8% | 271, 0.85 | 70.9% | 10.9% | 660 | +122 | +65 | 0% |
| topstep_50k_x | S2 continuation + A+ reversion, sealed bracket | development | 4038, 0.95 | 27.1% | 2.0% | 4038, 0.89 | 55.9% | 3.0% | 496 | +26 | -18 | 2% |
| topstep_50k_x | S2 continuation + A+ reversion, sealed bracket | benchmark | 480, 0.94 | 19.2% | 5.0% | 480, 0.87 | 36.9% | 7.4% | 1,154 | +33 | +3 | 13% |
| topstep_50k_x | S3 continuation only, walk-forward ATR bracket | development | 3139, 0.92 | 32.1% | 2.4% | 3123, 0.86 | 68.5% | 2.9% | 428 | +45 | -7 | 0% |
| topstep_50k_x | S3 continuation only, walk-forward ATR bracket | benchmark | 227, 0.79 | 23.5% | 7.8% | 185, 0.75 | 72.1% | 10.5% | 369 | +13 | -30 | 3% |
| topstep_50k_x | S4 S3 + A+ reversion, sealed bracket | development | 3389, 0.92 | 32.9% | 2.4% | 3385, 0.86 | 65.5% | 2.8% | 459 | +50 | -3 | 0% |
| topstep_50k_x | S4 S3 + A+ reversion, sealed bracket | benchmark | 272, 0.81 | 28.9% | 8.9% | 271, 0.80 | 71.8% | 5.4% | 540 | +63 | +15 | 0% |

## S0 sealed ledger

development: 7431 trades, -0.037 R per trade, -276.4 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 20.1% | 1.8% | 10 | 4748 (276) | 45.8% | 3.3% | 14 | 4753 (35) | 623 | +8 | -26 |
| fundednext_50k_flex | 1,000 | 12.6% | 1.4% | 12 | 4755 (310) | 37.9% | 3.2% | 14 | 4754 (9) | 672 | -38 | -38 |
| topstep_100k | 2,000 | 18.5% | 1.7% | 10 | 4749 (223) | 56.8% | 3.5% | 15 | 4752 (109) | 533 | -43 | -77 |
| tradeify_100k_growth | 2,000 | 30.2% | 1.7% | 5 | 4754 (140) | 12.6% | 2.1% | 28 | 4737 (1488) | 207 | -247 | -247 |

benchmark: 1258 trades, -0.071 R per trade, -89.1 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 8.7% | 4.0% | 17 | 310 (10) | 13.2% | 4.6% | 13 | 310 (0) | 1,800 | -28 | -44 |
| fundednext_50k_flex | 1,000 | 2.6% | 1.8% | 12 | 311 (8) | 7.7% | 3.2% | 12 | 311 (0) | 3,245 | -64 | -64 |
| topstep_100k | 2,000 | 8.1% | 3.5% | 17 | 310 (9) | 12.3% | 4.5% | 12 | 310 (0) | 2,636 | -73 | -90 |
| tradeify_100k_growth | 2,000 | 27.7% | 3.9% | 2 | 310 (0) | 5.2% | 3.5% | 38 | 309 (0) | 3,600 | -203 | -203 |

## S0r sealed brackets, flat 16:00

development: 7397 trades, -0.041 R per trade, -303.4 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 18.0% | 1.7% | 10 | 4748 (303) | 44.4% | 3.1% | 14 | 4753 (58) | 590 | -2 | -33 |
| fundednext_50k_flex | 1,000 | 10.8% | 1.3% | 11 | 4755 (301) | 35.4% | 2.8% | 13 | 4754 (10) | 672 | -44 | -44 |
| topstep_100k | 2,000 | 17.1% | 1.6% | 9 | 4749 (216) | 55.4% | 3.4% | 14 | 4752 (202) | 502 | -51 | -84 |
| tradeify_100k_growth | 2,000 | 28.6% | 1.7% | 5 | 4754 (151) | 12.4% | 2.2% | 26 | 4737 (1615) | 171 | -249 | -249 |

benchmark: 1250 trades, -0.072 R per trade, -90.4 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 7.7% | 3.9% | 17 | 310 (13) | 13.2% | 4.6% | 13 | 310 (0) | 1,800 | -31 | -45 |
| fundednext_50k_flex | 1,000 | 2.6% | 1.8% | 12 | 311 (8) | 7.7% | 3.2% | 12 | 311 (0) | 3,245 | -64 | -64 |
| topstep_100k | 2,000 | 7.1% | 3.4% | 16 | 310 (12) | 12.3% | 4.5% | 12 | 310 (0) | 2,636 | -76 | -93 |
| tradeify_100k_growth | 2,000 | 27.4% | 3.9% | 2 | 310 (0) | 5.2% | 3.5% | 38 | 309 (0) | 3,600 | -204 | -204 |

## S1 continuation only, sealed bracket

development: 3265 trades, +0.013 R per trade, +42.3 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 29.6% | 1.9% | 7 | 4747 (206) | 54.6% | 3.0% | 15 | 4746 (61) | 551 | +40 | -7 |
| fundednext_50k_flex | 1,000 | 20.2% | 1.7% | 9 | 4746 (203) | 44.3% | 2.8% | 14 | 4746 (10) | 694 | -8 | -8 |
| topstep_100k | 2,000 | 28.5% | 1.8% | 7 | 4747 (131) | 68.5% | 3.1% | 16 | 4746 (208) | 446 | -12 | -59 |
| tradeify_100k_growth | 2,000 | 29.3% | 1.8% | 6 | 4746 (159) | 17.7% | 2.9% | 36 | 4706 (1958) | 122 | -249 | -249 |

benchmark: 271 trades, +0.112 R per trade, +30.2 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 25.6% | 5.5% | 5 | 309 (3) | 63.6% | 10.2% | 12 | 302 (0) | 803 | +82 | +43 |
| fundednext_50k_flex | 1,000 | 18.4% | 4.6% | 7 | 309 (15) | 48.3% | 7.4% | 11 | 302 (0) | 941 | +14 | +14 |
| topstep_100k | 2,000 | 25.6% | 5.5% | 5 | 309 (3) | 75.5% | 11.7% | 12 | 302 (0) | 767 | +49 | +10 |
| tradeify_100k_growth | 2,000 | 31.1% | 5.4% | 4 | 309 (0) | 38.8% | 16.9% | 38 | 286 (54) | 147 | -237 | -237 |

## S2 continuation + A+ reversion, sealed bracket

development: 4038 trades, +0.001 R per trade, +3.4 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 26.4% | 1.8% | 8 | 4746 (245) | 52.4% | 2.9% | 14 | 4748 (61) | 560 | +28 | -15 |
| fundednext_50k_flex | 1,000 | 16.6% | 1.6% | 10 | 4744 (261) | 43.0% | 2.7% | 13 | 4748 (10) | 684 | -21 | -21 |
| topstep_100k | 2,000 | 25.1% | 1.7% | 8 | 4748 (164) | 65.9% | 3.1% | 15 | 4748 (209) | 477 | -20 | -63 |
| tradeify_100k_growth | 2,000 | 29.9% | 1.8% | 6 | 4749 (159) | 16.6% | 2.7% | 35 | 4718 (1936) | 153 | -247 | -247 |

benchmark: 480 trades, +0.062 R per trade, +29.6 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 19.4% | 4.8% | 9 | 310 (13) | 36.6% | 7.6% | 10 | 303 (0) | 1,232 | +38 | +7 |
| fundednext_50k_flex | 1,000 | 8.1% | 3.5% | 9 | 308 (17) | 24.8% | 5.5% | 9 | 303 (0) | 1,537 | -39 | -39 |
| topstep_100k | 2,000 | 18.4% | 4.4% | 8 | 310 (13) | 60.4% | 10.0% | 11 | 303 (0) | 878 | -2 | -33 |
| tradeify_100k_growth | 2,000 | 34.2% | 4.5% | 3 | 310 (0) | 9.8% | 6.9% | 46 | 285 (70) | 2,031 | -187 | -187 |

## S3 continuation only, walk-forward ATR bracket

development: 3139 trades, +0.042 R per trade, +133.2 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 29.3% | 2.1% | 10 | 4749 (180) | 63.4% | 2.9% | 16 | 4740 (63) | 502 | +44 | -2 |
| fundednext_50k_flex | 1,000 | 22.1% | 2.0% | 12 | 4746 (218) | 50.9% | 2.7% | 15 | 4743 (6) | 630 | +1 | +1 |
| topstep_100k | 2,000 | 27.8% | 2.0% | 9 | 4752 (121) | 75.1% | 2.8% | 17 | 4740 (216) | 440 | -7 | -53 |
| tradeify_100k_growth | 2,000 | 30.0% | 2.1% | 8 | 4752 (127) | 21.0% | 3.2% | 40 | 4706 (2359) | 111 | -248 | -248 |

benchmark: 227 trades, +0.084 R per trade, +19.1 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 22.8% | 6.5% | 7 | 302 (4) | 70.1% | 3.4% | 16 | 301 (0) | 528 | +36 | -0 |
| fundednext_50k_flex | 1,000 | 17.5% | 6.6% | 11 | 302 (15) | 43.9% | 5.8% | 14 | 301 (0) | 845 | -5 | -5 |
| topstep_100k | 2,000 | 22.5% | 6.5% | 7 | 302 (2) | 88.0% | 4.5% | 18 | 301 (15) | 417 | -16 | -52 |
| tradeify_100k_growth | 2,000 | 25.5% | 6.6% | 7 | 302 (0) | 18.9% | 9.7% | 30 | 254 (206) | 132 | -249 | -249 |

## S4 S3 + A+ reversion, sealed bracket

development: 3389 trades, +0.044 R per trade, +148.5 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 29.0% | 2.1% | 9 | 4751 (188) | 62.0% | 2.8% | 15 | 4745 (49) | 538 | +48 | +2 |
| fundednext_50k_flex | 1,000 | 22.6% | 1.9% | 12 | 4745 (208) | 51.0% | 2.6% | 14 | 4747 (6) | 684 | +9 | +9 |
| topstep_100k | 2,000 | 27.5% | 2.0% | 9 | 4752 (133) | 74.8% | 2.9% | 16 | 4745 (186) | 463 | -4 | -49 |
| tradeify_100k_growth | 2,000 | 31.8% | 2.1% | 8 | 4752 (120) | 23.8% | 3.3% | 37 | 4718 (2072) | 153 | -243 | -243 |

benchmark: 272 trades, +0.106 R per trade, +28.8 R.

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) | EV per evaluation | EV net of all fees |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 25.5% | 8.4% | 7 | 302 (16) | 74.4% | 5.9% | 14 | 301 (0) | 646 | +74 | +33 |
| fundednext_50k_flex | 1,000 | 20.9% | 8.0% | 11 | 302 (11) | 60.1% | 6.8% | 14 | 301 (0) | 802 | +31 | +31 |
| topstep_100k | 2,000 | 23.8% | 7.9% | 7 | 302 (16) | 89.4% | 3.9% | 15 | 301 (6) | 490 | +5 | -36 |
| tradeify_100k_growth | 2,000 | 35.4% | 7.3% | 6 | 302 (0) | 26.4% | 12.2% | 30 | 254 (187) | 126 | -243 | -243 |

## Bootstrap with the frozen simulator, topstep_50k

The frozen report's bootstrap (fpt.bootstrap.simulate_his_stats: 2,000 paths, seed 0, twelve months, everything reinvested, one payout per funded account, payouts gross) run on each stream's measured topstep_50k inputs from the summary (fractional sizing), exactly as the sealed report runs it on Baseline 0. P(bust) is the share of paths with no live account and too little cash for another evaluation within twelve months. Like the frozen calculator, the simulator charges one evaluation fee per evaluation and no activation fee, so these rates are optimistic wherever the net EV is below the frozen one.

| stream | period | P(bust) from $500 | $1,000 | $2,000 | $5,000 | P(zero payouts, first batch, $2,000) | median days to first payout ($2,000) | funded accounts month 12, median ($2,000) |
|---|---|---|---|---|---|---|---|---|
| S0 sealed ledger | development | 72% | 52% | 27% | 4% | 2% | 24 | 18 |
| S0 sealed ledger | benchmark | 100% | 100% | 100% | 100% | 63% | 30 | 0 |
| S0r sealed brackets, flat 16:00 | development | 89% | 78% | 61% | 30% | 4% | 24 | 0 |
| S0r sealed brackets, flat 16:00 | benchmark | 100% | 100% | 100% | 100% | 66% | 30 | 0 |
| S1 continuation only, sealed bracket | development | 26% | 7% | 0% | 0% | 0% | 22 | 37 |
| S1 continuation only, sealed bracket | benchmark | 20% | 4% | 0% | 0% | 0% | 17 | 38 |
| S2 continuation + A+ reversion, sealed bracket | development | 37% | 14% | 2% | 0% | 0% | 22 | 31 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | 58% | 34% | 12% | 0% | 5% | 19 | 16 |
| S3 continuation only, walk-forward ATR bracket | development | 19% | 4% | 0% | 0% | 0% | 26 | 32 |
| S3 continuation only, walk-forward ATR bracket | benchmark | 28% | 7% | 0% | 0% | 0% | 23 | 33 |
| S4 S3 + A+ reversion, sealed bracket | development | 19% | 4% | 0% | 0% | 0% | 24 | 33 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | 15% | 2% | 0% | 0% | 0% | 21 | 34 |

## Continuation by direction

Replayed continuation entries before the sequential pass, flat at 16:00. Cells: trades, mean (standard error of the mean, clustered by day). The drift is the same-direction trade from the same minute, at the same costs, averaged over every non-roll trading day of the same period label that has a bar at that minute (a development calendar year; for 2025, 1 January to the cut; the benchmark period); the excess is the trade held to 16:00 minus that drift, zero on average if the direction call adds nothing to the market's drift at that time of day. R per 25 points weighs a 2025 trade about eleven times a 2010 one (NQ went from about 2,000 to 22,000); per daily ATR (the excess in points over the previous session's daily ATR) weighs every year alike.

| outcome | period | long | short | both |
|---|---|---|---|---|
| sealed bracket | development | 1631, +0.025 (0.027) | 1634, +0.001 (0.026) | 3265, +0.013 (0.019) |
| sealed bracket | benchmark | 125, +0.099 (0.121) | 146, +0.123 (0.096) | 271, +0.112 (0.076) |
| S3 walk-forward bracket (sealed before 2013) | development | 1631, +0.056 (0.025) | 1634, +0.027 (0.027) | 3265, +0.041 (0.018) |
| S3 walk-forward bracket (sealed before 2013) | benchmark | 125, +0.180 (0.104) | 146, +0.026 (0.105) | 271, +0.097 (0.075) |
| held to 16:00 (R per 25 points) | development | 1631, +0.314 (0.164) | 1634, +0.134 (0.132) | 3265, +0.224 (0.105) |
| held to 16:00 (R per 25 points) | benchmark | 125, +1.688 (0.971) | 146, +0.473 (1.005) | 271, +1.033 (0.703) |
| held to 16:00, excess over the drift (R per 25 points) | development | 1631, +0.278 (0.164) | 1634, +0.243 (0.132) | 3265, +0.260 (0.105) |
| held to 16:00, excess over the drift (R per 25 points) | benchmark | 125, +1.428 (0.971) | 146, +0.794 (1.005) | 271, +1.087 (0.702) |
| held to 16:00, excess over the drift (per daily ATR) | development | 1631, +0.039 (0.015) | 1634, +0.031 (0.015) | 3265, +0.035 (0.011) |
| held to 16:00, excess over the drift (per daily ATR) | benchmark | 125, +0.068 (0.053) | 146, +0.044 (0.050) | 271, +0.055 (0.036) |

### Held to 16:00 against the drift, by year

| year | long: trades, held, drift, excess (R per 25 points) | short: trades, held, drift, excess (R per 25 points) | both: excess, R per 25 points (se) | both: excess per daily ATR (se) |
|---|---|---|---|---|
| 2010 | 46, +0.065, +0.000, +0.065 | 58, -0.040, -0.061, +0.021 | +0.040 (0.065) | +0.026 (0.046) |
| 2011 | 84, +0.103, -0.026, +0.128 | 98, +0.025, -0.035, +0.060 | +0.091 (0.070) | +0.027 (0.038) |
| 2012 | 75, +0.052, +0.001, +0.051 | 101, -0.078, -0.061, -0.017 | +0.012 (0.062) | +0.011 (0.040) |
| 2013 | 101, +0.114, +0.030, +0.084 | 91, -0.053, -0.090, +0.037 | +0.062 (0.052) | +0.040 (0.037) |
| 2014 | 91, +0.096, +0.007, +0.090 | 96, +0.011, -0.069, +0.080 | +0.085 (0.085) | +0.039 (0.045) |
| 2015 | 90, -0.221, -0.053, -0.169 | 108, -0.054, -0.007, -0.047 | -0.102 (0.110) | -0.035 (0.042) |
| 2016 | 100, +0.243, +0.029, +0.214 | 107, +0.133, -0.089, +0.222 | +0.218 (0.097) | +0.076 (0.038) |
| 2017 | 84, +0.011, +0.063, -0.051 | 115, -0.118, -0.126, +0.008 | -0.017 (0.089) | -0.036 (0.042) |
| 2018 | 116, +0.235, -0.215, +0.450 | 88, +0.166, +0.156, +0.010 | +0.260 (0.231) | +0.088 (0.046) |
| 2019 | 117, +0.107, +0.145, -0.038 | 103, -0.245, -0.206, -0.039 | -0.039 (0.147) | +0.008 (0.032) |
| 2020 | 122, +1.134, +0.155, +0.979 | 106, +1.154, -0.221, +1.375 | +1.163 (0.400) | +0.109 (0.042) |
| 2021 | 129, +0.286, +0.127, +0.159 | 112, +0.404, -0.190, +0.594 | +0.361 (0.416) | +0.027 (0.043) |
| 2022 | 149, +0.017, -0.602, +0.619 | 107, +0.797, +0.529, +0.268 | +0.472 (0.651) | +0.044 (0.043) |
| 2023 | 135, +0.816, +0.483, +0.333 | 101, -0.204, -0.542, +0.339 | +0.335 (0.393) | +0.030 (0.041) |
| 2024 | 103, +0.032, +0.078, -0.046 | 139, +0.270, -0.138, +0.408 | +0.215 (0.439) | +0.035 (0.037) |
| 2025 | 89, +1.568, +0.482, +1.086 | 104, -0.234, -0.545, +0.311 | +0.668 (1.123) | +0.054 (0.052) |
| benchmark | 125, +1.688, +0.260, +1.428 | 146, +0.473, -0.322, +0.794 | +1.087 (0.702) | +0.055 (0.036) |

Development years with a positive mean excess: 13 of 16 in R per 25 points, 14 of 16 per daily ATR. Mean of the yearly means per daily ATR +0.0340, standard error across years 0.0095 (each year one observation).
