# Anatomy of the sealed ledger

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report; analysed population 8689 equals the manifest's n_trades minus trades_excluded. Trades: 8689; development 7431, benchmark 1258 (benchmark = entries on or after 2025-10-06: the same window the sealed report calls out of sample, renamed because it has now been inspected; never used for selection).
Excursions are in points from the entry price: `mfe_held`/`mae_held` over the bars from entry to exit, with a stop bar's favourable extreme and a target bar's adverse extreme left out (the ledger takes the exit level to print first); `winners_room_*` use the MFE from entry through the bar before 16:00 New York or the exit bar, whichever is later; `losers_mfe_*` is how far a losing trade went toward the target before stopping out; `winners_mae_*` is how close a winner came to the stop. `stop_over_daily_atr` uses the previous Globex session's 14-session ATR; `target_over_opening_range` uses the 09:30-09:35 range.

## By period

| period | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | 1258 | 37.5% | -0.071 | 0.89 | 25.5 | 27.2 | 93% | 80% | 26% | 27% | 13% | 5% | 0.05 | 0.41 |
| development | 7431 | 40.2% | -0.037 | 0.94 | 20.8 | 25.2 | 70% | 53% | 24% | 24% | 9% | 3% | 0.11 | 0.94 |

## By period and setup

| period | setup | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | continuation | 272 | 44.9% | +0.114 | 1.20 | 38.5 | 31.2 | 93% | 78% | 20% | 27% | 10% | 3% | 0.07 | 0.59 |
| benchmark | reversion | 986 | 35.5% | -0.122 | 0.81 | 22.4 | 27.0 | 93% | 81% | 28% | 28% | 13% | 5% | 0.05 | 0.37 |
| development | continuation | 3281 | 44.1% | +0.020 | 1.04 | 19.2 | 22.0 | 50% | 36% | 20% | 20% | 8% | 2% | 0.24 | 2.04 |
| development | reversion | 4150 | 37.2% | -0.082 | 0.87 | 22.0 | 26.0 | 88% | 70% | 28% | 27% | 11% | 4% | 0.09 | 0.73 |

## By period and direction

| period | direction | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | -1 | 632 | 37.5% | -0.071 | 0.89 | 24.6 | 27.5 | 92% | 76% | 25% | 25% | 12% | 4% | 0.05 | 0.41 |
| benchmark | 1 | 626 | 37.5% | -0.070 | 0.89 | 25.8 | 27.1 | 94% | 83% | 28% | 30% | 14% | 5% | 0.05 | 0.41 |
| development | -1 | 3623 | 39.3% | -0.043 | 0.93 | 20.2 | 25.2 | 72% | 54% | 24% | 23% | 9% | 2% | 0.10 | 0.94 |
| development | 1 | 3808 | 41.1% | -0.032 | 0.94 | 21.0 | 25.5 | 68% | 53% | 25% | 25% | 10% | 4% | 0.11 | 0.94 |

## By period and grade

| period | grade | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | A | 865 | 36.0% | -0.111 | 0.83 | 22.8 | 27.2 | 94% | 83% | 27% | 27% | 14% | 5% | 0.05 | 0.39 |
| benchmark | A+ | 393 | 41.0% | +0.016 | 1.03 | 31.2 | 27.8 | 91% | 75% | 25% | 28% | 11% | 3% | 0.06 | 0.46 |
| development | A | 4639 | 38.5% | -0.068 | 0.89 | 20.5 | 25.5 | 75% | 57% | 25% | 25% | 10% | 3% | 0.10 | 0.84 |
| development | A+ | 2792 | 43.1% | +0.014 | 1.03 | 20.8 | 25.0 | 61% | 47% | 23% | 22% | 9% | 3% | 0.13 | 1.16 |

## By period and entry time

| period | entry_bucket | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | 09:30-09:35 | 261 | 44.8% | +0.114 | 1.20 | 38.8 | 31.2 | 92% | 77% | 20% | 27% | 10% | 3% | 0.07 | 0.61 |
| benchmark | 09:35-09:45 | 116 | 34.5% | -0.148 | 0.78 | 16.5 | 28.4 | 95% | 85% | 25% | 18% | 9% | 7% | 0.05 | 0.35 |
| benchmark | 09:45-10:00 | 251 | 35.9% | -0.113 | 0.83 | 22.5 | 27.0 | 93% | 82% | 27% | 27% | 14% | 6% | 0.05 | 0.37 |
| benchmark | 10:00-10:30 | 386 | 36.3% | -0.102 | 0.84 | 24.6 | 27.5 | 94% | 82% | 34% | 32% | 15% | 6% | 0.05 | 0.38 |
| benchmark | 10:30-11:00 | 240 | 35.4% | -0.124 | 0.81 | 20.5 | 26.2 | 92% | 75% | 22% | 26% | 11% | 3% | 0.05 | 0.38 |
| benchmark | after 11:00 | 4 | 0.0% | -1.020 | 0.00 | 4.0 | 28.9 | n/a | n/a | n/a | 25% | 0% | 0% | 0.04 | 0.35 |
| development | 09:30-09:35 | 3187 | 44.1% | +0.020 | 1.04 | 19.2 | 22.0 | 50% | 35% | 20% | 20% | 8% | 2% | 0.24 | 2.05 |
| development | 09:35-09:45 | 418 | 41.9% | +0.013 | 1.02 | 20.8 | 25.6 | 81% | 69% | 30% | 24% | 9% | 2% | 0.08 | 0.64 |
| development | 09:45-10:00 | 941 | 37.6% | -0.069 | 0.89 | 22.0 | 26.2 | 91% | 75% | 26% | 25% | 10% | 4% | 0.08 | 0.70 |
| development | 10:00-10:30 | 1657 | 37.1% | -0.083 | 0.87 | 22.8 | 26.0 | 87% | 69% | 29% | 29% | 11% | 4% | 0.09 | 0.76 |
| development | 10:30-11:00 | 1200 | 35.9% | -0.117 | 0.82 | 20.9 | 26.0 | 86% | 64% | 28% | 27% | 10% | 4% | 0.09 | 0.75 |
| development | after 11:00 | 28 | 35.7% | -0.116 | 0.82 | 21.5 | 26.8 | 90% | 80% | 10% | 22% | 11% | 11% | 0.09 | 0.76 |

## By period and volatility regime in points (terciles fitted on development days; confounded with price level)

| period | regime | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | high | 1252 | 37.4% | -0.074 | 0.88 | 25.4 | 27.5 | 93% | 80% | 26% | 27% | 13% | 5% | 0.05 | 0.41 |
| benchmark | mid | 6 | 66.7% | +0.667 | 2.96 | 38.4 | 22.5 | 50% | 25% | 50% | 50% | 0% | 0% | 0.05 | 1.92 |
| development | high | 4776 | 38.5% | -0.046 | 0.93 | 24.0 | 26.5 | 92% | 76% | 28% | 27% | 11% | 4% | 0.08 | 0.69 |
| development | low | 977 | 48.9% | +0.003 | 1.01 | 13.0 | 12.2 | 4% | 1% | 12% | 8% | 1% | 0% | 0.63 | 5.85 |
| development | mid | 1678 | 40.1% | -0.034 | 0.94 | 21.0 | 25.0 | 55% | 28% | 25% | 23% | 10% | 3% | 0.26 | 2.11 |

## By period and price-relative regime (daily ATR / previous close, terciles fitted on development days)

| period | rel_regime | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | high | 660 | 37.1% | -0.081 | 0.87 | 25.4 | 27.8 | 93% | 81% | 23% | 27% | 13% | 4% | 0.04 | 0.35 |
| benchmark | low | 82 | 28.0% | -0.310 | 0.58 | 20.2 | 28.5 | 78% | 65% | 26% | 32% | 15% | 8% | 0.09 | 0.60 |
| benchmark | mid | 516 | 39.5% | -0.020 | 0.97 | 26.4 | 26.8 | 94% | 80% | 30% | 28% | 12% | 5% | 0.06 | 0.45 |
| development | high | 3554 | 39.3% | -0.038 | 0.94 | 23.9 | 26.0 | 85% | 70% | 26% | 28% | 12% | 4% | 0.08 | 0.72 |
| development | low | 1573 | 41.6% | -0.047 | 0.91 | 16.8 | 21.8 | 41% | 26% | 19% | 19% | 7% | 2% | 0.34 | 2.53 |
| development | mid | 2296 | 40.7% | -0.029 | 0.95 | 19.2 | 25.2 | 67% | 48% | 25% | 21% | 8% | 3% | 0.12 | 1.01 |
| development | n/a | 8 | 62.5% | -0.023 | 0.94 | 19.9 | 12.4 | 0% | 0% | 0% | 0% | 0% | 0% | n/a | 6.91 |

## By period, setup and grade

| period | setup | grade | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | continuation | A | 95 | 50.5% | +0.257 | 1.51 | 39.5 | 26.2 | 98% | 90% | 19% | 36% | 15% | 6% | 0.06 | 0.49 |
| benchmark | continuation | A+ | 177 | 41.8% | +0.038 | 1.06 | 36.0 | 36.0 | 89% | 70% | 22% | 22% | 8% | 1% | 0.08 | 0.68 |
| benchmark | reversion | A | 770 | 34.2% | -0.156 | 0.77 | 19.9 | 27.2 | 93% | 81% | 28% | 26% | 13% | 5% | 0.05 | 0.38 |
| benchmark | reversion | A+ | 216 | 40.3% | -0.001 | 1.00 | 26.8 | 26.6 | 93% | 78% | 29% | 33% | 13% | 5% | 0.05 | 0.36 |
| development | continuation | A | 1272 | 42.8% | -0.010 | 0.98 | 17.5 | 21.2 | 47% | 32% | 19% | 19% | 6% | 2% | 0.27 | 2.49 |
| development | continuation | A+ | 2009 | 44.9% | +0.039 | 1.08 | 20.2 | 22.5 | 52% | 37% | 21% | 21% | 9% | 3% | 0.22 | 1.83 |
| development | reversion | A | 3367 | 36.8% | -0.090 | 0.86 | 22.0 | 26.0 | 88% | 68% | 28% | 27% | 11% | 4% | 0.09 | 0.74 |
| development | reversion | A+ | 783 | 38.6% | -0.049 | 0.92 | 22.0 | 26.0 | 88% | 76% | 30% | 26% | 9% | 4% | 0.08 | 0.67 |

## By period, setup and entry time

| period | setup | entry_bucket | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | continuation | 09:30-09:35 | 261 | 44.8% | +0.114 | 1.20 | 38.8 | 31.2 | 92% | 77% | 20% | 27% | 10% | 3% | 0.07 | 0.61 |
| benchmark | continuation | 09:35-09:45 | 11 | 45.5% | +0.130 | 1.23 | 27.2 | 38.8 | 100% | 100% | 40% | 17% | 0% | 0% | 0.05 | 0.31 |
| benchmark | reversion | 09:35-09:45 | 105 | 33.3% | -0.177 | 0.74 | 16.0 | 28.2 | 94% | 83% | 23% | 19% | 10% | 7% | 0.05 | 0.35 |
| benchmark | reversion | 09:45-10:00 | 251 | 35.9% | -0.113 | 0.83 | 22.5 | 27.0 | 93% | 82% | 27% | 27% | 14% | 6% | 0.05 | 0.37 |
| benchmark | reversion | 10:00-10:30 | 386 | 36.3% | -0.102 | 0.84 | 24.6 | 27.5 | 94% | 82% | 34% | 32% | 15% | 6% | 0.05 | 0.38 |
| benchmark | reversion | 10:30-11:00 | 240 | 35.4% | -0.124 | 0.81 | 20.5 | 26.2 | 92% | 75% | 22% | 26% | 11% | 3% | 0.05 | 0.38 |
| benchmark | reversion | after 11:00 | 4 | 0.0% | -1.020 | 0.00 | 4.0 | 28.9 | n/a | n/a | n/a | 25% | 0% | 0% | 0.04 | 0.35 |
| development | continuation | 09:30-09:35 | 3186 | 44.0% | +0.019 | 1.04 | 19.2 | 22.1 | 50% | 35% | 20% | 20% | 8% | 2% | 0.24 | 2.05 |
| development | continuation | 09:35-09:45 | 95 | 46.3% | +0.037 | 1.08 | 19.2 | 18.5 | 50% | 41% | 27% | 25% | 10% | 2% | 0.13 | 1.12 |
| development | reversion | 09:30-09:35 | 1 | 100.0% | +1.510 | inf | 65.0 | 0.0 | 100% | 100% | 0% | n/a | n/a | n/a | 0.05 | 0.36 |
| development | reversion | 09:35-09:45 | 323 | 40.6% | +0.006 | 1.01 | 22.2 | 26.2 | 92% | 78% | 31% | 23% | 9% | 3% | 0.08 | 0.60 |
| development | reversion | 09:45-10:00 | 941 | 37.6% | -0.069 | 0.89 | 22.0 | 26.2 | 91% | 75% | 26% | 25% | 10% | 4% | 0.08 | 0.70 |
| development | reversion | 10:00-10:30 | 1657 | 37.1% | -0.083 | 0.87 | 22.8 | 26.0 | 87% | 69% | 29% | 29% | 11% | 4% | 0.09 | 0.76 |
| development | reversion | 10:30-11:00 | 1200 | 35.9% | -0.117 | 0.82 | 20.9 | 26.0 | 86% | 64% | 28% | 27% | 10% | 4% | 0.09 | 0.75 |
| development | reversion | after 11:00 | 28 | 35.7% | -0.116 | 0.82 | 21.5 | 26.8 | 90% | 80% | 10% | 22% | 11% | 11% | 0.09 | 0.76 |

## By period, setup and price-relative regime

| period | setup | rel_regime | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | continuation | high | 136 | 41.9% | +0.041 | 1.07 | 35.6 | 33.2 | 96% | 81% | 18% | 28% | 11% | 4% | 0.05 | 0.49 |
| benchmark | continuation | low | 21 | 42.9% | +0.065 | 1.11 | 33.2 | 28.8 | 78% | 78% | 11% | 8% | 8% | 0% | 0.09 | 0.71 |
| benchmark | continuation | mid | 115 | 48.7% | +0.211 | 1.40 | 38.8 | 29.8 | 91% | 75% | 25% | 29% | 8% | 2% | 0.10 | 0.63 |
| benchmark | reversion | high | 524 | 35.9% | -0.112 | 0.83 | 22.2 | 27.5 | 93% | 81% | 24% | 26% | 13% | 4% | 0.04 | 0.35 |
| benchmark | reversion | low | 61 | 23.0% | -0.439 | 0.44 | 19.8 | 28.2 | 79% | 57% | 36% | 38% | 17% | 11% | 0.08 | 0.58 |
| benchmark | reversion | mid | 401 | 36.9% | -0.086 | 0.87 | 23.0 | 26.2 | 95% | 82% | 32% | 28% | 13% | 6% | 0.06 | 0.41 |
| development | continuation | high | 1158 | 41.7% | +0.003 | 1.01 | 24.1 | 25.5 | 73% | 57% | 24% | 26% | 11% | 3% | 0.10 | 1.02 |
| development | continuation | low | 1033 | 45.9% | +0.027 | 1.06 | 16.0 | 16.5 | 29% | 17% | 17% | 16% | 6% | 2% | 0.49 | 4.22 |
| development | continuation | mid | 1082 | 44.8% | +0.031 | 1.06 | 18.2 | 21.4 | 49% | 33% | 21% | 18% | 7% | 2% | 0.23 | 2.07 |
| development | continuation | n/a | 8 | 62.5% | -0.023 | 0.94 | 19.9 | 12.4 | 0% | 0% | 0% | 0% | 0% | 0% | n/a | 6.91 |
| development | reversion | high | 2396 | 38.1% | -0.058 | 0.91 | 23.6 | 26.2 | 92% | 76% | 27% | 29% | 13% | 4% | 0.07 | 0.64 |
| development | reversion | low | 540 | 33.3% | -0.189 | 0.72 | 18.4 | 25.8 | 73% | 49% | 26% | 24% | 7% | 3% | 0.13 | 0.98 |
| development | reversion | mid | 1214 | 37.0% | -0.083 | 0.87 | 20.8 | 25.9 | 86% | 65% | 30% | 24% | 8% | 3% | 0.10 | 0.83 |

## By year

| year | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2010 | 113 | 52.2% | -0.005 | 0.98 | 11.8 | 9.5 | 2% | 0% | 3% | 7% | 4% | 0% | 0.72 | 6.91 |
| 2011 | 193 | 48.7% | +0.056 | 1.15 | 16.5 | 14.0 | 11% | 2% | 15% | 15% | 5% | 2% | 0.55 | 5.24 |
| 2012 | 180 | 47.2% | -0.005 | 0.98 | 11.9 | 12.2 | 4% | 0% | 9% | 3% | 1% | 0% | 0.66 | 5.85 |
| 2013 | 195 | 51.3% | +0.047 | 1.18 | 13.0 | 10.8 | 3% | 0% | 13% | 11% | 2% | 1% | 0.72 | 6.08 |
| 2014 | 210 | 47.6% | +0.050 | 1.12 | 16.1 | 17.5 | 19% | 5% | 18% | 12% | 6% | 1% | 0.53 | 4.68 |
| 2015 | 249 | 42.6% | -0.022 | 0.96 | 19.0 | 20.8 | 28% | 12% | 22% | 21% | 8% | 2% | 0.40 | 3.10 |
| 2016 | 258 | 46.9% | +0.057 | 1.13 | 16.5 | 18.5 | 35% | 14% | 19% | 12% | 4% | 0% | 0.41 | 4.00 |
| 2017 | 226 | 44.2% | -0.031 | 0.93 | 15.9 | 19.2 | 20% | 8% | 21% | 13% | 5% | 2% | 0.47 | 4.05 |
| 2018 | 418 | 39.2% | -0.038 | 0.94 | 21.9 | 25.5 | 73% | 48% | 27% | 24% | 9% | 3% | 0.19 | 1.69 |
| 2019 | 366 | 38.8% | -0.046 | 0.92 | 22.0 | 25.2 | 59% | 28% | 21% | 26% | 10% | 2% | 0.22 | 1.96 |
| 2020 | 757 | 39.9% | -0.012 | 0.98 | 26.0 | 25.8 | 91% | 73% | 28% | 28% | 10% | 3% | 0.09 | 0.84 |
| 2021 | 734 | 33.8% | -0.168 | 0.75 | 20.0 | 26.5 | 84% | 67% | 24% | 26% | 11% | 5% | 0.12 | 0.81 |
| 2022 | 1104 | 39.6% | -0.018 | 0.97 | 25.5 | 26.8 | 93% | 80% | 28% | 30% | 12% | 6% | 0.07 | 0.56 |
| 2023 | 759 | 39.5% | -0.022 | 0.96 | 25.8 | 26.0 | 92% | 69% | 27% | 29% | 10% | 4% | 0.10 | 0.88 |
| 2024 | 883 | 37.9% | -0.060 | 0.90 | 22.5 | 26.5 | 92% | 74% | 31% | 25% | 10% | 3% | 0.09 | 0.78 |
| 2025 | 1048 | 37.7% | -0.067 | 0.90 | 23.1 | 27.0 | 94% | 80% | 28% | 26% | 11% | 4% | 0.06 | 0.58 |
| 2026 | 996 | 37.4% | -0.073 | 0.89 | 25.2 | 27.5 | 93% | 80% | 25% | 26% | 13% | 4% | 0.05 | 0.37 |

## By year and setup

| year | setup | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2010 | continuation | 112 | 51.8% | -0.016 | 0.95 | 11.8 | 9.6 | 2% | 0% | 3% | 7% | 4% | 0% | 0.72 | 6.91 |
| 2010 | reversion | 1 | 100.0% | +1.170 | inf | 35.8 | 2.0 | 0% | 0% | 0% | n/a | n/a | n/a | 0.62 | 5.43 |
| 2011 | continuation | 182 | 49.5% | +0.061 | 1.17 | 15.1 | 13.9 | 8% | 1% | 16% | 14% | 4% | 1% | 0.56 | 5.43 |
| 2011 | reversion | 11 | 36.4% | -0.013 | 0.98 | 27.5 | 21.5 | 75% | 25% | 0% | 29% | 14% | 14% | 0.37 | 3.30 |
| 2012 | continuation | 178 | 47.2% | -0.012 | 0.96 | 11.9 | 12.2 | 4% | 0% | 10% | 3% | 1% | 0% | 0.66 | 5.85 |
| 2012 | reversion | 2 | 50.0% | +0.560 | 3.87 | 23.9 | 9.6 | 0% | 0% | 0% | 0% | 0% | 0% | 0.63 | 8.47 |
| 2013 | continuation | 192 | 51.6% | +0.050 | 1.20 | 13.0 | 10.6 | 3% | 0% | 13% | 11% | 2% | 1% | 0.72 | 6.08 |
| 2013 | reversion | 3 | 33.3% | -0.177 | 0.74 | 18.0 | 25.2 | 0% | 0% | 0% | 0% | 0% | 0% | 0.66 | 5.63 |
| 2014 | continuation | 187 | 48.1% | +0.053 | 1.13 | 16.0 | 16.8 | 18% | 4% | 17% | 10% | 6% | 0% | 0.55 | 4.90 |
| 2014 | reversion | 23 | 43.5% | +0.025 | 1.06 | 19.0 | 20.0 | 30% | 10% | 30% | 23% | 8% | 8% | 0.47 | 3.71 |
| 2015 | continuation | 199 | 42.7% | -0.038 | 0.92 | 18.5 | 20.0 | 20% | 6% | 22% | 19% | 6% | 1% | 0.40 | 3.17 |
| 2015 | reversion | 50 | 42.0% | +0.041 | 1.08 | 25.0 | 24.0 | 62% | 38% | 19% | 28% | 14% | 7% | 0.39 | 2.63 |
| 2016 | continuation | 207 | 46.9% | +0.047 | 1.11 | 16.5 | 18.2 | 30% | 10% | 16% | 12% | 4% | 0% | 0.42 | 4.11 |
| 2016 | reversion | 51 | 47.1% | +0.094 | 1.19 | 21.5 | 22.0 | 54% | 29% | 29% | 11% | 4% | 0% | 0.32 | 2.76 |
| 2017 | continuation | 199 | 45.2% | -0.006 | 0.99 | 15.5 | 18.8 | 20% | 9% | 20% | 12% | 6% | 3% | 0.47 | 4.22 |
| 2017 | reversion | 27 | 37.0% | -0.216 | 0.64 | 18.0 | 25.2 | 20% | 0% | 30% | 18% | 0% | 0% | 0.45 | 3.30 |
| 2018 | continuation | 206 | 44.7% | +0.090 | 1.17 | 28.2 | 25.0 | 67% | 45% | 32% | 26% | 14% | 4% | 0.22 | 1.95 |
| 2018 | reversion | 212 | 34.0% | -0.162 | 0.75 | 16.5 | 25.8 | 79% | 53% | 22% | 23% | 6% | 2% | 0.17 | 1.47 |
| 2019 | continuation | 220 | 42.3% | +0.027 | 1.05 | 23.8 | 25.0 | 57% | 30% | 16% | 28% | 10% | 2% | 0.23 | 2.05 |
| 2019 | reversion | 146 | 33.6% | -0.157 | 0.76 | 18.5 | 25.6 | 63% | 24% | 31% | 24% | 10% | 3% | 0.21 | 1.80 |
| 2020 | continuation | 228 | 43.0% | +0.067 | 1.12 | 27.5 | 26.0 | 91% | 61% | 23% | 26% | 8% | 2% | 0.10 | 0.99 |
| 2020 | reversion | 529 | 38.6% | -0.047 | 0.93 | 24.2 | 25.8 | 92% | 78% | 30% | 29% | 10% | 4% | 0.09 | 0.78 |
| 2021 | continuation | 242 | 34.7% | -0.142 | 0.79 | 23.5 | 26.6 | 88% | 71% | 17% | 30% | 15% | 6% | 0.12 | 0.88 |
| 2021 | reversion | 492 | 33.3% | -0.181 | 0.73 | 18.8 | 26.5 | 82% | 64% | 27% | 24% | 9% | 4% | 0.12 | 0.79 |
| 2022 | continuation | 256 | 44.1% | +0.100 | 1.18 | 33.4 | 27.0 | 91% | 84% | 29% | 30% | 11% | 5% | 0.07 | 0.64 |
| 2022 | reversion | 848 | 38.2% | -0.053 | 0.92 | 23.9 | 26.5 | 94% | 79% | 27% | 30% | 13% | 6% | 0.07 | 0.55 |
| 2023 | continuation | 237 | 40.5% | +0.004 | 1.01 | 26.8 | 26.5 | 93% | 72% | 29% | 28% | 10% | 4% | 0.11 | 0.94 |
| 2023 | reversion | 522 | 39.1% | -0.033 | 0.95 | 25.5 | 25.8 | 92% | 68% | 26% | 29% | 11% | 3% | 0.10 | 0.87 |
| 2024 | continuation | 242 | 40.1% | -0.006 | 0.99 | 22.8 | 26.8 | 91% | 72% | 36% | 23% | 7% | 2% | 0.09 | 0.86 |
| 2024 | reversion | 641 | 37.1% | -0.081 | 0.87 | 22.5 | 26.5 | 92% | 74% | 29% | 25% | 11% | 3% | 0.08 | 0.75 |
| 2025 | continuation | 260 | 44.2% | +0.099 | 1.17 | 35.6 | 27.8 | 93% | 79% | 19% | 21% | 8% | 3% | 0.07 | 0.72 |
| 2025 | reversion | 788 | 35.5% | -0.121 | 0.82 | 20.5 | 26.8 | 95% | 81% | 32% | 28% | 12% | 4% | 0.06 | 0.54 |
| 2026 | continuation | 206 | 42.7% | +0.060 | 1.10 | 34.8 | 33.4 | 94% | 76% | 18% | 25% | 11% | 3% | 0.07 | 0.52 |
| 2026 | reversion | 790 | 36.1% | -0.107 | 0.84 | 22.8 | 27.0 | 92% | 81% | 27% | 27% | 13% | 5% | 0.05 | 0.36 |

## By period, setup and exit reason

| period | setup | exit_reason | trades | win_rate | expectancy_r | profit_factor | mfe_held_med | mae_held_med | winners_room_beyond_target_12pt | winners_room_2x_target | winners_mae_ge_60pct_stop | losers_mfe_ge_50pct_target | losers_mfe_ge_75pct_target | losers_mfe_ge_90pct_target | stop_over_daily_atr_med | target_over_opening_range_med |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | continuation | stop | 150 | 0.0% | -1.015 | 0.00 | 12.0 | 53.2 | n/a | n/a | n/a | 27% | 10% | 3% | 0.07 | 0.62 |
| benchmark | continuation | target | 122 | 100.0% | +1.503 | inf | 67.0 | 8.4 | 93% | 78% | 20% | n/a | n/a | n/a | 0.07 | 0.54 |
| benchmark | reversion | stop | 636 | 0.0% | -1.020 | 0.00 | 7.9 | 31.5 | n/a | n/a | n/a | 28% | 13% | 5% | 0.05 | 0.38 |
| benchmark | reversion | target | 350 | 100.0% | +1.510 | inf | 44.5 | 8.8 | 93% | 81% | 28% | n/a | n/a | n/a | 0.05 | 0.36 |
| development | continuation | session_end | 838 | 58.9% | +0.175 | 2.27 | 16.5 | 11.0 | 0% | 0% | 18% | 18% | 6% | 1% | 0.60 | 5.63 |
| development | continuation | stop | 1490 | 0.0% | -1.019 | 0.00 | 7.8 | 27.5 | n/a | n/a | n/a | 21% | 8% | 3% | 0.14 | 1.31 |
| development | continuation | target | 953 | 100.0% | +1.509 | inf | 40.5 | 7.5 | 76% | 54% | 22% | n/a | n/a | n/a | 0.13 | 1.13 |
| development | reversion | session_end | 55 | 58.2% | +0.268 | 3.69 | 27.2 | 16.2 | 0% | 0% | 50% | 35% | 17% | 4% | 0.41 | 3.45 |
| development | reversion | stop | 2585 | 0.0% | -1.020 | 0.00 | 10.0 | 28.8 | n/a | n/a | n/a | 27% | 10% | 4% | 0.09 | 0.73 |
| development | reversion | target | 1510 | 100.0% | +1.510 | inf | 42.2 | 9.2 | 90% | 71% | 28% | n/a | n/a | n/a | 0.09 | 0.70 |

## Bracket geometry by year

| year | trades | median price | median daily ATR (pts) | median 09:30-09:35 range (pts) | stop pts | target pts | stop / daily ATR | target / opening range | stop as % of price |
|---|---|---|---|---|---|---|---|---|---|
| 2010 | 113 | 1,953 | 35 | 5.5 | 25 | 38 | 0.721 | 6.91 | 1.280% |
| 2011 | 193 | 2,305 | 45 | 7.2 | 25 | 38 | 0.552 | 5.24 | 1.085% |
| 2012 | 180 | 2,636 | 38 | 6.5 | 25 | 38 | 0.659 | 5.85 | 0.948% |
| 2013 | 195 | 3,010 | 35 | 6.2 | 25 | 38 | 0.716 | 6.08 | 0.831% |
| 2014 | 210 | 3,800 | 47 | 8.1 | 25 | 38 | 0.533 | 4.68 | 0.658% |
| 2015 | 249 | 4,426 | 63 | 12.2 | 25 | 38 | 0.395 | 3.10 | 0.565% |
| 2016 | 258 | 4,524 | 61 | 9.5 | 25 | 38 | 0.410 | 4.00 | 0.553% |
| 2017 | 226 | 5,840 | 54 | 9.4 | 25 | 38 | 0.467 | 4.05 | 0.428% |
| 2018 | 418 | 6,944 | 134 | 22.5 | 25 | 38 | 0.186 | 1.69 | 0.360% |
| 2019 | 366 | 7,644 | 113 | 19.4 | 25 | 38 | 0.221 | 1.96 | 0.327% |
| 2020 | 757 | 10,549 | 269 | 45.8 | 25 | 38 | 0.093 | 0.83 | 0.237% |
| 2021 | 734 | 14,592 | 212 | 47.5 | 25 | 38 | 0.118 | 0.80 | 0.171% |
| 2022 | 1104 | 12,664 | 379 | 69.0 | 25 | 38 | 0.066 | 0.55 | 0.197% |
| 2023 | 759 | 14,725 | 246 | 43.2 | 25 | 38 | 0.102 | 0.88 | 0.170% |
| 2024 | 883 | 19,504 | 297 | 50.0 | 25 | 38 | 0.084 | 0.76 | 0.128% |
| 2025 | 1048 | 22,222 | 409 | 69.8 | 25 | 38 | 0.061 | 0.54 | 0.112% |
| 2026 | 996 | 28,829 | 518 | 106.5 | 25 | 38 | 0.048 | 0.36 | 0.087% |

## Excursion quantiles (points) by period and outcome

| period | outcome | mfe_held p25 | p50 | p75 | mae_held p25 | p50 | p75 | mfe_day p25 | p50 | p75 |
|---|---|---|---|---|---|---|---|---|---|---|
| benchmark | loss | 0.0 | 8.5 | 22.5 | 27.8 | 32.8 | 42.8 | 33.8 | 96.8 | 212.7 |
| benchmark | win | 40.9 | 46.5 | 59.3 | 2.2 | 8.6 | 16.6 | 95.8 | 185.6 | 321.9 |
| development | loss | 3.0 | 9.0 | 18.8 | 25.8 | 27.8 | 32.5 | 11.2 | 31.2 | 95.7 |
| development | win | 38.2 | 40.2 | 45.2 | 3.8 | 8.5 | 15.0 | 44.0 | 84.5 | 166.2 |
