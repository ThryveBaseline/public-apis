# Research plan after Baseline 0 (set by Chris, 2026-10-06)

> **Superseded on 2026-10-07 by `docs/research/FORWARD_POLICY.md`: forward only.** S3 runs forward unchanged. No further historical strategy research. Changes come as new versions judged only on later forward data. What follows is the record of the historical programme.

**Framing.** Baseline 0 is slightly negative, not dead: in-sample −0.037 R per trade (profit factor 0.94), untouched year −0.071 R (0.89), both after costs. The reconstructed rules are consistently close to, and slightly on the wrong side of, breakeven. The job is to find the missing +0.05 R to +0.15 R per trade: which piece of his framework carries edge, and which piece taxes it away.

**Data rule, binding from now on.**

| slice | dates | status |
|---|---|---|
| development | 2010-06-07 to 2025-10-05 | all candidate work, with walk-forward or nested validation inside it |
| Baseline 0 benchmark | 2025-10-06 to 2026-10-05 | inspected in `sealed/run1`; reported against, never used to choose anything |
| clean proof | bars after 2026-10-05, bought as they accrue, or a slice reserved before anyone looks at it | the only evidence that counts as unseen |

Once a tweak is chosen with knowledge of the 2025-26 year, that year is no longer unseen. Every candidate therefore shows three numbers: development (walk-forward), benchmark year (for comparison with run1 only), and clean proof when it exists.

**Research order.**

1. **Anatomize Baseline 0.** Continuation versus reversion, session and entry time, year, volatility regime, MAE and MFE, how often winners had room beyond 38 points, how often losers nearly reached the target first, how close winners came to the stop. Tool: `research/anatomy.py`, run on the GB10 against the sealed ledger; aggregates only are committed.
2. **Fixed versus normalized brackets.** ATR-scaled, session-range-scaled, opening-range-scaled, and price-normalized stops and targets. Hypothesis, not diagnosis: 25 and 38 points mean different things at 3,000 and at 25,000, and in an 80-point session versus a 400-point one.
3. **Separate the two strategies.** Continuation and reversion may carry different edge; one may be dragging the other.
4. **Conditional edge.** Volatility, trend, distance from fair value, opening-candle size and direction as conditions, pre-registered, not fitted.
5. **Signals from the broader research stack**, only if the raw structure still needs a filter or confirmation.

**Reversion as he states it (2026-10-07).** The corpus synthesis `docs/research/synthesis/reversion_rules.md` (53 verbatim quotes, each verified against the transcript lines) settles the class C question: on every prop account the reversion stop is a static 25 points, never a swing; what differs on funded accounts is the target (matched to the room to fair value: 38, 50, 75, 100 or the exact distance), the entry trigger (break of structure only), a move-away precondition (price must first move more than the target away from fair value), the wide-open 50/76 switch applying to reversions too, and a cadence of three or four attempts a session. The structure-stop, fair-value-target version is his live-account trade, which he says does not work on prop accounts. Baseline 0 matched his evaluation reversion except for the move-away gate and the wide-open switch. The pre-registered candidates are B2a to B2h and B2x in that file; the first composites to test are "evaluation reversion as stated" (B2b + B2d) and "funded reversion as stated" (B2a + B2b + B2c + B2f).

**Where it stands (2026-10-07).** B1 (`docs/reviews/run1_bracket_replay_read.md`): normalized brackets help continuation a little and reversion not at all. B2 (`docs/reviews/run1_b2_read.md`): his reversion rules remove most of the reversion drag but find no edge; continuation carries what edge there is, and held to 16:00 it is large in development, which may be the 2020-2026 bull market rather than the signal. B3 (`research/candidates.py`) answers both money questions on the sealed entries:

- each candidate stream (continuation only; continuation plus A+ reversion; each with the sealed bracket and with the walk-forward ATR bracket) scored with the frozen evaluator's own pass and payout functions under the four firm presets, with the frozen calculator's EV per evaluation and the frozen simulator's bootstrap from $500 to $5,000;
- continuation by direction, and held to 16:00 against the same-direction trade from the same minute on every day of its year: the excess is what the direction call adds beyond the market's drift.

Its gate: the sealed ledger scored its way reproduces the eight firm rows of `sealed/run1/report.md` character for character. Whatever survives B3 is then re-simulated on `research/engine.py`, the frozen rules with hooks that are inert at their defaults (proved on synthetic bars under 16 frozen configurations, and on the real bars by `research/engine_check.py`, which must rebuild `sealed/run1/trades.csv` byte for byte). The ledger replay changes exits but cannot add the entries the frozen engine skipped while a position was open; the re-simulation takes them.

**Rules that still hold.** `sealed/run1` and commit `f585bfb` are never modified. Candidates are B1, B2, ... with provenance (what changed, why, which weakness, what data invented it, what data tested it, result versus Baseline 0). Same-bar ambiguity stays resolved as a stop. Roll dates stay excluded. Costs stay in. Nothing is tuned on the benchmark year.

**Where it stands (2026-10-07, later).** B3's read (`docs/reviews/run1_b3_read.md`) is in: continuation's direction call beats the market's drift in 14 of 16 development years, the continuation streams pass a Topstep 50K evaluation about 29-30% of the time against 18-20% for the sealed ledger, and the first-payout EV net of every fee sits near zero on TopstepX (the best, S4 at 0.95, +$8 per evaluation in development). Step 4 (`research/run1_conditions.md`): of nine pre-registered conditions only H3 passes (continuation after a large opening candle), and its benchmark year points the other way. Four tools follow, each reviewed independently before it touches real data:

- **B4** (`research/lifetime.py`): what a funded account is worth over its life, with every payout under Topstep's Express Funded rules and every fee, at horizons of 60, 120 and 250 days and under two payout policies.
- **The trend exit** (`research/trend_exit.py`, pre-registered in `docs/research/preregistration_trend_exit.md`): a stop with no target for continuation, tested once against S3 on the same entries.
- **H3 through firm scoring** (`research/h3_filter.py`), as its registration requires.
- **B5** (`research/b5_paths.py`, pre-registered in `docs/research/preregistration_b5_bootstrap.md` before B4 had run): the $2,000 bootstrap on replayed market paths, every account trading the same days, with a fixed reading rule for what goes on to a forward test.

Every candidate here is chosen on development data. Only bars after 2026-10-05 can confirm any of them.
