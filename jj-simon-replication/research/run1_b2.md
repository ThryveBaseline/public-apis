# B2: reversion rules as stated, screened on the sealed ledger

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report; population 8689.

Base reproduction: the sequential pass (one position at a time, three-loss session stop) on the unfiltered ledger keeps all 8689 trades. That is a necessary condition only; that the pass reproduces the engine's stop is shown in the test suite by running the frozen engine with and without its loss stop.
Reversion entries: 5136. Pass the move-away gate from the open (B2b2): 5105; since the last return to fair (B2b1): 5100; B2b1 with the band at 76 on wide-open days: 5001; B2b1 with the band at the funded menu target: 4937. Room at the signal >= the whole target (B2h): 4392. Trades on wide-open days (09:30 body > 25 points): 1462.
Screening on a fixed ledger ignores freed positions and trades the sealed stop suppressed (documented caveat). The benchmark year is reported beside and never selected on.

## Filters with the sealed brackets (ledger R, including positions held past 11:00 and the sealed `session_end` exits at the end of the New York calendar day)

### Scope = all

| filter | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| base | development | 7431 | 40.2% | -0.037 | 0.94 | -276.4 |
| base | benchmark | 1258 | 37.5% | -0.071 | 0.89 | -89.1 |
| B2a | development | 4058 | 43.1% | +0.007 | 1.01 | +28.0 |
| B2a | benchmark | 484 | 42.8% | +0.062 | 1.11 | +29.9 |
| B2b2 | development | 7400 | 40.2% | -0.037 | 0.94 | -272.2 |
| B2b2 | benchmark | 1258 | 37.5% | -0.071 | 0.89 | -89.1 |
| B2b1 | development | 7395 | 40.2% | -0.037 | 0.94 | -271.1 |
| B2b1 | benchmark | 1258 | 37.5% | -0.071 | 0.89 | -89.1 |
| B2c4 | development | 7021 | 40.4% | -0.036 | 0.94 | -250.3 |
| B2c4 | benchmark | 1026 | 37.6% | -0.068 | 0.89 | -70.1 |
| B2c3 | development | 6689 | 40.5% | -0.033 | 0.94 | -220.3 |
| B2c3 | benchmark | 911 | 37.0% | -0.084 | 0.87 | -76.7 |
| B2h | development | 6740 | 40.5% | -0.033 | 0.94 | -221.6 |
| B2h | benchmark | 1183 | 38.0% | -0.058 | 0.91 | -68.3 |
| cut0945 | development | 3605 | 43.8% | +0.019 | 1.04 | +69.0 |
| cut0945 | benchmark | 377 | 41.6% | +0.033 | 1.06 | +12.6 |
| cut1000 | development | 4546 | 42.5% | +0.001 | 1.00 | +3.9 |
| cut1000 | benchmark | 628 | 39.3% | -0.025 | 0.96 | -15.8 |
| eval_as_stated | development | 7202 | 40.3% | -0.037 | 0.94 | -264.0 |
| eval_as_stated | benchmark | 1132 | 37.8% | -0.064 | 0.90 | -71.9 |
| funded_as_stated | development | 4042 | 43.0% | +0.006 | 1.01 | +23.9 |
| funded_as_stated | benchmark | 480 | 42.7% | +0.060 | 1.10 | +28.9 |

### Scope = reversion

| filter | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| base | development | 4150 | 37.2% | -0.082 | 0.87 | -341.8 |
| base | benchmark | 986 | 35.5% | -0.122 | 0.81 | -120.2 |
| B2a | development | 777 | 38.6% | -0.048 | 0.92 | -37.5 |
| B2a | benchmark | 212 | 40.1% | -0.006 | 0.99 | -1.2 |
| B2b2 | development | 4119 | 37.2% | -0.082 | 0.87 | -337.6 |
| B2b2 | benchmark | 986 | 35.5% | -0.122 | 0.81 | -120.2 |
| B2b1 | development | 4114 | 37.2% | -0.082 | 0.87 | -336.6 |
| B2b1 | benchmark | 986 | 35.5% | -0.122 | 0.81 | -120.2 |
| B2c4 | development | 3740 | 37.1% | -0.084 | 0.87 | -315.8 |
| B2c4 | benchmark | 754 | 35.0% | -0.134 | 0.80 | -101.2 |
| B2c3 | development | 3408 | 37.1% | -0.084 | 0.87 | -285.8 |
| B2c3 | benchmark | 639 | 33.6% | -0.169 | 0.75 | -107.8 |
| B2h | development | 3459 | 37.1% | -0.083 | 0.87 | -287.1 |
| B2h | benchmark | 911 | 36.0% | -0.109 | 0.83 | -99.4 |
| cut0945 | development | 324 | 40.7% | +0.011 | 1.02 | +3.5 |
| cut0945 | benchmark | 105 | 33.3% | -0.177 | 0.74 | -18.5 |
| cut1000 | development | 1265 | 38.4% | -0.049 | 0.92 | -61.6 |
| cut1000 | benchmark | 356 | 35.1% | -0.132 | 0.80 | -46.9 |
| eval_as_stated | development | 3921 | 37.1% | -0.084 | 0.87 | -329.5 |
| eval_as_stated | benchmark | 860 | 35.6% | -0.120 | 0.82 | -103.0 |
| funded_as_stated | development | 761 | 38.4% | -0.055 | 0.91 | -41.6 |
| funded_as_stated | benchmark | 208 | 39.9% | -0.010 | 0.98 | -2.2 |

### Scope = continuation

| filter | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| base | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| base | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2a | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2a | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2b2 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2b2 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2b1 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2b1 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2c4 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2c4 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2c3 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2c3 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| B2h | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| B2h | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| cut0945 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| cut0945 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| cut1000 | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| cut1000 | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| eval_as_stated | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| eval_as_stated | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |
| funded_as_stated | development | 3281 | 44.1% | +0.020 | 1.04 | +65.5 |
| funded_as_stated | benchmark | 272 | 44.9% | +0.114 | 1.20 | +31.1 |

### Development years, scope = all: expectancy R by year

| filter | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | mean | years > 0 | years better than base |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | -0.005 | +0.056 | -0.005 | +0.047 | +0.050 | -0.022 | +0.057 | -0.031 | -0.038 | -0.046 | -0.012 | -0.168 | -0.018 | -0.022 | -0.060 | -0.067 | -0.018 | 4/16 | 0/16 |
| B2a | -0.016 | +0.061 | -0.012 | +0.050 | +0.055 | -0.045 | +0.045 | -0.009 | +0.069 | +0.025 | +0.080 | -0.200 | +0.031 | +0.028 | -0.035 | +0.025 | +0.010 | 10/16 | 11/16 |
| B2b2 | -0.005 | +0.052 | -0.014 | +0.052 | +0.060 | -0.024 | +0.065 | -0.024 | -0.038 | -0.048 | -0.010 | -0.170 | -0.018 | -0.022 | -0.060 | -0.067 | -0.017 | 4/16 | 5/16 |
| B2b1 | -0.005 | +0.052 | -0.014 | +0.052 | +0.060 | -0.020 | +0.060 | -0.024 | -0.035 | -0.045 | -0.010 | -0.170 | -0.018 | -0.022 | -0.060 | -0.067 | -0.017 | 4/16 | 8/16 |
| B2c4 | -0.005 | +0.056 | -0.005 | +0.047 | +0.050 | -0.020 | +0.057 | -0.031 | -0.038 | -0.046 | -0.023 | -0.170 | -0.018 | -0.021 | -0.060 | -0.042 | -0.017 | 4/16 | 4/16 |
| B2c3 | -0.005 | +0.056 | -0.005 | +0.047 | +0.050 | -0.027 | +0.057 | -0.031 | -0.047 | -0.046 | -0.018 | -0.156 | -0.017 | -0.022 | -0.050 | -0.045 | -0.016 | 4/16 | 5/16 |
| B2h | -0.016 | +0.058 | -0.012 | +0.050 | +0.081 | -0.028 | +0.044 | -0.017 | -0.019 | -0.051 | -0.033 | -0.157 | -0.025 | +0.002 | -0.053 | -0.057 | -0.015 | 5/16 | 9/16 |
| cut0945 | -0.016 | +0.061 | -0.012 | +0.050 | +0.053 | -0.038 | +0.047 | -0.011 | +0.089 | +0.022 | +0.047 | -0.093 | +0.084 | +0.006 | -0.026 | +0.039 | +0.019 | 10/16 | 12/16 |
| cut1000 | -0.016 | +0.055 | -0.014 | +0.050 | +0.049 | -0.031 | +0.043 | -0.008 | +0.018 | -0.018 | +0.071 | -0.106 | +0.061 | -0.002 | -0.036 | -0.064 | +0.003 | 7/16 | 10/16 |
| eval_as_stated | -0.005 | +0.052 | -0.014 | +0.052 | +0.060 | -0.016 | +0.060 | -0.024 | -0.035 | -0.045 | -0.010 | -0.164 | -0.018 | -0.027 | -0.069 | -0.063 | -0.017 | 4/16 | 10/16 |
| funded_as_stated | -0.016 | +0.061 | -0.012 | +0.050 | +0.047 | -0.040 | +0.053 | -0.009 | +0.074 | +0.012 | +0.080 | -0.203 | +0.028 | +0.024 | -0.030 | +0.020 | +0.009 | 10/16 | 10/16 |

### Development years, scope = reversion: expectancy R by year

| filter | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | mean | years > 0 | years better than base |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base | +1.170 | -0.013 | +0.560 | -0.177 | +0.025 | +0.041 | +0.094 | -0.216 | -0.162 | -0.157 | -0.047 | -0.181 | -0.053 | -0.033 | -0.081 | -0.101 | +0.042 | 5/16 | 0/16 |
| B2a | n/a | n/a | n/a | n/a | +0.245 | -0.388 | -0.016 | -0.165 | -0.072 | +0.002 | +0.107 | -0.379 | -0.068 | +0.092 | -0.088 | +0.008 | -0.060 | 5/12 | 7/16 |
| B2b2 | +1.170 | -0.124 | -0.390 | +0.245 | +0.125 | +0.042 | +0.142 | -0.170 | -0.167 | -0.163 | -0.043 | -0.184 | -0.053 | -0.033 | -0.081 | -0.101 | +0.013 | 5/16 | 6/16 |
| B2b1 | +1.170 | -0.124 | -0.390 | +0.245 | +0.125 | +0.068 | +0.113 | -0.170 | -0.162 | -0.157 | -0.043 | -0.184 | -0.053 | -0.034 | -0.081 | -0.101 | +0.014 | 5/16 | 7/16 |
| B2c4 | +1.170 | -0.013 | +0.560 | -0.177 | +0.025 | +0.055 | +0.094 | -0.216 | -0.162 | -0.157 | -0.067 | -0.184 | -0.061 | -0.033 | -0.083 | -0.073 | +0.042 | 5/16 | 3/16 |
| B2c3 | +1.170 | -0.013 | +0.560 | -0.177 | +0.025 | +0.023 | +0.094 | -0.216 | -0.182 | -0.157 | -0.063 | -0.164 | -0.066 | -0.035 | -0.071 | -0.082 | +0.041 | 5/16 | 3/16 |
| B2h | n/a | -0.012 | n/a | n/a | +0.456 | +0.045 | +0.025 | -0.129 | -0.166 | -0.223 | -0.086 | -0.167 | -0.068 | +0.001 | -0.074 | -0.090 | -0.037 | 4/13 | 8/16 |
| cut0945 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | -1.020 | +0.064 | -0.177 | -0.051 | +0.144 | +0.031 | +0.022 | -0.137 | +0.050 | -0.119 | 5/9 | 5/16 |
| cut1000 | n/a | -1.020 | -0.390 | n/a | -0.173 | +0.091 | -0.071 | -0.177 | -0.262 | -0.331 | +0.077 | -0.052 | +0.025 | -0.011 | -0.077 | -0.164 | -0.181 | 3/14 | 7/16 |
| eval_as_stated | +1.170 | -0.124 | -0.390 | +0.245 | +0.125 | +0.095 | +0.113 | -0.170 | -0.162 | -0.157 | -0.045 | -0.175 | -0.056 | -0.041 | -0.094 | -0.099 | +0.015 | 5/16 | 9/16 |
| funded_as_stated | n/a | n/a | n/a | n/a | -1.020 | -0.177 | +0.213 | -0.165 | -0.040 | -0.177 | +0.107 | -0.396 | -0.077 | +0.076 | -0.074 | -0.004 | -0.144 | 3/12 | 7/16 |

## Composites: filters x brackets (replayed, flat at 16:00)

Join check: the replay covers every ledger entry once per variant, and the replayed sealed bracket equals the ledger in R and exit time on all 7656 stop or target exits before 16:00. Every composite is scored on the replayed entries (the replay drops entries without prior-session context for every variant), through the sequential pass with each replayed trade's own exit time: a longer hold blocks the entries it would have blocked, and the three-loss stop counts only outcomes that had printed.

### Scope = all

| composite | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| sealed bracket, flat 16:00 (control) | development | 7397 | 40.3% | -0.041 | 0.93 | -303.4 |
| sealed bracket, flat 16:00 (control) | benchmark | 1250 | 37.4% | -0.072 | 0.89 | -90.4 |
| B2d wide-open switch | development | 7143 | 40.5% | -0.037 | 0.93 | -263.5 |
| B2d wide-open switch | benchmark | 1039 | 38.1% | -0.052 | 0.92 | -53.9 |
| B2f1 target from room, menu | development | 6609 | 35.9% | -0.040 | 0.93 | -262.9 |
| B2f1 target from room, menu | benchmark | 970 | 27.1% | -0.122 | 0.84 | -118.5 |
| B2f2 target from room, exact | development | 6614 | 36.4% | -0.039 | 0.94 | -256.1 |
| B2f2 target from room, exact | benchmark | 972 | 27.6% | -0.123 | 0.83 | -119.3 |
| B2f3 target from room, half | development | 6845 | 37.4% | -0.038 | 0.94 | -259.6 |
| B2f3 target from room, half | benchmark | 1044 | 30.1% | -0.100 | 0.86 | -104.5 |
| B2f1 + B2e wide stop over 100 room | development | 6494 | 37.3% | -0.035 | 0.94 | -227.2 |
| B2f1 + B2e wide stop over 100 room | benchmark | 930 | 31.1% | -0.083 | 0.88 | -77.2 |
| B2a + B2f1 | development | 3970 | 41.6% | +0.016 | 1.03 | +62.8 |
| B2a + B2f1 | benchmark | 448 | 35.9% | +0.007 | 1.01 | +3.2 |
| evaluation as stated (B2b1 band = target, B2d) | development | 6999 | 40.4% | -0.040 | 0.93 | -276.5 |
| evaluation as stated (B2b1 band = target, B2d) | benchmark | 988 | 38.0% | -0.057 | 0.91 | -56.7 |
| funded filters with the sealed bracket | development | 4022 | 43.0% | -0.000 | 1.00 | -0.7 |
| funded filters with the sealed bracket | benchmark | 476 | 42.6% | +0.060 | 1.10 | +28.6 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | development | 3957 | 41.6% | +0.015 | 1.03 | +60.0 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | benchmark | 448 | 35.9% | +0.007 | 1.01 | +3.2 |
| funded as stated + B2e | development | 3947 | 42.2% | +0.015 | 1.03 | +58.1 |
| funded as stated + B2e | benchmark | 443 | 38.1% | +0.048 | 1.08 | +21.1 |

### Scope = reversion

| composite | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| sealed bracket, flat 16:00 (control) | development | 4132 | 37.3% | -0.084 | 0.87 | -345.7 |
| sealed bracket, flat 16:00 (control) | benchmark | 979 | 35.4% | -0.123 | 0.81 | -120.7 |
| B2d wide-open switch | development | 3878 | 37.5% | -0.079 | 0.88 | -305.1 |
| B2d wide-open switch | benchmark | 768 | 35.8% | -0.111 | 0.83 | -85.2 |
| B2f1 target from room, menu | development | 3344 | 27.9% | -0.091 | 0.87 | -305.2 |
| B2f1 target from room, menu | benchmark | 699 | 20.3% | -0.213 | 0.74 | -148.7 |
| B2f2 target from room, exact | development | 3349 | 29.0% | -0.089 | 0.88 | -298.3 |
| B2f2 target from room, exact | benchmark | 701 | 21.0% | -0.213 | 0.74 | -149.5 |
| B2f3 target from room, half | development | 3580 | 31.2% | -0.084 | 0.88 | -301.9 |
| B2f3 target from room, half | benchmark | 773 | 25.0% | -0.174 | 0.77 | -134.7 |
| B2f1 + B2e wide stop over 100 room | development | 3229 | 30.5% | -0.083 | 0.88 | -269.5 |
| B2f1 + B2e wide stop over 100 room | benchmark | 659 | 25.5% | -0.163 | 0.78 | -107.4 |
| B2a + B2f1 | development | 705 | 30.4% | +0.029 | 1.04 | +20.5 |
| B2a + B2f1 | benchmark | 177 | 22.6% | -0.153 | 0.81 | -27.0 |
| evaluation as stated (B2b1 band = target, B2d) | development | 3734 | 37.2% | -0.085 | 0.87 | -318.1 |
| evaluation as stated (B2b1 band = target, B2d) | benchmark | 717 | 35.4% | -0.123 | 0.81 | -88.0 |
| funded filters with the sealed bracket | development | 757 | 38.3% | -0.057 | 0.91 | -43.0 |
| funded filters with the sealed bracket | benchmark | 205 | 40.0% | -0.008 | 0.99 | -1.6 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | development | 692 | 30.2% | +0.026 | 1.04 | +17.8 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | benchmark | 177 | 22.6% | -0.153 | 0.81 | -27.0 |
| funded as stated + B2e | development | 682 | 33.4% | +0.023 | 1.03 | +15.8 |
| funded as stated + B2e | benchmark | 172 | 27.9% | -0.053 | 0.93 | -9.2 |

### Scope = continuation

| composite | period | trades | win rate | expectancy R | profit factor | total R |
|---|---|---|---|---|---|---|
| sealed bracket, flat 16:00 (control) | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| sealed bracket, flat 16:00 (control) | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| B2d wide-open switch | development | 3265 | 44.0% | +0.013 | 1.03 | +41.6 |
| B2d wide-open switch | benchmark | 271 | 44.6% | +0.116 | 1.21 | +31.4 |
| B2f1 target from room, menu | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| B2f1 target from room, menu | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| B2f2 target from room, exact | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| B2f2 target from room, exact | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| B2f3 target from room, half | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| B2f3 target from room, half | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| B2f1 + B2e wide stop over 100 room | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| B2f1 + B2e wide stop over 100 room | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| B2a + B2f1 | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| B2a + B2f1 | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| evaluation as stated (B2b1 band = target, B2d) | development | 3265 | 44.0% | +0.013 | 1.03 | +41.6 |
| evaluation as stated (B2b1 band = target, B2d) | benchmark | 271 | 44.6% | +0.116 | 1.21 | +31.4 |
| funded filters with the sealed bracket | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| funded filters with the sealed bracket | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |
| funded as stated + B2e | development | 3265 | 44.1% | +0.013 | 1.03 | +42.3 |
| funded as stated + B2e | benchmark | 271 | 44.6% | +0.112 | 1.20 | +30.2 |

### Development years, scope = all: expectancy R by year

| composite | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | mean | years > 0 | years better than the control |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sealed bracket, flat 16:00 (control) | +0.024 | +0.025 | -0.011 | +0.033 | +0.025 | -0.022 | +0.052 | -0.047 | -0.054 | -0.056 | -0.012 | -0.167 | -0.018 | -0.025 | -0.060 | -0.067 | -0.024 | 5/16 | 0/16 |
| B2d wide-open switch | +0.024 | +0.025 | -0.011 | +0.033 | +0.025 | -0.033 | +0.052 | -0.047 | -0.052 | -0.056 | +0.002 | -0.158 | -0.015 | -0.027 | -0.048 | -0.067 | -0.022 | 6/16 | 6/16 |
| B2f1 target from room, menu | +0.024 | +0.029 | -0.011 | +0.033 | +0.027 | -0.019 | +0.043 | -0.050 | -0.033 | -0.053 | -0.021 | -0.197 | +0.013 | -0.040 | -0.033 | -0.097 | -0.024 | 6/16 | 7/16 |
| B2f2 target from room, exact | +0.024 | +0.025 | -0.011 | +0.032 | +0.040 | -0.022 | +0.048 | -0.051 | -0.037 | -0.064 | -0.026 | -0.177 | +0.008 | -0.035 | -0.038 | -0.086 | -0.023 | 6/16 | 6/16 |
| B2f3 target from room, half | +0.024 | +0.029 | -0.011 | +0.033 | +0.027 | -0.016 | +0.047 | -0.050 | -0.042 | -0.047 | -0.012 | -0.175 | +0.000 | -0.012 | -0.043 | -0.106 | -0.022 | 6/16 | 9/16 |
| B2f1 + B2e wide stop over 100 room | +0.024 | +0.029 | -0.011 | +0.033 | +0.027 | -0.019 | +0.036 | -0.050 | -0.030 | -0.038 | -0.001 | -0.163 | +0.004 | -0.038 | -0.036 | -0.099 | -0.021 | 6/16 | 9/16 |
| B2a + B2f1 | +0.014 | +0.029 | -0.018 | +0.036 | +0.034 | -0.045 | +0.045 | -0.028 | +0.076 | +0.008 | +0.109 | -0.196 | +0.146 | +0.000 | -0.039 | +0.043 | +0.013 | 11/16 | 11/16 |
| evaluation as stated (B2b1 band = target, B2d) | +0.024 | +0.020 | -0.019 | +0.038 | +0.035 | -0.029 | +0.053 | -0.041 | -0.049 | -0.055 | +0.003 | -0.162 | -0.023 | -0.031 | -0.054 | -0.075 | -0.023 | 6/16 | 9/16 |
| funded filters with the sealed bracket | +0.014 | +0.029 | -0.018 | +0.036 | +0.026 | -0.040 | +0.047 | -0.028 | +0.060 | -0.009 | +0.084 | -0.207 | +0.031 | +0.019 | -0.027 | +0.015 | +0.002 | 10/16 | 11/16 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | +0.014 | +0.029 | -0.018 | +0.036 | +0.026 | -0.040 | +0.052 | -0.028 | +0.081 | -0.008 | +0.109 | -0.206 | +0.146 | +0.003 | -0.039 | +0.047 | +0.013 | 10/16 | 11/16 |
| funded as stated + B2e | +0.014 | +0.029 | -0.018 | +0.036 | +0.026 | -0.040 | +0.052 | -0.028 | +0.086 | -0.008 | +0.103 | -0.215 | +0.122 | +0.007 | -0.010 | +0.048 | +0.013 | 10/16 | 11/16 |

### Development years, scope = reversion: expectancy R by year

| composite | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | mean | years > 0 | years better than the control |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sealed bracket, flat 16:00 (control) | +0.990 | -0.054 | +0.635 | -0.177 | -0.029 | +0.042 | +0.102 | -0.221 | -0.183 | -0.146 | -0.049 | -0.176 | -0.055 | -0.034 | -0.082 | -0.100 | +0.029 | 4/16 | 0/16 |
| B2d wide-open switch | +0.990 | -0.054 | +0.635 | -0.177 | -0.029 | -0.009 | +0.102 | -0.221 | -0.178 | -0.146 | -0.026 | -0.164 | -0.055 | -0.039 | -0.067 | -0.105 | +0.029 | 3/16 | 5/16 |
| B2f1 target from room, menu | +0.990 | +0.034 | +0.635 | -0.177 | -0.010 | +0.068 | +0.056 | -0.241 | -0.148 | -0.140 | -0.072 | -0.226 | -0.023 | -0.060 | -0.048 | -0.154 | +0.030 | 5/16 | 7/16 |
| B2f2 target from room, exact | +0.990 | -0.040 | +0.575 | -0.187 | +0.107 | +0.052 | +0.082 | -0.253 | -0.154 | -0.166 | -0.079 | -0.195 | -0.031 | -0.053 | -0.056 | -0.137 | +0.028 | 5/16 | 6/16 |
| B2f3 target from room, half | +0.990 | +0.034 | +0.635 | -0.177 | -0.010 | +0.078 | +0.075 | -0.241 | -0.165 | -0.122 | -0.056 | -0.191 | -0.038 | -0.016 | -0.062 | -0.162 | +0.036 | 5/16 | 8/16 |
| B2f1 + B2e wide stop over 100 room | +0.990 | +0.034 | +0.635 | -0.177 | -0.010 | +0.068 | +0.019 | -0.241 | -0.142 | -0.102 | -0.043 | -0.173 | -0.038 | -0.059 | -0.054 | -0.160 | +0.034 | 5/16 | 9/16 |
| B2a + B2f1 | n/a | n/a | n/a | n/a | +0.175 | -0.388 | +0.149 | -0.247 | +0.066 | +0.050 | +0.200 | -0.348 | +0.212 | +0.009 | -0.114 | +0.064 | -0.014 | 8/12 | 8/16 |
| evaluation as stated (B2b1 band = target, B2d) | +0.990 | -0.173 | -0.240 | +0.245 | +0.065 | +0.022 | +0.112 | -0.182 | -0.179 | -0.145 | -0.026 | -0.170 | -0.068 | -0.044 | -0.076 | -0.119 | +0.001 | 5/16 | 9/16 |
| funded filters with the sealed bracket | n/a | n/a | n/a | n/a | -1.020 | -0.177 | +0.253 | -0.247 | -0.063 | -0.162 | +0.107 | -0.396 | -0.077 | +0.076 | -0.074 | -0.012 | -0.149 | 3/12 | 6/16 |
| funded as stated (B2a, B2b1, B2c4, B2f1) | n/a | n/a | n/a | n/a | -1.020 | -0.177 | +0.390 | -0.247 | +0.102 | -0.156 | +0.200 | -0.397 | +0.212 | +0.021 | -0.114 | +0.075 | -0.093 | 6/12 | 6/16 |
| funded as stated + B2e | n/a | n/a | n/a | n/a | -1.020 | -0.170 | +0.390 | -0.247 | +0.144 | -0.156 | +0.179 | -0.433 | +0.149 | +0.035 | -0.025 | +0.078 | -0.090 | 6/12 | 7/16 |
