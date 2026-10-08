# Forward tournament, version 1: 28 versions of JJ's rules

Decided by Chris on 2026-10-08, under `FORWARD_POLICY.md`. Frozen by the commit that adds this file, before any variant had a forward trade. It runs beside S3, S4 and JJ's full rules (B0). It changes none of them.

**Why.** At a few trades a day per stream, forward learning is slow. Running many frozen versions of JJ's rules at once gives tens of forward trades a night, on the same bars and gate, at no extra data cost.

**What runs.** `T00` is JJ's rules as frozen (Baseline 0). Each other version changes one dial, set to an alternative documented in the public record: JJ's own statements, fxreplay's codification, or a choice the engine already makes. None was picked on historical performance, and the tournament reports none.

Every version trades one contract. R is the same as at any size, and no trade is skipped because a wide stop rounds to zero contracts. The separate B0 stream keeps JJ's risk sizing exactly.

| version | what changes |
|---|---|
| T00 | JJ's rules as frozen (one contract per trade) |
| T01 | continuation window to 09:45 (fxreplay: 10-15 minutes) |
| T02 | skip the first 3 minutes (fxreplay's filtered test) |
| T03 | trading window ends 10:30 |
| T04 | trading window ends 12:00 |
| T05 | reversions only until 10:00 (fxreplay's filtered test) |
| T06 | adds the 14:00-15:00 afternoon session (JJ's earlier videos) |
| T07 | fair value fixed at the open (no rolling consolidation) |
| T08 | reversion only after touching the fair-value band |
| T09 | reversion only 20+ points from fair value |
| T10 | continuation direction from the side of fair value |
| T11 | fxreplay's wick displacement test |
| T12 | 3/3 swing pivots (fxreplay-style structure) |
| T13 | no continuation stall cut-off |
| T14 | grade A+ only, both setups |
| T15 | continuation only |
| T16 | reversion only |
| T17 | reversion A+ only, continuation all grades (S4's entries) |
| T18 | fxreplay's ATR stop ladder |
| T19 | target 2.0 x stop |
| T20 | target 1.0 x stop |
| T21 | 50-point stop (JJ's wide stop) |
| T22 | continuation bracket 0.4 x daily ATR, 2R (S3's) |
| T23 | flat at 16:00 |
| T24 | flat at the trading window's end (11:00) |
| T25 | no three-loss session stop |
| T26 | two-loss session stop |
| T27 | stop for the day after -2 R |

**How it runs.** `research/tournament.py` reuses the forward runner's checks unchanged:
- the forward file's form and continuity;
- the gap rules and holiday calendar;
- the session, completeness and roll rules;
- the ledger that never rewrites a scored date.

Gaps a person accepted for the v1 test are accepted here too.

A one-time `init` pins the code and the variants, and records no performance. Its only check is that the nightly tail rerun gives the same trades as a run started 60 days earlier. Any change to code or variants refuses, and becomes tournament version 2.

**Promotion rule, fixed now.** A version is promotable when both hold:
- it has at least 50 forward trades;
- the lower bound of its forward mean R per trade is above zero.

The lower bound is the mean less 2.91 day-clustered standard errors: one-sided at 5% divided by 28, because 28 versions are tried at once.

- **What promotable means.** The version is a candidate for a new frozen version, which Chris decides. That new version is judged only on forward data after it.
- **What it never means.** Nothing is dropped, ranked or changed on history. Versions that look bad forward simply keep running and keep being recorded.

**Reading it.** Many versions share most of their trades with T00, so their results move together. The forward record of each one is what counts. A single good week is not evidence; the bound is built to say so.
