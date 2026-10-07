# B2: reversion rules as he states them, read (Claude, cloud session, 2026-10-07)

Sources: `research/run1_b2.md` (sha256 3dd81d2e…) and `research/run1_bracket_replay_b2.md` (sha256 0fcbc823…), run on the GB10 at d0120a8 after two independent reviews and a verification against an independently written engine-like reference. Development years select; the benchmark year (the sealed out-of-sample year, already inspected) is shown beside and never used to choose.

**Gates, all passed.** Replay reproduction 100.00% / 0.0000 on 7,656 stop or target exits before 16:00. The sequential pass (one position at a time, three-loss stop) keeps all 8,689 ledger trades; the test suite shows it turns the frozen engine's no-stop ledger into its with-stop ledger exactly. Join check: every ledger entry is covered once per variant, and the replayed sealed bracket equals the ledger in R and exit time on all 7,656 checked exits.

## 1. His reversion rules, one at a time (sealed brackets, ledger R)

| filter on reversion entries | development: trades, expectancy R | benchmark |
|---|---|---|
| none (sealed) | 4,150, −0.082 | 986, −0.122 |
| A+ only (his funded trigger, B2a) | 777, −0.048 | 212, −0.006 |
| move-away gate since the last return to fair (B2b1) | 4,114, −0.082 | 986, −0.122 |
| at most 4 / 3 attempts a session (B2c) | 3,740, −0.084 / 3,408, −0.084 | 754, −0.134 / 639, −0.169 |
| room at least the whole target (B2h) | 3,459, −0.083 | 911, −0.109 |
| entries before 09:45 (ledger hypothesis, not his rule) | 324, +0.011 | 105, −0.177 |
| entries before 10:00 (ledger hypothesis) | 1,265, −0.049 | 356, −0.132 |

* **The move-away gate and the cadence cap do not bind.** 99% of the sealed reversion entries already pass the gate (the engine's room rule nearly implies it), and capping attempts removes trades of average quality.
* **A+ only is the one rule that matters.** It removes 81% of reversion trades, the A-grade displacement entries he says he reserves for evaluations, and the remainder is near zero rather than positive.

## 2. Targets matched to the room do not rescue reversion

Replayed, flat at 16:00, reversion entries only:

| bracket | development | benchmark |
|---|---|---|
| sealed 25/38 | −0.084 | −0.123 |
| menu 38/50/75/100 by room (B2f1) | −0.060 | −0.180 |
| exact distance to fair value (B2f2) | −0.061 | — |
| 50/76 on wide-open days (B2d) | −0.086 | −0.113 |
| widest scaled stop, 0.5 × daily ATR, RR 2 | −0.064 | −0.048 |
| hold to 16:00, no stop or target (control) | −0.247 | −0.311 |

Within A+ reversions the room target looks better in development (+0.026 against −0.057 with the sealed bracket) and much worse in the benchmark (−0.153 against −0.008). That is not evidence either way; it is not adopted.

**The hold-to-close control is the important line.** Held to the close, reversion entries lose in six of the eight development years from 2018 to 2025 and in the benchmark year: on average, the move away from fair value continues rather than reverts by the close. No bracket in the grid turns that into an edge.

## 3. Composites

| rule set (replayed, flat 16:00) | development: trades, R/trade, total R | benchmark |
|---|---|---|
| sealed bracket (control) | 7,397, −0.041, −303 | 1,250, −0.072, −90 |
| evaluation as stated (gate with band = target, 50/76 on wide-open days) | 6,999, −0.040, −277 | 988, −0.057, −57 |
| funded filters (A+, gate, 4 attempts) with the sealed bracket | 4,022, −0.000, −1 | 476, +0.060, +29 |
| funded as stated (the same with targets from the room) | 3,957, +0.015, +60 | 448, +0.007, +3 |

Continuation is untouched in every composite (+0.013 R a trade in development, +0.111 in the benchmark), so every difference is the reversion leg. The funded composites beat the control in all four development years from 2022 to 2025.

## 4. Where the edge is: continuation

| continuation, replayed | development | development years > 0 | 2022-2025 | benchmark |
|---|---|---|---|---|
| sealed bracket | +0.013 | 10/16 | +0.105, −0.003, −0.002, +0.032 | +0.112 |
| 0.4 × daily ATR stop, RR 2 | +0.052 | — | — | — |
| 0.5 × daily ATR stop, RR 2 | +0.048 | 13/16 | +0.107, +0.091, +0.036, +0.106 | +0.058 |
| 0.7 × daily ATR stop, RR 1.52 | +0.035 | 13/16 | +0.062, +0.055, +0.045, +0.082 | +0.071 |
| hold to 16:00, R in 25-point units (control) | +0.224 | 12/16 | +0.343, +0.380, +0.169, +0.597 | +1.033 |

The out-of-year chain on continuation, now selecting on pooled prior years, picks the 0.4-0.5 × ATR brackets and scores +0.047 against +0.014 for the sealed bracket. Held to the close, continuation entries are positive in every development year from 2020 on. The first five minutes' direction carries information about the rest of the day that the 25/38 bracket gives up.

Two cautions before this counts as an edge. **Beta:** 2020-2025 was a strong bull market; if the hold-to-close gain sits in long trades only, it is drift, not signal. The next tool splits it by direction. **Risk units:** hold-to-close has no stop, so its R is not a risk-adjusted number, and a prop account's drawdown is enforced on the way, not only at the close. Only stop-protected versions can be evaluated under firm rules.

## What this settles, and what is next

* **Reversion, as he trades it on prop accounts, does not carry an edge in this data.** His stated rules reduce the loss from the reversion leg to about zero, mainly by excluding A-grade entries; nothing in them makes it profitable.
* **Continuation carries the edge.** It is modest per trade with the sealed bracket and two to four times larger with a wide, volatility-scaled bracket, consistently across years.
* **Next (B3):** (1) split continuation results by direction to rule out bull-market drift; (2) evaluate candidate streams under the frozen firm rules with the frozen evaluator's walk-forward pass and payout probabilities: sealed; continuation only; continuation with A+ reversion; continuation with the walk-forward-chosen wide bracket, with and without A+ reversion; (3) full re-simulation of whichever survives, on a research engine that leaves `fpt/` untouched.
