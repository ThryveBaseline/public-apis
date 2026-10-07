# B4: the lifetime value of a funded account, and EV with every payout and every fee

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

A funded account is started on every trading day and kept for up to H walk-forward days (New York dates with bars, about six a week: 250 is about 42 weeks), until it breaches. On the Topstep presets Topstep's Express Funded payout rules apply: with a payout the maximum loss limit moves to the starting balance and stays there, and a payout after the first needs a positive net profit since the previous one. Two payout policies: ask, ask whenever eligible (the frozen walk-forward's policy; gated); wait, wait until the loss limit has reached the starting balance (Topstep's advice). Gate, passed on every row of the first policy: each start's first payout within 60 days (outcome, day and amount) equals the frozen payout walk-forward's, so the first payouts are B3's; B3's P(payout) is printed beside. Lifetime figures use every start: each is the sum over days 1 to H of that day's mean over the starts that have that day of data, so late starts are used as far as their data goes and none is dropped for surviving (starts with H days counts the starts that have all H); in a short period such a sum can pass 100%, so P(breach) and P(any payout) are capped there. EV per evaluation = P(pass) x expected lifetime payout by H (net of the split) - fees per evaluation (monthly billing and the activation fee). EV first payout only: B3's net EV (median-priced), and the policy's own first payout within 60 days priced at its mean (under the first policy that payout is B3's; under the second it comes later and is larger). Fractional sizing; the risk per trade stays at the budget after a payout. The benchmark year is reported beside and never used to choose.

Not modelled, and worth more once later payouts count: Topstep typically moves an Express Funded trader to a live account after about 30 winning days, so the longest horizons overstate what one Express Funded account pays; after a payout under the first policy the cushion is often less than one stop-out, where an account that books realised R only (a winning trade's dip toward the limit is not modelled) is most optimistic.

## topstep_50k_x at 1.00 of the budget

| stream | period | policy | H | P(pass) | fees per evaluation | starts (with H days) | B3 P(payout) | P(any payout by H) | payouts per account | expected paid per account | P(breach by H) | EV per evaluation | EV first payout only (B3, median) | EV first payout only (this policy, mean) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | development | ask | 60 | 18.5% | 80 | 4756 (4697) | 43.6% | 43.7% | 0.66 | 595 | 94.7% | +30 | -34 | -22 |
| S0r sealed brackets, flat 16:00 | development | ask | 120 | 18.5% | 80 | 4756 (4637) | 43.6% | 44.3% | 0.70 | 628 | 100.0% | +36 | -34 | -22 |
| S0r sealed brackets, flat 16:00 | development | ask | 250 | 18.5% | 80 | 4756 (4507) | 43.6% | 44.3% | 0.70 | 628 | 100.0% | +36 | -34 | -22 |
| S0r sealed brackets, flat 16:00 | development | wait | 60 | 18.5% | 80 | 4756 (4697) | 43.6% | 25.3% | 0.45 | 567 | 87.6% | +25 | -34 | -24 |
| S0r sealed brackets, flat 16:00 | development | wait | 120 | 18.5% | 80 | 4756 (4637) | 43.6% | 27.1% | 0.53 | 638 | 98.4% | +38 | -34 | -24 |
| S0r sealed brackets, flat 16:00 | development | wait | 250 | 18.5% | 80 | 4756 (4507) | 43.6% | 27.1% | 0.55 | 653 | 100.0% | +41 | -34 | -24 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 60 | 8.4% | 61 | 313 (254) | 8.4% | 8.6% | 0.13 | 222 | 99.3% | -43 | -49 | -50 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 120 | 8.4% | 61 | 313 (194) | 8.4% | 8.6% | 0.13 | 222 | 100.0% | -43 | -49 | -50 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 250 | 8.4% | 61 | 313 (64) | 8.4% | 8.6% | 0.13 | 222 | 100.0% | -43 | -49 | -50 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 60 | 8.4% | 61 | 313 (254) | 8.4% | 8.6% | 0.13 | 222 | 99.3% | -43 | -49 | -50 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 120 | 8.4% | 61 | 313 (194) | 8.4% | 8.6% | 0.13 | 222 | 100.0% | -43 | -49 | -50 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 250 | 8.4% | 61 | 313 (64) | 8.4% | 8.6% | 0.13 | 222 | 100.0% | -43 | -49 | -50 |
| S1 continuation only, sealed bracket | development | ask | 60 | 28.2% | 94 | 4756 (4697) | 54.6% | 54.6% | 0.88 | 732 | 92.5% | +112 | -9 | +4 |
| S1 continuation only, sealed bracket | development | ask | 120 | 28.2% | 94 | 4756 (4637) | 54.6% | 55.2% | 0.96 | 806 | 99.8% | +133 | -9 | +4 |
| S1 continuation only, sealed bracket | development | ask | 250 | 28.2% | 94 | 4756 (4507) | 54.6% | 55.2% | 0.96 | 806 | 99.9% | +133 | -9 | +4 |
| S1 continuation only, sealed bracket | development | wait | 60 | 28.2% | 94 | 4756 (4697) | 54.6% | 34.7% | 0.64 | 737 | 83.9% | +114 | -9 | +12 |
| S1 continuation only, sealed bracket | development | wait | 120 | 28.2% | 94 | 4756 (4637) | 54.6% | 36.6% | 0.76 | 863 | 97.7% | +149 | -9 | +12 |
| S1 continuation only, sealed bracket | development | wait | 250 | 28.2% | 94 | 4756 (4507) | 54.6% | 36.7% | 0.78 | 879 | 100.0% | +153 | -9 | +12 |
| S1 continuation only, sealed bracket | benchmark | ask | 60 | 26.5% | 89 | 313 (254) | 63.6% | 63.6% | 1.19 | 1,210 | 87.4% | +232 | +46 | +53 |
| S1 continuation only, sealed bracket | benchmark | ask | 120 | 26.5% | 89 | 313 (194) | 63.6% | 63.6% | 1.39 | 1,462 | 100.0% | +299 | +46 | +53 |
| S1 continuation only, sealed bracket | benchmark | ask | 250 | 26.5% | 89 | 313 (64) | 63.6% | 63.6% | 1.39 | 1,462 | 100.0% | +299 | +46 | +53 |
| S1 continuation only, sealed bracket | benchmark | wait | 60 | 26.5% | 89 | 313 (254) | 63.6% | 55.1% | 1.18 | 1,371 | 84.8% | +274 | +46 | +73 |
| S1 continuation only, sealed bracket | benchmark | wait | 120 | 26.5% | 89 | 313 (194) | 63.6% | 55.1% | 1.49 | 1,750 | 100.0% | +375 | +46 | +73 |
| S1 continuation only, sealed bracket | benchmark | wait | 250 | 26.5% | 89 | 313 (64) | 63.6% | 55.1% | 1.49 | 1,750 | 100.0% | +375 | +46 | +73 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 60 | 25.7% | 91 | 4756 (4697) | 52.1% | 52.1% | 0.81 | 702 | 93.0% | +90 | -16 | +0 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 120 | 25.7% | 91 | 4756 (4637) | 52.1% | 52.8% | 0.86 | 748 | 99.8% | +102 | -16 | +0 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 250 | 25.7% | 91 | 4756 (4507) | 52.1% | 52.8% | 0.86 | 748 | 99.9% | +102 | -16 | +0 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 60 | 25.7% | 91 | 4756 (4697) | 52.1% | 33.0% | 0.58 | 708 | 85.3% | +92 | -16 | +5 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 120 | 25.7% | 91 | 4756 (4637) | 52.1% | 34.9% | 0.67 | 792 | 97.7% | +113 | -16 | +5 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 250 | 25.7% | 91 | 4756 (4507) | 52.1% | 35.0% | 0.69 | 808 | 100.0% | +117 | -16 | +5 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 60 | 17.2% | 75 | 313 (254) | 35.6% | 35.5% | 0.62 | 849 | 91.0% | +70 | +3 | -4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 120 | 17.2% | 75 | 313 (194) | 35.6% | 35.5% | 0.67 | 933 | 93.8% | +85 | +3 | -4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 250 | 17.2% | 75 | 313 (64) | 35.6% | 35.5% | 0.67 | 933 | 93.8% | +85 | +3 | -4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 60 | 17.2% | 75 | 313 (254) | 35.6% | 32.0% | 0.56 | 848 | 90.8% | +70 | +3 | +2 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 120 | 17.2% | 75 | 313 (194) | 35.6% | 32.0% | 0.62 | 964 | 94.5% | +90 | +3 | +2 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 250 | 17.2% | 75 | 313 (64) | 35.6% | 32.0% | 0.62 | 964 | 94.5% | +90 | +3 | +2 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 60 | 28.9% | 95 | 4756 (4697) | 63.4% | 63.4% | 1.05 | 841 | 86.9% | +148 | -3 | +17 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 120 | 28.9% | 95 | 4756 (4637) | 63.4% | 63.9% | 1.22 | 1,041 | 97.8% | +206 | -3 | +17 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 250 | 28.9% | 95 | 4756 (4507) | 63.4% | 63.9% | 1.28 | 1,117 | 100.0% | +228 | -3 | +17 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 60 | 28.9% | 95 | 4756 (4697) | 63.4% | 42.6% | 0.77 | 867 | 78.6% | +156 | -3 | +37 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 120 | 28.9% | 95 | 4756 (4637) | 63.4% | 43.2% | 0.97 | 1,104 | 96.6% | +224 | -3 | +37 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 250 | 28.9% | 95 | 4756 (4507) | 63.4% | 43.2% | 1.05 | 1,222 | 100.0% | +258 | -3 | +37 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 60 | 22.8% | 85 | 313 (254) | 70.1% | 70.9% | 0.88 | 661 | 92.1% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 120 | 22.8% | 85 | 313 (194) | 70.1% | 70.9% | 0.88 | 661 | 92.6% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 250 | 22.8% | 85 | 313 (64) | 70.1% | 70.9% | 0.88 | 661 | 92.6% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 60 | 22.8% | 85 | 313 (254) | 70.1% | 31.5% | 0.48 | 554 | 94.7% | +42 | -0 | -5 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 120 | 22.8% | 85 | 313 (194) | 70.1% | 31.5% | 0.48 | 554 | 95.2% | +42 | -0 | -5 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 250 | 22.8% | 85 | 313 (64) | 70.1% | 31.5% | 0.48 | 554 | 95.2% | +42 | -0 | -5 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 60 | 29.4% | 96 | 4756 (4697) | 61.4% | 61.5% | 1.02 | 860 | 88.4% | +157 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 120 | 29.4% | 96 | 4756 (4637) | 61.4% | 62.0% | 1.16 | 1,026 | 98.2% | +206 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 250 | 29.4% | 96 | 4756 (4507) | 61.4% | 62.0% | 1.17 | 1,042 | 99.9% | +211 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 60 | 29.4% | 96 | 4756 (4697) | 61.4% | 40.9% | 0.76 | 884 | 79.9% | +164 | +2 | +35 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 120 | 29.4% | 96 | 4756 (4637) | 61.4% | 41.3% | 0.92 | 1,109 | 97.5% | +231 | +2 | +35 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 250 | 29.4% | 96 | 4756 (4507) | 61.4% | 41.3% | 0.94 | 1,127 | 100.0% | +236 | +2 | +35 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 60 | 27.5% | 91 | 313 (254) | 73.4% | 73.9% | 1.01 | 851 | 89.3% | +143 | +40 | +53 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 120 | 27.5% | 91 | 313 (194) | 73.4% | 73.9% | 1.01 | 851 | 90.5% | +143 | +40 | +53 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 250 | 27.5% | 91 | 313 (64) | 73.4% | 73.9% | 1.01 | 851 | 90.5% | +143 | +40 | +53 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 60 | 27.5% | 91 | 313 (254) | 73.4% | 58.2% | 0.92 | 1,147 | 82.9% | +225 | +40 | +113 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 120 | 27.5% | 91 | 313 (194) | 73.4% | 58.2% | 0.97 | 1,195 | 92.9% | +238 | +40 | +113 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 250 | 27.5% | 91 | 313 (64) | 73.4% | 58.2% | 0.97 | 1,195 | 92.9% | +238 | +40 | +113 |

## topstep_50k_x at 0.95 of the budget

| stream | period | policy | H | P(pass) | fees per evaluation | starts (with H days) | B3 P(payout) | P(any payout by H) | payouts per account | expected paid per account | P(breach by H) | EV per evaluation | EV first payout only (B3, median) | EV first payout only (this policy, mean) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | development | ask | 60 | 19.6% | 83 | 4756 (4697) | 46.0% | 46.1% | 0.69 | 607 | 94.0% | +37 | -33 | -20 |
| S0r sealed brackets, flat 16:00 | development | ask | 120 | 19.6% | 83 | 4756 (4637) | 46.0% | 47.0% | 0.74 | 639 | 100.0% | +43 | -33 | -20 |
| S0r sealed brackets, flat 16:00 | development | ask | 250 | 19.6% | 83 | 4756 (4507) | 46.0% | 47.0% | 0.74 | 639 | 100.0% | +43 | -33 | -20 |
| S0r sealed brackets, flat 16:00 | development | wait | 60 | 19.6% | 83 | 4756 (4697) | 46.0% | 26.5% | 0.47 | 582 | 85.9% | +32 | -33 | -21 |
| S0r sealed brackets, flat 16:00 | development | wait | 120 | 19.6% | 83 | 4756 (4637) | 46.0% | 28.2% | 0.55 | 651 | 97.6% | +45 | -33 | -21 |
| S0r sealed brackets, flat 16:00 | development | wait | 250 | 19.6% | 83 | 4756 (4507) | 46.0% | 28.3% | 0.57 | 672 | 100.0% | +49 | -33 | -21 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 60 | 9.3% | 63 | 313 (254) | 11.0% | 11.2% | 0.16 | 262 | 99.5% | -39 | -45 | -47 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 120 | 9.3% | 63 | 313 (194) | 11.0% | 11.2% | 0.16 | 262 | 100.0% | -39 | -45 | -47 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 250 | 9.3% | 63 | 313 (64) | 11.0% | 11.2% | 0.16 | 262 | 100.0% | -39 | -45 | -47 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 60 | 9.3% | 63 | 313 (254) | 11.0% | 10.3% | 0.15 | 258 | 99.5% | -39 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 120 | 9.3% | 63 | 313 (194) | 11.0% | 10.3% | 0.15 | 258 | 100.0% | -39 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 250 | 9.3% | 63 | 313 (64) | 11.0% | 10.3% | 0.15 | 258 | 100.0% | -39 | -45 | -48 |
| S1 continuation only, sealed bracket | development | ask | 60 | 30.2% | 98 | 4756 (4697) | 58.7% | 58.8% | 0.94 | 737 | 91.4% | +125 | -6 | +7 |
| S1 continuation only, sealed bracket | development | ask | 120 | 30.2% | 98 | 4756 (4637) | 58.7% | 59.7% | 1.02 | 815 | 99.7% | +148 | -6 | +7 |
| S1 continuation only, sealed bracket | development | ask | 250 | 30.2% | 98 | 4756 (4507) | 58.7% | 59.7% | 1.02 | 816 | 100.0% | +148 | -6 | +7 |
| S1 continuation only, sealed bracket | development | wait | 60 | 30.2% | 98 | 4756 (4697) | 58.7% | 38.3% | 0.69 | 771 | 80.7% | +135 | -6 | +25 |
| S1 continuation only, sealed bracket | development | wait | 120 | 30.2% | 98 | 4756 (4637) | 58.7% | 40.5% | 0.82 | 910 | 96.8% | +177 | -6 | +25 |
| S1 continuation only, sealed bracket | development | wait | 250 | 30.2% | 98 | 4756 (4507) | 58.7% | 40.6% | 0.85 | 928 | 100.0% | +182 | -6 | +25 |
| S1 continuation only, sealed bracket | benchmark | ask | 60 | 38.9% | 109 | 313 (254) | 66.6% | 66.7% | 1.23 | 1,177 | 87.4% | +348 | +82 | +96 |
| S1 continuation only, sealed bracket | benchmark | ask | 120 | 38.9% | 109 | 313 (194) | 66.6% | 66.7% | 1.42 | 1,417 | 100.0% | +441 | +82 | +96 |
| S1 continuation only, sealed bracket | benchmark | ask | 250 | 38.9% | 109 | 313 (64) | 66.6% | 66.7% | 1.42 | 1,417 | 100.0% | +441 | +82 | +96 |
| S1 continuation only, sealed bracket | benchmark | wait | 60 | 38.9% | 109 | 313 (254) | 66.6% | 61.9% | 1.32 | 1,450 | 80.7% | +454 | +82 | +145 |
| S1 continuation only, sealed bracket | benchmark | wait | 120 | 38.9% | 109 | 313 (194) | 66.6% | 61.9% | 1.84 | 2,063 | 100.0% | +693 | +82 | +145 |
| S1 continuation only, sealed bracket | benchmark | wait | 250 | 38.9% | 109 | 313 (64) | 66.6% | 61.9% | 1.87 | 2,100 | 100.0% | +707 | +82 | +145 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 60 | 27.1% | 94 | 4756 (4697) | 55.1% | 55.2% | 0.85 | 703 | 92.1% | +97 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 120 | 27.1% | 94 | 4756 (4637) | 55.1% | 56.1% | 0.90 | 745 | 99.9% | +108 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 250 | 27.1% | 94 | 4756 (4507) | 55.1% | 56.1% | 0.90 | 745 | 99.9% | +108 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 60 | 27.1% | 94 | 4756 (4697) | 55.1% | 34.8% | 0.61 | 725 | 82.8% | +103 | -15 | +11 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 120 | 27.1% | 94 | 4756 (4637) | 55.1% | 37.1% | 0.70 | 811 | 97.0% | +126 | -15 | +11 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 250 | 27.1% | 94 | 4756 (4507) | 55.1% | 37.2% | 0.73 | 828 | 100.0% | +130 | -15 | +11 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 60 | 19.2% | 79 | 313 (254) | 38.9% | 38.8% | 0.67 | 886 | 91.5% | +91 | +8 | +4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 120 | 19.2% | 79 | 313 (194) | 38.9% | 38.8% | 0.72 | 970 | 94.2% | +107 | +8 | +4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 250 | 19.2% | 79 | 313 (64) | 38.9% | 38.8% | 0.72 | 970 | 94.2% | +107 | +8 | +4 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 60 | 19.2% | 79 | 313 (254) | 38.9% | 34.6% | 0.60 | 884 | 91.3% | +90 | +8 | +10 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 120 | 19.2% | 79 | 313 (194) | 38.9% | 34.6% | 0.67 | 999 | 95.0% | +113 | +8 | +10 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 250 | 19.2% | 79 | 313 (64) | 38.9% | 34.6% | 0.67 | 999 | 95.0% | +113 | +8 | +10 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 60 | 32.1% | 101 | 4756 (4697) | 65.5% | 65.5% | 1.07 | 820 | 85.7% | +162 | +0 | +21 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 120 | 32.1% | 101 | 4756 (4637) | 65.5% | 66.3% | 1.24 | 1,008 | 97.8% | +223 | +0 | +21 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 250 | 32.1% | 101 | 4756 (4507) | 65.5% | 66.3% | 1.29 | 1,080 | 100.0% | +246 | +0 | +21 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 60 | 32.1% | 101 | 4756 (4697) | 65.5% | 44.3% | 0.78 | 863 | 74.4% | +176 | +0 | +49 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 120 | 32.1% | 101 | 4756 (4637) | 65.5% | 45.5% | 1.01 | 1,127 | 96.1% | +261 | +0 | +49 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 250 | 32.1% | 101 | 4756 (4507) | 65.5% | 45.5% | 1.08 | 1,228 | 100.0% | +293 | +0 | +49 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 60 | 28.5% | 93 | 313 (254) | 69.8% | 70.6% | 0.87 | 625 | 92.3% | +85 | +11 | +24 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 120 | 28.5% | 93 | 313 (194) | 69.8% | 70.6% | 0.87 | 625 | 92.7% | +85 | +11 | +24 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 250 | 28.5% | 93 | 313 (64) | 69.8% | 70.6% | 0.87 | 625 | 92.7% | +85 | +11 | +24 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 60 | 28.5% | 93 | 313 (254) | 69.8% | 29.1% | 0.45 | 513 | 91.8% | +53 | +11 | -2 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 120 | 28.5% | 93 | 313 (194) | 69.8% | 29.1% | 0.45 | 513 | 95.9% | +53 | +11 | -2 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 250 | 28.5% | 93 | 313 (64) | 69.8% | 29.1% | 0.45 | 513 | 95.9% | +53 | +11 | -2 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 60 | 33.0% | 102 | 4756 (4697) | 63.6% | 63.7% | 1.05 | 851 | 87.2% | +179 | +8 | +26 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 120 | 33.0% | 102 | 4756 (4637) | 63.6% | 64.4% | 1.19 | 1,009 | 98.4% | +231 | +8 | +26 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 250 | 33.0% | 102 | 4756 (4507) | 63.6% | 64.4% | 1.20 | 1,025 | 100.0% | +236 | +8 | +26 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 60 | 33.0% | 102 | 4756 (4697) | 63.6% | 42.8% | 0.77 | 887 | 77.3% | +191 | +8 | +48 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 120 | 33.0% | 102 | 4756 (4637) | 63.6% | 43.2% | 0.95 | 1,119 | 96.7% | +267 | +8 | +48 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 250 | 33.0% | 102 | 4756 (4507) | 63.6% | 43.2% | 0.96 | 1,139 | 100.0% | +274 | +8 | +48 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 60 | 30.5% | 96 | 313 (254) | 74.4% | 75.0% | 1.00 | 797 | 88.7% | +147 | +43 | +56 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 120 | 30.5% | 96 | 313 (194) | 74.4% | 75.0% | 1.00 | 797 | 89.9% | +147 | +43 | +56 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 250 | 30.5% | 96 | 313 (64) | 74.4% | 75.0% | 1.00 | 797 | 89.9% | +147 | +43 | +56 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 60 | 30.5% | 96 | 313 (254) | 74.4% | 59.9% | 0.95 | 1,133 | 80.4% | +249 | +43 | +132 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 120 | 30.5% | 96 | 313 (194) | 74.4% | 59.9% | 1.00 | 1,194 | 91.6% | +268 | +43 | +132 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 250 | 30.5% | 96 | 313 (64) | 74.4% | 59.9% | 1.00 | 1,194 | 91.6% | +268 | +43 | +132 |

## topstep_50k at 1.00 of the budget

| stream | period | policy | H | P(pass) | fees per evaluation | starts (with H days) | B3 P(payout) | P(any payout by H) | payouts per account | expected paid per account | P(breach by H) | EV per evaluation | EV first payout only (B3, median) | EV first payout only (this policy, mean) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | development | ask | 60 | 18.0% | 80 | 4756 (4697) | 44.4% | 44.5% | 0.67 | 595 | 94.3% | +27 | -33 | -22 |
| S0r sealed brackets, flat 16:00 | development | ask | 120 | 18.0% | 80 | 4756 (4637) | 44.4% | 45.1% | 0.71 | 640 | 100.0% | +35 | -33 | -22 |
| S0r sealed brackets, flat 16:00 | development | ask | 250 | 18.0% | 80 | 4756 (4507) | 44.4% | 45.1% | 0.71 | 640 | 100.0% | +35 | -33 | -22 |
| S0r sealed brackets, flat 16:00 | development | wait | 60 | 18.0% | 80 | 4756 (4697) | 44.4% | 26.0% | 0.45 | 567 | 87.3% | +22 | -33 | -24 |
| S0r sealed brackets, flat 16:00 | development | wait | 120 | 18.0% | 80 | 4756 (4637) | 44.4% | 27.8% | 0.54 | 651 | 98.2% | +37 | -33 | -24 |
| S0r sealed brackets, flat 16:00 | development | wait | 250 | 18.0% | 80 | 4756 (4507) | 44.4% | 27.8% | 0.56 | 666 | 100.0% | +40 | -33 | -24 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 60 | 7.7% | 64 | 313 (254) | 13.2% | 13.6% | 0.20 | 327 | 99.0% | -39 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 120 | 7.7% | 64 | 313 (194) | 13.2% | 13.6% | 0.22 | 356 | 100.0% | -36 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | ask | 250 | 7.7% | 64 | 313 (64) | 13.2% | 13.6% | 0.22 | 356 | 100.0% | -36 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 60 | 7.7% | 64 | 313 (254) | 13.2% | 12.6% | 0.19 | 321 | 99.0% | -39 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 120 | 7.7% | 64 | 313 (194) | 13.2% | 12.6% | 0.21 | 350 | 100.0% | -37 | -45 | -48 |
| S0r sealed brackets, flat 16:00 | benchmark | wait | 250 | 7.7% | 64 | 313 (64) | 13.2% | 12.6% | 0.21 | 350 | 100.0% | -37 | -45 | -48 |
| S1 continuation only, sealed bracket | development | ask | 60 | 29.6% | 96 | 4756 (4697) | 54.6% | 54.6% | 0.88 | 733 | 92.5% | +120 | -7 | +6 |
| S1 continuation only, sealed bracket | development | ask | 120 | 29.6% | 96 | 4756 (4637) | 54.6% | 55.2% | 0.96 | 806 | 99.8% | +142 | -7 | +6 |
| S1 continuation only, sealed bracket | development | ask | 250 | 29.6% | 96 | 4756 (4507) | 54.6% | 55.2% | 0.96 | 806 | 99.9% | +142 | -7 | +6 |
| S1 continuation only, sealed bracket | development | wait | 60 | 29.6% | 96 | 4756 (4697) | 54.6% | 34.7% | 0.64 | 739 | 83.9% | +122 | -7 | +15 |
| S1 continuation only, sealed bracket | development | wait | 120 | 29.6% | 96 | 4756 (4637) | 54.6% | 36.6% | 0.76 | 866 | 97.7% | +160 | -7 | +15 |
| S1 continuation only, sealed bracket | development | wait | 250 | 29.6% | 96 | 4756 (4507) | 54.6% | 36.7% | 0.78 | 882 | 100.0% | +165 | -7 | +15 |
| S1 continuation only, sealed bracket | benchmark | ask | 60 | 25.6% | 88 | 313 (254) | 63.6% | 63.6% | 1.19 | 1,211 | 87.4% | +222 | +43 | +50 |
| S1 continuation only, sealed bracket | benchmark | ask | 120 | 25.6% | 88 | 313 (194) | 63.6% | 63.6% | 1.39 | 1,464 | 100.0% | +287 | +43 | +50 |
| S1 continuation only, sealed bracket | benchmark | ask | 250 | 25.6% | 88 | 313 (64) | 63.6% | 63.6% | 1.39 | 1,464 | 100.0% | +287 | +43 | +50 |
| S1 continuation only, sealed bracket | benchmark | wait | 60 | 25.6% | 88 | 313 (254) | 63.6% | 55.1% | 1.18 | 1,372 | 84.8% | +263 | +43 | +69 |
| S1 continuation only, sealed bracket | benchmark | wait | 120 | 25.6% | 88 | 313 (194) | 63.6% | 55.1% | 1.49 | 1,753 | 100.0% | +361 | +43 | +69 |
| S1 continuation only, sealed bracket | benchmark | wait | 250 | 25.6% | 88 | 313 (64) | 63.6% | 55.1% | 1.49 | 1,753 | 100.0% | +361 | +43 | +69 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 60 | 26.4% | 92 | 4756 (4697) | 52.4% | 52.5% | 0.82 | 706 | 93.0% | +94 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 120 | 26.4% | 92 | 4756 (4637) | 52.4% | 53.1% | 0.87 | 751 | 99.8% | +106 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | ask | 250 | 26.4% | 92 | 4756 (4507) | 52.4% | 53.1% | 0.87 | 752 | 99.9% | +106 | -15 | +2 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 60 | 26.4% | 92 | 4756 (4697) | 52.4% | 33.2% | 0.59 | 710 | 85.3% | +95 | -15 | +7 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 120 | 26.4% | 92 | 4756 (4637) | 52.4% | 35.1% | 0.67 | 793 | 97.7% | +117 | -15 | +7 |
| S2 continuation + A+ reversion, sealed bracket | development | wait | 250 | 26.4% | 92 | 4756 (4507) | 52.4% | 35.3% | 0.70 | 809 | 100.0% | +121 | -15 | +7 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 60 | 19.4% | 80 | 313 (254) | 36.6% | 36.5% | 0.64 | 860 | 90.7% | +87 | +7 | +3 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 120 | 19.4% | 80 | 313 (194) | 36.6% | 36.5% | 0.73 | 1,032 | 97.2% | +120 | +7 | +3 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | ask | 250 | 19.4% | 80 | 313 (64) | 36.6% | 36.5% | 0.73 | 1,032 | 97.2% | +120 | +7 | +3 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 60 | 19.4% | 80 | 313 (254) | 36.6% | 33.0% | 0.57 | 851 | 90.5% | +85 | +7 | +8 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 120 | 19.4% | 80 | 313 (194) | 36.6% | 33.0% | 0.68 | 1,038 | 96.9% | +121 | +7 | +8 |
| S2 continuation + A+ reversion, sealed bracket | benchmark | wait | 250 | 19.4% | 80 | 313 (64) | 36.6% | 33.0% | 0.68 | 1,038 | 96.9% | +121 | +7 | +8 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 60 | 29.3% | 96 | 4756 (4697) | 63.4% | 63.4% | 1.05 | 841 | 86.9% | +151 | -2 | +18 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 120 | 29.3% | 96 | 4756 (4637) | 63.4% | 63.9% | 1.22 | 1,041 | 97.8% | +210 | -2 | +18 |
| S3 continuation only, walk-forward ATR bracket | development | ask | 250 | 29.3% | 96 | 4756 (4507) | 63.4% | 63.9% | 1.28 | 1,117 | 100.0% | +232 | -2 | +18 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 60 | 29.3% | 96 | 4756 (4697) | 63.4% | 42.6% | 0.77 | 867 | 78.6% | +158 | -2 | +38 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 120 | 29.3% | 96 | 4756 (4637) | 63.4% | 43.2% | 0.97 | 1,104 | 96.6% | +228 | -2 | +38 |
| S3 continuation only, walk-forward ATR bracket | development | wait | 250 | 29.3% | 96 | 4756 (4507) | 63.4% | 43.2% | 1.05 | 1,222 | 100.0% | +263 | -2 | +38 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 60 | 22.8% | 85 | 313 (254) | 70.1% | 70.9% | 0.88 | 661 | 92.1% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 120 | 22.8% | 85 | 313 (194) | 70.1% | 70.9% | 0.88 | 661 | 92.6% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | ask | 250 | 22.8% | 85 | 313 (64) | 70.1% | 70.9% | 0.88 | 661 | 92.6% | +66 | -0 | +14 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 60 | 22.8% | 85 | 313 (254) | 70.1% | 31.5% | 0.48 | 554 | 94.7% | +42 | -0 | -5 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 120 | 22.8% | 85 | 313 (194) | 70.1% | 31.5% | 0.48 | 554 | 95.2% | +42 | -0 | -5 |
| S3 continuation only, walk-forward ATR bracket | benchmark | wait | 250 | 22.8% | 85 | 313 (64) | 70.1% | 31.5% | 0.48 | 554 | 95.2% | +42 | -0 | -5 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 60 | 29.0% | 95 | 4756 (4697) | 62.0% | 62.1% | 1.04 | 873 | 88.2% | +158 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 120 | 29.0% | 95 | 4756 (4637) | 62.0% | 62.6% | 1.17 | 1,036 | 98.5% | +206 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | ask | 250 | 29.0% | 95 | 4756 (4507) | 62.0% | 62.6% | 1.18 | 1,047 | 99.9% | +209 | +2 | +19 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 60 | 29.0% | 95 | 4756 (4697) | 62.0% | 41.6% | 0.77 | 904 | 79.7% | +167 | +2 | +36 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 120 | 29.0% | 95 | 4756 (4637) | 62.0% | 42.0% | 0.94 | 1,125 | 97.7% | +232 | +2 | +36 |
| S4 S3 + A+ reversion, sealed bracket | development | wait | 250 | 29.0% | 95 | 4756 (4507) | 62.0% | 42.0% | 0.95 | 1,143 | 100.0% | +237 | +2 | +36 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 60 | 25.5% | 90 | 313 (254) | 74.4% | 74.9% | 1.11 | 967 | 87.4% | +157 | +33 | +44 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 120 | 25.5% | 90 | 313 (194) | 74.4% | 74.9% | 1.11 | 967 | 91.1% | +157 | +33 | +44 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | ask | 250 | 25.5% | 90 | 313 (64) | 74.4% | 74.9% | 1.11 | 967 | 91.1% | +157 | +33 | +44 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 60 | 25.5% | 90 | 313 (254) | 74.4% | 58.5% | 1.00 | 1,238 | 81.9% | +226 | +33 | +100 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 120 | 25.5% | 90 | 313 (194) | 74.4% | 58.5% | 1.04 | 1,286 | 93.6% | +238 | +33 | +100 |
| S4 S3 + A+ reversion, sealed bracket | benchmark | wait | 250 | 25.5% | 90 | 313 (64) | 74.4% | 58.5% | 1.04 | 1,286 | 93.6% | +238 | +33 | +100 |
