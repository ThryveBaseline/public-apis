# B5: the $2,000 bootstrap on replayed market paths

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

Implements docs/research/preregistration_b5_bootstrap.md as registered in df2bc28, clarified in 1995b2c, 7465eed and d2046ee and amended in eb01d37, all before any B5 number (sha256 of the file read: 10695c98305ba41c7d8b7d6f1c28c72bc90d203e0a33980d9efc7b3ff6eb877d, the pinned value). Development: New York days through 2025-10-05; benchmark from 2025-10-06, one path over the benchmark year, reported beside and never used. From $2,000 of cash, each path runs Topstep 50K evaluations and Express Funded accounts for 365 calendar days on the stream's own trading days, every live account taking the same trades on the same day: $49 an evaluation at purchase and every 30 calendar days it stays live, $149 to activate a pass, payouts net of the split credited five trading days after they are requested, at most one purchase a day, evaluations closed after 30 trading days; ruin is cash below $49 with nothing live and nothing pending. Gates, passed on every run: each evaluation compared (those cancelled for fees or cut off by the path's end are not) equals the frozen pass walk-forward for its start day in outcome and day, and each Express Funded account's first payout within 60 days equals the frozen payout walk-forward's (B4's walk-forward of the same policy under "wait") in outcome, day and amount; B4's own gate passed on every stream in the selection. Whole micros run on TopstepX only (clarification 5); a selected configuration on the frozen topstep_50k preset is shown at its B4 size for the record and decides nothing. Every run is shown twice (amendment 10): without a call-up, and with Topstep's call-up to a Live account at the path's 3rd payout request, where every account closes, nothing more is bought and the Live account counts for nothing. That bounds from below what a called-up path is worth, not B5's own numbers: stopping the purchases also stops the ones that ruin paths at cap 5, so with the call-up P(ruin) can only fall and the cash can rise (clarification 12). Not modelled: Topstep's limit of 20 account purchases a month, which binds on part of the paths at cap 5 (in the review's synthetic probe enforcing it moved P(ruin) by under a point).

Streams: B3's S0r and S1 to S4 on all the data; the trend exit failed its registered test (one-sided p 0.4929, positive in 7 of 13 chain years): S5 and S6 do not run; H3 passed its registered test on these inputs (Holm p 0.0468, positive in 11 of 15 years): its favoured-side streams from 2011-01-01.

## Which configurations run (B4's development lifetime EV per evaluation at H 250)

| stream | preset | size | policy | P(pass) | fees per evaluation | expected paid per funded account | EV per evaluation | runs |
|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | topstep_50k_x | 1.00 | ask | 18.5% | 80 | 628 | +36 | yes |
| S0r sealed brackets, flat 16:00 | topstep_50k_x | 1.00 | wait | 18.5% | 80 | 653 | +41 | yes |
| S0r sealed brackets, flat 16:00 | topstep_50k_x | 0.95 | ask | 19.6% | 83 | 639 | +43 | yes |
| S0r sealed brackets, flat 16:00 | topstep_50k_x | 0.95 | wait | 19.6% | 83 | 672 | +49 | yes |
| S0r sealed brackets, flat 16:00 | topstep_50k | 1.00 | ask | 18.0% | 80 | 640 | +35 | yes |
| S0r sealed brackets, flat 16:00 | topstep_50k | 1.00 | wait | 18.0% | 80 | 666 | +40 | yes |
| S1 continuation only, sealed bracket | topstep_50k_x | 1.00 | ask | 28.2% | 94 | 806 | +133 | yes |
| S1 continuation only, sealed bracket | topstep_50k_x | 1.00 | wait | 28.2% | 94 | 879 | +153 | yes |
| S1 continuation only, sealed bracket | topstep_50k_x | 0.95 | ask | 30.2% | 98 | 816 | +148 | yes |
| S1 continuation only, sealed bracket | topstep_50k_x | 0.95 | wait | 30.2% | 98 | 928 | +182 | yes |
| S1 continuation only, sealed bracket | topstep_50k | 1.00 | ask | 29.6% | 96 | 806 | +142 | yes |
| S1 continuation only, sealed bracket | topstep_50k | 1.00 | wait | 29.6% | 96 | 882 | +165 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k_x | 1.00 | ask | 25.7% | 91 | 748 | +102 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k_x | 1.00 | wait | 25.7% | 91 | 808 | +117 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k_x | 0.95 | ask | 27.1% | 94 | 745 | +108 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k_x | 0.95 | wait | 27.1% | 94 | 828 | +130 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k | 1.00 | ask | 26.4% | 92 | 752 | +106 | yes |
| S2 continuation + A+ reversion, sealed bracket | topstep_50k | 1.00 | wait | 26.4% | 92 | 809 | +121 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k_x | 1.00 | ask | 28.9% | 95 | 1,117 | +228 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k_x | 1.00 | wait | 28.9% | 95 | 1,222 | +258 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k_x | 0.95 | ask | 32.1% | 101 | 1,080 | +246 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k_x | 0.95 | wait | 32.1% | 101 | 1,228 | +293 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k | 1.00 | ask | 29.3% | 96 | 1,117 | +232 | yes |
| S3 continuation only, walk-forward ATR bracket | topstep_50k | 1.00 | wait | 29.3% | 96 | 1,222 | +263 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k_x | 1.00 | ask | 29.4% | 96 | 1,042 | +211 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k_x | 1.00 | wait | 29.4% | 96 | 1,127 | +236 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k_x | 0.95 | ask | 33.0% | 102 | 1,025 | +236 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k_x | 0.95 | wait | 33.0% | 102 | 1,139 | +274 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k | 1.00 | ask | 29.0% | 95 | 1,047 | +209 | yes |
| S4 S3 + A+ reversion, sealed bracket | topstep_50k | 1.00 | wait | 29.0% | 95 | 1,143 | +237 | yes |
| S1 on H3's favoured side | topstep_50k_x | 1.00 | ask | 26.9% | 97 | 1,033 | +180 | yes |
| S1 on H3's favoured side | topstep_50k_x | 1.00 | wait | 26.9% | 97 | 1,279 | +246 | yes |
| S1 on H3's favoured side | topstep_50k_x | 0.95 | ask | 27.6% | 102 | 1,033 | +183 | yes |
| S1 on H3's favoured side | topstep_50k_x | 0.95 | wait | 27.6% | 102 | 1,349 | +270 | yes |
| S1 on H3's favoured side | topstep_50k | 1.00 | ask | 28.4% | 100 | 1,033 | +193 | yes |
| S1 on H3's favoured side | topstep_50k | 1.00 | wait | 28.4% | 100 | 1,280 | +263 | yes |
| S3 on H3's favoured side | topstep_50k_x | 1.00 | ask | 29.6% | 103 | 1,438 | +323 | yes |
| S3 on H3's favoured side | topstep_50k_x | 1.00 | wait | 29.6% | 103 | 1,771 | +422 | yes |
| S3 on H3's favoured side | topstep_50k_x | 0.95 | ask | 31.3% | 109 | 1,419 | +335 | yes |
| S3 on H3's favoured side | topstep_50k_x | 0.95 | wait | 31.3% | 109 | 1,750 | +438 | yes |
| S3 on H3's favoured side | topstep_50k | 1.00 | ask | 29.8% | 104 | 1,438 | +324 | yes |
| S3 on H3's favoured side | topstep_50k | 1.00 | wait | 29.8% | 104 | 1,771 | +424 | yes |
| S4 on H3's favoured side | topstep_50k_x | 1.00 | ask | 30.6% | 102 | 1,390 | +324 | yes |
| S4 on H3's favoured side | topstep_50k_x | 1.00 | wait | 30.6% | 102 | 1,674 | +411 | yes |
| S4 on H3's favoured side | topstep_50k_x | 0.95 | ask | 32.8% | 107 | 1,406 | +354 | yes |
| S4 on H3's favoured side | topstep_50k_x | 0.95 | wait | 32.8% | 107 | 1,651 | +435 | yes |
| S4 on H3's favoured side | topstep_50k | 1.00 | ask | 31.1% | 103 | 1,367 | +322 | yes |
| S4 on H3's favoured side | topstep_50k | 1.00 | wait | 31.1% | 103 | 1,631 | +404 | yes |

## Results

Cash at the end counts payouts requested and not yet credited; accounts live at the end count for nothing. Development paths cover 365 calendar days; the benchmark path's span is shown. Ruin day and first payout: trading days into the path (about 310 a year), the payout on the day it is requested. Deepest fall: how far cash went below $2,000 at its lowest (the money actually at risk). Years: the non-overlapping years of data behind the development paths (the paths overlap, so this, not the number of paths, is the sample). Frozen bootstrap: the frozen simulator from $2,000 on that period's B3 firm row at the same stream, preset and sizing, as B3 calls it (independent accounts, one payout each, no activation fee): P(bust), median days to the first payout, funded accounts at month 12.

### S0r sealed brackets, flat 16:00: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 26.8% | 164 | 34 / 46 / 2,268 / 3,625 / 6,063 | 2,513 | 52.1% | 17.7% | 1,016 / 1,966 | n/a | 69%, 23, 0 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 151 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | n/a | 100%, 17, 0 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 26.8% | 164 | 34 / 46 / 2,417 / 3,352 / 4,575 | 2,181 | 55.4% | 14.5% | 1,016 / 1,966 | 60.4% (204) | 69%, 23, 0 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 151 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | 0.0% (n/a) | 100%, 17, 0 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 76.4% | 74 | 17 / 30 / 36 / 47 / 9,655 | 2,560 | 21.0% | 19.8% | 1,966 / 1,986 | n/a | 69%, 23, 0 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 17, 0 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 56.6% | 55 | 30 / 34 / 40 / 2,066 / 4,463 | 1,345 | 25.8% | 12.4% | 1,962 / 1,974 | 43.4% (50) | 69%, 23, 0 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 17, 0 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 25.0% | 185 | 32 / 48 / 2,627 / 3,859 / 7,820 | 2,908 | 58.9% | 23.8% | 841 / 1,968 | n/a | 64%, 23, 0 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 36 / 36 / 36 / 36 / 36 | 36 | 0.0% | 0.0% | 1,964 / 1,964 | n/a | 100%, 17, 0 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 25.0% | 185 | 32 / 48 / 2,329 / 3,503 / 4,704 | 2,310 | 60.5% | 15.4% | 841 / 1,968 | 61.9% (176) | 64%, 23, 0 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 36 / 36 / 36 / 36 / 36 | 36 | 0.0% | 0.0% | 1,964 / 1,964 | 0.0% (n/a) | 100%, 17, 0 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 69.8% | 80 | 20 / 30 / 38 / 1,680 / 9,711 | 2,797 | 24.7% | 22.8% | 1,966 / 1,983 | n/a | 64%, 23, 0 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 17, 0 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 54.0% | 63 | 28 / 34 / 40 / 2,390 / 4,452 | 1,422 | 29.4% | 12.1% | 1,962 / 1,974 | 46.0% (51) | 64%, 23, 0 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 17, 0 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 24.9% | 186 | 32 / 48 / 2,796 / 3,939 / 8,381 | 3,041 | 60.8% | 24.7% | 838 / 1,968 | n/a | 52%, 23, 0 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | n/a | 100%, 16, 0 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 24.9% | 186 | 32 / 48 / 2,470 / 3,717 / 4,993 | 2,439 | 61.9% | 19.5% | 838 / 1,968 | 59.7% (179) | 52%, 23, 0 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | 0.0% (n/a) | 100%, 16, 0 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 70.1% | 79 | 21 / 30 / 38 / 1,655 / 10,935 | 3,282 | 24.5% | 23.8% | 1,966 / 1,986 | n/a | 52%, 23, 0 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 16, 0 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 53.8% | 63 | 28 / 34 / 40 / 2,522 / 4,583 | 1,488 | 30.4% | 13.3% | 1,962 / 1,976 | 46.2% (51) | 52%, 23, 0 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 16, 0 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 7397, 7397 | 28.7 | 4.90 | 0.06 | 0.00 | 4.58 | 2.85 | 2,162 | 2,675 | 73 | 21.0% | 125772, 20746 |
| 1.00 of the budget | 1 | none | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 1.00 of the budget | 1 | at payout 3 | development | 7397, 7397 | 21.9 | 3.87 | 0.06 | 0.00 | 3.16 | 2.09 | 1,667 | 1,848 | 73 | 21.0% | 97091, 16744 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 1.00 of the budget | 5 | none | development | 7397, 7397 | 57.9 | 10.41 | 1.36 | 0.17 | 8.70 | 5.50 | 4,294 | 4,854 | 44 | 49.0% | 254179, 39196 |
| 1.00 of the budget | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 1.00 of the budget | 5 | at payout 3 | development | 7397, 7397 | 25.6 | 5.01 | 0.99 | 0.10 | 2.26 | 1.73 | 1,907 | 1,252 | 44 | 49.0% | 112228, 16142 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| whole micros | 1 | none | development | 7397, 7397 | 25.4 | 4.78 | 0.10 | 0.00 | 4.38 | 3.15 | 1,973 | 2,882 | 71 | 20.9% | 111183, 20000 |
| whole micros | 1 | none | benchmark | 1250, 1250 | 34.0 | 2.00 | 0.00 | 0.00 | 2.00 | 0.00 | 1,964 | 0 | n/a | 100.0% | 34, 2 |
| whole micros | 1 | at payout 3 | development | 7397, 7397 | 17.7 | 3.58 | 0.10 | 0.00 | 2.80 | 2.12 | 1,411 | 1,721 | 71 | 20.9% | 78379, 15252 |
| whole micros | 1 | at payout 3 | benchmark | 1250, 1250 | 34.0 | 2.00 | 0.00 | 0.00 | 2.00 | 0.00 | 1,964 | 0 | n/a | 100.0% | 34, 2 |
| whole micros | 5 | none | development | 7397, 7397 | 59.3 | 11.43 | 1.35 | 0.21 | 9.55 | 6.13 | 4,526 | 5,323 | 45 | 47.5% | 259522, 43092 |
| whole micros | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| whole micros | 5 | at payout 3 | development | 7397, 7397 | 24.5 | 5.14 | 0.98 | 0.15 | 2.30 | 1.82 | 1,883 | 1,305 | 45 | 47.5% | 106628, 16746 |
| whole micros | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 0.95 of the budget | 1 | none | development | 7397, 7397 | 26.0 | 4.72 | 0.10 | 0.00 | 4.36 | 3.11 | 2,004 | 3,045 | 72 | 20.8% | 113773, 19837 |
| 0.95 of the budget | 1 | none | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 0.95 of the budget | 1 | at payout 3 | development | 7397, 7397 | 18.4 | 3.53 | 0.10 | 0.00 | 2.77 | 2.10 | 1,447 | 1,886 | 72 | 20.8% | 81428, 15044 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 0.95 of the budget | 5 | none | development | 7397, 7397 | 59.8 | 11.47 | 1.32 | 0.22 | 9.71 | 6.32 | 4,569 | 5,850 | 45 | 46.9% | 261492, 43778 |
| 0.95 of the budget | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 0.95 of the budget | 5 | at payout 3 | development | 7397, 7397 | 24.7 | 5.13 | 0.97 | 0.17 | 2.29 | 1.85 | 1,896 | 1,384 | 45 | 46.9% | 107516, 16784 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |

### S0r sealed brackets, flat 16:00: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 26.8% | 164 | 34 / 46 / 2,039 / 3,540 / 5,807 | 2,458 | 50.6% | 20.4% | 1,184 / 1,966 | n/a | 69%, 23, 0 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 151 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | n/a | 100%, 17, 0 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 26.8% | 164 | 34 / 46 / 2,039 / 3,869 / 4,681 | 2,269 | 50.6% | 21.1% | 1,184 / 1,966 | 43.9% (223) | 69%, 23, 0 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 151 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | 0.0% (n/a) | 100%, 17, 0 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 79.2% | 70 | 24 / 30 / 34 / 40 / 8,631 | 2,293 | 19.2% | 16.4% | 1,966 / 1,978 | n/a | 69%, 23, 0 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 17, 0 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 73.5% | 65 | 26 / 30 / 36 / 2,118 / 4,979 | 1,231 | 25.8% | 14.8% | 1,966 / 1,974 | 26.5% (54) | 69%, 23, 0 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 17, 0 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 24.7% | 170 | 32 / 863 / 3,195 / 4,532 / 7,822 | 3,180 | 62.4% | 34.0% | 839 / 1,968 | n/a | 64%, 23, 0 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 36 / 36 / 36 / 36 / 36 | 36 | 0.0% | 0.0% | 1,964 / 1,964 | n/a | 100%, 17, 0 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 24.7% | 170 | 32 / 863 / 3,200 / 3,961 / 4,858 | 2,646 | 62.4% | 23.3% | 839 / 1,968 | 52.2% (205) | 64%, 23, 0 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 36 / 36 / 36 / 36 / 36 | 36 | 0.0% | 0.0% | 1,964 / 1,964 | 0.0% (n/a) | 100%, 17, 0 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 73.1% | 74 | 24 / 30 / 36 / 1,745 / 11,820 | 2,879 | 24.9% | 21.8% | 1,966 / 1,977 | n/a | 64%, 23, 0 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 17, 0 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 69.1% | 70 | 26 / 30 / 38 / 3,154 / 5,370 | 1,441 | 29.9% | 18.3% | 1,966 / 1,976 | 30.9% (55) | 64%, 23, 0 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 17, 0 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 24.7% | 184 | 32 / 620 / 3,223 / 4,706 / 8,562 | 3,432 | 61.2% | 36.0% | 886 / 1,968 | n/a | 52%, 23, 0 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | n/a | 100%, 16, 0 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 24.7% | 184 | 32 / 620 / 3,385 / 4,213 / 5,194 | 2,715 | 61.2% | 31.9% | 886 / 1,968 | 51.8% (189) | 52%, 23, 0 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 154 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | 0.0% (n/a) | 100%, 16, 0 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 73.7% | 75 | 26 / 30 / 36 / 1,394 / 14,517 | 3,285 | 24.8% | 22.8% | 1,966 / 1,976 | n/a | 52%, 23, 0 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | n/a | 100%, 16, 0 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 68.0% | 70 | 26 / 30 / 38 / 3,046 / 5,372 | 1,477 | 30.2% | 18.2% | 1,966 / 1,974 | 32.0% (55) | 52%, 23, 0 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 39 | 30 / 30 / 30 / 30 / 30 | 30 | 0.0% | 0.0% | 1,970 / 1,970 | 0.0% (n/a) | 100%, 16, 0 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 7397, 7397 | 27.6 | 4.74 | 0.06 | 0.00 | 4.37 | 2.09 | 2,077 | 2,535 | 96 | 30.1% | 120963, 19870 |
| 1.00 of the budget | 1 | none | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 1.00 of the budget | 1 | at payout 3 | development | 7397, 7397 | 22.9 | 4.07 | 0.06 | 0.00 | 3.43 | 1.72 | 1,740 | 2,009 | 96 | 30.1% | 101054, 17370 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 1.00 of the budget | 5 | none | development | 7397, 7397 | 50.8 | 9.33 | 1.27 | 0.13 | 7.69 | 3.36 | 3,778 | 4,072 | 45 | 67.8% | 223257, 34593 |
| 1.00 of the budget | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 1.00 of the budget | 5 | at payout 3 | development | 7397, 7397 | 26.8 | 5.36 | 1.15 | 0.13 | 3.07 | 1.05 | 1,996 | 1,227 | 45 | 67.8% | 117977, 17483 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| whole micros | 1 | none | development | 7397, 7397 | 23.8 | 4.37 | 0.09 | 0.00 | 3.94 | 2.50 | 1,830 | 3,009 | 97 | 32.7% | 104225, 18080 |
| whole micros | 1 | none | benchmark | 1250, 1250 | 34.0 | 2.00 | 0.00 | 0.00 | 2.00 | 0.00 | 1,964 | 0 | n/a | 100.0% | 34, 2 |
| whole micros | 1 | at payout 3 | development | 7397, 7397 | 17.6 | 3.49 | 0.09 | 0.00 | 2.75 | 1.82 | 1,390 | 2,036 | 97 | 32.7% | 77872, 14742 |
| whole micros | 1 | at payout 3 | benchmark | 1250, 1250 | 34.0 | 2.00 | 0.00 | 0.00 | 2.00 | 0.00 | 1,964 | 0 | n/a | 100.0% | 34, 2 |
| whole micros | 5 | none | development | 7397, 7397 | 52.1 | 10.05 | 1.20 | 0.19 | 8.35 | 4.22 | 3,975 | 4,854 | 52 | 63.8% | 228227, 37660 |
| whole micros | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| whole micros | 5 | at payout 3 | development | 7397, 7397 | 25.9 | 5.46 | 1.10 | 0.18 | 3.05 | 1.27 | 1,989 | 1,430 | 52 | 63.8% | 113720, 18264 |
| whole micros | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 0.95 of the budget | 1 | none | development | 7397, 7397 | 24.6 | 4.34 | 0.09 | 0.00 | 3.95 | 2.61 | 1,874 | 3,306 | 97 | 28.6% | 107652, 18103 |
| 0.95 of the budget | 1 | none | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 0.95 of the budget | 1 | at payout 3 | development | 7397, 7397 | 18.6 | 3.39 | 0.09 | 0.00 | 2.68 | 1.84 | 1,430 | 2,145 | 97 | 28.6% | 82055, 14386 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 37.0 | 2.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1,962 | 0 | n/a | 100.0% | 37, 1 |
| 0.95 of the budget | 5 | none | development | 7397, 7397 | 51.4 | 10.14 | 1.19 | 0.20 | 8.51 | 4.33 | 3,958 | 5,243 | 48 | 63.8% | 224773, 38417 |
| 0.95 of the budget | 5 | none | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |
| 0.95 of the budget | 5 | at payout 3 | development | 7397, 7397 | 25.9 | 5.42 | 1.09 | 0.20 | 2.97 | 1.28 | 1,984 | 1,461 | 48 | 63.8% | 113623, 17881 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 25.0 | 5.00 | 0.00 | 0.00 | 5.00 | 0.00 | 1,970 | 0 | n/a | 100.0% | 25, 5 |

### S0r sealed brackets, flat 16:00: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 23.4% | 230 | 34 / 336 / 2,302 / 4,566 / 7,624 | 3,169 | 54.5% | 26.5% | 1,020 / 1,966 | n/a | 61%, 24, 0 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 213 | 34 / 34 / 34 / 34 / 34 | 34 | 0.0% | 0.0% | 1,966 / 1,966 | n/a | 100%, 30, 0 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 23.4% | 230 | 34 / 336 / 2,494 / 3,885 / 5,805 | 2,471 | 56.5% | 23.7% | 1,002 / 1,966 | 62.4% (187) | 61%, 24, 0 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 213 | 34 / 34 / 34 / 34 / 34 | 34 | 0.0% | 0.0% | 1,966 / 1,966 | 0.0% (n/a) | 100%, 30, 0 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 76.1% | 80 | 19 / 30 / 38 / 47 / 9,550 | 3,016 | 20.7% | 17.4% | 1,966 / 1,984 | n/a | 61%, 24, 0 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 80 | 41 / 41 / 41 / 41 / 41 | 41 | 0.0% | 0.0% | 1,959 / 1,959 | n/a | 100%, 30, 0 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 58.7% | 69 | 30 / 34 / 40 / 1,935 / 4,325 | 1,239 | 24.4% | 11.3% | 1,962 / 1,975 | 41.3% (51) | 61%, 24, 0 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 80 | 41 / 41 / 41 / 41 / 41 | 41 | 0.0% | 0.0% | 1,959 / 1,959 | 0.0% (n/a) | 100%, 30, 0 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 7397, 7397 | 26.3 | 4.48 | 0.05 | 0.00 | 4.18 | 3.17 | 1,998 | 3,167 | 77 | 20.0% | 115058, 18965 |
| 1.00 of the budget | 1 | none | benchmark | 1250, 1250 | 29.0 | 4.00 | 1.00 | 0.00 | 3.00 | 0.00 | 1,966 | 0 | n/a | 100.0% | 29, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 7397, 7397 | 19.1 | 3.34 | 0.05 | 0.00 | 2.61 | 2.14 | 1,465 | 1,936 | 77 | 20.0% | 84522, 14419 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 29.0 | 4.00 | 1.00 | 0.00 | 3.00 | 0.00 | 1,966 | 0 | n/a | 100.0% | 29, 3 |
| 1.00 of the budget | 5 | none | development | 7397, 7397 | 53.6 | 9.80 | 1.30 | 0.29 | 8.16 | 5.47 | 4,020 | 5,036 | 47 | 49.4% | 234037, 36726 |
| 1.00 of the budget | 5 | none | benchmark | 1250, 1250 | 38.0 | 9.00 | 0.00 | 0.00 | 9.00 | 1.00 | 3,399 | 1,440 | 22 | 0.0% | 38, 9 |
| 1.00 of the budget | 5 | at payout 3 | development | 7397, 7397 | 25.8 | 4.79 | 0.95 | 0.20 | 2.13 | 1.65 | 1,906 | 1,145 | 47 | 49.4% | 112610, 15412 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 38.0 | 9.00 | 0.00 | 0.00 | 9.00 | 1.00 | 3,399 | 1,440 | 22 | 0.0% | 38, 9 |

### S0r sealed brackets, flat 16:00: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 24.3% | 225 | 34 / 71 / 1,522 / 4,868 / 7,624 | 3,054 | 48.8% | 28.7% | 1,186 / 1,966 | n/a | 61%, 24, 0 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 213 | 34 / 34 / 34 / 34 / 34 | 34 | 0.0% | 0.0% | 1,966 / 1,966 | n/a | 100%, 30, 0 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 24.3% | 225 | 34 / 71 / 1,522 / 4,306 / 5,828 | 2,444 | 48.4% | 29.6% | 1,186 / 1,966 | 43.3% (177) | 61%, 24, 0 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 213 | 34 / 34 / 34 / 34 / 34 | 34 | 0.0% | 0.0% | 1,966 / 1,966 | 0.0% (n/a) | 100%, 30, 0 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 79.1% | 77 | 24 / 30 / 34 / 40 / 9,895 | 3,017 | 19.3% | 17.8% | 1,966 / 1,976 | n/a | 61%, 24, 0 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 80 | 41 / 41 / 41 / 41 / 41 | 41 | 0.0% | 0.0% | 1,959 / 1,959 | n/a | 100%, 30, 0 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 73.7% | 74 | 26 / 30 / 38 / 2,091 / 4,700 | 1,167 | 25.7% | 13.6% | 1,966 / 1,974 | 26.3% (53) | 61%, 24, 0 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 80 | 41 / 41 / 41 / 41 / 41 | 41 | 0.0% | 0.0% | 1,959 / 1,959 | 0.0% (n/a) | 100%, 30, 0 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 7397, 7397 | 25.0 | 4.30 | 0.06 | 0.00 | 3.94 | 2.33 | 1,897 | 2,951 | 103 | 32.0% | 109242, 17977 |
| 1.00 of the budget | 1 | none | benchmark | 1250, 1250 | 29.0 | 4.00 | 1.00 | 0.00 | 3.00 | 0.00 | 1,966 | 0 | n/a | 100.0% | 29, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 7397, 7397 | 19.5 | 3.50 | 0.06 | 0.00 | 2.87 | 1.62 | 1,504 | 1,948 | 103 | 32.0% | 85916, 14881 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1250, 1250 | 29.0 | 4.00 | 1.00 | 0.00 | 3.00 | 0.00 | 1,966 | 0 | n/a | 100.0% | 29, 3 |
| 1.00 of the budget | 5 | none | development | 7397, 7397 | 47.9 | 8.76 | 1.17 | 0.26 | 7.23 | 3.69 | 3,586 | 4,603 | 50 | 69.6% | 209606, 32569 |
| 1.00 of the budget | 5 | none | benchmark | 1250, 1250 | 38.0 | 9.00 | 0.00 | 0.00 | 9.00 | 1.00 | 3,399 | 1,440 | 22 | 0.0% | 38, 9 |
| 1.00 of the budget | 5 | at payout 3 | development | 7397, 7397 | 26.3 | 5.12 | 1.08 | 0.26 | 2.92 | 1.01 | 1,964 | 1,130 | 50 | 69.6% | 115365, 16763 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1250, 1250 | 38.0 | 9.00 | 0.00 | 0.00 | 9.00 | 1.00 | 3,399 | 1,440 | 22 | 0.0% | 38, 9 |

### S1 continuation only, sealed bracket: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 6.1% | 169 | 636 / 2,232 / 4,432 / 6,501 / 10,157 | 4,767 | 77.8% | 55.1% | 690 / 1,757 | n/a | 1%, 22, 36 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,767 / 6,767 / 6,767 / 6,767 / 6,767 | 6,767 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 17, 39 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 6.1% | 169 | 636 / 2,236 / 3,322 / 4,253 / 5,210 | 3,165 | 78.9% | 31.5% | 641 / 1,757 | 83.4% (156) | 1%, 22, 36 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,754 / 5,754 / 5,754 / 5,754 / 5,754 | 5,754 | 100.0% | 100.0% | 198 / 198 | 100.0% (47) | 0%, 17, 39 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 61.0% | 95 | 19 / 28 / 38 / 10,635 / 23,476 | 7,434 | 37.8% | 35.2% | 1,968 / 1,986 | n/a | 1%, 22, 36 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 26,206 / 26,206 / 26,206 / 26,206 / 26,206 | 26,206 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 17, 39 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 42.6% | 61 | 26 / 32 / 1,194 / 3,112 / 4,894 | 1,804 | 37.5% | 18.0% | 1,962 / 1,975 | 57.4% (44) | 1%, 22, 36 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,946 / 5,946 / 5,946 / 5,946 / 5,946 | 5,946 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 17, 39 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 0.7% | 218 | 1,367 / 2,302 / 3,688 / 5,527 / 9,041 | 4,389 | 78.2% | 46.1% | 579 / 1,188 | n/a | 1%, 24, 34 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 7,611 / 7,611 / 7,611 / 7,611 / 7,611 | 7,611 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 20, 35 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.7% | 218 | 1,399 / 2,013 / 3,056 / 3,922 / 4,647 | 3,032 | 75.4% | 22.5% | 576 / 1,188 | 84.5% (174) | 1%, 24, 34 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,962 / 2,962 / 2,962 / 2,962 / 2,962 | 2,962 | 100.0% | 0.0% | 198 / 198 | 100.0% (199) | 0%, 20, 35 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 52.7% | 110 | 22 / 30 / 43 / 11,843 / 25,875 | 7,913 | 45.5% | 42.5% | 1,966 / 1,987 | n/a | 1%, 24, 34 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 29,445 / 29,445 / 29,445 / 29,445 / 29,445 | 29,445 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 20, 35 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 37.4% | 82 | 30 / 34 / 1,457 / 3,225 / 4,634 | 1,870 | 41.6% | 15.7% | 1,954 / 1,974 | 62.6% (48) | 1%, 24, 34 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,176 / 4,176 / 4,176 / 4,176 / 4,176 | 4,176 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 20, 35 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.7% | 218 | 1,335 / 2,285 / 3,621 / 5,775 / 9,911 | 4,555 | 77.7% | 41.9% | 576 / 1,280 | n/a | 0%, 24, 34 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,489 / 5,489 / 5,489 / 5,489 / 5,489 | 5,489 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 20, 37 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.7% | 218 | 1,409 / 2,075 / 3,231 / 4,065 / 4,891 | 3,123 | 77.5% | 25.8% | 549 / 1,280 | 84.1% (173) | 0%, 24, 34 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,379 / 3,379 / 3,379 / 3,379 / 3,379 | 3,379 | 100.0% | 0.0% | 198 / 198 | 100.0% (179) | 0%, 20, 37 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 53.1% | 110 | 23 / 30 / 42 / 11,746 / 25,927 | 8,182 | 45.4% | 42.3% | 1,966 / 1,985 | n/a | 0%, 24, 34 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 24,479 / 24,479 / 24,479 / 24,479 / 24,479 | 24,479 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 20, 37 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 37.7% | 81 | 28 / 34 / 1,523 / 3,340 / 4,736 | 1,945 | 43.1% | 17.8% | 1,960 / 1,974 | 62.3% (48) | 0%, 24, 34 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,527 / 4,527 / 4,527 / 4,527 / 4,527 | 4,527 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 20, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3265, 3265 | 22.2 | 6.83 | 0.04 | 0.00 | 6.34 | 5.12 | 2,134 | 4,901 | 59 | 3.2% | 96725, 28987 |
| 1.00 of the budget | 1 | none | benchmark | 271, 271 | 27.0 | 11.00 | 0.00 | 0.00 | 10.00 | 8.00 | 2,962 | 7,729 | 13 | 0.0% | 27, 11 |
| 1.00 of the budget | 1 | at payout 3 | development | 3265, 3265 | 12.7 | 3.98 | 0.04 | 0.00 | 3.06 | 2.72 | 1,236 | 2,401 | 59 | 3.2% | 56092, 17368 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 4,150 | 13 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3265, 3265 | 62.7 | 17.73 | 1.54 | 0.15 | 15.39 | 11.43 | 5,578 | 11,012 | 37 | 34.6% | 274330, 69843 |
| 1.00 of the budget | 5 | none | benchmark | 271, 271 | 109.0 | 37.00 | 0.00 | 0.00 | 32.00 | 35.00 | 11,001 | 35,207 | 13 | 0.0% | 109, 35 |
| 1.00 of the budget | 5 | at payout 3 | development | 3265, 3265 | 21.1 | 6.26 | 1.03 | 0.06 | 2.72 | 2.31 | 1,857 | 1,661 | 37 | 34.6% | 92305, 20582 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 990 | 4,936 | 13 | 0.0% | 5, 4 |
| whole micros | 1 | none | development | 3265, 3265 | 16.9 | 5.60 | 0.01 | 0.00 | 5.13 | 4.82 | 1,685 | 4,074 | 66 | 3.7% | 72877, 23621 |
| whole micros | 1 | none | benchmark | 271, 271 | 15.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 1,727 | 7,338 | 13 | 0.0% | 15, 5 |
| whole micros | 1 | at payout 3 | development | 3265, 3265 | 10.4 | 3.73 | 0.01 | 0.00 | 2.80 | 2.75 | 1,085 | 2,117 | 66 | 3.7% | 46106, 16260 |
| whole micros | 1 | at payout 3 | benchmark | 271, 271 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,282 | 2,244 | 13 | 0.0% | 12, 4 |
| whole micros | 5 | none | development | 3265, 3265 | 58.3 | 17.76 | 1.55 | 0.16 | 15.29 | 13.18 | 5,390 | 11,302 | 41 | 32.3% | 253529, 69472 |
| whole micros | 5 | none | benchmark | 271, 271 | 67.0 | 32.00 | 0.00 | 0.00 | 27.00 | 42.00 | 8,345 | 35,790 | 13 | 0.0% | 67, 28 |
| whole micros | 5 | at payout 3 | development | 3265, 3265 | 19.5 | 6.05 | 0.92 | 0.11 | 2.39 | 2.48 | 1,776 | 1,646 | 41 | 32.3% | 84842, 19832 |
| whole micros | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 990 | 3,166 | 13 | 0.0% | 5, 3 |
| 0.95 of the budget | 1 | none | development | 3265, 3265 | 17.3 | 5.57 | 0.01 | 0.00 | 5.14 | 4.76 | 1,711 | 4,266 | 65 | 3.7% | 74759, 23636 |
| 0.95 of the budget | 1 | none | benchmark | 271, 271 | 17.0 | 7.00 | 0.00 | 0.00 | 6.00 | 7.00 | 1,925 | 5,414 | 13 | 0.0% | 17, 7 |
| 0.95 of the budget | 1 | at payout 3 | development | 3265, 3265 | 10.8 | 3.76 | 0.01 | 0.00 | 2.85 | 2.75 | 1,117 | 2,239 | 65 | 3.7% | 47678, 16445 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,233 | 2,612 | 13 | 0.0% | 12, 4 |
| 0.95 of the budget | 5 | none | development | 3265, 3265 | 58.6 | 17.86 | 1.54 | 0.21 | 15.42 | 12.73 | 5,418 | 11,600 | 41 | 32.2% | 254329, 70120 |
| 0.95 of the budget | 5 | none | benchmark | 271, 271 | 72.0 | 37.00 | 0.00 | 0.00 | 32.00 | 36.00 | 9,237 | 31,716 | 13 | 0.0% | 72, 33 |
| 0.95 of the budget | 5 | at payout 3 | development | 3265, 3265 | 19.6 | 6.07 | 0.96 | 0.13 | 2.41 | 2.46 | 1,782 | 1,727 | 41 | 32.2% | 85325, 19795 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 990 | 3,517 | 13 | 0.0% | 5, 3 |

### S1 continuation only, sealed bracket: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 5.9% | 168 | 765 / 2,427 / 4,156 / 6,239 / 9,630 | 4,787 | 78.1% | 53.1% | 690 / 1,578 | n/a | 1%, 22, 36 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,754 / 10,754 / 10,754 / 10,754 / 10,754 | 10,754 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 17, 39 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 5.9% | 168 | 765 / 2,510 / 3,904 / 4,600 / 5,411 | 3,490 | 78.5% | 46.3% | 690 / 1,578 | 70.7% (162) | 1%, 22, 36 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,754 / 5,754 / 5,754 / 5,754 / 5,754 | 5,754 | 100.0% | 100.0% | 198 / 198 | 100.0% (47) | 0%, 17, 39 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 60.7% | 84 | 24 / 30 / 36 / 10,570 / 29,782 | 7,907 | 35.9% | 33.7% | 1,968 / 1,978 | n/a | 1%, 22, 36 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 22,087 / 22,087 / 22,087 / 22,087 / 22,087 | 22,087 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 17, 39 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 54.7% | 77 | 26 / 30 / 40 / 4,032 / 5,575 | 1,987 | 43.1% | 25.2% | 1,966 / 1,975 | 45.3% (51) | 1%, 22, 36 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,946 / 5,946 / 5,946 / 5,946 / 5,946 | 5,946 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 17, 39 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 1.3% | 270 | 1,064 / 2,528 / 4,360 / 6,890 / 9,227 | 4,913 | 82.1% | 56.7% | 543 / 1,331 | n/a | 1%, 24, 34 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,131 / 6,131 / 6,131 / 6,131 / 6,131 | 6,131 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 20, 35 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 1.3% | 270 | 1,064 / 2,530 / 3,956 / 4,544 / 4,971 | 3,548 | 82.2% | 47.9% | 543 / 1,331 | 69.8% (177) | 1%, 24, 34 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,724 / 3,724 / 3,724 / 3,724 / 3,724 | 3,724 | 100.0% | 0.0% | 198 / 198 | 100.0% (207) | 0%, 20, 35 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 51.0% | 97 | 24 / 30 / 42 / 16,553 / 28,460 | 9,462 | 46.1% | 42.5% | 1,966 / 1,980 | n/a | 1%, 24, 34 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 30,710 / 30,710 / 30,710 / 30,710 / 30,710 | 30,710 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 20, 35 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 47.9% | 93 | 26 / 30 / 1,451 / 4,179 / 5,485 | 2,228 | 49.0% | 27.1% | 1,966 / 1,976 | 52.1% (58) | 1%, 24, 34 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,176 / 4,176 / 4,176 / 4,176 / 4,176 | 4,176 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 20, 35 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 1.5% | 282 | 965 / 2,579 / 4,448 / 7,766 / 10,046 | 5,154 | 83.4% | 56.9% | 543 / 1,358 | n/a | 0%, 24, 34 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,766 / 9,766 / 9,766 / 9,766 / 9,766 | 9,766 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 20, 37 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 1.5% | 282 | 965 / 2,581 / 4,123 / 4,737 / 5,204 | 3,669 | 83.4% | 54.5% | 543 / 1,358 | 69.9% (178) | 0%, 24, 34 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,204 / 4,204 / 4,204 / 4,204 / 4,204 | 4,204 | 100.0% | 100.0% | 198 / 198 | 100.0% (200) | 0%, 20, 37 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 51.3% | 95 | 24 / 30 / 40 / 17,381 / 31,042 | 10,049 | 45.9% | 43.3% | 1,966 / 1,980 | n/a | 0%, 24, 34 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 36,810 / 36,810 / 36,810 / 36,810 / 36,810 | 36,810 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 20, 37 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 48.1% | 91 | 26 / 30 / 1,240 / 4,197 / 5,686 | 2,251 | 48.1% | 27.4% | 1,966 / 1,976 | 51.6% (57) | 0%, 24, 34 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,527 / 4,527 / 4,527 / 4,527 / 4,527 | 4,527 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 20, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3265, 3265 | 20.5 | 6.44 | 0.04 | 0.00 | 5.90 | 3.96 | 1,989 | 4,776 | 74 | 10.2% | 89611, 27032 |
| 1.00 of the budget | 1 | none | benchmark | 271, 271 | 22.0 | 8.00 | 0.00 | 0.00 | 7.00 | 9.00 | 2,270 | 11,024 | 13 | 0.0% | 22, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 3265, 3265 | 13.2 | 4.21 | 0.04 | 0.00 | 3.34 | 2.40 | 1,292 | 2,782 | 74 | 10.2% | 58074, 18155 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 4,150 | 13 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3265, 3265 | 57.6 | 16.23 | 1.32 | 0.10 | 14.04 | 9.13 | 5,131 | 11,038 | 41 | 47.4% | 252296, 63678 |
| 1.00 of the budget | 5 | none | benchmark | 271, 271 | 107.0 | 35.00 | 0.00 | 0.00 | 30.00 | 25.00 | 10,605 | 30,692 | 13 | 0.0% | 107, 30 |
| 1.00 of the budget | 5 | at payout 3 | development | 3265, 3265 | 23.2 | 6.92 | 1.19 | 0.10 | 3.67 | 1.83 | 2,036 | 2,022 | 41 | 47.4% | 101873, 22865 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 990 | 4,936 | 13 | 0.0% | 5, 4 |
| whole micros | 1 | none | development | 3265, 3265 | 15.2 | 5.08 | 0.01 | 0.00 | 4.53 | 4.01 | 1,520 | 4,433 | 85 | 10.9% | 65967, 21065 |
| whole micros | 1 | none | benchmark | 271, 271 | 16.0 | 6.00 | 0.00 | 0.00 | 5.00 | 6.00 | 1,776 | 5,907 | 13 | 0.0% | 16, 5 |
| whole micros | 1 | at payout 3 | development | 3265, 3265 | 10.5 | 3.68 | 0.01 | 0.00 | 2.81 | 2.42 | 1,075 | 2,623 | 85 | 10.9% | 46058, 15798 |
| whole micros | 1 | at payout 3 | benchmark | 271, 271 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,282 | 3,006 | 13 | 0.0% | 12, 4 |
| whole micros | 5 | none | development | 3265, 3265 | 51.7 | 15.93 | 1.27 | 0.17 | 13.54 | 11.00 | 4,817 | 12,280 | 50 | 41.7% | 224305, 61815 |
| whole micros | 5 | none | benchmark | 271, 271 | 63.0 | 31.00 | 0.00 | 0.00 | 26.00 | 37.00 | 8,000 | 36,710 | 13 | 0.0% | 63, 26 |
| whole micros | 5 | at payout 3 | development | 3265, 3265 | 21.4 | 6.81 | 1.16 | 0.16 | 3.28 | 2.06 | 1,961 | 2,189 | 50 | 41.7% | 93851, 22180 |
| whole micros | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 990 | 3,166 | 13 | 0.0% | 5, 3 |
| 0.95 of the budget | 1 | none | development | 3265, 3265 | 15.9 | 4.89 | 0.01 | 0.00 | 4.39 | 4.01 | 1,533 | 4,687 | 85 | 10.9% | 68521, 20400 |
| 0.95 of the budget | 1 | none | benchmark | 271, 271 | 16.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 1,727 | 9,493 | 13 | 0.0% | 16, 5 |
| 0.95 of the budget | 1 | at payout 3 | development | 3265, 3265 | 10.9 | 3.57 | 0.01 | 0.00 | 2.72 | 2.42 | 1,092 | 2,761 | 85 | 10.9% | 47969, 15409 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,233 | 3,437 | 13 | 0.0% | 12, 4 |
| 0.95 of the budget | 5 | none | development | 3265, 3265 | 52.1 | 15.97 | 1.31 | 0.17 | 13.61 | 11.01 | 4,844 | 12,893 | 49 | 42.2% | 226190, 62063 |
| 0.95 of the budget | 5 | none | benchmark | 271, 271 | 65.0 | 30.00 | 0.00 | 0.00 | 25.00 | 39.00 | 7,851 | 42,661 | 13 | 0.0% | 65, 25 |
| 0.95 of the budget | 5 | at payout 3 | development | 3265, 3265 | 21.5 | 6.81 | 1.21 | 0.16 | 3.23 | 2.02 | 1,961 | 2,212 | 49 | 42.2% | 94433, 21991 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 990 | 3,517 | 13 | 0.0% | 5, 3 |

### S1 continuation only, sealed bracket: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.3% | 165 | 925 / 2,484 / 4,581 / 6,772 / 10,207 | 4,970 | 79.8% | 58.2% | 643 / 1,614 | n/a | 0%, 22, 37 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 7,121 / 7,121 / 7,121 / 7,121 / 7,121 | 7,121 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 17, 38 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.3% | 165 | 942 / 2,318 / 3,322 / 4,322 / 5,183 | 3,221 | 80.6% | 32.2% | 622 / 1,614 | 84.9% (153) | 0%, 22, 37 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,754 / 5,754 / 5,754 / 5,754 / 5,754 | 5,754 | 100.0% | 100.0% | 198 / 198 | 100.0% (47) | 0%, 17, 38 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 59.9% | 93 | 20 / 28 / 38 / 11,479 / 26,654 | 7,766 | 38.6% | 36.2% | 1,968 / 1,984 | n/a | 0%, 22, 37 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 30,435 / 30,435 / 30,435 / 30,435 / 30,435 | 30,435 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 17, 38 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 42.6% | 62 | 26 / 32 / 1,235 / 3,048 / 5,004 | 1,855 | 39.4% | 17.9% | 1,964 / 1,976 | 57.4% (43) | 0%, 22, 37 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,946 / 5,946 / 5,946 / 5,946 / 5,946 | 5,946 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 17, 38 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3265, 3265 | 21.9 | 6.82 | 0.03 | 0.00 | 6.32 | 5.26 | 2,119 | 5,090 | 58 | 3.0% | 95453, 28972 |
| 1.00 of the budget | 1 | none | benchmark | 271, 271 | 23.0 | 10.00 | 0.00 | 0.00 | 9.00 | 8.00 | 2,617 | 7,738 | 13 | 0.0% | 23, 10 |
| 1.00 of the budget | 1 | at payout 3 | development | 3265, 3265 | 12.3 | 3.94 | 0.03 | 0.00 | 3.01 | 2.75 | 1,214 | 2,435 | 58 | 3.0% | 54562, 17230 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 4,150 | 13 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3265, 3265 | 62.0 | 18.04 | 1.44 | 0.16 | 15.77 | 11.66 | 5,602 | 11,368 | 37 | 34.5% | 271067, 71553 |
| 1.00 of the budget | 5 | none | benchmark | 271, 271 | 106.0 | 36.00 | 0.00 | 0.00 | 31.00 | 39.00 | 10,656 | 39,091 | 13 | 0.0% | 106, 34 |
| 1.00 of the budget | 5 | at payout 3 | development | 3265, 3265 | 20.7 | 6.37 | 1.05 | 0.06 | 2.77 | 2.32 | 1,852 | 1,706 | 37 | 34.5% | 90804, 20985 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 990 | 4,936 | 13 | 0.0% | 5, 4 |

### S1 continuation only, sealed bracket: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.1% | 164 | 816 / 2,578 / 4,376 / 6,575 / 10,307 | 5,025 | 80.2% | 55.5% | 675 / 1,429 | n/a | 0%, 22, 37 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 11,063 / 11,063 / 11,063 / 11,063 / 11,063 | 11,063 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 17, 38 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.1% | 164 | 816 / 2,610 / 3,921 / 4,622 / 5,396 | 3,575 | 80.3% | 47.0% | 675 / 1,429 | 72.5% (159) | 0%, 22, 37 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,754 / 5,754 / 5,754 / 5,754 / 5,754 | 5,754 | 100.0% | 100.0% | 198 / 198 | 100.0% (47) | 0%, 17, 38 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 59.5% | 83 | 24 / 30 / 36 / 11,824 / 29,554 | 8,230 | 37.3% | 34.6% | 1,968 / 1,976 | n/a | 0%, 22, 37 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 30,215 / 30,215 / 30,215 / 30,215 / 30,215 | 30,215 | 100.0% | 100.0% | 990 / 990 | n/a | 0%, 17, 38 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 54.7% | 78 | 26 / 30 / 40 / 4,040 / 5,711 | 2,020 | 43.1% | 25.4% | 1,966 / 1,976 | 45.3% (50) | 0%, 22, 37 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,946 / 5,946 / 5,946 / 5,946 / 5,946 | 5,946 | 100.0% | 100.0% | 990 / 990 | 100.0% (14) | 0%, 17, 38 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3265, 3265 | 20.4 | 6.50 | 0.03 | 0.00 | 5.96 | 4.16 | 1,995 | 5,021 | 73 | 8.7% | 89161, 27353 |
| 1.00 of the budget | 1 | none | benchmark | 271, 271 | 19.0 | 7.00 | 0.00 | 0.00 | 6.00 | 9.00 | 1,974 | 11,037 | 13 | 0.0% | 19, 6 |
| 1.00 of the budget | 1 | at payout 3 | development | 3265, 3265 | 12.8 | 4.18 | 0.03 | 0.00 | 3.30 | 2.45 | 1,272 | 2,847 | 73 | 8.7% | 56597, 18066 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 271, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 4,150 | 13 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3265, 3265 | 57.0 | 16.67 | 1.30 | 0.10 | 14.46 | 9.48 | 5,173 | 11,404 | 41 | 47.3% | 249643, 65604 |
| 1.00 of the budget | 5 | none | benchmark | 271, 271 | 101.0 | 32.00 | 0.00 | 0.00 | 27.00 | 32.00 | 9,815 | 38,030 | 13 | 0.0% | 101, 27 |
| 1.00 of the budget | 5 | at payout 3 | development | 3265, 3265 | 22.8 | 7.00 | 1.22 | 0.10 | 3.73 | 1.84 | 2,029 | 2,048 | 41 | 47.3% | 100429, 23291 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 271, 271 | 5.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 990 | 4,936 | 13 | 0.0% | 5, 4 |

### S2 continuation + A+ reversion, sealed bracket: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 7.9% | 198 | 461 / 1,491 / 3,870 / 6,552 / 8,624 | 4,296 | 69.9% | 48.6% | 709 / 1,820 | n/a | 3%, 22, 30 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,642 / 12,642 / 12,642 / 12,642 / 12,642 | 12,642 | 100.0% | 100.0% | 247 / 247 | n/a | 18%, 16, 21 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 7.9% | 198 | 461 / 1,953 / 3,067 / 4,089 / 5,174 | 2,995 | 74.4% | 26.7% | 690 / 1,820 | 83.9% (163) | 3%, 22, 30 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,840 / 3,840 / 3,840 / 3,840 / 3,840 | 3,840 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 18%, 16, 21 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 64.5% | 82 | 18 / 30 / 36 / 8,828 / 25,522 | 6,736 | 34.3% | 31.1% | 1,966 / 1,986 | n/a | 3%, 22, 30 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 101 | 4 / 4 / 4 / 4 / 4 | 4 | 0.0% | 0.0% | 1,996 / 1,996 | n/a | 18%, 16, 21 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 45.8% | 60 | 28 / 32 / 876 / 3,175 / 4,745 | 1,725 | 36.5% | 15.2% | 1,964 / 1,974 | 54.2% (44) | 3%, 22, 30 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 101 | 4 / 4 / 4 / 4 / 4 | 4 | 0.0% | 0.0% | 1,996 / 1,996 | 0.0% (n/a) | 18%, 16, 21 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 3.9% | 224 | 832 / 1,683 / 3,111 / 4,403 / 7,294 | 3,637 | 66.9% | 34.3% | 609 / 1,646 | n/a | 2%, 24, 31 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,778 / 10,778 / 10,778 / 10,778 / 10,778 | 10,778 | 100.0% | 100.0% | 247 / 247 | n/a | 13%, 19, 20 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 3.9% | 224 | 912 / 1,719 / 2,819 / 3,693 / 4,297 | 2,714 | 67.9% | 16.0% | 604 / 1,646 | 76.1% (184) | 2%, 24, 31 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,783 / 3,783 / 3,783 / 3,783 / 3,783 | 3,783 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 13%, 19, 20 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 61.1% | 103 | 18 / 30 / 37 / 7,170 / 19,494 | 5,696 | 35.7% | 32.2% | 1,966 / 1,985 | n/a | 2%, 24, 31 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 20 / 20 / 20 / 20 / 20 | 20 | 0.0% | 0.0% | 1,980 / 1,980 | n/a | 13%, 19, 20 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 43.6% | 77 | 29 / 33 / 953 / 2,988 / 4,385 | 1,654 | 34.6% | 13.5% | 1,962 / 1,974 | 56.4% (48) | 2%, 24, 31 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 20 / 20 / 20 / 20 / 20 | 20 | 0.0% | 0.0% | 1,980 / 1,980 | 0.0% (n/a) | 13%, 19, 20 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.2% | 228 | 1,085 / 1,765 / 3,178 / 4,668 / 8,270 | 3,918 | 69.4% | 34.6% | 630 / 1,476 | n/a | 1%, 23, 29 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,684 / 12,684 / 12,684 / 12,684 / 12,684 | 12,684 | 100.0% | 100.0% | 247 / 247 | n/a | 11%, 16, 23 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.2% | 228 | 1,063 / 1,895 / 2,896 / 3,727 / 4,546 | 2,870 | 72.7% | 20.3% | 592 / 1,476 | 80.1% (183) | 1%, 23, 29 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,931 / 3,931 / 3,931 / 3,931 / 3,931 | 3,931 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 11%, 16, 23 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 59.8% | 102 | 23 / 30 / 38 / 8,458 / 21,061 | 6,253 | 38.0% | 33.7% | 1,966 / 1,981 | n/a | 1%, 23, 29 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 16 / 16 / 16 / 16 / 16 | 16 | 0.0% | 0.0% | 1,984 / 1,984 | n/a | 11%, 16, 23 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 43.2% | 76 | 28 / 34 / 1,051 / 3,195 / 4,585 | 1,760 | 36.5% | 14.8% | 1,962 / 1,975 | 56.8% (47) | 1%, 23, 29 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 16 / 16 / 16 / 16 / 16 | 16 | 0.0% | 0.0% | 1,984 / 1,984 | 0.0% (n/a) | 11%, 16, 23 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4038, 4038 | 23.2 | 6.36 | 0.04 | 0.00 | 5.91 | 4.77 | 2,123 | 4,419 | 60 | 4.7% | 101246, 26994 |
| 1.00 of the budget | 1 | none | benchmark | 480, 480 | 28.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 2,266 | 12,908 | 14 | 0.0% | 28, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 4038, 4038 | 14.0 | 4.04 | 0.04 | 0.00 | 3.13 | 2.71 | 1,316 | 2,311 | 60 | 4.7% | 62261, 17656 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 27.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 2,068 | 3,908 | 14 | 0.0% | 27, 5 |
| 1.00 of the budget | 5 | none | development | 4038, 4038 | 60.7 | 15.57 | 1.45 | 0.14 | 13.50 | 10.52 | 5,185 | 9,921 | 39 | 38.2% | 265831, 61008 |
| 1.00 of the budget | 5 | none | benchmark | 480, 480 | 50.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,685 | 2,689 | 14 | 0.0% | 50, 15 |
| 1.00 of the budget | 5 | at payout 3 | development | 4038, 4038 | 21.8 | 5.92 | 1.01 | 0.06 | 2.53 | 2.18 | 1,845 | 1,569 | 39 | 38.2% | 95517, 19349 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 50.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,685 | 2,689 | 14 | 0.0% | 50, 15 |
| whole micros | 1 | none | development | 4038, 4038 | 19.0 | 5.87 | 0.02 | 0.00 | 5.43 | 4.09 | 1,843 | 3,480 | 66 | 6.1% | 82388, 24807 |
| whole micros | 1 | none | benchmark | 480, 480 | 24.0 | 6.00 | 0.00 | 0.00 | 5.00 | 7.00 | 2,070 | 10,848 | 14 | 0.0% | 24, 5 |
| whole micros | 1 | at payout 3 | development | 4038, 4038 | 13.1 | 4.28 | 0.02 | 0.00 | 3.40 | 2.61 | 1,306 | 2,020 | 66 | 6.1% | 58004, 18556 |
| whole micros | 1 | at payout 3 | benchmark | 480, 480 | 23.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,872 | 3,655 | 14 | 0.0% | 23, 5 |
| whole micros | 5 | none | development | 4038, 4038 | 55.0 | 15.66 | 1.55 | 0.21 | 13.42 | 10.28 | 4,938 | 8,634 | 41 | 36.1% | 239279, 60689 |
| whole micros | 5 | none | benchmark | 480, 480 | 47.0 | 13.00 | 0.00 | 0.00 | 13.00 | 2.00 | 4,289 | 2,309 | 14 | 0.0% | 47, 13 |
| whole micros | 5 | at payout 3 | development | 4038, 4038 | 20.6 | 6.00 | 0.98 | 0.14 | 2.58 | 2.23 | 1,823 | 1,478 | 41 | 36.1% | 89902, 19663 |
| whole micros | 5 | at payout 3 | benchmark | 480, 480 | 47.0 | 13.00 | 0.00 | 0.00 | 13.00 | 2.00 | 4,289 | 2,309 | 14 | 0.0% | 47, 13 |
| 0.95 of the budget | 1 | none | development | 4038, 4038 | 19.5 | 5.66 | 0.02 | 0.00 | 5.26 | 4.20 | 1,848 | 3,765 | 65 | 6.1% | 84565, 24067 |
| 0.95 of the budget | 1 | none | benchmark | 480, 480 | 25.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 2,119 | 12,803 | 14 | 0.0% | 25, 5 |
| 0.95 of the budget | 1 | at payout 3 | development | 4038, 4038 | 13.1 | 4.03 | 0.02 | 0.00 | 3.15 | 2.65 | 1,276 | 2,147 | 65 | 6.1% | 57897, 17585 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 23.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,872 | 3,803 | 14 | 0.0% | 23, 5 |
| 0.95 of the budget | 5 | none | development | 4038, 4038 | 56.5 | 15.88 | 1.48 | 0.25 | 13.72 | 10.57 | 5,054 | 9,307 | 41 | 35.8% | 245201, 62088 |
| 0.95 of the budget | 5 | none | benchmark | 480, 480 | 46.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,538 | 2,554 | 14 | 0.0% | 46, 15 |
| 0.95 of the budget | 5 | at payout 3 | development | 4038, 4038 | 20.7 | 5.93 | 0.97 | 0.16 | 2.50 | 2.25 | 1,817 | 1,577 | 41 | 35.8% | 90029, 19454 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 46.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,538 | 2,554 | 14 | 0.0% | 46, 15 |

### S2 continuation + A+ reversion, sealed bracket: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 7.1% | 190 | 716 / 1,986 / 3,799 / 6,797 / 8,510 | 4,358 | 73.9% | 46.5% | 692 / 1,687 | n/a | 3%, 22, 30 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,642 / 12,642 / 12,642 / 12,642 / 12,642 | 12,642 | 100.0% | 100.0% | 247 / 247 | n/a | 18%, 16, 21 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 7.1% | 190 | 716 / 2,060 / 3,526 / 4,350 / 5,244 | 3,262 | 75.9% | 37.5% | 692 / 1,687 | 72.1% (178) | 3%, 22, 30 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,840 / 3,840 / 3,840 / 3,840 / 3,840 | 3,840 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 18%, 16, 21 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 66.0% | 78 | 26 / 30 / 34 / 7,318 / 27,009 | 6,537 | 30.4% | 28.4% | 1,968 / 1,976 | n/a | 3%, 22, 30 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 101 | 4 / 4 / 4 / 4 / 4 | 4 | 0.0% | 0.0% | 1,996 / 1,996 | n/a | 18%, 16, 21 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 58.5% | 70 | 26 / 30 / 36 / 3,683 / 5,112 | 1,740 | 38.1% | 20.2% | 1,966 / 1,975 | 41.5% (52) | 3%, 22, 30 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 101 | 4 / 4 / 4 / 4 / 4 | 4 | 0.0% | 0.0% | 1,996 / 1,996 | 0.0% (n/a) | 18%, 16, 21 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 4.1% | 228 | 1,036 / 1,591 / 3,272 / 5,522 / 8,349 | 4,035 | 68.5% | 42.6% | 643 / 1,480 | n/a | 2%, 24, 31 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,778 / 10,778 / 10,778 / 10,778 / 10,778 | 10,778 | 100.0% | 100.0% | 247 / 247 | n/a | 13%, 19, 20 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.1% | 228 | 1,036 / 1,604 / 3,405 / 4,175 / 4,980 | 3,050 | 68.5% | 32.2% | 643 / 1,480 | 57.6% (182) | 2%, 24, 31 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,783 / 3,783 / 3,783 / 3,783 / 3,783 | 3,783 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 13%, 19, 20 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 61.1% | 96 | 22 / 30 / 36 / 8,468 / 21,287 | 6,283 | 36.0% | 32.5% | 1,968 / 1,980 | n/a | 2%, 24, 31 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 20 / 20 / 20 / 20 / 20 | 20 | 0.0% | 0.0% | 1,980 / 1,980 | n/a | 13%, 19, 20 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 56.5% | 90 | 24 / 30 / 38 / 3,709 / 5,303 | 1,831 | 39.0% | 21.7% | 1,966 / 1,978 | 43.5% (57) | 2%, 24, 31 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 20 / 20 / 20 / 20 / 20 | 20 | 0.0% | 0.0% | 1,980 / 1,980 | 0.0% (n/a) | 13%, 19, 20 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.1% | 228 | 916 / 2,081 / 3,315 / 5,791 / 8,726 | 4,245 | 76.0% | 41.6% | 639 / 1,409 | n/a | 1%, 23, 29 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,684 / 12,684 / 12,684 / 12,684 / 12,684 | 12,684 | 100.0% | 100.0% | 247 / 247 | n/a | 11%, 16, 23 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.1% | 228 | 916 / 2,081 / 3,464 / 4,281 / 5,245 | 3,237 | 75.9% | 37.1% | 639 / 1,409 | 63.4% (182) | 1%, 23, 29 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,931 / 3,931 / 3,931 / 3,931 / 3,931 | 3,931 | 100.0% | 0.0% | 247 / 247 | 100.0% (199) | 11%, 16, 23 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 57.7% | 90 | 24 / 30 / 38 / 9,614 / 27,275 | 7,360 | 39.6% | 34.6% | 1,968 / 1,978 | n/a | 1%, 23, 29 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 16 / 16 / 16 / 16 / 16 | 16 | 0.0% | 0.0% | 1,984 / 1,984 | n/a | 11%, 16, 23 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 54.0% | 86 | 26 / 30 / 40 / 3,868 / 5,508 | 1,977 | 41.1% | 23.0% | 1,966 / 1,976 | 45.7% (57) | 1%, 23, 29 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 100.0% | 107 | 16 / 16 / 16 / 16 / 16 | 16 | 0.0% | 0.0% | 1,984 / 1,984 | 0.0% (n/a) | 11%, 16, 23 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4038, 4038 | 22.1 | 6.25 | 0.03 | 0.00 | 5.75 | 3.79 | 2,045 | 4,403 | 77 | 11.0% | 96398, 26279 |
| 1.00 of the budget | 1 | none | benchmark | 480, 480 | 28.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 2,266 | 12,908 | 14 | 0.0% | 28, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 4038, 4038 | 15.0 | 4.29 | 0.03 | 0.00 | 3.42 | 2.42 | 1,397 | 2,659 | 77 | 11.0% | 66091, 18562 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 27.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 2,068 | 3,908 | 14 | 0.0% | 27, 5 |
| 1.00 of the budget | 5 | none | development | 4038, 4038 | 54.5 | 14.30 | 1.39 | 0.11 | 12.26 | 7.78 | 4,690 | 9,227 | 42 | 52.7% | 238780, 55348 |
| 1.00 of the budget | 5 | none | benchmark | 480, 480 | 50.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,685 | 2,689 | 14 | 0.0% | 50, 15 |
| 1.00 of the budget | 5 | at payout 3 | development | 4038, 4038 | 23.7 | 6.53 | 1.18 | 0.10 | 3.54 | 1.63 | 2,009 | 1,749 | 42 | 52.7% | 103890, 21549 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 50.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,685 | 2,689 | 14 | 0.0% | 50, 15 |
| whole micros | 1 | none | development | 4038, 4038 | 17.8 | 5.36 | 0.02 | 0.00 | 4.86 | 3.32 | 1,702 | 3,737 | 88 | 11.7% | 77350, 22356 |
| whole micros | 1 | none | benchmark | 480, 480 | 24.0 | 6.00 | 0.00 | 0.00 | 5.00 | 7.00 | 2,070 | 10,848 | 14 | 0.0% | 24, 5 |
| whole micros | 1 | at payout 3 | development | 4038, 4038 | 13.9 | 4.30 | 0.02 | 0.00 | 3.53 | 2.24 | 1,347 | 2,398 | 88 | 11.7% | 61034, 18442 |
| whole micros | 1 | at payout 3 | benchmark | 480, 480 | 23.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,872 | 3,655 | 14 | 0.0% | 23, 5 |
| whole micros | 5 | none | development | 4038, 4038 | 50.2 | 13.86 | 1.35 | 0.22 | 11.74 | 7.79 | 4,456 | 8,739 | 50 | 46.7% | 218429, 53169 |
| whole micros | 5 | none | benchmark | 480, 480 | 47.0 | 13.00 | 0.00 | 0.00 | 13.00 | 2.00 | 4,289 | 2,309 | 14 | 0.0% | 47, 13 |
| whole micros | 5 | at payout 3 | development | 4038, 4038 | 23.1 | 6.75 | 1.22 | 0.20 | 3.58 | 1.77 | 2,039 | 1,870 | 50 | 46.7% | 101343, 22107 |
| whole micros | 5 | at payout 3 | benchmark | 480, 480 | 47.0 | 13.00 | 0.00 | 0.00 | 13.00 | 2.00 | 4,289 | 2,309 | 14 | 0.0% | 47, 13 |
| 0.95 of the budget | 1 | none | development | 4038, 4038 | 18.3 | 5.23 | 0.02 | 0.00 | 4.78 | 3.38 | 1,720 | 3,964 | 85 | 11.7% | 79459, 21956 |
| 0.95 of the budget | 1 | none | benchmark | 480, 480 | 25.0 | 6.00 | 0.00 | 0.00 | 5.00 | 8.00 | 2,119 | 12,803 | 14 | 0.0% | 25, 5 |
| 0.95 of the budget | 1 | at payout 3 | development | 4038, 4038 | 13.7 | 4.03 | 0.02 | 0.00 | 3.23 | 2.31 | 1,303 | 2,540 | 85 | 11.7% | 60111, 17374 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 23.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,872 | 3,803 | 14 | 0.0% | 23, 5 |
| 0.95 of the budget | 5 | none | development | 4038, 4038 | 52.2 | 14.29 | 1.33 | 0.20 | 12.15 | 8.64 | 4,620 | 9,980 | 49 | 45.8% | 226758, 55067 |
| 0.95 of the budget | 5 | none | benchmark | 480, 480 | 46.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,538 | 2,554 | 14 | 0.0% | 46, 15 |
| 0.95 of the budget | 5 | at payout 3 | development | 4038, 4038 | 23.2 | 6.68 | 1.21 | 0.19 | 3.42 | 1.87 | 2,034 | 2,011 | 49 | 45.8% | 101718, 21976 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 46.0 | 15.00 | 0.00 | 0.00 | 15.00 | 2.00 | 4,538 | 2,554 | 14 | 0.0% | 46, 15 |

### S2 continuation + A+ reversion, sealed bracket: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.9% | 194 | 827 / 2,019 / 3,843 / 5,984 / 9,284 | 4,445 | 75.4% | 49.1% | 688 / 1,622 | n/a | 2%, 22, 31 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 14,819 / 14,819 / 14,819 / 14,819 / 14,819 | 14,819 | 100.0% | 100.0% | 247 / 247 | n/a | 12%, 19, 16 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.9% | 194 | 976 / 2,029 / 3,274 / 4,163 / 4,975 | 3,079 | 75.7% | 27.6% | 641 / 1,622 | 83.6% (178) | 2%, 22, 31 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,338 / 3,338 / 3,338 / 3,338 / 3,338 | 3,338 | 100.0% | 0.0% | 247 / 247 | 100.0% (136) | 12%, 19, 16 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 62.4% | 94 | 18 / 30 / 37 / 10,139 / 25,638 | 7,214 | 36.7% | 34.2% | 1,966 / 1,986 | n/a | 2%, 22, 31 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 124 | 31 / 31 / 31 / 31 / 31 | 31 | 0.0% | 0.0% | 1,969 / 1,969 | n/a | 12%, 19, 16 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 43.8% | 67 | 28 / 34 / 1,024 / 3,066 / 4,897 | 1,791 | 37.1% | 15.4% | 1,962 / 1,974 | 56.2% (45) | 2%, 22, 31 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,232 / 3,232 / 3,232 / 3,232 / 3,232 | 3,232 | 100.0% | 0.0% | 1,088 / 1,088 | 100.0% (43) | 12%, 19, 16 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4038, 4038 | 22.6 | 5.91 | 0.02 | 0.00 | 5.49 | 4.69 | 2,030 | 4,476 | 62 | 3.7% | 98237, 25136 |
| 1.00 of the budget | 1 | none | benchmark | 480, 480 | 23.0 | 6.00 | 0.00 | 0.00 | 5.00 | 10.00 | 2,021 | 14,840 | 14 | 0.0% | 23, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 4038, 4038 | 14.7 | 4.00 | 0.02 | 0.00 | 3.10 | 2.74 | 1,348 | 2,427 | 62 | 3.7% | 64959, 17513 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 13.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,233 | 2,571 | 14 | 0.0% | 13, 4 |
| 1.00 of the budget | 5 | none | development | 4038, 4038 | 61.3 | 15.85 | 1.45 | 0.15 | 13.74 | 10.98 | 5,259 | 10,474 | 40 | 35.8% | 267847, 62242 |
| 1.00 of the budget | 5 | none | benchmark | 480, 480 | 61.0 | 16.00 | 1.00 | 0.00 | 15.00 | 3.00 | 5,224 | 3,255 | 14 | 0.0% | 61, 15 |
| 1.00 of the budget | 5 | at payout 3 | development | 4038, 4038 | 22.5 | 6.06 | 1.04 | 0.06 | 2.59 | 2.27 | 1,898 | 1,690 | 40 | 35.8% | 98342, 19825 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 20.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 2,023 | 3,255 | 14 | 0.0% | 16, 7 |

### S2 continuation + A+ reversion, sealed bracket: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 4.3% | 188 | 865 / 2,078 / 3,872 / 6,470 / 9,379 | 4,566 | 76.4% | 47.3% | 643 / 1,430 | n/a | 2%, 22, 31 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 15,716 / 15,716 / 15,716 / 15,716 / 15,716 | 15,716 | 100.0% | 100.0% | 247 / 247 | n/a | 12%, 19, 16 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 4.3% | 188 | 865 / 2,078 / 3,736 / 4,435 / 5,092 | 3,344 | 76.4% | 40.9% | 643 / 1,430 | 69.6% (190) | 2%, 22, 31 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,234 / 4,234 / 4,234 / 4,234 / 4,234 | 4,234 | 100.0% | 100.0% | 247 / 247 | 100.0% (136) | 12%, 19, 16 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 63.6% | 85 | 24 / 30 / 36 / 9,636 / 27,414 | 7,225 | 33.0% | 31.5% | 1,968 / 1,978 | n/a | 2%, 22, 31 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 22,736 / 22,736 / 22,736 / 22,736 / 22,736 | 22,736 | 100.0% | 100.0% | 1,978 / 1,978 | n/a | 12%, 19, 16 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 57.0% | 79 | 26 / 30 / 38 / 3,801 / 5,425 | 1,855 | 39.1% | 21.8% | 1,966 / 1,976 | 43.0% (52) | 2%, 22, 31 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,830 / 3,830 / 3,830 / 3,830 / 3,830 | 3,830 | 100.0% | 0.0% | 1,088 / 1,088 | 100.0% (44) | 12%, 19, 16 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4038, 4038 | 21.5 | 5.73 | 0.02 | 0.00 | 5.27 | 3.78 | 1,945 | 4,511 | 77 | 9.9% | 93779, 24148 |
| 1.00 of the budget | 1 | none | benchmark | 480, 480 | 23.0 | 6.00 | 0.00 | 0.00 | 5.00 | 10.00 | 2,021 | 15,737 | 14 | 0.0% | 23, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 4038, 4038 | 15.8 | 4.31 | 0.02 | 0.00 | 3.47 | 2.43 | 1,444 | 2,788 | 77 | 9.9% | 69584, 18636 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 480, 480 | 13.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,233 | 3,467 | 14 | 0.0% | 13, 4 |
| 1.00 of the budget | 5 | none | development | 4038, 4038 | 54.9 | 14.31 | 1.42 | 0.12 | 12.19 | 8.26 | 4,714 | 9,939 | 43 | 50.2% | 240084, 55179 |
| 1.00 of the budget | 5 | none | benchmark | 480, 480 | 120.0 | 33.00 | 2.00 | 0.00 | 26.00 | 21.00 | 10,695 | 31,431 | 14 | 0.0% | 120, 26 |
| 1.00 of the budget | 5 | at payout 3 | development | 4038, 4038 | 24.3 | 6.71 | 1.25 | 0.11 | 3.60 | 1.75 | 2,063 | 1,919 | 43 | 50.2% | 106792, 22159 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 480, 480 | 20.0 | 9.00 | 0.00 | 0.00 | 6.00 | 3.00 | 2,321 | 4,151 | 14 | 0.0% | 18, 7 |

### S3 continuation only, walk-forward ATR bracket: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,764 / 2,927 / 4,594 / 6,690 / 9,649 | 5,182 | 88.1% | 62.4% | 575 / 1,080 | n/a | 0%, 25, 32 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,621 / 3,621 / 3,621 / 3,621 / 3,621 | 3,621 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,519 / 2,403 / 3,297 / 3,977 / 4,765 | 3,253 | 85.1% | 24.5% | 551 / 1,080 | 91.1% (152) | 0%, 25, 32 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,460 / 4,460 / 4,460 / 4,460 / 4,460 | 4,460 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 23, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 52.1% | 98 | 22 / 31 / 42 / 17,647 / 31,146 | 10,095 | 47.2% | 44.9% | 1,965 / 1,982 | n/a | 0%, 25, 32 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,619 / 9,619 / 9,619 / 9,619 / 9,619 | 9,619 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 38.2% | 84 | 30 / 35 / 1,568 / 3,067 / 4,883 | 1,869 | 41.3% | 16.4% | 1,960 / 1,974 | 61.8% (46) | 0%, 25, 32 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,754 / 3,754 / 3,754 / 3,754 / 3,754 | 3,754 | 100.0% | 0.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 23, 33 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,273 / 2,509 / 3,967 / 5,917 / 8,094 | 4,509 | 83.7% | 49.8% | 494 / 982 | n/a | 0%, 28, 32 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,004 / 5,004 / 5,004 / 5,004 / 5,004 | 5,004 | 100.0% | 100.0% | 198 / 198 | n/a | 3%, 28, 28 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,273 / 2,402 / 2,963 / 3,918 / 4,557 | 3,091 | 82.5% | 22.5% | 494 / 982 | 85.9% (155) | 0%, 28, 32 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,941 / 3,941 / 3,941 / 3,941 / 3,941 | 3,941 | 100.0% | 0.0% | 198 / 198 | 100.0% (49) | 3%, 28, 28 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 43.4% | 119 | 25 / 32 / 6,147 / 17,515 / 28,117 | 10,260 | 54.6% | 52.6% | 1,960 / 1,979 | n/a | 0%, 28, 32 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 11,890 / 11,890 / 11,890 / 11,890 / 11,890 | 11,890 | 100.0% | 100.0% | 1,137 / 1,137 | n/a | 3%, 28, 28 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 32.5% | 100 | 30 / 39 / 1,863 / 3,028 / 4,450 | 1,930 | 46.9% | 13.7% | 1,815 / 1,974 | 67.5% (49) | 0%, 28, 32 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,892 / 3,892 / 3,892 / 3,892 / 3,892 | 3,892 | 100.0% | 0.0% | 1,137 / 1,137 | 100.0% (33) | 3%, 28, 28 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,629 / 2,383 / 3,934 / 6,175 / 8,926 | 4,749 | 84.0% | 48.7% | 494 / 974 | n/a | 0%, 27, 32 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,739 / 3,739 / 3,739 / 3,739 / 3,739 | 3,739 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 24, 36 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,697 / 2,372 / 3,079 / 4,007 / 4,800 | 3,191 | 83.7% | 25.1% | 494 / 974 | 88.4% (155) | 0%, 27, 32 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,331 / 4,331 / 4,331 / 4,331 / 4,331 | 4,331 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 24, 36 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 45.3% | 111 | 24 / 32 / 5,032 / 17,719 / 28,920 | 10,574 | 53.3% | 51.3% | 1,960 / 1,983 | n/a | 0%, 27, 32 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,652 / 9,652 / 9,652 / 9,652 / 9,652 | 9,652 | 100.0% | 100.0% | 1,533 / 1,533 | n/a | 0%, 24, 36 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 34.7% | 97 | 27 / 36 / 1,945 / 3,149 / 4,573 | 1,986 | 48.8% | 15.6% | 1,874 / 1,976 | 65.3% (49) | 0%, 27, 32 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,660 / 3,660 / 3,660 / 3,660 / 3,660 | 3,660 | 100.0% | 0.0% | 1,533 / 1,533 | 100.0% (33) | 0%, 24, 36 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3139, 3139 | 17.5 | 5.40 | 0.00 | 0.00 | 4.87 | 5.65 | 1,694 | 4,875 | 60 | 0.0% | 76098, 22811 |
| 1.00 of the budget | 1 | none | benchmark | 227, 227 | 13.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 1,927 | 3,548 | 26 | 0.0% | 13, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 3139, 3139 | 10.5 | 3.13 | 0.00 | 0.00 | 2.18 | 2.88 | 1,001 | 2,254 | 60 | 0.0% | 46695, 13761 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 6.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,088 | 3,548 | 26 | 0.0% | 6, 5 |
| 1.00 of the budget | 5 | none | development | 3139, 3139 | 55.2 | 16.34 | 1.41 | 0.12 | 13.85 | 14.98 | 5,033 | 13,128 | 42 | 27.0% | 240561, 63960 |
| 1.00 of the budget | 5 | none | benchmark | 227, 227 | 96.0 | 33.00 | 0.00 | 0.00 | 28.00 | 17.00 | 9,768 | 17,387 | 26 | 0.0% | 96, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 3139, 3139 | 20.5 | 5.99 | 1.09 | 0.05 | 2.18 | 2.56 | 1,779 | 1,648 | 42 | 27.0% | 89890, 19302 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 3,434 | 26 | 0.0% | 13, 6 |
| whole micros | 1 | none | development | 3139, 3123 | 13.9 | 4.58 | 0.00 | 0.00 | 4.04 | 5.14 | 1,406 | 3,915 | 61 | 3.0% | 59839, 19141 |
| whole micros | 1 | none | benchmark | 227, 185 | 5.0 | 4.00 | 0.00 | 0.00 | 3.00 | 6.00 | 890 | 3,894 | 23 | 0.0% | 5, 4 |
| whole micros | 1 | at payout 3 | development | 3139, 3123 | 8.7 | 2.88 | 0.00 | 0.00 | 1.96 | 2.75 | 883 | 1,974 | 61 | 3.0% | 38560, 12612 |
| whole micros | 1 | at payout 3 | benchmark | 227, 185 | 1.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 198 | 2,139 | 23 | 0.0% | 1, 1 |
| whole micros | 5 | none | development | 3139, 3123 | 50.6 | 16.44 | 1.29 | 0.15 | 13.73 | 17.00 | 4,899 | 13,159 | 45 | 24.4% | 219152, 64096 |
| whole micros | 5 | none | benchmark | 227, 185 | 54.0 | 17.00 | 0.00 | 0.00 | 14.00 | 22.00 | 5,865 | 15,755 | 23 | 0.0% | 52, 15 |
| whole micros | 5 | at payout 3 | development | 3139, 3123 | 18.6 | 5.85 | 0.97 | 0.10 | 1.92 | 2.77 | 1,703 | 1,632 | 45 | 24.4% | 80925, 18934 |
| whole micros | 5 | at payout 3 | benchmark | 227, 185 | 8.0 | 5.00 | 0.00 | 0.00 | 0.00 | 5.00 | 1,137 | 3,029 | 23 | 0.0% | 8, 3 |
| 0.95 of the budget | 1 | none | development | 3139, 3139 | 14.6 | 4.73 | 0.00 | 0.00 | 4.23 | 5.23 | 1,467 | 4,216 | 62 | 3.0% | 62901, 19885 |
| 0.95 of the budget | 1 | none | benchmark | 227, 227 | 10.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,631 | 3,370 | 26 | 0.0% | 10, 6 |
| 0.95 of the budget | 1 | at payout 3 | development | 3139, 3139 | 9.0 | 2.81 | 0.00 | 0.00 | 1.89 | 2.77 | 889 | 2,080 | 62 | 3.0% | 39530, 12391 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 5.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,039 | 3,370 | 26 | 0.0% | 5, 5 |
| 0.95 of the budget | 5 | none | development | 3139, 3139 | 51.4 | 16.90 | 1.33 | 0.16 | 14.29 | 16.15 | 5,000 | 13,575 | 44 | 25.1% | 222553, 66044 |
| 0.95 of the budget | 5 | none | benchmark | 227, 227 | 71.0 | 32.00 | 0.00 | 0.00 | 27.00 | 17.00 | 8,492 | 16,144 | 26 | 0.0% | 71, 27 |
| 0.95 of the budget | 5 | at payout 3 | development | 3139, 3139 | 19.0 | 5.95 | 0.99 | 0.11 | 2.10 | 2.72 | 1,732 | 1,718 | 44 | 25.1% | 82497, 19512 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 10.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,533 | 3,193 | 26 | 0.0% | 10, 6 |

### S3 continuation only, walk-forward ATR bracket: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,430 / 3,734 / 5,275 / 7,853 / 10,413 | 5,740 | 87.7% | 71.9% | 641 / 1,327 | n/a | 0%, 25, 32 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,861 / 3,861 / 3,861 / 3,861 / 3,861 | 3,861 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,430 / 3,502 / 4,046 / 4,579 / 5,086 | 3,819 | 87.7% | 52.4% | 641 / 1,327 | 84.7% (158) | 0%, 25, 32 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,700 / 4,700 / 4,700 / 4,700 / 4,700 | 4,700 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 23, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 51.0% | 90 | 28 / 30 / 40 / 18,853 / 34,550 | 11,252 | 47.5% | 46.3% | 1,966 / 1,974 | n/a | 0%, 25, 32 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,501 / 9,501 / 9,501 / 9,501 / 9,501 | 9,501 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 48.6% | 88 | 28 / 30 / 1,595 / 4,354 / 5,719 | 2,218 | 47.6% | 28.4% | 1,966 / 1,974 | 51.4% (55) | 0%, 25, 32 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,113 / 5,113 / 5,113 / 5,113 / 5,113 | 5,113 | 100.0% | 100.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 23, 33 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,261 / 3,333 / 4,780 / 7,002 / 8,696 | 5,114 | 85.3% | 60.5% | 541 / 1,135 | n/a | 0%, 28, 32 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,866 / 3,866 / 3,866 / 3,866 / 3,866 | 3,866 | 100.0% | 0.0% | 198 / 198 | n/a | 3%, 28, 28 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,261 / 3,433 / 4,061 / 4,565 / 5,193 | 3,780 | 85.3% | 54.5% | 541 / 1,135 | 78.0% (172) | 0%, 28, 32 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,456 / 4,456 / 4,456 / 4,456 / 4,456 | 4,456 | 100.0% | 100.0% | 198 / 198 | 100.0% (154) | 3%, 28, 28 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 45.3% | 107 | 28 / 30 / 6,780 / 20,964 / 31,039 | 11,917 | 53.6% | 52.3% | 1,962 / 1,974 | n/a | 0%, 28, 32 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,259 / 10,259 / 10,259 / 10,259 / 10,259 | 10,259 | 100.0% | 100.0% | 1,137 / 1,137 | n/a | 3%, 28, 28 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 43.0% | 104 | 28 / 30 / 1,950 / 4,228 / 5,474 | 2,267 | 49.6% | 26.9% | 1,962 / 1,974 | 57.0% (67) | 0%, 28, 32 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,604 / 5,604 / 5,604 / 5,604 / 5,604 | 5,604 | 100.0% | 100.0% | 1,137 / 1,137 | 100.0% (34) | 3%, 28, 28 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,210 / 3,155 / 4,759 / 7,279 / 9,116 | 5,235 | 84.2% | 59.1% | 541 / 1,231 | n/a | 0%, 27, 32 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,967 / 3,967 / 3,967 / 3,967 / 3,967 | 3,967 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 24, 36 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,210 / 3,036 / 4,112 / 4,643 / 5,237 | 3,736 | 84.2% | 56.8% | 541 / 1,231 | 76.3% (170) | 0%, 27, 32 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,559 / 4,559 / 4,559 / 4,559 / 4,559 | 4,559 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 24, 36 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 45.7% | 103 | 26 / 30 / 7,176 / 21,719 / 31,673 | 12,198 | 53.7% | 52.6% | 1,962 / 1,976 | n/a | 0%, 27, 32 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,511 / 9,511 / 9,511 / 9,511 / 9,511 | 9,511 | 100.0% | 100.0% | 1,533 / 1,533 | n/a | 0%, 24, 36 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 43.5% | 101 | 26 / 30 / 2,118 / 4,672 / 6,031 | 2,461 | 50.5% | 33.0% | 1,962 / 1,976 | 56.5% (62) | 0%, 27, 32 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,952 / 4,952 / 4,952 / 4,952 / 4,952 | 4,952 | 100.0% | 100.0% | 1,533 / 1,533 | 100.0% (33) | 0%, 24, 36 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3139, 3139 | 16.2 | 4.76 | 0.00 | 0.00 | 4.19 | 4.88 | 1,534 | 5,275 | 75 | 9.7% | 70269, 19861 |
| 1.00 of the budget | 1 | none | benchmark | 227, 227 | 13.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 1,927 | 3,788 | 28 | 0.0% | 13, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 3139, 3139 | 10.3 | 3.01 | 0.00 | 0.00 | 2.08 | 2.62 | 973 | 2,792 | 75 | 9.7% | 45614, 13120 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 6.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,088 | 3,788 | 28 | 0.0% | 6, 5 |
| 1.00 of the budget | 5 | none | development | 3139, 3139 | 49.6 | 14.87 | 1.30 | 0.09 | 12.33 | 12.69 | 4,547 | 13,799 | 46 | 44.4% | 216041, 57309 |
| 1.00 of the budget | 5 | none | benchmark | 227, 227 | 88.0 | 33.00 | 0.00 | 0.00 | 28.00 | 14.00 | 9,376 | 16,877 | 28 | 0.0% | 88, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 3139, 3139 | 22.5 | 6.53 | 1.23 | 0.08 | 3.04 | 2.08 | 1,937 | 2,155 | 46 | 44.4% | 98741, 21243 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 4,793 | 28 | 0.0% | 13, 6 |
| whole micros | 1 | none | development | 3139, 3123 | 12.4 | 4.11 | 0.00 | 0.00 | 3.51 | 4.12 | 1,249 | 4,363 | 84 | 10.1% | 53443, 16760 |
| whole micros | 1 | none | benchmark | 227, 185 | 8.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,233 | 3,099 | 32 | 0.0% | 8, 3 |
| whole micros | 1 | at payout 3 | development | 3139, 3123 | 8.4 | 2.78 | 0.00 | 0.00 | 1.88 | 2.52 | 847 | 2,628 | 84 | 10.1% | 37031, 12006 |
| whole micros | 1 | at payout 3 | benchmark | 227, 185 | 3.0 | 3.00 | 0.00 | 0.00 | 2.00 | 3.00 | 643 | 3,099 | 32 | 0.0% | 3, 3 |
| whole micros | 5 | none | development | 3139, 3123 | 42.0 | 13.73 | 1.21 | 0.14 | 10.96 | 13.31 | 4,071 | 13,988 | 55 | 39.6% | 182121, 51717 |
| whole micros | 5 | none | benchmark | 227, 185 | 45.0 | 17.00 | 0.00 | 0.00 | 14.00 | 14.00 | 5,473 | 13,732 | 32 | 0.0% | 43, 15 |
| whole micros | 5 | at payout 3 | development | 3139, 3123 | 20.7 | 6.63 | 1.14 | 0.14 | 2.87 | 2.19 | 1,903 | 2,171 | 55 | 39.6% | 90866, 21019 |
| whole micros | 5 | at payout 3 | benchmark | 227, 185 | 8.0 | 5.00 | 0.00 | 0.00 | 0.00 | 5.00 | 1,137 | 4,741 | 32 | 0.0% | 8, 5 |
| 0.95 of the budget | 1 | none | development | 3139, 3139 | 13.1 | 4.29 | 0.00 | 0.00 | 3.73 | 4.13 | 1,315 | 4,550 | 82 | 10.1% | 56339, 17653 |
| 0.95 of the budget | 1 | none | benchmark | 227, 227 | 10.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,631 | 3,598 | 28 | 0.0% | 10, 6 |
| 0.95 of the budget | 1 | at payout 3 | development | 3139, 3139 | 9.2 | 2.94 | 0.00 | 0.00 | 2.05 | 2.50 | 914 | 2,650 | 82 | 10.1% | 40279, 12696 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 5.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,039 | 3,598 | 28 | 0.0% | 5, 5 |
| 0.95 of the budget | 5 | none | development | 3139, 3139 | 44.4 | 14.84 | 1.17 | 0.13 | 12.20 | 13.18 | 4,349 | 14,547 | 52 | 39.6% | 192391, 56926 |
| 0.95 of the budget | 5 | none | benchmark | 227, 227 | 64.0 | 32.00 | 0.00 | 0.00 | 27.00 | 14.00 | 8,149 | 15,660 | 28 | 0.0% | 64, 27 |
| 0.95 of the budget | 5 | at payout 3 | development | 3139, 3139 | 20.8 | 6.67 | 1.13 | 0.13 | 2.90 | 2.30 | 1,914 | 2,375 | 52 | 39.6% | 91444, 21665 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 10.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,533 | 4,485 | 28 | 0.0% | 10, 6 |

### S3 continuation only, walk-forward ATR bracket: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,764 / 2,928 / 4,581 / 6,690 / 9,649 | 5,170 | 88.2% | 62.7% | 590 / 1,084 | n/a | 0%, 26, 32 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,621 / 3,621 / 3,621 / 3,621 / 3,621 | 3,621 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,520 / 2,395 / 3,255 / 3,967 / 4,772 | 3,244 | 85.1% | 23.6% | 590 / 1,084 | 91.0% (152) | 0%, 26, 32 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,460 / 4,460 / 4,460 / 4,460 / 4,460 | 4,460 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 23, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 52.3% | 98 | 22 / 31 / 42 / 18,103 / 31,146 | 10,099 | 47.0% | 44.7% | 1,965 / 1,981 | n/a | 0%, 26, 32 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,619 / 9,619 / 9,619 / 9,619 / 9,619 | 9,619 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 38.0% | 84 | 30 / 36 / 1,559 / 3,055 / 4,883 | 1,872 | 40.9% | 16.4% | 1,960 / 1,974 | 62.0% (46) | 0%, 26, 32 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,754 / 3,754 / 3,754 / 3,754 / 3,754 | 3,754 | 100.0% | 0.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 23, 33 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3139, 3139 | 17.4 | 5.48 | 0.00 | 0.00 | 4.94 | 5.66 | 1,697 | 4,867 | 60 | 0.0% | 75329, 23141 |
| 1.00 of the budget | 1 | none | benchmark | 227, 227 | 13.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 1,927 | 3,548 | 26 | 0.0% | 13, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 3139, 3139 | 10.4 | 3.18 | 0.00 | 0.00 | 2.23 | 2.88 | 1,002 | 2,246 | 60 | 0.0% | 46038, 14006 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 6.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,088 | 3,548 | 26 | 0.0% | 6, 5 |
| 1.00 of the budget | 5 | none | development | 3139, 3139 | 54.9 | 16.49 | 1.48 | 0.10 | 13.92 | 15.02 | 5,024 | 13,123 | 42 | 27.0% | 238956, 64283 |
| 1.00 of the budget | 5 | none | benchmark | 227, 227 | 96.0 | 33.00 | 0.00 | 0.00 | 28.00 | 17.00 | 9,768 | 17,387 | 26 | 0.0% | 96, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 3139, 3139 | 20.4 | 6.07 | 1.13 | 0.04 | 2.21 | 2.56 | 1,780 | 1,651 | 42 | 27.0% | 89526, 19451 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 3,434 | 26 | 0.0% | 13, 6 |

### S3 continuation only, walk-forward ATR bracket: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,430 / 3,953 / 5,315 / 7,853 / 10,417 | 5,801 | 87.7% | 74.8% | 595 / 1,327 | n/a | 0%, 26, 32 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,861 / 3,861 / 3,861 / 3,861 / 3,861 | 3,861 | 100.0% | 0.0% | 396 / 396 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,430 / 3,503 / 4,046 / 4,588 / 5,083 | 3,822 | 87.7% | 52.3% | 595 / 1,327 | 85.0% (157) | 0%, 26, 32 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,700 / 4,700 / 4,700 / 4,700 / 4,700 | 4,700 | 100.0% | 100.0% | 396 / 396 | 100.0% (163) | 0%, 23, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 51.2% | 91 | 28 / 30 / 40 / 19,266 / 34,550 | 11,415 | 47.3% | 46.5% | 1,966 / 1,974 | n/a | 0%, 26, 32 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 9,501 / 9,501 / 9,501 / 9,501 / 9,501 | 9,501 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 23, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 48.7% | 88 | 28 / 30 / 1,497 / 4,286 / 5,700 | 2,213 | 47.5% | 27.7% | 1,966 / 1,974 | 51.3% (54) | 0%, 26, 32 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,113 / 5,113 / 5,113 / 5,113 / 5,113 | 5,113 | 100.0% | 100.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 23, 33 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3139, 3139 | 16.1 | 4.84 | 0.00 | 0.00 | 4.27 | 4.95 | 1,544 | 5,344 | 73 | 9.7% | 70059, 20204 |
| 1.00 of the budget | 1 | none | benchmark | 227, 227 | 13.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 1,927 | 3,788 | 28 | 0.0% | 13, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 3139, 3139 | 10.2 | 3.04 | 0.00 | 0.00 | 2.12 | 2.63 | 972 | 2,794 | 73 | 9.7% | 44981, 13296 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 227, 227 | 6.0 | 5.00 | 0.00 | 0.00 | 4.00 | 3.00 | 1,088 | 3,788 | 28 | 0.0% | 6, 5 |
| 1.00 of the budget | 5 | none | development | 3139, 3139 | 49.2 | 14.97 | 1.31 | 0.09 | 12.40 | 12.87 | 4,539 | 13,954 | 46 | 44.4% | 214415, 57673 |
| 1.00 of the budget | 5 | none | benchmark | 227, 227 | 88.0 | 33.00 | 0.00 | 0.00 | 28.00 | 14.00 | 9,376 | 16,877 | 28 | 0.0% | 88, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 3139, 3139 | 22.1 | 6.48 | 1.25 | 0.08 | 2.97 | 2.06 | 1,908 | 2,121 | 46 | 44.4% | 97134, 20951 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 227, 227 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 4,793 | 28 | 0.0% | 13, 6 |

### S4 S3 + A+ reversion, sealed bracket: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 2.9% | 267 | 1,112 / 2,759 / 4,827 / 7,744 / 11,240 | 5,502 | 83.9% | 59.4% | 549 / 1,190 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,359 / 6,359 / 6,359 / 6,359 / 6,359 | 6,359 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 22, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 2.9% | 267 | 1,162 / 2,322 / 3,364 / 4,140 / 5,045 | 3,252 | 79.5% | 30.0% | 543 / 1,182 | 87.5% (139) | 0%, 24, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,915 / 4,915 / 4,915 / 4,915 / 4,915 | 4,915 | 100.0% | 100.0% | 396 / 396 | 100.0% (47) | 0%, 22, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 50.5% | 97 | 23 / 32 / 46 / 21,895 / 39,129 | 12,157 | 48.2% | 46.4% | 1,964 / 1,979 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 20,704 / 20,704 / 20,704 / 20,704 / 20,704 | 20,704 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 22, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 35.6% | 81 | 30 / 36 / 1,543 / 3,328 / 5,086 | 1,988 | 41.4% | 20.5% | 1,921 / 1,974 | 64.4% (44) | 0%, 24, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,754 / 3,754 / 3,754 / 3,754 / 3,754 | 3,754 | 100.0% | 0.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 22, 33 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,123 / 2,682 / 4,447 / 6,866 / 10,711 | 5,180 | 80.6% | 57.3% | 537 / 1,033 | n/a | 0%, 26, 35 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,377 / 5,377 / 5,377 / 5,377 / 5,377 | 5,377 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 24, 33 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,122 / 2,378 / 3,238 / 4,088 / 4,758 | 3,148 | 79.7% | 27.8% | 527 / 1,033 | 85.6% (144) | 0%, 26, 35 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,639 / 4,639 / 4,639 / 4,639 / 4,639 | 4,639 | 100.0% | 100.0% | 396 / 396 | 100.0% (47) | 0%, 24, 33 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 46.5% | 119 | 24 / 32 / 2,619 / 23,142 / 36,249 | 11,868 | 50.7% | 49.1% | 1,961 / 1,982 | n/a | 0%, 26, 35 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 16,093 / 16,093 / 16,093 / 16,093 / 16,093 | 16,093 | 100.0% | 100.0% | 1,631 / 1,631 | n/a | 0%, 24, 33 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 32.5% | 100 | 30 / 38 / 1,806 / 3,070 / 4,610 | 1,959 | 46.1% | 15.1% | 1,823 / 1,972 | 67.5% (46) | 0%, 26, 35 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,954 / 2,954 / 2,954 / 2,954 / 2,954 | 2,954 | 100.0% | 0.0% | 1,631 / 1,631 | 100.0% (33) | 0%, 24, 33 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,118 / 2,474 / 4,677 / 7,094 / 10,335 | 5,117 | 78.4% | 61.2% | 542 / 1,025 | n/a | 0%, 25, 33 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,155 / 6,155 / 6,155 / 6,155 / 6,155 | 6,155 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 22, 35 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,204 / 2,485 / 3,185 / 4,127 / 4,890 | 3,188 | 81.8% | 27.4% | 529 / 1,025 | 86.2% (148) | 0%, 25, 33 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,750 / 4,750 / 4,750 / 4,750 / 4,750 | 4,750 | 100.0% | 100.0% | 396 / 396 | 100.0% (47) | 0%, 22, 35 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 45.2% | 113 | 23 / 32 / 4,288 / 23,355 / 38,634 | 12,936 | 52.5% | 50.4% | 1,960 / 1,982 | n/a | 0%, 25, 33 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 21,548 / 21,548 / 21,548 / 21,548 / 21,548 | 21,548 | 100.0% | 100.0% | 1,631 / 1,631 | n/a | 0%, 22, 35 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 32.9% | 99 | 28 / 38 / 1,824 / 3,253 / 4,938 | 2,063 | 47.0% | 17.2% | 1,827 / 1,976 | 67.1% (47) | 0%, 25, 33 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,631 / 3,631 / 3,631 / 3,631 / 3,631 | 3,631 | 100.0% | 0.0% | 1,631 / 1,631 | 100.0% (28) | 0%, 22, 35 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3389, 3389 | 18.8 | 5.74 | 0.02 | 0.00 | 5.24 | 5.74 | 1,801 | 5,303 | 57 | 0.0% | 81499, 24317 |
| 1.00 of the budget | 1 | none | benchmark | 272, 272 | 12.0 | 7.00 | 0.00 | 0.00 | 6.00 | 5.00 | 1,680 | 6,039 | 26 | 0.0% | 12, 6 |
| 1.00 of the budget | 1 | at payout 3 | development | 3389, 3389 | 11.0 | 3.38 | 0.02 | 0.00 | 2.44 | 2.83 | 1,057 | 2,309 | 57 | 0.0% | 48863, 14758 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 3,311 | 26 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3389, 3389 | 58.5 | 17.86 | 1.40 | 0.10 | 15.38 | 16.84 | 5,407 | 15,563 | 40 | 26.6% | 254960, 70787 |
| 1.00 of the budget | 5 | none | benchmark | 272, 272 | 82.0 | 30.00 | 0.00 | 0.00 | 25.00 | 26.00 | 8,635 | 27,339 | 26 | 0.0% | 82, 25 |
| 1.00 of the budget | 5 | at payout 3 | development | 3389, 3389 | 20.4 | 5.94 | 1.02 | 0.04 | 2.07 | 2.64 | 1,768 | 1,757 | 40 | 26.6% | 89379, 19083 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 3,434 | 26 | 0.0% | 13, 6 |
| whole micros | 1 | none | development | 3389, 3385 | 15.1 | 4.90 | 0.00 | 0.00 | 4.40 | 5.57 | 1,499 | 4,679 | 60 | 3.0% | 64890, 20589 |
| whole micros | 1 | none | benchmark | 272, 271 | 13.0 | 6.00 | 0.00 | 0.00 | 5.00 | 5.00 | 1,580 | 4,957 | 27 | 0.0% | 13, 5 |
| whole micros | 1 | at payout 3 | development | 3389, 3385 | 9.3 | 2.98 | 0.00 | 0.00 | 2.07 | 2.75 | 922 | 2,070 | 60 | 3.0% | 41152, 13071 |
| whole micros | 1 | at payout 3 | benchmark | 272, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 3,035 | 27 | 0.0% | 2, 2 |
| whole micros | 5 | none | development | 3389, 3385 | 52.7 | 17.35 | 1.30 | 0.17 | 14.79 | 17.59 | 5,102 | 14,970 | 42 | 24.6% | 228707, 68246 |
| whole micros | 5 | none | benchmark | 272, 271 | 65.0 | 26.00 | 0.00 | 0.00 | 21.00 | 22.00 | 7,304 | 21,397 | 27 | 0.0% | 65, 21 |
| whole micros | 5 | at payout 3 | development | 3389, 3385 | 18.7 | 5.88 | 0.91 | 0.11 | 1.97 | 2.76 | 1,714 | 1,673 | 42 | 24.6% | 81734, 19254 |
| whole micros | 5 | at payout 3 | benchmark | 272, 271 | 12.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,631 | 2,585 | 27 | 0.0% | 12, 6 |
| 0.95 of the budget | 1 | none | development | 3389, 3389 | 15.7 | 4.78 | 0.00 | 0.00 | 4.32 | 5.31 | 1,523 | 4,641 | 59 | 3.0% | 67418, 20248 |
| 0.95 of the budget | 1 | none | benchmark | 272, 272 | 10.0 | 7.00 | 0.00 | 0.00 | 6.00 | 5.00 | 1,582 | 5,737 | 26 | 0.0% | 10, 6 |
| 0.95 of the budget | 1 | at payout 3 | development | 3389, 3389 | 10.0 | 2.99 | 0.00 | 0.00 | 2.08 | 2.76 | 961 | 2,148 | 59 | 3.0% | 43957, 13147 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 3,146 | 26 | 0.0% | 2, 2 |
| 0.95 of the budget | 5 | none | development | 3389, 3389 | 54.4 | 17.75 | 1.39 | 0.17 | 15.11 | 18.11 | 5,242 | 16,178 | 42 | 24.7% | 235678, 69870 |
| 0.95 of the budget | 5 | none | benchmark | 272, 272 | 67.0 | 31.00 | 0.00 | 0.00 | 26.00 | 27.00 | 7,951 | 27,499 | 26 | 0.0% | 67, 26 |
| 0.95 of the budget | 5 | at payout 3 | development | 3389, 3389 | 19.1 | 5.92 | 0.93 | 0.13 | 2.02 | 2.81 | 1,735 | 1,797 | 42 | 24.7% | 82974, 19519 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 12.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,631 | 3,262 | 26 | 0.0% | 12, 6 |

### S4 S3 + A+ reversion, sealed bracket: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 1.4% | 263 | 675 / 3,066 / 5,255 / 8,236 / 11,468 | 5,809 | 81.9% | 69.3% | 643 / 1,429 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,853 / 6,853 / 6,853 / 6,853 / 6,853 | 6,853 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 22, 33 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 1.4% | 263 | 675 / 3,079 / 4,144 / 4,823 / 5,677 | 3,759 | 82.0% | 56.2% | 643 / 1,429 | 78.8% (154) | 0%, 24, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,479 / 4,479 / 4,479 / 4,479 / 4,479 | 4,479 | 100.0% | 100.0% | 396 / 396 | 100.0% (61) | 0%, 22, 33 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 55.1% | 88 | 28 / 30 / 40 / 21,142 / 46,319 | 12,943 | 43.9% | 42.9% | 1,966 / 1,974 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 21,405 / 21,405 / 21,405 / 21,405 / 21,405 | 21,405 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 22, 33 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 51.5% | 85 | 28 / 30 / 40 / 4,306 / 5,654 | 2,136 | 45.4% | 27.8% | 1,966 / 1,974 | 48.5% (49) | 0%, 24, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,113 / 5,113 / 5,113 / 5,113 / 5,113 | 5,113 | 100.0% | 100.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 22, 33 |
| whole micros | 1 | none | development | 4445 (15.3; 365 days) | 2.4% | 283 | 963 / 2,712 / 4,594 / 7,477 / 11,016 | 5,323 | 78.5% | 64.1% | 543 / 1,233 | n/a | 0%, 26, 35 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,265 / 5,265 / 5,265 / 5,265 / 5,265 | 5,265 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 24, 33 |
| whole micros | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 2.4% | 283 | 963 / 2,835 / 4,103 / 4,669 / 5,192 | 3,635 | 78.5% | 57.1% | 543 / 1,233 | 74.4% (157) | 0%, 26, 35 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,572 / 4,572 / 4,572 / 4,572 / 4,572 | 4,572 | 100.0% | 100.0% | 396 / 396 | 100.0% (61) | 0%, 24, 33 |
| whole micros | 5 | none | development | 4445 (15.3; 365 days) | 48.8% | 103 | 28 / 30 / 1,854 / 22,985 / 44,281 | 13,203 | 49.9% | 48.4% | 1,966 / 1,976 | n/a | 0%, 26, 35 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,550 / 10,550 / 10,550 / 10,550 / 10,550 | 10,550 | 100.0% | 100.0% | 1,631 / 1,631 | n/a | 0%, 24, 33 |
| whole micros | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 45.8% | 101 | 28 / 30 / 1,660 / 4,331 / 5,683 | 2,269 | 48.6% | 29.4% | 1,964 / 1,976 | 54.2% (58) | 0%, 26, 35 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,232 / 5,232 / 5,232 / 5,232 / 5,232 | 5,232 | 100.0% | 100.0% | 1,631 / 1,631 | 100.0% (34) | 0%, 24, 33 |
| 0.95 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 2.4% | 295 | 867 / 2,795 / 4,816 / 7,594 / 11,730 | 5,596 | 80.9% | 68.1% | 543 / 1,329 | n/a | 0%, 25, 33 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,632 / 6,632 / 6,632 / 6,632 / 6,632 | 6,632 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 22, 35 |
| 0.95 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 2.4% | 295 | 867 / 2,930 / 4,083 / 4,699 / 5,296 | 3,647 | 80.9% | 54.3% | 543 / 1,329 | 75.8% (154) | 0%, 25, 33 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,336 / 4,336 / 4,336 / 4,336 / 4,336 | 4,336 | 100.0% | 100.0% | 396 / 396 | 100.0% (61) | 0%, 22, 35 |
| 0.95 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 49.6% | 103 | 26 / 30 / 638 / 26,806 / 46,971 | 14,068 | 49.4% | 48.6% | 1,964 / 1,976 | n/a | 0%, 25, 33 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 22,235 / 22,235 / 22,235 / 22,235 / 22,235 | 22,235 | 100.0% | 100.0% | 1,631 / 1,631 | n/a | 0%, 22, 35 |
| 0.95 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 46.5% | 101 | 26 / 30 / 1,781 / 4,329 / 5,500 | 2,274 | 49.2% | 29.7% | 1,964 / 1,976 | 53.5% (55) | 0%, 25, 33 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,922 / 4,922 / 4,922 / 4,922 / 4,922 | 4,922 | 100.0% | 100.0% | 1,631 / 1,631 | 100.0% (28) | 0%, 22, 35 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3389, 3389 | 17.0 | 5.27 | 0.01 | 0.00 | 4.69 | 4.59 | 1,640 | 5,448 | 74 | 10.7% | 74073, 21864 |
| 1.00 of the budget | 1 | none | benchmark | 272, 272 | 13.0 | 6.00 | 0.00 | 0.00 | 5.00 | 6.00 | 1,531 | 6,384 | 28 | 0.0% | 13, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 3389, 3389 | 11.4 | 3.50 | 0.01 | 0.00 | 2.60 | 2.51 | 1,093 | 2,852 | 74 | 10.7% | 50129, 15165 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 2,875 | 28 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3389, 3389 | 49.2 | 14.46 | 1.36 | 0.07 | 12.00 | 12.83 | 4,436 | 15,379 | 43 | 47.5% | 214814, 55655 |
| 1.00 of the budget | 5 | none | benchmark | 272, 272 | 79.0 | 28.00 | 0.00 | 0.00 | 23.00 | 26.00 | 8,190 | 27,595 | 28 | 0.0% | 79, 23 |
| 1.00 of the budget | 5 | at payout 3 | development | 3389, 3389 | 22.4 | 6.56 | 1.27 | 0.06 | 3.11 | 1.93 | 1,927 | 2,063 | 43 | 47.5% | 98727, 21069 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 4,793 | 28 | 0.0% | 13, 6 |
| whole micros | 1 | none | development | 3389, 3385 | 13.5 | 4.50 | 0.01 | 0.00 | 3.94 | 4.31 | 1,357 | 4,679 | 79 | 13.6% | 58145, 18473 |
| whole micros | 1 | none | benchmark | 272, 271 | 13.0 | 6.00 | 0.00 | 0.00 | 5.00 | 6.00 | 1,580 | 4,845 | 32 | 0.0% | 13, 5 |
| whole micros | 1 | at payout 3 | development | 3389, 3385 | 9.1 | 3.03 | 0.01 | 0.00 | 2.15 | 2.41 | 913 | 2,548 | 79 | 13.6% | 40103, 13032 |
| whole micros | 1 | at payout 3 | benchmark | 272, 271 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 2,968 | 32 | 0.0% | 2, 2 |
| whole micros | 5 | none | development | 3389, 3385 | 43.5 | 14.22 | 1.28 | 0.13 | 11.58 | 13.58 | 4,177 | 15,381 | 51 | 42.4% | 188571, 54253 |
| whole micros | 5 | none | benchmark | 272, 271 | 67.0 | 28.00 | 0.00 | 0.00 | 23.00 | 18.00 | 7,749 | 16,299 | 32 | 0.0% | 67, 23 |
| whole micros | 5 | at payout 3 | development | 3389, 3385 | 20.7 | 6.70 | 1.21 | 0.13 | 3.01 | 2.15 | 1,893 | 2,162 | 51 | 42.4% | 90800, 21690 |
| whole micros | 5 | at payout 3 | benchmark | 272, 271 | 12.0 | 7.00 | 0.00 | 0.00 | 2.00 | 5.00 | 1,631 | 4,863 | 32 | 0.0% | 12, 7 |
| 0.95 of the budget | 1 | none | development | 3389, 3389 | 14.0 | 4.31 | 0.02 | 0.00 | 3.79 | 4.51 | 1,365 | 4,961 | 77 | 13.2% | 60492, 17916 |
| 0.95 of the budget | 1 | none | benchmark | 272, 272 | 11.0 | 6.00 | 0.00 | 0.00 | 5.00 | 6.00 | 1,433 | 6,065 | 28 | 0.0% | 11, 5 |
| 0.95 of the budget | 1 | at payout 3 | development | 3389, 3389 | 9.6 | 3.00 | 0.02 | 0.00 | 2.13 | 2.45 | 941 | 2,588 | 77 | 13.2% | 42386, 12958 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 2,732 | 28 | 0.0% | 2, 2 |
| 0.95 of the budget | 5 | none | development | 3389, 3389 | 45.1 | 14.46 | 1.25 | 0.13 | 11.93 | 14.18 | 4,301 | 16,368 | 49 | 42.4% | 195716, 55720 |
| 0.95 of the budget | 5 | none | benchmark | 272, 272 | 64.0 | 29.00 | 0.00 | 0.00 | 24.00 | 27.00 | 7,506 | 27,741 | 28 | 0.0% | 64, 24 |
| 0.95 of the budget | 5 | at payout 3 | development | 3389, 3389 | 20.8 | 6.61 | 1.18 | 0.13 | 3.01 | 2.14 | 1,891 | 2,166 | 49 | 42.4% | 91263, 21607 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 12.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,631 | 4,553 | 28 | 0.0% | 12, 6 |

### S4 S3 + A+ reversion, sealed bracket: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,211 / 2,851 / 4,576 / 6,339 / 10,193 | 5,047 | 84.4% | 58.3% | 573 / 1,165 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,657 / 6,657 / 6,657 / 6,657 / 6,657 | 6,657 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 21, 34 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 0.0% | n/a | 1,289 / 2,371 / 3,288 / 4,056 / 4,865 | 3,244 | 81.7% | 26.7% | 558 / 1,165 | 88.5% (145) | 0%, 24, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,920 / 4,920 / 4,920 / 4,920 / 4,920 | 4,920 | 100.0% | 100.0% | 396 / 396 | 100.0% (47) | 0%, 21, 34 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 49.9% | 99 | 23 / 32 / 49 / 20,030 / 38,346 | 11,921 | 49.2% | 47.9% | 1,964 / 1,982 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 18,231 / 18,231 / 18,231 / 18,231 / 18,231 | 18,231 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 21, 34 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 34.9% | 83 | 30 / 36 / 1,575 / 3,332 / 4,965 | 2,010 | 42.4% | 19.4% | 1,878 / 1,974 | 65.1% (45) | 0%, 24, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,754 / 3,754 / 3,754 / 3,754 / 3,754 | 3,754 | 100.0% | 0.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 21, 34 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3389, 3389 | 19.1 | 6.02 | 0.00 | 0.00 | 5.52 | 5.47 | 1,862 | 4,910 | 57 | 0.0% | 82817, 25493 |
| 1.00 of the budget | 1 | none | benchmark | 272, 272 | 16.0 | 6.00 | 0.00 | 0.00 | 5.00 | 6.00 | 1,776 | 6,433 | 26 | 0.0% | 16, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 3389, 3389 | 11.3 | 3.52 | 0.00 | 0.00 | 2.59 | 2.86 | 1,093 | 2,337 | 57 | 0.0% | 49766, 15477 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 3,316 | 26 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3389, 3389 | 58.6 | 17.72 | 1.43 | 0.09 | 15.17 | 16.81 | 5,389 | 15,310 | 41 | 25.6% | 255477, 69952 |
| 1.00 of the budget | 5 | none | benchmark | 272, 272 | 91.0 | 26.00 | 0.00 | 0.00 | 21.00 | 25.00 | 8,676 | 24,907 | 26 | 0.0% | 91, 21 |
| 1.00 of the budget | 5 | at payout 3 | development | 3389, 3389 | 20.3 | 5.95 | 1.06 | 0.04 | 2.02 | 2.68 | 1,764 | 1,774 | 41 | 25.6% | 89024, 19039 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 3,434 | 26 | 0.0% | 13, 6 |

### S4 S3 + A+ reversion, sealed bracket: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4445 (15.3; 365 days) | 1.0% | 260 | 767 / 3,115 / 5,204 / 8,098 / 11,059 | 5,692 | 82.3% | 68.5% | 641 / 1,380 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 7,104 / 7,104 / 7,104 / 7,104 / 7,104 | 7,104 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 21, 34 |
| 1.00 of the budget | 1 | at payout 3 | development | 4445 (15.3; 365 days) | 1.0% | 260 | 767 / 3,206 / 4,193 / 4,790 / 5,335 | 3,795 | 82.4% | 58.3% | 641 / 1,380 | 79.0% (156) | 0%, 24, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,487 / 4,487 / 4,487 / 4,487 / 4,487 | 4,487 | 100.0% | 100.0% | 396 / 396 | 100.0% (61) | 0%, 21, 34 |
| 1.00 of the budget | 5 | none | development | 4445 (15.3; 365 days) | 53.5% | 90 | 28 / 30 / 40 / 22,328 / 36,321 | 12,042 | 45.3% | 44.0% | 1,966 / 1,974 | n/a | 0%, 24, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 18,938 / 18,938 / 18,938 / 18,938 / 18,938 | 18,938 | 100.0% | 100.0% | 1,680 / 1,680 | n/a | 0%, 21, 34 |
| 1.00 of the budget | 5 | at payout 3 | development | 4445 (15.3; 365 days) | 49.9% | 87 | 28 / 30 / 493 / 4,138 / 5,617 | 2,153 | 45.8% | 26.6% | 1,966 / 1,974 | 50.1% (51) | 0%, 24, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,113 / 5,113 / 5,113 / 5,113 / 5,113 | 5,113 | 100.0% | 100.0% | 1,680 / 1,680 | 100.0% (28) | 0%, 21, 34 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 3389, 3389 | 17.1 | 5.30 | 0.01 | 0.00 | 4.73 | 4.53 | 1,651 | 5,343 | 72 | 10.6% | 74161, 22038 |
| 1.00 of the budget | 1 | none | benchmark | 272, 272 | 15.0 | 6.00 | 0.00 | 0.00 | 5.00 | 7.00 | 1,678 | 6,782 | 28 | 0.0% | 15, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 3389, 3389 | 11.2 | 3.48 | 0.01 | 0.00 | 2.58 | 2.51 | 1,085 | 2,879 | 72 | 10.6% | 49465, 15090 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 272, 272 | 2.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 396 | 2,883 | 28 | 0.0% | 2, 2 |
| 1.00 of the budget | 5 | none | development | 3389, 3389 | 50.4 | 14.84 | 1.43 | 0.06 | 12.30 | 12.48 | 4,549 | 14,591 | 44 | 46.1% | 219790, 56856 |
| 1.00 of the budget | 5 | none | benchmark | 272, 272 | 86.0 | 25.00 | 0.00 | 0.00 | 20.00 | 25.00 | 8,233 | 25,171 | 28 | 0.0% | 86, 20 |
| 1.00 of the budget | 5 | at payout 3 | development | 3389, 3389 | 22.3 | 6.57 | 1.32 | 0.06 | 2.99 | 1.97 | 1,918 | 2,071 | 44 | 46.1% | 98289, 20752 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 272, 272 | 13.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,680 | 4,793 | 28 | 0.0% | 13, 6 |

### S1 on H3's favoured side: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,472 / 2,083 / 3,761 / 6,043 / 7,630 | 4,265 | 76.6% | 47.0% | 540 / 986 | n/a | 0%, 35, 40 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,177 / 4,177 / 4,177 / 4,177 / 4,177 | 4,177 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 31, 35 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,472 / 2,177 / 3,436 / 4,500 / 5,652 | 3,466 | 78.2% | 36.3% | 539 / 986 | 73.6% (200) | 0%, 35, 40 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,886 / 3,886 / 3,886 / 3,886 / 3,886 | 3,886 | 100.0% | 0.0% | 396 / 396 | 100.0% (201) | 0%, 31, 35 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 44.7% | 113 | 24 / 32 / 467 / 12,575 / 26,269 | 7,913 | 44.7% | 39.3% | 1,964 / 1,988 | n/a | 0%, 35, 40 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,589 / 5,589 / 5,589 / 5,589 / 5,589 | 5,589 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 31, 35 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 35.7% | 94 | 30 / 36 / 1,386 / 3,751 / 5,473 | 2,111 | 40.2% | 22.2% | 1,960 / 1,975 | 64.3% (67) | 0%, 35, 40 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,700 / 6,700 / 6,700 / 6,700 / 6,700 | 6,700 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 31, 35 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,269 / 1,971 / 3,178 / 5,815 / 6,728 | 3,797 | 74.4% | 39.7% | 494 / 943 | n/a | 0%, 39, 36 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,960 / 5,960 / 5,960 / 5,960 / 5,960 | 5,960 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 32, 36 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,269 / 1,987 / 3,029 / 4,239 / 5,013 | 3,197 | 74.8% | 29.3% | 494 / 943 | 66.2% (204) | 0%, 39, 36 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,932 / 4,932 / 4,932 / 4,932 / 4,932 | 4,932 | 100.0% | 100.0% | 198 / 198 | 100.0% (61) | 0%, 32, 36 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 43.4% | 133 | 24 / 34 / 1,577 / 13,010 / 21,523 | 7,252 | 48.5% | 40.7% | 1,960 / 1,982 | n/a | 0%, 39, 36 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 19,189 / 19,189 / 19,189 / 19,189 / 19,189 | 19,189 | 100.0% | 100.0% | 1,088 / 1,088 | n/a | 0%, 32, 36 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 34.1% | 124 | 30 / 40 / 1,579 / 3,421 / 4,999 | 2,006 | 42.1% | 18.6% | 1,872 / 1,974 | 65.7% (69) | 0%, 39, 36 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 1,276 / 1,276 / 1,276 / 1,276 / 1,276 | 1,276 | 0.0% | 0.0% | 1,088 / 1,088 | 100.0% (29) | 0%, 32, 36 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,221 / 2,036 / 3,583 / 5,965 / 6,671 | 3,940 | 75.6% | 43.8% | 493 / 951 | n/a | 0%, 38, 35 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,160 / 6,160 / 6,160 / 6,160 / 6,160 | 6,160 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 33, 37 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,221 / 2,053 / 3,165 / 4,396 / 5,169 | 3,276 | 76.9% | 31.7% | 493 / 951 | 66.6% (197) | 0%, 38, 35 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,657 / 4,657 / 4,657 / 4,657 / 4,657 | 4,657 | 100.0% | 100.0% | 396 / 396 | 100.0% (187) | 0%, 33, 37 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 42.3% | 132 | 27 / 36 / 1,985 / 14,714 / 22,592 | 7,838 | 49.9% | 41.7% | 1,960 / 1,979 | n/a | 0%, 38, 35 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 21,857 / 21,857 / 21,857 / 21,857 / 21,857 | 21,857 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 33, 37 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 33.9% | 124 | 30 / 40 / 1,646 / 3,586 / 5,188 | 2,089 | 43.3% | 19.9% | 1,876 / 1,972 | 65.8% (68) | 0%, 38, 35 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 7,167 / 7,167 / 7,167 / 7,167 / 7,167 | 7,167 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 33, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1887, 1887 | 13.8 | 3.69 | 0.00 | 0.00 | 3.18 | 3.67 | 1,306 | 3,570 | 87 | 0.0% | 56736, 14615 |
| 1.00 of the budget | 1 | none | benchmark | 172, 172 | 20.0 | 6.00 | 0.00 | 0.00 | 5.00 | 4.00 | 1,923 | 4,100 | 34 | 0.0% | 20, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 1887, 1887 | 10.2 | 2.81 | 0.00 | 0.00 | 1.97 | 2.66 | 988 | 2,454 | 87 | 0.0% | 42990, 11632 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 15.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,380 | 3,266 | 34 | 0.0% | 15, 4 |
| 1.00 of the budget | 5 | none | development | 1887, 1887 | 47.0 | 12.66 | 1.36 | 0.40 | 9.95 | 10.68 | 4,260 | 10,173 | 60 | 26.8% | 193976, 45176 |
| 1.00 of the budget | 5 | none | benchmark | 172, 172 | 99.0 | 28.00 | 0.00 | 0.00 | 23.00 | 15.00 | 9,121 | 12,710 | 34 | 0.0% | 99, 23 |
| 1.00 of the budget | 5 | at payout 3 | development | 1887, 1887 | 20.2 | 5.60 | 1.01 | 0.27 | 1.86 | 2.64 | 1,805 | 1,916 | 60 | 26.8% | 84074, 17565 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 13.0 | 8.00 | 0.00 | 0.00 | 6.00 | 4.00 | 1,829 | 6,530 | 34 | 0.0% | 10, 8 |
| whole micros | 1 | none | development | 1887, 1887 | 10.6 | 3.16 | 0.00 | 0.00 | 2.65 | 3.25 | 1,094 | 2,891 | 96 | 0.2% | 43235, 12398 |
| whole micros | 1 | none | benchmark | 172, 172 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 6.00 | 1,233 | 5,193 | 28 | 0.0% | 12, 3 |
| whole micros | 1 | at payout 3 | development | 1887, 1887 | 8.2 | 2.51 | 0.00 | 0.00 | 1.69 | 2.49 | 870 | 2,067 | 96 | 0.2% | 34412, 10232 |
| whole micros | 1 | at payout 3 | benchmark | 172, 172 | 1.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 198 | 3,130 | 28 | 0.0% | 1, 1 |
| whole micros | 5 | none | development | 1887, 1887 | 41.4 | 11.42 | 1.14 | 0.50 | 8.96 | 10.55 | 3,948 | 9,199 | 66 | 26.8% | 168965, 41122 |
| whole micros | 5 | none | benchmark | 172, 172 | 63.0 | 22.00 | 0.00 | 0.00 | 17.00 | 27.00 | 6,414 | 23,603 | 28 | 0.0% | 63, 17 |
| whole micros | 5 | at payout 3 | development | 1887, 1887 | 18.5 | 5.15 | 0.87 | 0.36 | 1.43 | 2.74 | 1,738 | 1,745 | 66 | 26.8% | 76060, 16141 |
| whole micros | 5 | at payout 3 | benchmark | 172, 172 | 7.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 1,088 | 364 | 28 | 0.0% | 7, 3 |
| 0.95 of the budget | 1 | none | development | 1887, 1887 | 10.6 | 3.19 | 0.00 | 0.00 | 2.69 | 3.34 | 1,100 | 3,039 | 93 | 0.2% | 43213, 12521 |
| 0.95 of the budget | 1 | none | benchmark | 172, 172 | 13.0 | 5.00 | 0.00 | 0.00 | 4.00 | 5.00 | 1,431 | 5,591 | 43 | 0.0% | 13, 4 |
| 0.95 of the budget | 1 | at payout 3 | development | 1887, 1887 | 8.1 | 2.50 | 0.00 | 0.00 | 1.68 | 2.49 | 862 | 2,139 | 93 | 0.2% | 33921, 10206 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 9.0 | 3.00 | 0.00 | 0.00 | 2.00 | 3.00 | 937 | 3,594 | 43 | 0.0% | 9, 3 |
| 0.95 of the budget | 5 | none | development | 1887, 1887 | 41.4 | 11.48 | 1.13 | 0.52 | 9.01 | 10.76 | 3,958 | 9,797 | 65 | 26.8% | 168675, 41318 |
| 0.95 of the budget | 5 | none | benchmark | 172, 172 | 65.0 | 24.00 | 0.00 | 0.00 | 19.00 | 25.00 | 6,859 | 26,716 | 43 | 0.0% | 65, 19 |
| 0.95 of the budget | 5 | at payout 3 | development | 1887, 1887 | 18.5 | 5.18 | 0.88 | 0.36 | 1.45 | 2.76 | 1,741 | 1,830 | 65 | 26.8% | 76221, 16214 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 10.0 | 8.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,682 | 6,849 | 43 | 0.0% | 10, 7 |

### S1 on H3's favoured side: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,606 / 2,655 / 4,411 / 5,936 / 7,509 | 4,550 | 84.2% | 55.9% | 494 / 1,132 | n/a | 0%, 35, 40 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,283 / 4,283 / 4,283 / 4,283 / 4,283 | 4,283 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 31, 35 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,606 / 2,655 / 4,230 / 5,209 / 5,984 | 3,989 | 84.2% | 54.0% | 494 / 1,132 | 59.4% (206) | 0%, 35, 40 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,037 / 4,037 / 4,037 / 4,037 / 4,037 | 4,037 | 100.0% | 100.0% | 396 / 396 | 100.0% (217) | 0%, 31, 35 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 42.5% | 99 | 30 / 34 / 2,124 / 13,215 / 25,573 | 8,136 | 50.6% | 46.9% | 1,964 / 1,973 | n/a | 0%, 35, 40 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 8,914 / 8,914 / 8,914 / 8,914 / 8,914 | 8,914 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 31, 35 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 41.2% | 97 | 30 / 34 / 3,156 / 5,054 / 6,169 | 2,746 | 54.6% | 37.7% | 1,964 / 1,972 | 55.9% (78) | 0%, 35, 40 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,700 / 6,700 / 6,700 / 6,700 / 6,700 | 6,700 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 31, 35 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,459 / 2,241 / 3,723 / 5,657 / 7,251 | 4,065 | 85.7% | 44.2% | 445 / 890 | n/a | 0%, 39, 36 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,766 / 4,766 / 4,766 / 4,766 / 4,766 | 4,766 | 100.0% | 100.0% | 198 / 198 | n/a | 0%, 32, 36 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,459 / 2,241 / 3,756 / 5,011 / 5,917 | 3,707 | 85.7% | 45.4% | 445 / 890 | 50.7% (209) | 0%, 39, 36 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,405 / 4,405 / 4,405 / 4,405 / 4,405 | 4,405 | 100.0% | 100.0% | 198 / 198 | 100.0% (197) | 0%, 32, 36 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 40.1% | 126 | 30 / 34 / 3,217 / 11,562 / 21,616 | 7,600 | 53.7% | 48.5% | 1,960 / 1,974 | n/a | 0%, 39, 36 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 14,342 / 14,342 / 14,342 / 14,342 / 14,342 | 14,342 | 100.0% | 100.0% | 1,088 / 1,088 | n/a | 0%, 32, 36 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.0% | 124 | 30 / 36 / 3,169 / 4,897 / 5,886 | 2,690 | 56.4% | 38.1% | 1,960 / 1,972 | 57.5% (83) | 0%, 39, 36 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,882 / 3,882 / 3,882 / 3,882 / 3,882 | 3,882 | 100.0% | 0.0% | 1,088 / 1,088 | 100.0% (34) | 0%, 32, 36 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 2,025 / 2,581 / 3,886 / 5,841 / 7,440 | 4,313 | 90.5% | 46.4% | 445 / 888 | n/a | 0%, 38, 35 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,264 / 6,264 / 6,264 / 6,264 / 6,264 | 6,264 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 33, 37 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 2,025 / 2,581 / 3,885 / 5,000 / 6,096 | 3,886 | 90.5% | 47.3% | 445 / 888 | 53.4% (211) | 0%, 38, 35 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,185 / 5,185 / 5,185 / 5,185 / 5,185 | 5,185 | 100.0% | 100.0% | 396 / 396 | 100.0% (194) | 0%, 33, 37 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 39.2% | 125 | 30 / 36 / 3,363 / 13,332 / 23,597 | 8,363 | 55.4% | 49.2% | 1,960 / 1,974 | n/a | 0%, 38, 35 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 22,271 / 22,271 / 22,271 / 22,271 / 22,271 | 22,271 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 33, 37 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.1% | 125 | 30 / 36 / 3,434 / 5,139 / 6,010 | 2,821 | 56.7% | 41.3% | 1,960 / 1,972 | 57.8% (79) | 0%, 38, 35 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 7,167 / 7,167 / 7,167 / 7,167 / 7,167 | 7,167 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 33, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1887, 1887 | 12.1 | 3.34 | 0.00 | 0.00 | 2.73 | 2.97 | 1,153 | 3,703 | 117 | 6.4% | 50029, 13034 |
| 1.00 of the budget | 1 | none | benchmark | 172, 172 | 19.0 | 6.00 | 0.00 | 0.00 | 5.00 | 4.00 | 1,874 | 4,157 | 34 | 0.0% | 19, 5 |
| 1.00 of the budget | 1 | at payout 3 | development | 1887, 1887 | 9.5 | 2.68 | 0.00 | 0.00 | 1.82 | 2.31 | 918 | 2,907 | 117 | 6.4% | 39896, 10893 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 15.0 | 4.00 | 0.00 | 0.00 | 3.00 | 3.00 | 1,380 | 3,417 | 34 | 0.0% | 15, 4 |
| 1.00 of the budget | 5 | none | development | 1887, 1887 | 41.8 | 10.95 | 1.04 | 0.26 | 8.31 | 8.41 | 3,756 | 9,892 | 73 | 38.8% | 172939, 39106 |
| 1.00 of the budget | 5 | none | benchmark | 172, 172 | 91.0 | 25.00 | 0.00 | 0.00 | 20.00 | 13.00 | 8,282 | 15,196 | 34 | 0.0% | 91, 20 |
| 1.00 of the budget | 5 | at payout 3 | development | 1887, 1887 | 21.0 | 5.86 | 1.00 | 0.26 | 2.27 | 2.32 | 1,891 | 2,637 | 73 | 38.8% | 87670, 18699 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 13.0 | 8.00 | 0.00 | 0.00 | 6.00 | 4.00 | 1,829 | 6,530 | 34 | 0.0% | 10, 8 |
| whole micros | 1 | none | development | 1887, 1887 | 9.3 | 2.86 | 0.00 | 0.00 | 2.26 | 2.55 | 966 | 3,031 | 130 | 8.1% | 38260, 11170 |
| whole micros | 1 | none | benchmark | 172, 172 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,233 | 3,999 | 33 | 0.0% | 12, 3 |
| whole micros | 1 | at payout 3 | development | 1887, 1887 | 7.6 | 2.40 | 0.00 | 0.00 | 1.56 | 2.11 | 805 | 2,511 | 130 | 8.1% | 31961, 9678 |
| whole micros | 1 | at payout 3 | benchmark | 172, 172 | 7.0 | 2.00 | 0.00 | 0.00 | 1.00 | 3.00 | 690 | 3,095 | 33 | 0.0% | 7, 2 |
| whole micros | 5 | none | development | 1887, 1887 | 37.2 | 10.08 | 1.05 | 0.36 | 7.49 | 8.02 | 3,508 | 9,108 | 82 | 37.9% | 151757, 35555 |
| whole micros | 5 | none | benchmark | 172, 172 | 67.0 | 21.00 | 0.00 | 0.00 | 16.00 | 18.00 | 6,559 | 18,901 | 33 | 0.0% | 67, 16 |
| whole micros | 5 | at payout 3 | development | 1887, 1887 | 19.8 | 5.47 | 0.97 | 0.36 | 1.79 | 2.37 | 1,852 | 2,542 | 82 | 37.9% | 82014, 17184 |
| whole micros | 5 | at payout 3 | benchmark | 172, 172 | 7.0 | 5.00 | 0.00 | 0.00 | 0.00 | 3.00 | 1,088 | 2,970 | 33 | 0.0% | 7, 3 |
| 0.95 of the budget | 1 | none | development | 1887, 1887 | 9.2 | 2.84 | 0.00 | 0.00 | 2.23 | 2.69 | 954 | 3,267 | 124 | 7.3% | 37829, 11079 |
| 0.95 of the budget | 1 | none | benchmark | 172, 172 | 12.0 | 5.00 | 0.00 | 0.00 | 4.00 | 5.00 | 1,382 | 5,646 | 43 | 0.0% | 12, 4 |
| 0.95 of the budget | 1 | at payout 3 | development | 1887, 1887 | 7.5 | 2.39 | 0.00 | 0.00 | 1.53 | 2.21 | 791 | 2,677 | 124 | 7.3% | 31462, 9647 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 9.0 | 3.00 | 0.00 | 0.00 | 2.00 | 3.00 | 937 | 4,122 | 43 | 0.0% | 9, 3 |
| 0.95 of the budget | 5 | none | development | 1887, 1887 | 37.3 | 9.98 | 0.97 | 0.34 | 7.42 | 8.40 | 3,524 | 9,887 | 79 | 36.9% | 152417, 35667 |
| 0.95 of the budget | 5 | none | benchmark | 172, 172 | 61.0 | 24.00 | 0.00 | 0.00 | 19.00 | 25.00 | 6,663 | 26,934 | 43 | 0.0% | 61, 19 |
| 0.95 of the budget | 5 | at payout 3 | development | 1887, 1887 | 19.5 | 5.40 | 0.96 | 0.34 | 1.70 | 2.42 | 1,828 | 2,650 | 79 | 36.9% | 80985, 16938 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 10.0 | 8.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,682 | 6,849 | 43 | 0.0% | 10, 7 |

### S1 on H3's favoured side: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,486 / 2,029 / 3,499 / 6,354 / 8,308 | 4,460 | 75.7% | 47.7% | 493 / 935 | n/a | 0%, 35, 41 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,424 / 4,424 / 4,424 / 4,424 / 4,424 | 4,424 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 31, 34 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,486 / 2,121 / 3,234 / 4,625 / 5,650 | 3,444 | 77.4% | 35.9% | 492 / 935 | 72.1% (193) | 0%, 35, 41 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,133 / 4,133 / 4,133 / 4,133 / 4,133 | 4,133 | 100.0% | 100.0% | 396 / 396 | 100.0% (201) | 0%, 31, 34 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 41.8% | 114 | 23 / 34 / 1,123 / 15,261 / 26,552 | 8,463 | 47.0% | 41.0% | 1,962 / 1,988 | n/a | 0%, 35, 41 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 8,447 / 8,447 / 8,447 / 8,447 / 8,447 | 8,447 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 31, 34 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 34.3% | 98 | 30 / 38 / 1,487 / 3,802 / 5,510 | 2,174 | 41.5% | 22.6% | 1,960 / 1,976 | 65.6% (67) | 0%, 35, 41 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,700 / 6,700 / 6,700 / 6,700 / 6,700 | 6,700 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 31, 34 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1887, 1887 | 13.1 | 3.56 | 0.00 | 0.00 | 3.03 | 3.85 | 1,247 | 3,707 | 84 | 0.0% | 53845, 14076 |
| 1.00 of the budget | 1 | none | benchmark | 172, 172 | 18.0 | 5.00 | 0.00 | 0.00 | 4.00 | 4.00 | 1,676 | 4,100 | 34 | 0.0% | 18, 4 |
| 1.00 of the budget | 1 | at payout 3 | development | 1887, 1887 | 9.8 | 2.76 | 0.00 | 0.00 | 1.92 | 2.64 | 956 | 2,400 | 84 | 0.0% | 41038, 11380 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 13.0 | 3.00 | 0.00 | 0.00 | 2.00 | 3.00 | 1,133 | 3,266 | 34 | 0.0% | 13, 3 |
| 1.00 of the budget | 5 | none | development | 1887, 1887 | 46.4 | 13.16 | 1.41 | 0.37 | 10.29 | 11.21 | 4,280 | 10,743 | 60 | 24.1% | 191537, 46832 |
| 1.00 of the budget | 5 | none | benchmark | 172, 172 | 95.0 | 28.00 | 0.00 | 0.00 | 23.00 | 17.00 | 8,925 | 15,372 | 34 | 0.0% | 95, 23 |
| 1.00 of the budget | 5 | at payout 3 | development | 1887, 1887 | 20.0 | 5.80 | 1.08 | 0.23 | 1.88 | 2.72 | 1,806 | 1,981 | 60 | 24.1% | 83432, 17997 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 13.0 | 8.00 | 0.00 | 0.00 | 6.00 | 4.00 | 1,829 | 6,530 | 34 | 0.0% | 10, 8 |

### S1 on H3's favoured side: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,607 / 2,640 / 4,334 / 6,132 / 8,210 | 4,703 | 86.5% | 55.5% | 492 / 1,082 | n/a | 0%, 35, 41 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,530 / 4,530 / 4,530 / 4,530 / 4,530 | 4,530 | 100.0% | 100.0% | 396 / 396 | n/a | 0%, 31, 34 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,607 / 2,640 / 4,153 / 5,190 / 5,997 | 3,990 | 86.5% | 52.6% | 492 / 1,082 | 61.1% (208) | 0%, 35, 41 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,284 / 4,284 / 4,284 / 4,284 / 4,284 | 4,284 | 100.0% | 100.0% | 396 / 396 | 100.0% (217) | 0%, 31, 34 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 40.1% | 99 | 30 / 34 / 3,654 / 14,613 / 26,294 | 8,955 | 53.8% | 49.6% | 1,964 / 1,974 | n/a | 0%, 35, 41 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,780 / 10,780 / 10,780 / 10,780 / 10,780 | 10,780 | 100.0% | 100.0% | 1,682 / 1,682 | n/a | 0%, 31, 34 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.0% | 97 | 30 / 34 / 3,345 / 5,131 / 6,165 | 2,845 | 56.8% | 38.8% | 1,964 / 1,974 | 57.9% (79) | 0%, 35, 41 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,700 / 6,700 / 6,700 / 6,700 / 6,700 | 6,700 | 100.0% | 100.0% | 1,682 / 1,682 | 100.0% (44) | 0%, 31, 34 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1887, 1887 | 11.2 | 3.21 | 0.00 | 0.00 | 2.58 | 3.14 | 1,084 | 3,787 | 116 | 6.3% | 46338, 12591 |
| 1.00 of the budget | 1 | none | benchmark | 172, 172 | 17.0 | 5.00 | 0.00 | 0.00 | 4.00 | 4.00 | 1,627 | 4,157 | 34 | 0.0% | 17, 4 |
| 1.00 of the budget | 1 | at payout 3 | development | 1887, 1887 | 8.9 | 2.60 | 0.00 | 0.00 | 1.73 | 2.34 | 874 | 2,863 | 116 | 6.3% | 37490, 10644 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 172, 172 | 13.0 | 3.00 | 0.00 | 0.00 | 2.00 | 3.00 | 1,133 | 3,417 | 34 | 0.0% | 13, 3 |
| 1.00 of the budget | 5 | none | development | 1887, 1887 | 40.5 | 11.24 | 1.07 | 0.21 | 8.47 | 9.11 | 3,717 | 10,672 | 74 | 37.3% | 167411, 40178 |
| 1.00 of the budget | 5 | none | benchmark | 172, 172 | 88.0 | 25.00 | 0.00 | 0.00 | 20.00 | 15.00 | 8,135 | 16,916 | 34 | 0.0% | 88, 20 |
| 1.00 of the budget | 5 | at payout 3 | development | 1887, 1887 | 20.5 | 5.98 | 1.04 | 0.21 | 2.25 | 2.40 | 1,868 | 2,713 | 74 | 37.3% | 85567, 18999 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 172, 172 | 13.0 | 8.00 | 0.00 | 0.00 | 6.00 | 4.00 | 1,829 | 6,530 | 34 | 0.0% | 10, 8 |

### S3 on H3's favoured side: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,472 / 2,651 / 4,683 / 7,194 / 8,842 | 5,009 | 83.9% | 57.4% | 492 / 919 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,895 / 4,895 / 4,895 / 4,895 / 4,895 | 4,895 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,472 / 2,701 / 3,613 / 4,794 / 5,815 | 3,704 | 84.3% | 44.7% | 492 / 919 | 75.8% (187) | 0%, 39, 34 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,548 / 4,548 / 4,548 / 4,548 / 4,548 | 4,548 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 32, 37 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 40.2% | 120 | 26 / 34 / 3,460 / 17,868 / 28,706 | 9,808 | 52.5% | 48.7% | 1,960 / 1,987 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 13,037 / 13,037 / 13,037 / 13,037 / 13,037 | 13,037 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 28.2% | 108 | 32 / 40 / 1,779 / 4,084 / 5,682 | 2,323 | 45.1% | 25.7% | 1,736 / 1,970 | 71.7% (69) | 0%, 39, 34 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,066 / 5,066 / 5,066 / 5,066 / 5,066 | 5,066 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 32, 37 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,344 / 2,159 / 3,564 / 5,847 / 7,458 | 4,075 | 77.2% | 45.5% | 443 / 925 | n/a | 0%, 43, 32 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,902 / 4,902 / 4,902 / 4,902 / 4,902 | 4,902 | 100.0% | 100.0% | 247 / 247 | n/a | 29%, 35, 4 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,344 / 2,207 / 3,059 / 3,973 / 5,051 | 3,146 | 78.4% | 23.1% | 443 / 925 | 68.6% (196) | 0%, 43, 32 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,131 / 4,131 / 4,131 / 4,131 / 4,131 | 4,131 | 100.0% | 100.0% | 247 / 247 | 100.0% (85) | 29%, 35, 4 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 36.3% | 134 | 21 / 38 / 4,617 / 14,409 / 26,832 | 9,029 | 56.0% | 51.9% | 1,960 / 1,988 | n/a | 0%, 43, 32 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 16,155 / 16,155 / 16,155 / 16,155 / 16,155 | 16,155 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 29%, 35, 4 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 25.6% | 124 | 30 / 41 / 1,943 / 3,477 / 5,031 | 2,236 | 48.7% | 19.0% | 1,725 / 1,970 | 74.2% (73) | 0%, 43, 32 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,073 / 4,073 / 4,073 / 4,073 / 4,073 | 4,073 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (34) | 29%, 35, 4 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,227 / 2,423 / 4,118 / 6,651 / 8,556 | 4,592 | 79.4% | 52.8% | 443 / 933 | n/a | 0%, 41, 36 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,735 / 4,735 / 4,735 / 4,735 / 4,735 | 4,735 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 33, 36 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,227 / 2,501 / 3,305 / 4,277 / 5,630 | 3,405 | 79.9% | 34.9% | 443 / 933 | 69.5% (185) | 0%, 41, 36 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,408 / 4,408 / 4,408 / 4,408 / 4,408 | 4,408 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 33, 36 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 38.1% | 131 | 28 / 35 / 6,031 / 18,007 / 29,442 | 10,171 | 55.8% | 52.3% | 1,960 / 1,985 | n/a | 0%, 41, 36 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,564 / 12,564 / 12,564 / 12,564 / 12,564 | 12,564 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 33, 36 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 27.8% | 123 | 30 / 40 / 1,906 / 3,716 / 5,651 | 2,345 | 48.2% | 22.0% | 1,725 / 1,970 | 72.0% (70) | 0%, 41, 36 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,851 / 4,851 / 4,851 / 4,851 / 4,851 | 4,851 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 33, 36 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1814, 1814 | 11.6 | 2.87 | 0.00 | 0.00 | 2.29 | 4.13 | 1,083 | 4,091 | 84 | 0.3% | 47927, 11234 |
| 1.00 of the budget | 1 | none | benchmark | 152, 152 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,282 | 4,177 | 33 | 0.0% | 12, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 1814, 1814 | 8.7 | 2.18 | 0.00 | 0.00 | 1.29 | 2.69 | 823 | 2,527 | 84 | 0.3% | 36901, 8911 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,795 | 33 | 0.0% | 2, 1 |
| 1.00 of the budget | 5 | none | development | 1814, 1814 | 44.0 | 12.31 | 1.28 | 0.43 | 9.47 | 13.40 | 4,092 | 11,900 | 61 | 23.0% | 180927, 43714 |
| 1.00 of the budget | 5 | none | benchmark | 152, 152 | 69.0 | 17.00 | 0.00 | 0.00 | 15.00 | 21.00 | 6,404 | 17,441 | 33 | 0.0% | 66, 16 |
| 1.00 of the budget | 5 | at payout 3 | development | 1814, 1814 | 18.7 | 5.34 | 0.79 | 0.22 | 1.38 | 3.02 | 1,735 | 2,058 | 61 | 23.0% | 77602, 17335 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,301 | 33 | 0.0% | 10, 4 |
| whole micros | 1 | none | development | 1814, 1809 | 9.3 | 2.90 | 0.00 | 0.00 | 2.33 | 3.67 | 988 | 3,063 | 86 | 0.4% | 37909, 11196 |
| whole micros | 1 | none | benchmark | 152, 130 | 10.0 | 3.00 | 0.00 | 0.00 | 2.00 | 5.00 | 1,035 | 3,937 | 33 | 0.0% | 10, 2 |
| whole micros | 1 | at payout 3 | development | 1814, 1809 | 7.3 | 2.23 | 0.00 | 0.00 | 1.38 | 2.53 | 772 | 1,918 | 86 | 0.4% | 30526, 9099 |
| whole micros | 1 | at payout 3 | benchmark | 152, 130 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,378 | 33 | 0.0% | 2, 1 |
| whole micros | 5 | none | development | 1814, 1809 | 37.2 | 11.99 | 1.11 | 0.51 | 9.19 | 13.13 | 3,822 | 10,852 | 66 | 20.9% | 151092, 42676 |
| whole micros | 5 | none | benchmark | 152, 130 | 49.0 | 11.00 | 0.00 | 0.00 | 10.00 | 26.00 | 4,579 | 18,734 | 33 | 0.0% | 45, 10 |
| whole micros | 5 | at payout 3 | development | 1814, 1809 | 17.2 | 5.26 | 0.77 | 0.37 | 1.20 | 3.12 | 1,699 | 1,935 | 66 | 20.9% | 70550, 16941 |
| whole micros | 5 | at payout 3 | benchmark | 152, 130 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 3,308 | 33 | 0.0% | 10, 4 |
| 0.95 of the budget | 1 | none | development | 1814, 1814 | 9.5 | 2.88 | 0.00 | 0.00 | 2.31 | 3.89 | 993 | 3,584 | 84 | 2.2% | 38629, 11207 |
| 0.95 of the budget | 1 | none | benchmark | 152, 152 | 11.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,233 | 3,968 | 33 | 0.0% | 11, 3 |
| 0.95 of the budget | 1 | at payout 3 | development | 1814, 1814 | 7.3 | 2.19 | 0.00 | 0.00 | 1.35 | 2.53 | 768 | 2,173 | 84 | 2.2% | 30492, 8976 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,655 | 33 | 0.0% | 2, 1 |
| 0.95 of the budget | 5 | none | development | 1814, 1814 | 38.0 | 12.02 | 1.19 | 0.38 | 9.17 | 13.69 | 3,826 | 11,998 | 63 | 23.3% | 155217, 42775 |
| 0.95 of the budget | 5 | none | benchmark | 152, 152 | 57.0 | 17.00 | 0.00 | 0.00 | 15.00 | 21.00 | 5,816 | 16,380 | 33 | 0.0% | 54, 16 |
| 0.95 of the budget | 5 | at payout 3 | development | 1814, 1814 | 17.1 | 5.32 | 0.81 | 0.25 | 1.25 | 3.08 | 1,691 | 2,036 | 63 | 23.3% | 70959, 17136 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,086 | 33 | 0.0% | 10, 4 |

### S3 on H3's favoured side: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,557 / 2,871 / 4,865 / 7,512 / 8,879 | 5,204 | 84.3% | 61.7% | 443 / 1,033 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,895 / 4,895 / 4,895 / 4,895 / 4,895 | 4,895 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,557 / 2,871 / 4,244 / 5,174 / 5,960 | 4,004 | 84.3% | 54.6% | 443 / 1,033 | 64.3% (194) | 0%, 39, 34 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,548 / 4,548 / 4,548 / 4,548 / 4,548 | 4,548 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 32, 37 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 39.9% | 114 | 30 / 34 / 6,322 / 18,255 / 32,498 | 10,826 | 56.5% | 53.9% | 1,960 / 1,970 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,580 / 12,580 / 12,580 / 12,580 / 12,580 | 12,580 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.7% | 114 | 30 / 34 / 3,276 / 5,063 / 6,380 | 2,814 | 56.1% | 37.4% | 1,960 / 1,970 | 57.6% (85) | 0%, 39, 34 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,066 / 5,066 / 5,066 / 5,066 / 5,066 | 5,066 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 32, 37 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,459 / 2,508 / 4,131 / 5,945 / 8,575 | 4,488 | 84.6% | 54.1% | 394 / 937 | n/a | 0%, 43, 32 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,846 / 4,846 / 4,846 / 4,846 / 4,846 | 4,846 | 100.0% | 100.0% | 247 / 247 | n/a | 29%, 35, 4 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,459 / 2,508 / 4,111 / 4,800 / 5,647 | 3,754 | 84.6% | 52.2% | 394 / 937 | 54.0% (198) | 0%, 43, 32 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,074 / 4,074 / 4,074 / 4,074 / 4,074 | 4,074 | 100.0% | 100.0% | 247 / 247 | 100.0% (93) | 29%, 35, 4 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 35.9% | 126 | 30 / 36 / 5,147 / 16,603 / 28,589 | 10,027 | 58.1% | 53.5% | 1,960 / 1,974 | n/a | 0%, 43, 32 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 15,197 / 15,197 / 15,197 / 15,197 / 15,197 | 15,197 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 29%, 35, 4 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 35.5% | 126 | 30 / 38 / 3,186 / 5,368 / 6,007 | 2,881 | 58.7% | 38.7% | 1,960 / 1,974 | 61.1% (99) | 0%, 43, 32 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,716 / 4,716 / 4,716 / 4,716 / 4,716 | 4,716 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (34) | 29%, 35, 4 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,359 / 2,775 / 4,469 / 7,161 / 9,025 | 4,858 | 83.1% | 57.3% | 443 / 1,032 | n/a | 0%, 41, 36 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,735 / 4,735 / 4,735 / 4,735 / 4,735 | 4,735 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 33, 36 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,359 / 2,775 / 4,259 / 5,073 / 5,851 | 3,894 | 83.1% | 56.1% | 443 / 1,032 | 60.3% (189) | 0%, 41, 36 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,408 / 4,408 / 4,408 / 4,408 / 4,408 | 4,408 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 33, 36 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 39.1% | 126 | 30 / 34 / 6,902 / 19,773 / 32,112 | 11,403 | 57.3% | 55.7% | 1,960 / 1,972 | n/a | 0%, 41, 36 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 10,723 / 10,723 / 10,723 / 10,723 / 10,723 | 10,723 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 33, 36 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.0% | 126 | 30 / 34 / 3,357 / 5,514 / 6,282 | 2,915 | 57.1% | 39.9% | 1,960 / 1,972 | 58.9% (89) | 0%, 41, 36 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,851 / 4,851 / 4,851 / 4,851 / 4,851 | 4,851 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 33, 36 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1814, 1814 | 10.3 | 2.63 | 0.00 | 0.00 | 1.96 | 3.50 | 963 | 4,167 | 102 | 10.4% | 42740, 10164 |
| 1.00 of the budget | 1 | none | benchmark | 152, 152 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,282 | 4,177 | 33 | 0.0% | 12, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 1814, 1814 | 8.3 | 2.07 | 0.00 | 0.00 | 1.18 | 2.35 | 773 | 2,777 | 102 | 10.4% | 34991, 8396 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,795 | 33 | 0.0% | 2, 1 |
| 1.00 of the budget | 5 | none | development | 1814, 1814 | 36.7 | 10.28 | 0.89 | 0.24 | 7.55 | 10.50 | 3,447 | 12,273 | 74 | 33.7% | 151539, 36576 |
| 1.00 of the budget | 5 | none | benchmark | 152, 152 | 69.0 | 17.00 | 0.00 | 0.00 | 15.00 | 20.00 | 6,404 | 16,984 | 33 | 0.0% | 66, 15 |
| 1.00 of the budget | 5 | at payout 3 | development | 1814, 1814 | 20.3 | 5.71 | 0.87 | 0.24 | 2.10 | 2.45 | 1,863 | 2,676 | 74 | 33.7% | 84938, 18416 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,301 | 33 | 0.0% | 10, 4 |
| whole micros | 1 | none | development | 1814, 1809 | 8.0 | 2.43 | 0.00 | 0.00 | 1.77 | 2.88 | 838 | 3,326 | 116 | 11.3% | 32703, 9267 |
| whole micros | 1 | none | benchmark | 152, 130 | 10.0 | 3.00 | 0.00 | 0.00 | 2.00 | 5.00 | 1,035 | 3,881 | 34 | 0.0% | 10, 2 |
| whole micros | 1 | at payout 3 | development | 1814, 1809 | 6.5 | 1.92 | 0.00 | 0.00 | 1.07 | 2.17 | 680 | 2,434 | 116 | 11.3% | 27230, 7676 |
| whole micros | 1 | at payout 3 | benchmark | 152, 130 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,321 | 34 | 0.0% | 2, 1 |
| whole micros | 5 | none | development | 1814, 1809 | 31.3 | 10.01 | 0.94 | 0.26 | 7.07 | 9.88 | 3,203 | 11,229 | 85 | 32.7% | 128120, 34601 |
| whole micros | 5 | none | benchmark | 152, 130 | 43.0 | 11.00 | 0.00 | 0.00 | 10.00 | 23.00 | 4,089 | 17,286 | 34 | 0.0% | 39, 10 |
| whole micros | 5 | at payout 3 | development | 1814, 1809 | 19.0 | 5.79 | 0.91 | 0.26 | 1.93 | 2.64 | 1,863 | 2,744 | 85 | 32.7% | 79471, 18639 |
| whole micros | 5 | at payout 3 | benchmark | 152, 130 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 3,951 | 34 | 0.0% | 10, 4 |
| 0.95 of the budget | 1 | none | development | 1814, 1814 | 8.3 | 2.61 | 0.00 | 0.00 | 1.97 | 3.18 | 884 | 3,742 | 107 | 13.3% | 34155, 10003 |
| 0.95 of the budget | 1 | none | benchmark | 152, 152 | 11.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,233 | 3,968 | 33 | 0.0% | 11, 3 |
| 0.95 of the budget | 1 | at payout 3 | development | 1814, 1814 | 6.7 | 2.04 | 0.00 | 0.00 | 1.18 | 2.22 | 705 | 2,598 | 107 | 13.3% | 27974, 8286 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,655 | 33 | 0.0% | 2, 1 |
| 0.95 of the budget | 5 | none | development | 1814, 1814 | 32.2 | 10.31 | 0.98 | 0.25 | 7.45 | 11.04 | 3,275 | 12,678 | 76 | 34.0% | 132159, 36061 |
| 0.95 of the budget | 5 | none | benchmark | 152, 152 | 49.0 | 17.00 | 0.00 | 0.00 | 15.00 | 16.00 | 5,424 | 14,147 | 33 | 0.0% | 46, 15 |
| 0.95 of the budget | 5 | at payout 3 | development | 1814, 1814 | 19.0 | 5.84 | 0.97 | 0.25 | 2.02 | 2.57 | 1,847 | 2,762 | 76 | 34.0% | 79510, 18685 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,086 | 33 | 0.0% | 10, 4 |

### S3 on H3's favoured side: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,470 / 2,650 / 4,677 / 7,194 / 8,832 | 5,003 | 83.6% | 57.4% | 492 / 933 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,895 / 4,895 / 4,895 / 4,895 / 4,895 | 4,895 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,470 / 2,699 / 3,613 / 4,801 / 5,815 | 3,701 | 84.1% | 44.9% | 492 / 933 | 75.6% (187) | 0%, 39, 34 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,548 / 4,548 / 4,548 / 4,548 / 4,548 | 4,548 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 32, 37 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 40.2% | 120 | 25 / 34 / 3,460 / 18,387 / 28,706 | 9,848 | 52.4% | 48.7% | 1,960 / 1,987 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 13,037 / 13,037 / 13,037 / 13,037 / 13,037 | 13,037 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 28.4% | 108 | 31 / 40 / 1,779 / 4,084 / 5,692 | 2,325 | 45.1% | 25.7% | 1,745 / 1,970 | 71.6% (69) | 0%, 39, 34 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,066 / 5,066 / 5,066 / 5,066 / 5,066 | 5,066 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 32, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1814, 1814 | 11.6 | 2.87 | 0.00 | 0.00 | 2.29 | 4.13 | 1,086 | 4,089 | 83 | 0.3% | 48016, 11245 |
| 1.00 of the budget | 1 | none | benchmark | 152, 152 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,282 | 4,177 | 33 | 0.0% | 12, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 1814, 1814 | 8.8 | 2.18 | 0.00 | 0.00 | 1.29 | 2.69 | 827 | 2,528 | 83 | 0.3% | 37027, 8923 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,795 | 33 | 0.0% | 2, 1 |
| 1.00 of the budget | 5 | none | development | 1814, 1814 | 44.0 | 12.32 | 1.29 | 0.42 | 9.47 | 13.42 | 4,097 | 11,945 | 61 | 23.1% | 181148, 43702 |
| 1.00 of the budget | 5 | none | benchmark | 152, 152 | 69.0 | 17.00 | 0.00 | 0.00 | 15.00 | 21.00 | 6,404 | 17,441 | 33 | 0.0% | 66, 16 |
| 1.00 of the budget | 5 | at payout 3 | development | 1814, 1814 | 18.6 | 5.35 | 0.80 | 0.22 | 1.38 | 3.01 | 1,733 | 2,058 | 61 | 23.1% | 77482, 17328 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,301 | 33 | 0.0% | 10, 4 |

### S3 on H3's favoured side: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,557 / 2,871 / 4,834 / 7,512 / 8,879 | 5,180 | 84.0% | 61.4% | 443 / 1,033 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,895 / 4,895 / 4,895 / 4,895 / 4,895 | 4,895 | 100.0% | 100.0% | 247 / 247 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,557 / 2,871 / 4,244 / 5,212 / 5,959 | 3,998 | 84.0% | 54.3% | 443 / 1,033 | 64.0% (194) | 0%, 39, 34 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,548 / 4,548 / 4,548 / 4,548 / 4,548 | 4,548 | 100.0% | 100.0% | 247 / 247 | 100.0% (80) | 1%, 32, 37 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 40.0% | 114 | 30 / 34 / 6,341 / 18,251 / 32,498 | 10,822 | 56.4% | 53.9% | 1,960 / 1,970 | n/a | 0%, 39, 34 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 12,580 / 12,580 / 12,580 / 12,580 / 12,580 | 12,580 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 1%, 32, 37 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 39.8% | 114 | 30 / 34 / 3,276 / 5,063 / 6,378 | 2,815 | 56.0% | 38.0% | 1,960 / 1,970 | 57.6% (85) | 0%, 39, 34 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,066 / 5,066 / 5,066 / 5,066 / 5,066 | 5,066 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (33) | 1%, 32, 37 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 1814, 1814 | 10.4 | 2.63 | 0.00 | 0.00 | 1.99 | 3.48 | 973 | 4,152 | 102 | 10.4% | 43086, 10212 |
| 1.00 of the budget | 1 | none | benchmark | 152, 152 | 12.0 | 4.00 | 0.00 | 0.00 | 3.00 | 4.00 | 1,282 | 4,177 | 33 | 0.0% | 12, 3 |
| 1.00 of the budget | 1 | at payout 3 | development | 1814, 1814 | 8.4 | 2.07 | 0.00 | 0.00 | 1.18 | 2.34 | 780 | 2,779 | 102 | 10.4% | 35289, 8414 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 152, 152 | 2.0 | 1.00 | 0.00 | 0.00 | 0.00 | 3.00 | 247 | 2,795 | 33 | 0.0% | 2, 1 |
| 1.00 of the budget | 5 | none | development | 1814, 1814 | 36.6 | 10.28 | 0.89 | 0.23 | 7.55 | 10.49 | 3,447 | 12,269 | 74 | 33.8% | 151402, 36571 |
| 1.00 of the budget | 5 | none | benchmark | 152, 152 | 69.0 | 17.00 | 0.00 | 0.00 | 15.00 | 20.00 | 6,404 | 16,984 | 33 | 0.0% | 66, 15 |
| 1.00 of the budget | 5 | at payout 3 | development | 1814, 1814 | 20.3 | 5.71 | 0.88 | 0.23 | 2.10 | 2.45 | 1,861 | 2,676 | 74 | 33.8% | 84815, 18407 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 152, 152 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,301 | 33 | 0.0% | 10, 4 |

### S4 on H3's favoured side: topstep_50k_x, ask

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,270 / 2,867 / 4,666 / 7,335 / 9,636 | 5,235 | 83.8% | 63.1% | 541 / 1,133 | n/a | 0%, 34, 36 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,768 / 2,768 / 2,768 / 2,768 / 2,768 | 2,768 | 100.0% | 0.0% | 736 / 736 | n/a | 0%, 23, 30 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,270 / 2,597 / 3,806 / 4,832 / 5,428 | 3,638 | 83.9% | 46.7% | 541 / 1,133 | 77.3% (172) | 0%, 34, 36 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,768 / 2,768 / 2,768 / 2,768 / 2,768 | 2,768 | 100.0% | 0.0% | 736 / 736 | 100.0% (313) | 0%, 23, 30 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 45.5% | 106 | 24 / 34 / 1,736 / 18,586 / 35,598 | 10,948 | 49.3% | 47.4% | 1,962 / 1,983 | n/a | 0%, 34, 36 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 272 | 41 / 41 / 41 / 41 / 41 | 41 | 0.0% | 0.0% | 1,959 / 1,959 | n/a | 0%, 23, 30 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 35.6% | 98 | 30 / 40 / 1,637 / 4,119 / 5,478 | 2,236 | 44.3% | 26.0% | 1,926 / 1,972 | 64.3% (60) | 0%, 34, 36 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,928 / 3,928 / 3,928 / 3,928 / 3,928 | 3,928 | 100.0% | 0.0% | 1,431 / 1,431 | 100.0% (34) | 0%, 23, 30 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,223 / 2,053 / 4,203 / 6,413 / 8,656 | 4,479 | 75.9% | 52.7% | 492 / 1,034 | n/a | 0%, 36, 38 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,081 / 3,081 / 3,081 / 3,081 / 3,081 | 3,081 | 100.0% | 0.0% | 247 / 247 | n/a | 0%, 30, 31 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,223 / 2,116 / 3,338 / 4,421 / 4,976 | 3,224 | 76.0% | 31.9% | 492 / 1,034 | 66.4% (166) | 0%, 36, 38 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,081 / 3,081 / 3,081 / 3,081 / 3,081 | 3,081 | 100.0% | 0.0% | 247 / 247 | 100.0% (313) | 0%, 30, 31 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 44.6% | 122 | 26 / 34 / 2,240 / 19,279 / 33,635 | 10,484 | 50.3% | 47.3% | 1,960 / 1,980 | n/a | 0%, 36, 38 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,571 / 3,571 / 3,571 / 3,571 / 3,571 | 3,571 | 100.0% | 0.0% | 1,333 / 1,333 | n/a | 0%, 30, 31 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 35.7% | 115 | 30 / 40 / 1,799 / 3,730 / 5,033 | 2,155 | 47.6% | 20.4% | 1,874 / 1,974 | 64.1% (62) | 0%, 36, 38 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,144 / 3,144 / 3,144 / 3,144 / 3,144 | 3,144 | 100.0% | 0.0% | 1,333 / 1,333 | 100.0% (43) | 0%, 30, 31 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,190 / 2,177 / 4,400 / 6,712 / 9,107 | 4,734 | 80.4% | 55.0% | 481 / 1,033 | n/a | 0%, 35, 34 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,142 / 3,142 / 3,142 / 3,142 / 3,142 | 3,142 | 100.0% | 0.0% | 287 / 287 | n/a | 0%, 24, 29 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,190 / 2,177 / 3,184 / 4,573 / 5,298 | 3,319 | 80.4% | 34.7% | 481 / 1,033 | 65.4% (169) | 0%, 35, 34 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,142 / 3,142 / 3,142 / 3,142 / 3,142 | 3,142 | 100.0% | 0.0% | 287 / 287 | 100.0% (313) | 0%, 24, 29 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 43.6% | 122 | 26 / 32 / 4,083 / 20,714 / 34,169 | 11,143 | 52.3% | 50.1% | 1,960 / 1,982 | n/a | 0%, 35, 34 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 1,441 / 1,441 / 1,441 / 1,441 / 1,441 | 1,441 | 0.0% | 0.0% | 1,988 / 1,988 | n/a | 0%, 24, 29 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 34.4% | 114 | 30 / 40 / 1,820 / 4,127 / 5,551 | 2,341 | 48.5% | 26.1% | 1,872 / 1,976 | 65.4% (62) | 0%, 35, 34 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 3,956 / 3,956 / 3,956 / 3,956 / 3,956 | 3,956 | 100.0% | 0.0% | 1,235 / 1,235 | 100.0% (34) | 0%, 24, 29 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 2295, 2295 | 14.3 | 3.87 | 0.00 | 0.00 | 3.32 | 4.30 | 1,334 | 4,570 | 79 | 1.9% | 59066, 15333 |
| 1.00 of the budget | 1 | none | benchmark | 246, 246 | 20.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 2,172 | 2,940 | 34 | 0.0% | 20, 8 |
| 1.00 of the budget | 1 | at payout 3 | development | 2295, 2295 | 9.6 | 2.57 | 0.00 | 0.00 | 1.68 | 2.62 | 902 | 2,540 | 79 | 1.9% | 40641, 10657 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 20.0 | 8.00 | 0.00 | 0.00 | 7.00 | 3.00 | 2,172 | 2,940 | 34 | 0.0% | 20, 8 |
| 1.00 of the budget | 5 | none | development | 2295, 2295 | 48.1 | 14.23 | 1.12 | 0.32 | 11.81 | 13.14 | 4,510 | 13,458 | 54 | 27.9% | 199336, 53017 |
| 1.00 of the budget | 5 | none | benchmark | 246, 246 | 96.0 | 31.00 | 0.00 | 0.00 | 31.00 | 10.00 | 9,323 | 7,364 | 34 | 0.0% | 96, 31 |
| 1.00 of the budget | 5 | at payout 3 | development | 2295, 2295 | 19.8 | 5.33 | 0.75 | 0.21 | 1.74 | 2.71 | 1,760 | 1,996 | 54 | 27.9% | 82758, 17748 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 14.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,431 | 3,359 | 34 | 0.0% | 14, 4 |
| whole micros | 1 | none | development | 2295, 2290 | 11.9 | 3.56 | 0.00 | 0.00 | 3.03 | 4.05 | 1,202 | 3,682 | 81 | 3.0% | 48984, 14125 |
| whole micros | 1 | none | benchmark | 246, 248 | 14.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,729 | 2,810 | 44 | 0.0% | 14, 7 |
| whole micros | 1 | at payout 3 | development | 2295, 2290 | 8.6 | 2.41 | 0.00 | 0.00 | 1.59 | 2.43 | 855 | 2,079 | 81 | 3.0% | 36011, 9925 |
| whole micros | 1 | at payout 3 | benchmark | 246, 248 | 14.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,729 | 2,810 | 44 | 0.0% | 14, 7 |
| whole micros | 5 | none | development | 2295, 2290 | 41.6 | 13.07 | 0.96 | 0.37 | 10.75 | 13.83 | 4,108 | 12,592 | 57 | 28.1% | 171053, 48611 |
| whole micros | 5 | none | benchmark | 246, 248 | 72.0 | 31.00 | 0.00 | 0.00 | 26.00 | 15.00 | 8,196 | 9,767 | 34 | 0.0% | 72, 27 |
| whole micros | 5 | at payout 3 | development | 2295, 2290 | 18.6 | 5.24 | 0.78 | 0.30 | 1.55 | 2.77 | 1,730 | 1,885 | 57 | 28.1% | 77329, 17125 |
| whole micros | 5 | at payout 3 | benchmark | 246, 248 | 12.0 | 7.00 | 0.00 | 0.00 | 2.00 | 4.00 | 1,631 | 2,775 | 34 | 0.0% | 12, 4 |
| 0.95 of the budget | 1 | none | development | 2295, 2295 | 11.9 | 3.64 | 0.00 | 0.00 | 3.12 | 3.97 | 1,211 | 3,944 | 80 | 3.0% | 48911, 14482 |
| 0.95 of the budget | 1 | none | benchmark | 246, 246 | 16.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,827 | 2,969 | 43 | 0.0% | 16, 7 |
| 0.95 of the budget | 1 | at payout 3 | development | 2295, 2295 | 8.8 | 2.55 | 0.00 | 0.00 | 1.74 | 2.43 | 882 | 2,201 | 80 | 3.0% | 36677, 10494 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 16.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,827 | 2,969 | 43 | 0.0% | 16, 7 |
| 0.95 of the budget | 5 | none | development | 2295, 2295 | 42.9 | 14.19 | 0.96 | 0.35 | 11.82 | 13.61 | 4,322 | 13,465 | 57 | 26.5% | 176364, 53249 |
| 0.95 of the budget | 5 | none | benchmark | 246, 246 | 83.0 | 36.00 | 3.00 | 0.00 | 31.00 | 11.00 | 8,984 | 8,425 | 34 | 0.0% | 82, 32 |
| 0.95 of the budget | 5 | at payout 3 | development | 2295, 2295 | 18.3 | 5.38 | 0.74 | 0.30 | 1.68 | 2.81 | 1,737 | 2,078 | 57 | 26.5% | 76245, 17733 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 3,191 | 34 | 0.0% | 10, 4 |

### S4 on H3's favoured side: topstep_50k_x, wait

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,643 / 3,243 / 4,663 / 7,392 / 9,675 | 5,248 | 85.9% | 62.6% | 492 / 1,180 | n/a | 0%, 34, 36 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,919 / 2,919 / 2,919 / 2,919 / 2,919 | 2,919 | 100.0% | 0.0% | 586 / 586 | n/a | 0%, 23, 30 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,643 / 3,243 / 4,095 / 5,090 / 5,736 | 3,962 | 85.9% | 53.2% | 492 / 1,180 | 68.7% (190) | 0%, 34, 36 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,919 / 2,919 / 2,919 / 2,919 / 2,919 | 2,919 | 100.0% | 0.0% | 586 / 586 | 0.0% (n/a) | 0%, 23, 30 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 45.1% | 103 | 30 / 34 / 2,610 / 19,091 / 35,253 | 10,869 | 50.7% | 47.5% | 1,962 / 1,974 | n/a | 0%, 34, 36 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 257 | 38 / 38 / 38 / 38 / 38 | 38 | 0.0% | 0.0% | 1,962 / 1,962 | n/a | 0%, 23, 30 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 42.8% | 101 | 30 / 34 / 2,599 / 5,086 / 6,133 | 2,628 | 51.6% | 35.3% | 1,962 / 1,974 | 54.6% (68) | 0%, 34, 36 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,723 / 5,723 / 5,723 / 5,723 / 5,723 | 5,723 | 100.0% | 100.0% | 1,431 / 1,431 | 100.0% (40) | 0%, 23, 30 |
| whole micros | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,080 / 2,301 / 4,416 / 7,217 / 9,151 | 4,832 | 79.3% | 56.5% | 492 / 1,082 | n/a | 0%, 36, 38 |
| whole micros | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,635 / 2,635 / 2,635 / 2,635 / 2,635 | 2,635 | 100.0% | 0.0% | 600 / 600 | n/a | 0%, 30, 31 |
| whole micros | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,080 / 2,301 / 4,178 / 4,947 / 5,559 | 3,684 | 79.3% | 52.0% | 492 / 1,082 | 59.2% (182) | 0%, 36, 38 |
| whole micros | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,635 / 2,635 / 2,635 / 2,635 / 2,635 | 2,635 | 100.0% | 0.0% | 600 / 600 | 0.0% (n/a) | 0%, 30, 31 |
| whole micros | 5 | none | development | 4266 (14.8; 365 days) | 43.2% | 120 | 30 / 32 / 3,929 / 19,780 / 36,600 | 11,633 | 51.8% | 49.9% | 1,960 / 1,976 | n/a | 0%, 36, 38 |
| whole micros | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,735 / 6,735 / 6,735 / 6,735 / 6,735 | 6,735 | 100.0% | 100.0% | 1,235 / 1,235 | n/a | 0%, 30, 31 |
| whole micros | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 42.0% | 119 | 30 / 34 / 2,804 / 5,063 / 6,043 | 2,625 | 53.3% | 35.1% | 1,960 / 1,976 | 55.6% (75) | 0%, 36, 38 |
| whole micros | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,505 / 6,505 / 6,505 / 6,505 / 6,505 | 6,505 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (44) | 0%, 30, 31 |
| 0.95 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,261 / 2,347 / 4,563 / 6,890 / 9,164 | 4,875 | 82.5% | 55.2% | 492 / 1,080 | n/a | 0%, 35, 34 |
| 0.95 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,625 / 2,625 / 2,625 / 2,625 / 2,625 | 2,625 | 100.0% | 0.0% | 804 / 804 | n/a | 0%, 24, 29 |
| 0.95 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,261 / 2,347 / 4,023 / 5,033 / 5,588 | 3,720 | 82.5% | 50.7% | 492 / 1,080 | 57.4% (185) | 0%, 35, 34 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,625 / 2,625 / 2,625 / 2,625 / 2,625 | 2,625 | 100.0% | 0.0% | 804 / 804 | 0.0% (n/a) | 0%, 24, 29 |
| 0.95 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 45.0% | 117 | 30 / 32 / 3,670 / 20,051 / 38,225 | 11,874 | 51.4% | 49.5% | 1,962 / 1,976 | n/a | 0%, 35, 34 |
| 0.95 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 23 / 23 / 23 / 23 / 23 | 23 | 0.0% | 0.0% | 1,977 / 1,977 | n/a | 0%, 24, 29 |
| 0.95 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 44.2% | 116 | 30 / 32 / 2,568 / 5,004 / 6,095 | 2,592 | 52.0% | 35.7% | 1,961 / 1,976 | 54.0% (73) | 0%, 35, 34 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 5,661 / 5,661 / 5,661 / 5,661 / 5,661 | 5,661 | 100.0% | 100.0% | 1,235 / 1,235 | 100.0% (40) | 0%, 24, 29 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 2295, 2295 | 13.1 | 3.64 | 0.00 | 0.00 | 3.01 | 3.64 | 1,227 | 4,476 | 100 | 9.3% | 54292, 14300 |
| 1.00 of the budget | 1 | none | benchmark | 246, 246 | 19.0 | 6.00 | 0.00 | 0.00 | 5.00 | 2.00 | 1,874 | 2,793 | 40 | 0.0% | 19, 6 |
| 1.00 of the budget | 1 | at payout 3 | development | 2295, 2295 | 9.2 | 2.54 | 0.00 | 0.00 | 1.63 | 2.40 | 870 | 2,832 | 100 | 9.3% | 39087, 10452 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 19.0 | 6.00 | 0.00 | 0.00 | 5.00 | 2.00 | 1,874 | 2,793 | 40 | 0.0% | 19, 6 |
| 1.00 of the budget | 5 | none | development | 2295, 2295 | 42.7 | 12.42 | 0.98 | 0.21 | 9.98 | 10.60 | 3,958 | 12,827 | 63 | 37.8% | 177093, 45640 |
| 1.00 of the budget | 5 | none | benchmark | 246, 246 | 79.0 | 28.00 | 0.00 | 0.00 | 28.00 | 5.00 | 8,141 | 6,179 | 40 | 0.0% | 79, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 2295, 2295 | 21.0 | 5.61 | 0.84 | 0.20 | 2.23 | 2.29 | 1,853 | 2,482 | 63 | 37.8% | 87806, 18542 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 14.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,431 | 5,154 | 40 | 0.0% | 14, 4 |
| whole micros | 1 | none | development | 2295, 2290 | 10.5 | 3.12 | 0.00 | 0.00 | 2.53 | 3.32 | 1,055 | 3,887 | 105 | 13.5% | 42961, 12146 |
| whole micros | 1 | none | benchmark | 246, 248 | 13.0 | 7.00 | 0.00 | 0.00 | 6.00 | 2.00 | 1,680 | 2,315 | 44 | 0.0% | 13, 7 |
| whole micros | 1 | at payout 3 | development | 2295, 2290 | 8.2 | 2.29 | 0.00 | 0.00 | 1.47 | 2.20 | 812 | 2,497 | 105 | 13.5% | 34231, 9381 |
| whole micros | 1 | at payout 3 | benchmark | 246, 248 | 13.0 | 7.00 | 0.00 | 0.00 | 6.00 | 2.00 | 1,680 | 2,315 | 44 | 0.0% | 13, 7 |
| whole micros | 5 | none | development | 2295, 2290 | 37.2 | 11.49 | 0.94 | 0.28 | 9.06 | 11.26 | 3,631 | 13,264 | 67 | 37.9% | 152825, 41757 |
| whole micros | 5 | none | benchmark | 246, 248 | 62.0 | 29.00 | 0.00 | 0.00 | 24.00 | 13.00 | 7,408 | 12,143 | 40 | 0.0% | 62, 25 |
| whole micros | 5 | at payout 3 | development | 2295, 2290 | 20.2 | 5.80 | 0.91 | 0.27 | 2.21 | 2.39 | 1,885 | 2,510 | 67 | 37.9% | 84770, 18402 |
| whole micros | 5 | at payout 3 | benchmark | 246, 248 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 5.00 | 1,235 | 5,740 | 40 | 0.0% | 10, 5 |
| 0.95 of the budget | 1 | none | development | 2295, 2295 | 11.0 | 3.39 | 0.00 | 0.00 | 2.82 | 3.26 | 1,116 | 3,992 | 101 | 13.3% | 45050, 13305 |
| 0.95 of the budget | 1 | none | benchmark | 246, 246 | 15.0 | 7.00 | 0.00 | 0.00 | 6.00 | 2.00 | 1,778 | 2,403 | 43 | 0.0% | 15, 7 |
| 0.95 of the budget | 1 | at payout 3 | development | 2295, 2295 | 8.6 | 2.60 | 0.00 | 0.00 | 1.79 | 2.19 | 874 | 2,594 | 101 | 13.3% | 36019, 10637 |
| 0.95 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 15.0 | 7.00 | 0.00 | 0.00 | 6.00 | 2.00 | 1,778 | 2,403 | 43 | 0.0% | 15, 7 |
| 0.95 of the budget | 5 | none | development | 2295, 2295 | 37.3 | 12.18 | 0.88 | 0.28 | 9.81 | 11.14 | 3,732 | 13,606 | 63 | 39.5% | 153416, 44757 |
| 0.95 of the budget | 5 | none | benchmark | 246, 246 | 73.0 | 34.00 | 6.00 | 0.00 | 28.00 | 5.00 | 7,847 | 5,870 | 40 | 0.0% | 72, 28 |
| 0.95 of the budget | 5 | at payout 3 | development | 2295, 2295 | 19.9 | 5.82 | 0.87 | 0.28 | 2.44 | 2.30 | 1,867 | 2,459 | 63 | 39.5% | 82929, 19261 |
| 0.95 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 10.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,235 | 4,896 | 40 | 0.0% | 10, 4 |

### S4 on H3's favoured side: topstep_50k, ask (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,184 / 2,609 / 4,609 / 8,005 / 10,681 | 5,389 | 82.8% | 59.8% | 541 / 1,139 | n/a | 0%, 35, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,847 / 2,847 / 2,847 / 2,847 / 2,847 | 2,847 | 100.0% | 0.0% | 657 / 657 | n/a | 0%, 24, 29 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,184 / 2,461 / 4,001 / 4,995 / 5,503 | 3,691 | 82.4% | 50.0% | 541 / 1,139 | 76.1% (170) | 0%, 35, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,847 / 2,847 / 2,847 / 2,847 / 2,847 | 2,847 | 100.0% | 0.0% | 657 / 657 | 100.0% (313) | 0%, 24, 29 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 45.2% | 109 | 22 / 32 / 1,853 / 22,516 / 37,421 | 12,043 | 49.7% | 47.9% | 1,960 / 1,986 | n/a | 0%, 35, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 302 | 23 / 23 / 23 / 23 / 23 | 23 | 0.0% | 0.0% | 1,977 / 1,977 | n/a | 0%, 24, 29 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 34.8% | 101 | 30 / 40 / 1,690 / 4,242 / 5,436 | 2,289 | 46.1% | 27.0% | 1,919 / 1,974 | 65.1% (62) | 0%, 35, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 4,062 / 4,062 / 4,062 / 4,062 / 4,062 | 4,062 | 100.0% | 100.0% | 1,333 / 1,333 | 100.0% (34) | 0%, 24, 29 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 2295, 2295 | 13.9 | 4.00 | 0.00 | 0.00 | 3.46 | 4.29 | 1,344 | 4,733 | 76 | 1.8% | 57746, 15893 |
| 1.00 of the budget | 1 | none | benchmark | 246, 246 | 17.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,876 | 2,723 | 38 | 0.0% | 17, 7 |
| 1.00 of the budget | 1 | at payout 3 | development | 2295, 2295 | 9.7 | 2.65 | 0.00 | 0.00 | 1.76 | 2.60 | 922 | 2,613 | 76 | 1.8% | 40994, 10958 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 17.0 | 7.00 | 0.00 | 0.00 | 6.00 | 3.00 | 1,876 | 2,723 | 38 | 0.0% | 17, 7 |
| 1.00 of the budget | 5 | none | development | 2295, 2295 | 46.8 | 13.75 | 1.01 | 0.33 | 11.40 | 13.74 | 4,409 | 14,451 | 54 | 26.4% | 193545, 51428 |
| 1.00 of the budget | 5 | none | benchmark | 246, 246 | 96.0 | 32.00 | 4.00 | 0.00 | 28.00 | 10.00 | 8,974 | 6,997 | 34 | 0.0% | 96, 28 |
| 1.00 of the budget | 5 | at payout 3 | development | 2295, 2295 | 19.6 | 5.33 | 0.75 | 0.20 | 1.69 | 2.72 | 1,758 | 2,047 | 54 | 26.4% | 81944, 17538 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 12.0 | 5.00 | 0.00 | 0.00 | 0.00 | 4.00 | 1,333 | 3,395 | 34 | 0.0% | 12, 4 |

### S4 on H3's favoured side: topstep_50k, wait (for the record: decides nothing)

| sizing | cap | call-up | period | paths (years; span) | P(ruin) | median ruin day | cash at the end: p10 / p25 / median / p75 / p90 | mean | P(above $2,000) | P(above $4,000) | deepest fall: median / p90 | called up (median day) | frozen bootstrap: P(bust), first payout days, funded at month 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,606 / 2,831 / 4,761 / 7,858 / 10,419 | 5,387 | 84.8% | 60.7% | 492 / 1,229 | n/a | 0%, 35, 33 |
| 1.00 of the budget | 1 | none | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,850 / 2,850 / 2,850 / 2,850 / 2,850 | 2,850 | 100.0% | 0.0% | 654 / 654 | n/a | 0%, 24, 29 |
| 1.00 of the budget | 1 | at payout 3 | development | 4266 (14.8; 365 days) | 0.0% | n/a | 1,606 / 2,831 / 4,088 / 5,256 / 5,678 | 3,922 | 84.8% | 52.5% | 492 / 1,229 | 65.4% (177) | 0%, 35, 33 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 2,850 / 2,850 / 2,850 / 2,850 / 2,850 | 2,850 | 100.0% | 0.0% | 654 / 654 | 0.0% (n/a) | 0%, 24, 29 |
| 1.00 of the budget | 5 | none | development | 4266 (14.8; 365 days) | 43.4% | 105 | 30 / 32 / 3,556 / 20,789 / 35,892 | 11,611 | 51.8% | 49.6% | 1,962 / 1,976 | n/a | 0%, 35, 33 |
| 1.00 of the budget | 5 | none | benchmark | 1 (1.0; 365 days) | 100.0% | 302 | 46 / 46 / 46 / 46 / 46 | 46 | 0.0% | 0.0% | 1,954 / 1,954 | n/a | 0%, 24, 29 |
| 1.00 of the budget | 5 | at payout 3 | development | 4266 (14.8; 365 days) | 42.4% | 105 | 30 / 34 / 2,670 / 4,988 / 6,076 | 2,618 | 52.2% | 36.0% | 1,962 / 1,976 | 55.0% (70) | 0%, 35, 33 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 1 (1.0; 365 days) | 0.0% | n/a | 6,950 / 6,950 / 6,950 / 6,950 / 6,950 | 6,950 | 100.0% | 100.0% | 1,333 / 1,333 | 100.0% (40) | 0%, 24, 29 |

| sizing | cap | call-up | period | trades: evaluation, funded | evaluations | passes | lost passes | cancelled | Express Funded breaches | payouts | fees | paid | first payout requested (median day) | no payout | gate: evaluations, funded compared |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.00 of the budget | 1 | none | development | 2295, 2295 | 12.9 | 3.89 | 0.00 | 0.00 | 3.27 | 3.75 | 1,261 | 4,647 | 99 | 9.8% | 53544, 15365 |
| 1.00 of the budget | 1 | none | benchmark | 246, 246 | 17.0 | 6.00 | 0.00 | 0.00 | 5.00 | 2.00 | 1,727 | 2,577 | 40 | 0.0% | 17, 6 |
| 1.00 of the budget | 1 | at payout 3 | development | 2295, 2295 | 9.4 | 2.64 | 0.00 | 0.00 | 1.76 | 2.36 | 900 | 2,822 | 99 | 9.8% | 39800, 10870 |
| 1.00 of the budget | 1 | at payout 3 | benchmark | 246, 246 | 17.0 | 6.00 | 0.00 | 0.00 | 5.00 | 2.00 | 1,727 | 2,577 | 40 | 0.0% | 17, 6 |
| 1.00 of the budget | 5 | none | development | 2295, 2295 | 42.3 | 12.57 | 0.87 | 0.21 | 10.24 | 11.17 | 3,993 | 13,604 | 64 | 37.3% | 175019, 46811 |
| 1.00 of the budget | 5 | none | benchmark | 246, 246 | 84.0 | 29.00 | 2.00 | 0.00 | 27.00 | 5.00 | 8,237 | 6,283 | 40 | 0.0% | 84, 27 |
| 1.00 of the budget | 5 | at payout 3 | development | 2295, 2295 | 20.9 | 5.64 | 0.81 | 0.20 | 2.25 | 2.26 | 1,869 | 2,487 | 64 | 37.3% | 87679, 18518 |
| 1.00 of the budget | 5 | at payout 3 | benchmark | 246, 246 | 12.0 | 5.00 | 0.00 | 0.00 | 0.00 | 5.00 | 1,333 | 6,283 | 40 | 0.0% | 12, 5 |

## Reading (the registered rule, as amended)

A configuration goes on to a forward test only if, on development paths in whole micros on TopstepX, at one cap, the thresholds hold both without a call-up and with the call-up at the 3rd payout: P(ruin within 12 months) at most 10%, median final cash above $2,000, its 25th percentile at least $1,000. One that qualifies only without the call-up depends on the Live account's value and is not carried forward on this evidence. The benchmark path decides nothing; clean proof comes only from data after 2026-10-05.

| stream | policy | cap 1: no call-up / call-up | cap 5: no call-up / call-up | goes on to a forward test |
|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | ask | no / no | no / no | no |
| S0r sealed brackets, flat 16:00 | wait | no / no | no / no | no |
| S1 continuation only, sealed bracket | ask | yes / yes | no / no | **yes** |
| S1 continuation only, sealed bracket | wait | yes / yes | no / no | **yes** |
| S2 continuation + A+ reversion, sealed bracket | ask | yes / yes | no / no | **yes** |
| S2 continuation + A+ reversion, sealed bracket | wait | yes / yes | no / no | **yes** |
| S3 continuation only, walk-forward ATR bracket | ask | yes / yes | no / no | **yes** |
| S3 continuation only, walk-forward ATR bracket | wait | yes / yes | no / no | **yes** |
| S4 S3 + A+ reversion, sealed bracket | ask | yes / yes | no / no | **yes** |
| S4 S3 + A+ reversion, sealed bracket | wait | yes / yes | no / no | **yes** |
| S1 on H3's favoured side | ask | yes / yes | no / no | **yes** |
| S1 on H3's favoured side | wait | yes / yes | no / no | **yes** |
| S3 on H3's favoured side | ask | yes / yes | no / no | **yes** |
| S3 on H3's favoured side | wait | yes / yes | no / no | **yes** |
| S4 on H3's favoured side | ask | yes / yes | no / no | **yes** |
| S4 on H3's favoured side | wait | yes / yes | no / no | **yes** |
