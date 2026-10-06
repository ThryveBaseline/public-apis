# Evaluation of the implemented rules on this data

Data hygiene: 121 trades on 66 contract-roll dates excluded; 7 of 8689 trades (0.1%) exited on a bar that contained both the stop and the target, each resolved as a STOP (worst case), never in the strategy's favour.

Trades: 8689 from 2010-06-08 to 2026-10-05; in-sample through 2025-10-05 (7431 trades), out-of-sample after it (1258 trades, untouched by any tuning).
Days are New York trading days (every day with bars, traded or not); rates are the share of starts that reached the outcome within the horizon, with open starts counted as not reached and starts cut off by the end of the data excluded; +/- is a Newey-West standard error that allows for the overlap of neighbouring starts.

## R distribution, in sample

| dimension | bucket | trades | win rate | expectancy R | profit factor | trades/day |
|---|---|---|---|---|---|---|
| all | all | 7431 | 40.2% | -0.037 | 0.94 | 1.56 |
| year | 2010 | 113 | 52.2% | -0.005 | 0.98 | 0.63 |
| year | 2011 | 193 | 48.7% | +0.056 | 1.15 | 0.62 |
| year | 2012 | 180 | 47.2% | -0.005 | 0.98 | 0.58 |
| year | 2013 | 195 | 51.3% | +0.047 | 1.18 | 0.64 |
| year | 2014 | 210 | 47.6% | +0.050 | 1.12 | 0.69 |
| year | 2015 | 249 | 42.6% | -0.022 | 0.96 | 0.80 |
| year | 2016 | 258 | 46.9% | +0.057 | 1.13 | 0.83 |
| year | 2017 | 226 | 44.2% | -0.031 | 0.93 | 0.73 |
| year | 2018 | 418 | 39.2% | -0.038 | 0.94 | 1.34 |
| year | 2019 | 366 | 38.8% | -0.046 | 0.92 | 1.17 |
| year | 2020 | 757 | 39.9% | -0.012 | 0.98 | 2.43 |
| year | 2021 | 734 | 33.8% | -0.168 | 0.75 | 2.36 |
| year | 2022 | 1104 | 39.6% | -0.018 | 0.97 | 3.56 |
| year | 2023 | 759 | 39.5% | -0.022 | 0.96 | 2.45 |
| year | 2024 | 883 | 37.9% | -0.060 | 0.90 | 2.82 |
| year | 2025 | 786 | 37.7% | -0.067 | 0.89 | 3.32 |
| quarter | 2010Q2 | 11 | 63.6% | +0.055 | 1.15 | 0.50 |
| quarter | 2010Q3 | 52 | 55.8% | +0.080 | 1.30 | 0.66 |
| quarter | 2010Q4 | 50 | 46.0% | -0.108 | 0.64 | 0.64 |
| quarter | 2011Q1 | 44 | 47.7% | +0.088 | 1.33 | 0.57 |
| quarter | 2011Q2 | 41 | 46.3% | -0.105 | 0.71 | 0.53 |
| quarter | 2011Q3 | 58 | 44.8% | +0.028 | 1.05 | 0.73 |
| quarter | 2011Q4 | 50 | 56.0% | +0.194 | 1.61 | 0.66 |
| quarter | 2012Q1 | 51 | 41.2% | -0.065 | 0.78 | 0.67 |
| quarter | 2012Q2 | 47 | 48.9% | +0.015 | 1.04 | 0.60 |
| quarter | 2012Q3 | 40 | 45.0% | +0.003 | 1.01 | 0.51 |
| quarter | 2012Q4 | 42 | 54.8% | +0.037 | 1.10 | 0.54 |
| quarter | 2013Q1 | 47 | 40.4% | -0.153 | 0.52 | 0.64 |
| quarter | 2013Q2 | 47 | 61.7% | +0.139 | 1.57 | 0.61 |
| quarter | 2013Q3 | 52 | 57.7% | +0.136 | 1.71 | 0.67 |
| quarter | 2013Q4 | 49 | 44.9% | +0.055 | 1.20 | 0.63 |
| quarter | 2014Q1 | 48 | 43.8% | -0.030 | 0.93 | 0.65 |
| quarter | 2014Q2 | 56 | 51.8% | +0.160 | 1.41 | 0.75 |
| quarter | 2014Q3 | 47 | 42.6% | -0.086 | 0.78 | 0.62 |
| quarter | 2014Q4 | 59 | 50.8% | +0.117 | 1.29 | 0.76 |
| quarter | 2015Q1 | 59 | 47.5% | +0.072 | 1.18 | 0.77 |
| quarter | 2015Q2 | 54 | 37.0% | -0.098 | 0.81 | 0.69 |
| quarter | 2015Q3 | 75 | 48.0% | +0.060 | 1.12 | 0.95 |
| quarter | 2015Q4 | 61 | 36.1% | -0.148 | 0.74 | 0.78 |
| quarter | 2016Q1 | 74 | 48.6% | +0.127 | 1.24 | 0.97 |
| quarter | 2016Q2 | 60 | 45.0% | +0.070 | 1.16 | 0.77 |
| quarter | 2016Q3 | 54 | 50.0% | +0.030 | 1.09 | 0.68 |
| quarter | 2016Q4 | 70 | 44.3% | -0.009 | 0.98 | 0.91 |
| quarter | 2017Q1 | 46 | 34.8% | -0.248 | 0.47 | 0.60 |
| quarter | 2017Q2 | 57 | 47.4% | -0.062 | 0.86 | 0.74 |
| quarter | 2017Q3 | 59 | 44.1% | +0.066 | 1.13 | 0.76 |
| quarter | 2017Q4 | 64 | 48.4% | +0.064 | 1.17 | 0.83 |
| quarter | 2018Q1 | 87 | 33.3% | -0.181 | 0.73 | 1.14 |
| quarter | 2018Q2 | 102 | 40.2% | +0.004 | 1.01 | 1.31 |
| quarter | 2018Q3 | 95 | 48.4% | +0.155 | 1.32 | 1.20 |
| quarter | 2018Q4 | 134 | 35.8% | -0.114 | 0.83 | 1.70 |
| quarter | 2019Q1 | 98 | 35.7% | -0.122 | 0.81 | 1.27 |
| quarter | 2019Q2 | 92 | 27.2% | -0.329 | 0.54 | 1.19 |
| quarter | 2019Q3 | 92 | 45.7% | +0.145 | 1.28 | 1.16 |
| quarter | 2019Q4 | 84 | 47.6% | +0.142 | 1.28 | 1.06 |
| quarter | 2020Q1 | 190 | 42.1% | +0.045 | 1.08 | 2.44 |
| quarter | 2020Q2 | 169 | 31.4% | -0.227 | 0.68 | 2.19 |
| quarter | 2020Q3 | 209 | 41.1% | +0.015 | 1.03 | 2.65 |
| quarter | 2020Q4 | 189 | 43.9% | +0.091 | 1.16 | 2.42 |
| quarter | 2021Q1 | 209 | 45.0% | +0.118 | 1.21 | 2.75 |
| quarter | 2021Q2 | 151 | 28.5% | -0.301 | 0.58 | 1.94 |
| quarter | 2021Q3 | 170 | 27.6% | -0.330 | 0.55 | 2.15 |
| quarter | 2021Q4 | 204 | 31.4% | -0.226 | 0.68 | 2.62 |
| quarter | 2022Q1 | 337 | 42.4% | +0.054 | 1.09 | 4.38 |
| quarter | 2022Q2 | 308 | 37.0% | -0.083 | 0.87 | 4.00 |
| quarter | 2022Q3 | 220 | 34.1% | -0.157 | 0.77 | 2.78 |
| quarter | 2022Q4 | 239 | 43.9% | +0.095 | 1.17 | 3.10 |
| quarter | 2023Q1 | 215 | 38.6% | -0.043 | 0.93 | 2.79 |
| quarter | 2023Q2 | 187 | 39.0% | -0.039 | 0.94 | 2.40 |
| quarter | 2023Q3 | 183 | 40.4% | +0.003 | 1.00 | 2.35 |
| quarter | 2023Q4 | 174 | 40.2% | -0.003 | 1.00 | 2.26 |
| quarter | 2024Q1 | 175 | 37.1% | -0.080 | 0.87 | 2.27 |
| quarter | 2024Q2 | 179 | 40.2% | -0.003 | 1.00 | 2.29 |
| quarter | 2024Q3 | 276 | 37.3% | -0.076 | 0.88 | 3.49 |
| quarter | 2024Q4 | 253 | 37.5% | -0.070 | 0.89 | 3.20 |
| quarter | 2025Q1 | 309 | 40.8% | +0.011 | 1.02 | 4.01 |
| quarter | 2025Q2 | 236 | 36.9% | -0.087 | 0.86 | 3.06 |
| quarter | 2025Q3 | 229 | 34.9% | -0.136 | 0.79 | 2.90 |
| quarter | 2025Q4 | 12 | 25.0% | -0.388 | 0.49 | 3.00 |
| session | am | 7431 | 40.2% | -0.037 | 0.94 | 1.56 |
| setup | continuation | 3281 | 44.1% | +0.020 | 1.04 | 0.69 |
| setup | reversion | 4150 | 37.2% | -0.082 | 0.87 | 0.87 |
| grade | A | 4639 | 38.5% | -0.068 | 0.89 | 0.98 |
| grade | A+ | 2792 | 43.1% | +0.014 | 1.03 | 0.59 |
| direction | long | 3808 | 41.1% | -0.032 | 0.94 | 0.80 |
| direction | short | 3623 | 39.3% | -0.043 | 0.93 | 0.76 |
| regime | high | 4776 | 38.5% | -0.046 | 0.93 | 3.64 |
| regime | low | 977 | 48.9% | +0.003 | 1.01 | 0.74 |
| regime | mid | 1678 | 40.1% | -0.034 | 0.94 | 1.28 |

## Pass and payout probability under exact firm rules, in sample (one evaluation / funded account started on every trading day)

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) |
|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 20.1% | 1.8% | 10 | 4748 (276) | 45.8% | 3.3% | 14 | 4753 (35) | 623 |
| fundednext_50k_flex | 1,000 | 12.6% | 1.4% | 12 | 4755 (310) | 37.9% | 3.2% | 14 | 4754 (9) | 672 |
| topstep_100k | 2,000 | 18.5% | 1.7% | 10 | 4749 (223) | 56.8% | 3.5% | 15 | 4752 (109) | 533 |
| tradeify_100k_growth | 2,000 | 30.2% | 1.7% | 5 | 4754 (140) | 12.6% | 2.1% | 28 | 4737 (1488) | 207 |

Pass probability by start period, topstep_50k: year 2010: 11% (n=179); year 2011: 30% (n=309); year 2012: 22% (n=311); year 2013: 28% (n=306); year 2014: 39% (n=303); year 2015: 26% (n=312); year 2016: 31% (n=310); year 2017: 26% (n=309); year 2018: 20% (n=312); year 2019: 25% (n=312); year 2020: 15% (n=312); year 2021: 6% (n=311); year 2022: 10% (n=310); year 2023: 9% (n=310); year 2024: 5% (n=313); year 2025: 12% (n=229); quarter 2010Q2: 0% (n=22); quarter 2010Q3: 22% (n=79); quarter 2010Q4: 4% (n=78); quarter 2011Q1: 39% (n=77); quarter 2011Q2: 9% (n=77); quarter 2011Q3: 33% (n=79); quarter 2011Q4: 38% (n=76); quarter 2012Q1: 16% (n=76); quarter 2012Q2: 28% (n=78); quarter 2012Q3: 19% (n=79); quarter 2012Q4: 26% (n=78); quarter 2013Q1: 12% (n=73); quarter 2013Q2: 32% (n=77); quarter 2013Q3: 26% (n=78); quarter 2013Q4: 42% (n=78); quarter 2014Q1: 28% (n=74); quarter 2014Q2: 40% (n=75); quarter 2014Q3: 37% (n=76); quarter 2014Q4: 50% (n=78); quarter 2015Q1: 53% (n=77); quarter 2015Q2: 17% (n=78); quarter 2015Q3: 18% (n=79); quarter 2015Q4: 18% (n=78); quarter 2016Q1: 32% (n=76); quarter 2016Q2: 21% (n=78); quarter 2016Q3: 34% (n=79); quarter 2016Q4: 38% (n=77); quarter 2017Q1: 0% (n=77); quarter 2017Q2: 25% (n=77); quarter 2017Q3: 15% (n=78); quarter 2017Q4: 64% (n=77); quarter 2018Q1: 8% (n=76); quarter 2018Q2: 21% (n=78); quarter 2018Q3: 41% (n=79); quarter 2018Q4: 9% (n=79); quarter 2019Q1: 5% (n=77); quarter 2019Q2: 10% (n=77); quarter 2019Q3: 47% (n=79); quarter 2019Q4: 38% (n=79); quarter 2020Q1: 24% (n=78); quarter 2020Q2: 5% (n=77); quarter 2020Q3: 8% (n=79); quarter 2020Q4: 24% (n=78); quarter 2021Q1: 13% (n=76); quarter 2021Q2: 1% (n=78); quarter 2021Q3: 1% (n=79); quarter 2021Q4: 8% (n=78); quarter 2022Q1: 5% (n=77); quarter 2022Q2: 0% (n=77); quarter 2022Q3: 4% (n=79); quarter 2022Q4: 32% (n=77); quarter 2023Q1: 8% (n=77); quarter 2023Q2: 5% (n=78); quarter 2023Q3: 5% (n=78); quarter 2023Q4: 18% (n=77); quarter 2024Q1: 6% (n=77); quarter 2024Q2: 0% (n=78); quarter 2024Q3: 0% (n=79); quarter 2024Q4: 13% (n=79); quarter 2025Q1: 8% (n=77); quarter 2025Q2: 14% (n=77); quarter 2025Q3: 14% (n=73); quarter 2025Q4: 0% (n=2); regime high: 10% (n=1306); regime low: 27% (n=1313); regime mid: 23% (n=1312); regime n/a: 20% (n=817)

Pass probability by start period, fundednext_50k_flex: year 2010: 9% (n=179); year 2011: 18% (n=309); year 2012: 10% (n=311); year 2013: 18% (n=306); year 2014: 25% (n=303); year 2015: 22% (n=312); year 2016: 20% (n=310); year 2017: 12% (n=309); year 2018: 16% (n=312); year 2019: 18% (n=312); year 2020: 7% (n=312); year 2021: 6% (n=311); year 2022: 7% (n=310); year 2023: 5% (n=310); year 2024: 1% (n=313); year 2025: 6% (n=236); quarter 2010Q2: 0% (n=22); quarter 2010Q3: 16% (n=79); quarter 2010Q4: 4% (n=78); quarter 2011Q1: 21% (n=77); quarter 2011Q2: 9% (n=77); quarter 2011Q3: 22% (n=79); quarter 2011Q4: 21% (n=76); quarter 2012Q1: 8% (n=76); quarter 2012Q2: 14% (n=78); quarter 2012Q3: 10% (n=79); quarter 2012Q4: 6% (n=78); quarter 2013Q1: 12% (n=73); quarter 2013Q2: 27% (n=77); quarter 2013Q3: 14% (n=78); quarter 2013Q4: 19% (n=78); quarter 2014Q1: 14% (n=74); quarter 2014Q2: 32% (n=75); quarter 2014Q3: 16% (n=76); quarter 2014Q4: 38% (n=78); quarter 2015Q1: 43% (n=77); quarter 2015Q2: 13% (n=78); quarter 2015Q3: 16% (n=79); quarter 2015Q4: 15% (n=78); quarter 2016Q1: 20% (n=76); quarter 2016Q2: 12% (n=78); quarter 2016Q3: 20% (n=79); quarter 2016Q4: 27% (n=77); quarter 2017Q1: 0% (n=77); quarter 2017Q2: 16% (n=77); quarter 2017Q3: 1% (n=78); quarter 2017Q4: 31% (n=77); quarter 2018Q1: 4% (n=76); quarter 2018Q2: 21% (n=78); quarter 2018Q3: 33% (n=79); quarter 2018Q4: 5% (n=79); quarter 2019Q1: 8% (n=77); quarter 2019Q2: 3% (n=77); quarter 2019Q3: 42% (n=79); quarter 2019Q4: 20% (n=79); quarter 2020Q1: 3% (n=78); quarter 2020Q2: 0% (n=77); quarter 2020Q3: 4% (n=79); quarter 2020Q4: 23% (n=78); quarter 2021Q1: 20% (n=76); quarter 2021Q2: 0% (n=78); quarter 2021Q3: 1% (n=79); quarter 2021Q4: 3% (n=78); quarter 2022Q1: 6% (n=77); quarter 2022Q2: 0% (n=77); quarter 2022Q3: 1% (n=79); quarter 2022Q4: 22% (n=77); quarter 2023Q1: 8% (n=77); quarter 2023Q2: 0% (n=78); quarter 2023Q3: 1% (n=78); quarter 2023Q4: 9% (n=77); quarter 2024Q1: 0% (n=77); quarter 2024Q2: 3% (n=78); quarter 2024Q3: 0% (n=79); quarter 2024Q4: 0% (n=79); quarter 2025Q1: 6% (n=77); quarter 2025Q2: 12% (n=77); quarter 2025Q3: 0% (n=79); quarter 2025Q4: 0% (n=3); regime high: 6% (n=1312); regime low: 17% (n=1313); regime mid: 16% (n=1312); regime n/a: 12% (n=818)

Pass probability by start period, topstep_100k: year 2010: 11% (n=179); year 2011: 23% (n=309); year 2012: 21% (n=311); year 2013: 28% (n=306); year 2014: 31% (n=303); year 2015: 26% (n=312); year 2016: 30% (n=310); year 2017: 21% (n=309); year 2018: 19% (n=312); year 2019: 25% (n=312); year 2020: 15% (n=312); year 2021: 6% (n=311); year 2022: 10% (n=310); year 2023: 9% (n=310); year 2024: 5% (n=313); year 2025: 11% (n=230); quarter 2010Q2: 0% (n=22); quarter 2010Q3: 20% (n=79); quarter 2010Q4: 4% (n=78); quarter 2011Q1: 21% (n=77); quarter 2011Q2: 9% (n=77); quarter 2011Q3: 32% (n=79); quarter 2011Q4: 32% (n=76); quarter 2012Q1: 16% (n=76); quarter 2012Q2: 22% (n=78); quarter 2012Q3: 19% (n=79); quarter 2012Q4: 26% (n=78); quarter 2013Q1: 12% (n=73); quarter 2013Q2: 32% (n=77); quarter 2013Q3: 26% (n=78); quarter 2013Q4: 42% (n=78); quarter 2014Q1: 20% (n=74); quarter 2014Q2: 39% (n=75); quarter 2014Q3: 18% (n=76); quarter 2014Q4: 46% (n=78); quarter 2015Q1: 53% (n=77); quarter 2015Q2: 17% (n=78); quarter 2015Q3: 18% (n=79); quarter 2015Q4: 18% (n=78); quarter 2016Q1: 28% (n=76); quarter 2016Q2: 21% (n=78); quarter 2016Q3: 34% (n=79); quarter 2016Q4: 38% (n=77); quarter 2017Q1: 0% (n=77); quarter 2017Q2: 19% (n=77); quarter 2017Q3: 13% (n=78); quarter 2017Q4: 51% (n=77); quarter 2018Q1: 8% (n=76); quarter 2018Q2: 19% (n=78); quarter 2018Q3: 39% (n=79); quarter 2018Q4: 9% (n=79); quarter 2019Q1: 5% (n=77); quarter 2019Q2: 10% (n=77); quarter 2019Q3: 47% (n=79); quarter 2019Q4: 38% (n=79); quarter 2020Q1: 24% (n=78); quarter 2020Q2: 3% (n=77); quarter 2020Q3: 8% (n=79); quarter 2020Q4: 24% (n=78); quarter 2021Q1: 13% (n=76); quarter 2021Q2: 1% (n=78); quarter 2021Q3: 1% (n=79); quarter 2021Q4: 8% (n=78); quarter 2022Q1: 5% (n=77); quarter 2022Q2: 0% (n=77); quarter 2022Q3: 4% (n=79); quarter 2022Q4: 32% (n=77); quarter 2023Q1: 8% (n=77); quarter 2023Q2: 5% (n=78); quarter 2023Q3: 5% (n=78); quarter 2023Q4: 18% (n=77); quarter 2024Q1: 6% (n=77); quarter 2024Q2: 0% (n=78); quarter 2024Q3: 0% (n=79); quarter 2024Q4: 13% (n=79); quarter 2025Q1: 6% (n=77); quarter 2025Q2: 14% (n=77); quarter 2025Q3: 12% (n=74); quarter 2025Q4: 0% (n=2); regime high: 10% (n=1307); regime low: 24% (n=1313); regime mid: 21% (n=1312); regime n/a: 18% (n=817)

Pass probability by start period, tradeify_100k_growth: year 2010: 17% (n=179); year 2011: 30% (n=309); year 2012: 22% (n=311); year 2013: 31% (n=306); year 2014: 36% (n=303); year 2015: 38% (n=312); year 2016: 38% (n=310); year 2017: 24% (n=309); year 2018: 27% (n=312); year 2019: 37% (n=312); year 2020: 31% (n=312); year 2021: 17% (n=311); year 2022: 31% (n=310); year 2023: 36% (n=310); year 2024: 27% (n=313); year 2025: 36% (n=235); quarter 2010Q2: 55% (n=22); quarter 2010Q3: 20% (n=79); quarter 2010Q4: 4% (n=78); quarter 2011Q1: 38% (n=77); quarter 2011Q2: 9% (n=77); quarter 2011Q3: 34% (n=79); quarter 2011Q4: 38% (n=76); quarter 2012Q1: 16% (n=76); quarter 2012Q2: 27% (n=78); quarter 2012Q3: 19% (n=79); quarter 2012Q4: 26% (n=78); quarter 2013Q1: 12% (n=73); quarter 2013Q2: 32% (n=77); quarter 2013Q3: 38% (n=78); quarter 2013Q4: 41% (n=78); quarter 2014Q1: 28% (n=74); quarter 2014Q2: 47% (n=75); quarter 2014Q3: 18% (n=76); quarter 2014Q4: 50% (n=78); quarter 2015Q1: 57% (n=77); quarter 2015Q2: 42% (n=78); quarter 2015Q3: 33% (n=79); quarter 2015Q4: 18% (n=78); quarter 2016Q1: 41% (n=76); quarter 2016Q2: 23% (n=78); quarter 2016Q3: 48% (n=79); quarter 2016Q4: 40% (n=77); quarter 2017Q1: 0% (n=77); quarter 2017Q2: 19% (n=77); quarter 2017Q3: 24% (n=78); quarter 2017Q4: 53% (n=77); quarter 2018Q1: 14% (n=76); quarter 2018Q2: 31% (n=78); quarter 2018Q3: 39% (n=79); quarter 2018Q4: 22% (n=79); quarter 2019Q1: 26% (n=77); quarter 2019Q2: 14% (n=77); quarter 2019Q3: 57% (n=79); quarter 2019Q4: 51% (n=79); quarter 2020Q1: 36% (n=78); quarter 2020Q2: 8% (n=77); quarter 2020Q3: 33% (n=79); quarter 2020Q4: 47% (n=78); quarter 2021Q1: 42% (n=76); quarter 2021Q2: 6% (n=78); quarter 2021Q3: 8% (n=79); quarter 2021Q4: 14% (n=78); quarter 2022Q1: 31% (n=77); quarter 2022Q2: 29% (n=77); quarter 2022Q3: 18% (n=79); quarter 2022Q4: 48% (n=77); quarter 2023Q1: 36% (n=77); quarter 2023Q2: 40% (n=78); quarter 2023Q3: 33% (n=78); quarter 2023Q4: 34% (n=77); quarter 2024Q1: 22% (n=77); quarter 2024Q2: 32% (n=78); quarter 2024Q3: 29% (n=79); quarter 2024Q4: 25% (n=79); quarter 2025Q1: 42% (n=77); quarter 2025Q2: 36% (n=77); quarter 2025Q3: 32% (n=79); quarter 2025Q4: 0% (n=2); regime high: 32% (n=1311); regime low: 29% (n=1313); regime mid: 31% (n=1312); regime n/a: 29% (n=818)

## Bootstrap survival from the measured inputs (in sample, topstep_50k: $49 per evaluation, pass 20%, payout 46% of $623, 10 days to pass, 14 days to payout)

Calculator: gross $57 per evaluation, EV +8, P(payout per evaluation) 9.2%.

| start cash | P(bust, 12 months) | P(zero payouts, first batch) | median first payout (days) | funded accounts month 12 (median) |
|---|---|---|---|---|
| 500 | 72% | 38% | 24 | 0 |
| 1,000 | 52% | 15% | 24 | 0 |
| 2,000 | 27% | 2% | 24 | 18 |
| 5,000 | 4% | 0% | 24 | 21 |

## R distribution, out of sample

| dimension | bucket | trades | win rate | expectancy R | profit factor | trades/day |
|---|---|---|---|---|---|---|
| all | all | 1258 | 37.5% | -0.071 | 0.89 | 4.02 |
| year | 2025 | 262 | 37.8% | -0.064 | 0.90 | 3.49 |
| year | 2026 | 996 | 37.4% | -0.073 | 0.89 | 4.18 |
| quarter | 2025Q4 | 262 | 37.8% | -0.064 | 0.90 | 3.49 |
| quarter | 2026Q1 | 312 | 35.6% | -0.120 | 0.82 | 4.05 |
| quarter | 2026Q2 | 358 | 41.9% | +0.040 | 1.07 | 4.59 |
| quarter | 2026Q3 | 313 | 34.8% | -0.139 | 0.79 | 3.96 |
| quarter | 2026Q4 | 13 | 23.1% | -0.435 | 0.44 | 3.25 |
| session | am | 1258 | 37.5% | -0.071 | 0.89 | 4.02 |
| setup | continuation | 272 | 44.9% | +0.114 | 1.20 | 0.87 |
| setup | reversion | 986 | 35.5% | -0.122 | 0.81 | 3.15 |
| grade | A | 865 | 36.0% | -0.111 | 0.83 | 2.76 |
| grade | A+ | 393 | 41.0% | +0.016 | 1.03 | 1.26 |
| direction | long | 626 | 37.5% | -0.070 | 0.89 | 2.00 |
| direction | short | 632 | 37.5% | -0.071 | 0.89 | 2.02 |
| regime | high | 1252 | 37.4% | -0.074 | 0.88 | 4.93 |
| regime | mid | 6 | 66.7% | +0.667 | 2.96 | 1.50 |

## Pass and payout probability under exact firm rules, out of sample (one evaluation / funded account started on every trading day)

| firm | eval risk | P(pass) within 30 days | +/- | days to pass (median) | starts (open) | P(payout before breach) within 60 days | +/- | days to payout | starts (open) | payout (median $) |
|---|---|---|---|---|---|---|---|---|---|---|
| topstep_50k | 1,000 | 8.7% | 4.0% | 17 | 310 (10) | 13.2% | 4.6% | 13 | 310 (0) | 1,800 |
| fundednext_50k_flex | 1,000 | 2.6% | 1.8% | 12 | 311 (8) | 7.7% | 3.2% | 12 | 311 (0) | 3,245 |
| topstep_100k | 2,000 | 8.1% | 3.5% | 17 | 310 (9) | 12.3% | 4.5% | 12 | 310 (0) | 2,636 |
| tradeify_100k_growth | 2,000 | 27.7% | 3.9% | 2 | 310 (0) | 5.2% | 3.5% | 38 | 309 (0) | 3,600 |

Pass probability by start period, topstep_50k: year 2025: 16% (n=75); year 2026: 6% (n=235); quarter 2025Q4: 16% (n=75); quarter 2026Q1: 0% (n=77); quarter 2026Q2: 19% (n=78); quarter 2026Q3: 0% (n=79); quarter 2026Q4: 0% (n=1); regime high: 9% (n=252); regime mid: 0% (n=4); regime n/a: 9% (n=54)

Pass probability by start period, fundednext_50k_flex: year 2025: 3% (n=75); year 2026: 3% (n=236); quarter 2025Q4: 3% (n=75); quarter 2026Q1: 0% (n=77); quarter 2026Q2: 8% (n=78); quarter 2026Q3: 0% (n=79); quarter 2026Q4: 0% (n=2); regime high: 3% (n=253); regime mid: 0% (n=4); regime n/a: 2% (n=54)

Pass probability by start period, topstep_100k: year 2025: 16% (n=75); year 2026: 6% (n=235); quarter 2025Q4: 16% (n=75); quarter 2026Q1: 0% (n=77); quarter 2026Q2: 17% (n=78); quarter 2026Q3: 0% (n=79); quarter 2026Q4: 0% (n=1); regime high: 8% (n=252); regime mid: 0% (n=4); regime n/a: 9% (n=54)

Pass probability by start period, tradeify_100k_growth: year 2025: 31% (n=75); year 2026: 27% (n=235); quarter 2025Q4: 31% (n=75); quarter 2026Q1: 21% (n=77); quarter 2026Q2: 45% (n=78); quarter 2026Q3: 15% (n=79); quarter 2026Q4: 0% (n=1); regime high: 27% (n=252); regime mid: 0% (n=4); regime n/a: 35% (n=54)

## Bootstrap survival from the measured inputs (out of sample, topstep_50k: $49 per evaluation, pass 9%, payout 13% of $1,800, 17 days to pass, 13 days to payout)

Calculator: gross $21 per evaluation, EV -28, P(payout per evaluation) 1.2%.

| start cash | P(bust, 12 months) | P(zero payouts, first batch) | median first payout (days) | funded accounts month 12 (median) |
|---|---|---|---|---|
| 500 | 100% | 89% | 30 | 0 |
| 1,000 | 100% | 79% | 30 | 0 |
| 2,000 | 100% | 63% | 30 | 0 |
| 5,000 | 100% | 31% | 30 | 0 |
