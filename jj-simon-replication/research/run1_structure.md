# Structure versus edge: B4's lifetime EV with the development edge removed

Data hygiene: 121 trades on 66 contract-roll dates excluded, as in the sealed report. Provenance: the trades, the bar file and the report given (sealed/run1/report.md) have the manifest's sha256. Reproduction gate: the sealed ledger scored here reproduces all 8 firm rows of sealed/run1/report.md character for character. Replay join: checked on 7656 stop or target exits before 16:00 (R and exit time); every variant read is present for every replayed entry.

Development: New York days through 2025-10-05; benchmark from 2025-10-06, moved the same way and shown beside. Two nulls remove each stream's development mean while keeping every entry and its timing. Shift: every R moves by the development mean (the shift column). Re-label: trades on the side that gives the stream its mean take a middle development outcome of the other side (its lower median), in a seeded random order, until the development mean is as close to zero as one more trade can bring it (the share column, averaged over orders), so outcome sizes stay the stream's own; it is averaged over 10 orders, with the standard deviation across them beside it, because one order moves its EV by about $12-21. All copies go through B4's lifetime_rows (research/lifetime.py; its first-payout gate passed on every row), on TopstepX only: at the sealed sizing a stop-out sits 0.02 R from the frozen preset's soft daily limit, so shifting R by a few hundredths would cross it and measure that artifact. EV with no edge is what the same pattern of trades earns with a zero development mean: a funded account's loss is capped by the drawdown while half of every upswing can be withdrawn. The edge's part is the difference, under each null; where the two nulls disagree by more than the re-label null's spread, the split depends on the null. Descriptive only; nothing is chosen here.

## topstep_50k_x at 1.00 of the budget

| stream | shift (R per trade) | re-labelled share | period | policy | H | P(pass): stream / shift / re-label | EV per evaluation | EV with no edge: shift / re-label (sd across orders) | the edge's part: shift / re-label |
|---|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 60 | 18.5% / 25.2% / 22.5% | +30 | +115 / +91 (9) | -85 / -61 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 120 | 18.5% / 25.2% / 22.5% | +36 | +138 / +110 (13) | -102 / -74 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 250 | 18.5% / 25.2% / 22.5% | +36 | +138 / +111 (13) | -103 / -75 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 60 | 18.5% / 25.2% / 22.5% | +25 | +115 / +89 (8) | -90 / -65 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 120 | 18.5% / 25.2% / 22.5% | +38 | +156 / +123 (12) | -118 / -85 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 250 | 18.5% / 25.2% / 22.5% | +41 | +161 / +129 (15) | -121 / -89 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 60 | 8.4% / 12.2% / 10.5% | -43 | -11 / -12 (8) | -32 / -30 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 120 | 8.4% / 12.2% / 10.5% | -43 | -4 / -10 (9) | -39 / -33 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 250 | 8.4% / 12.2% / 10.5% | -43 | -4 / -10 (9) | -39 / -33 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 60 | 8.4% / 12.2% / 10.5% | -43 | -11 / -12 (8) | -32 / -31 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 120 | 8.4% / 12.2% / 10.5% | -43 | -4 / -10 (9) | -38 / -33 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 250 | 8.4% / 12.2% / 10.5% | -43 | -4 / -10 (9) | -38 / -33 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 60 | 28.2% / 25.3% / 26.9% | +112 | +83 / +91 (5) | +29 / +21 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 120 | 28.2% / 25.3% / 26.9% | +133 | +96 / +107 (7) | +36 / +25 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 250 | 28.2% / 25.3% / 26.9% | +133 | +96 / +107 (7) | +37 / +25 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 60 | 28.2% / 25.3% / 26.9% | +114 | +83 / +90 (6) | +30 / +23 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 120 | 28.2% / 25.3% / 26.9% | +149 | +108 / +120 (9) | +41 / +29 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 250 | 28.2% / 25.3% / 26.9% | +153 | +112 / +124 (9) | +41 / +30 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 60 | 26.5% / 24.3% / 25.3% | +232 | +178 / +177 (29) | +54 / +55 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 120 | 26.5% / 24.3% / 25.3% | +299 | +231 / +211 (49) | +68 / +88 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 250 | 26.5% / 24.3% / 25.3% | +299 | +231 / +211 (49) | +68 / +88 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 60 | 26.5% / 24.3% / 25.3% | +274 | +208 / +216 (33) | +67 / +59 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 120 | 26.5% / 24.3% / 25.3% | +375 | +279 / +268 (64) | +97 / +107 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 250 | 26.5% / 24.3% / 25.3% | +375 | +279 / +268 (64) | +97 / +107 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 60 | 25.7% / 25.6% / 25.7% | +90 | +89 / +89 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 120 | 25.7% / 25.6% / 25.7% | +102 | +100 / +100 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 250 | 25.7% / 25.6% / 25.7% | +102 | +100 / +100 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 60 | 25.7% / 25.6% / 25.7% | +92 | +91 / +90 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 120 | 25.7% / 25.6% / 25.7% | +113 | +112 / +112 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 250 | 25.7% / 25.6% / 25.7% | +117 | +116 / +116 (1) | +1 / +1 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 60 | 17.2% / 17.2% / 17.2% | +70 | +70 / +70 (0) | +0 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 120 | 17.2% / 17.2% / 17.2% | +85 | +82 / +85 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 250 | 17.2% / 17.2% / 17.2% | +85 | +82 / +85 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 60 | 17.2% / 17.2% / 17.2% | +70 | +70 / +70 (0) | +0 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 120 | 17.2% / 17.2% / 17.2% | +90 | +87 / +90 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 250 | 17.2% / 17.2% / 17.2% | +90 | +87 / +90 (0) | +3 / +0 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 60 | 28.9% / 25.5% / 24.8% | +148 | +75 / +74 (6) | +74 / +74 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 120 | 28.9% / 25.5% / 24.8% | +206 | +104 / +106 (10) | +102 / +100 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 250 | 28.9% / 25.5% / 24.8% | +228 | +107 / +117 (15) | +121 / +112 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 60 | 28.9% / 25.5% / 24.8% | +156 | +79 / +76 (7) | +77 / +80 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 120 | 28.9% / 25.5% / 24.8% | +224 | +118 / +117 (10) | +106 / +107 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 250 | 28.9% / 25.5% / 24.8% | +258 | +122 / +135 (16) | +136 / +124 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 60 | 22.8% / 22.2% / 19.7% | +66 | +34 / +28 (10) | +32 / +38 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 120 | 22.8% / 22.2% / 19.7% | +66 | +34 / +28 (10) | +32 / +38 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 250 | 22.8% / 22.2% / 19.7% | +66 | +34 / +28 (10) | +32 / +38 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 60 | 22.8% / 22.2% / 19.7% | +42 | +11 / +7 (13) | +31 / +35 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 120 | 22.8% / 22.2% / 19.7% | +42 | +11 / +7 (13) | +31 / +35 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 250 | 22.8% / 22.2% / 19.7% | +42 | +11 / +7 (13) | +31 / +35 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 60 | 29.4% / 25.5% / 24.9% | +157 | +75 / +73 (8) | +82 / +84 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 120 | 29.4% / 25.5% / 24.9% | +206 | +91 / +92 (12) | +115 / +114 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 250 | 29.4% / 25.5% / 24.9% | +211 | +92 / +93 (12) | +119 / +117 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 60 | 29.4% / 25.5% / 24.9% | +164 | +81 / +75 (9) | +83 / +89 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 120 | 29.4% / 25.5% / 24.9% | +231 | +114 / +106 (12) | +116 / +125 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 250 | 29.4% / 25.5% / 24.9% | +236 | +118 / +108 (13) | +118 / +128 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 60 | 27.5% / 26.2% / 23.3% | +143 | +97 / +66 (21) | +46 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 120 | 27.5% / 26.2% / 23.3% | +143 | +97 / +67 (21) | +46 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 250 | 27.5% / 26.2% / 23.3% | +143 | +97 / +67 (21) | +46 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 60 | 27.5% / 26.2% / 23.3% | +225 | +129 / +90 (29) | +96 / +134 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 120 | 27.5% / 26.2% / 23.3% | +238 | +129 / +92 (30) | +109 / +146 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 250 | 27.5% / 26.2% / 23.3% | +238 | +129 / +92 (30) | +109 / +146 |

## topstep_50k_x at 0.95 of the budget

| stream | shift (R per trade) | re-labelled share | period | policy | H | P(pass): stream / shift / re-label | EV per evaluation | EV with no edge: shift / re-label (sd across orders) | the edge's part: shift / re-label |
|---|---|---|---|---|---|---|---|---|---|
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 60 | 19.6% / 24.6% / 24.0% | +37 | +104 / +104 (11) | -68 / -68 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 120 | 19.6% / 24.6% / 24.0% | +43 | +127 / +125 (16) | -84 / -82 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | ask | 250 | 19.6% / 24.6% / 24.0% | +43 | +127 / +126 (16) | -85 / -83 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 60 | 19.6% / 24.6% / 24.0% | +32 | +103 / +104 (10) | -72 / -72 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 120 | 19.6% / 24.6% / 24.0% | +45 | +143 / +141 (15) | -98 / -95 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | development | wait | 250 | 19.6% / 24.6% / 24.0% | +49 | +149 / +149 (17) | -100 / -99 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 60 | 9.3% / 12.2% / 12.2% | -39 | -11 / +3 (9) | -28 / -42 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 120 | 9.3% / 12.2% / 12.2% | -39 | -4 / +7 (10) | -34 / -45 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | ask | 250 | 9.3% / 12.2% / 12.2% | -39 | -4 / +7 (10) | -34 / -45 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 60 | 9.3% / 12.2% / 12.2% | -39 | -11 / +3 (9) | -28 / -42 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 120 | 9.3% / 12.2% / 12.2% | -39 | -5 / +7 (10) | -34 / -46 |
| S0r sealed brackets, flat 16:00 | -0.041 | 2.8% | benchmark | wait | 250 | 9.3% / 12.2% / 12.2% | -39 | -5 / +7 (10) | -34 / -46 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 60 | 30.2% / 28.9% / 28.8% | +125 | +99 / +102 (6) | +25 / +23 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 120 | 30.2% / 28.9% / 28.8% | +148 | +116 / +121 (8) | +32 / +28 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | ask | 250 | 30.2% / 28.9% / 28.8% | +148 | +116 / +121 (8) | +32 / +28 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 60 | 30.2% / 28.9% / 28.8% | +135 | +104 / +108 (7) | +31 / +27 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 120 | 30.2% / 28.9% / 28.8% | +177 | +136 / +142 (11) | +41 / +35 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | development | wait | 250 | 30.2% / 28.9% / 28.8% | +182 | +141 / +147 (11) | +41 / +35 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 60 | 38.9% / 35.5% / 36.2% | +348 | +266 / +265 (45) | +82 / +84 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 120 | 38.9% / 35.5% / 36.2% | +441 | +339 / +311 (71) | +102 / +130 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | ask | 250 | 38.9% / 35.5% / 36.2% | +441 | +339 / +311 (71) | +102 / +130 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 60 | 38.9% / 35.5% / 36.2% | +454 | +319 / +350 (51) | +135 / +104 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 120 | 38.9% / 35.5% / 36.2% | +693 | +425 / +473 (111) | +267 / +220 |
| S1 continuation only, sealed bracket | +0.013 | 1.4% | benchmark | wait | 250 | 38.9% / 35.5% / 36.2% | +707 | +425 / +476 (114) | +281 / +231 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 60 | 27.1% / 27.0% / 27.0% | +97 | +96 / +95 (1) | +1 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 120 | 27.1% / 27.0% / 27.0% | +108 | +107 / +106 (1) | +1 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | ask | 250 | 27.1% / 27.0% / 27.0% | +108 | +107 / +107 (1) | +1 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 60 | 27.1% / 27.0% / 27.0% | +103 | +101 / +101 (1) | +2 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 120 | 27.1% / 27.0% / 27.0% | +126 | +124 / +124 (1) | +2 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | development | wait | 250 | 27.1% / 27.0% / 27.0% | +130 | +128 / +129 (1) | +2 / +2 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 60 | 19.2% / 19.2% / 19.2% | +91 | +91 / +91 (0) | +0 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 120 | 19.2% / 19.2% / 19.2% | +107 | +104 / +107 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | ask | 250 | 19.2% / 19.2% / 19.2% | +107 | +104 / +107 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 60 | 19.2% / 19.2% / 19.2% | +90 | +90 / +90 (0) | +0 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 120 | 19.2% / 19.2% / 19.2% | +113 | +109 / +113 (0) | +3 / +0 |
| S2 continuation + A+ reversion, sealed bracket | +0.001 | 0.1% | benchmark | wait | 250 | 19.2% / 19.2% / 19.2% | +113 | +109 / +113 (0) | +3 / +0 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 60 | 32.1% / 27.0% / 27.5% | +162 | +76 / +82 (7) | +86 / +80 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 120 | 32.1% / 27.0% / 27.5% | +223 | +111 / +115 (11) | +112 / +107 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | ask | 250 | 32.1% / 27.0% / 27.5% | +246 | +116 / +127 (15) | +130 / +119 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 60 | 32.1% / 27.0% / 27.5% | +176 | +79 / +86 (8) | +97 / +90 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 120 | 32.1% / 27.0% / 27.5% | +261 | +122 / +136 (12) | +139 / +125 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | development | wait | 250 | 32.1% / 27.0% / 27.5% | +293 | +128 / +154 (15) | +165 / +139 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 60 | 28.5% / 23.2% / 24.9% | +85 | +36 / +43 (15) | +49 / +42 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 120 | 28.5% / 23.2% / 24.9% | +85 | +36 / +43 (15) | +49 / +42 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | ask | 250 | 28.5% / 23.2% / 24.9% | +85 | +36 / +43 (15) | +49 / +42 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 60 | 28.5% / 23.2% / 24.9% | +53 | +7 / +14 (17) | +45 / +39 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 120 | 28.5% / 23.2% / 24.9% | +53 | +7 / +14 (17) | +45 / +39 |
| S3 continuation only, walk-forward ATR bracket | +0.042 | 4.7% | benchmark | wait | 250 | 28.5% / 23.2% / 24.9% | +53 | +7 / +14 (17) | +45 / +39 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 60 | 33.0% / 27.2% / 27.9% | +179 | +78 / +85 (8) | +101 / +94 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 120 | 33.0% / 27.2% / 27.9% | +231 | +98 / +106 (12) | +133 / +125 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | ask | 250 | 33.0% / 27.2% / 27.9% | +236 | +99 / +106 (13) | +136 / +129 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 60 | 33.0% / 27.2% / 27.9% | +191 | +82 / +88 (9) | +108 / +103 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 120 | 33.0% / 27.2% / 27.9% | +267 | +120 / +124 (13) | +147 / +143 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | development | wait | 250 | 33.0% / 27.2% / 27.9% | +274 | +124 / +126 (14) | +149 / +148 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 60 | 30.5% / 26.5% / 25.7% | +147 | +96 / +70 (22) | +51 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 120 | 30.5% / 26.5% / 25.7% | +147 | +96 / +70 (22) | +51 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | ask | 250 | 30.5% / 26.5% / 25.7% | +147 | +96 / +70 (22) | +51 / +77 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 60 | 30.5% / 26.5% / 25.7% | +249 | +123 / +100 (32) | +126 / +149 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 120 | 30.5% / 26.5% / 25.7% | +268 | +123 / +102 (33) | +145 / +166 |
| S4 S3 + A+ reversion, sealed bracket | +0.044 | 4.7% | benchmark | wait | 250 | 30.5% / 26.5% / 25.7% | +268 | +123 / +102 (33) | +145 / +166 |
