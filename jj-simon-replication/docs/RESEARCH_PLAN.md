# Research plan after Baseline 0 (set by Chris, 2026-10-06)

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

**Rules that still hold.** `sealed/run1` and commit `f585bfb` are never modified. Candidates are B1, B2, ... with provenance (what changed, why, which weakness, what data invented it, what data tested it, result versus Baseline 0). Same-bar ambiguity stays resolved as a stop. Roll dates stay excluded. Costs stay in. Nothing is tuned on the benchmark year.
