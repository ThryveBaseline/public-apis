# Pre-registration: conditional edge (research step 4)

Registered 2026-10-07, before the tool exists and before any of these splits has been computed on any data. At the time of writing, B3 (`research/candidates.py`) has not been run on real data either; nothing below was chosen after seeing a result for these conditions. The commit that adds this file is the registration; any later change to it is a new registration and must say so.

## What has already been seen, and is therefore not tested

The sealed ledger has been split, on development and benchmark, by setup, direction, grade, entry time, year, exit reason, bracket geometry, and volatility regime (daily ATR in points and as a share of price, terciles; `research/run1_anatomy.md`). B1 and B2 looked at bracket families, room to fair value against the target (reversion), the wide-open opening candle (25-point body), move-away gates and attempt caps. Volatility regime is reported descriptively below but not tested, because its pattern is known (development continuation +0.027 / +0.031 / +0.003 R in the low / mid / high terciles). Nothing else in this file has been computed.

## Population and outcome

- Entries: the sealed ledger (`sealed/run1/trades.csv`), roll dates excluded as in the sealed report, restricted to entries the B2 replay file covers (`research/private/run1_bracket_replay_b2.csv`).
- Primary outcome: R of the sealed bracket replayed, flat at 16:00 (`ledger_bracket`), the outcome a trader of these entries would get under the firms' end-of-day rule.
- Secondary outcome, continuation only, reported and not tested: the hold to 16:00 minus the same-direction drift, per daily ATR (`research/candidates.py`, `hold_drift`).
- Development: New York days up to 2025-10-05. Benchmark: 2025-10-06 onward, reported beside every number and never used for any threshold, test or decision.

## Context, all known before the entry

Day D is the entry's New York date, which equals its Globex session (18:00 on D-1 to 17:00 on D). From the bars:

- `atr`: daily ATR(14) of complete Globex sessions up to D-1 (`research.anatomy.daily_context`).
- `prev_close`, `prev_high`, `prev_low`: the close, high and low of the Globex session ending on D-1.
- `open`: the open of D's 09:30 bar. `body`: the absolute body of D's 09:30 bar, known at 09:31 (no entry precedes 09:31).
- `gap`: `open - prev_close` (the overnight move, from the 17:00 close to the 09:30 open).
- `overnight_range`: high minus low of D's session bars from its 18:00 open through the 09:29 bar.
- `trend20`: the sign of `prev_close` minus the close of the session 20 sessions earlier.
- From the ledger: `direction` (+1 long, -1 short) and `distance_from_fv` at the signal bar.

Trades without a defined value (the first 20 sessions, a session without a 09:30 bar, a zero gap or flat trend) sit out of that test only.

## Thresholds

Sign conditions use no threshold. Continuous conditions split at a walk-forward median: for a development trade in year Y, the median over all earlier development years (for day-level quantities, every trading day with a 09:30 bar and a defined `atr`; for `distance_from_fv`, the entries of the tested population: continuation of every grade for H6, reversion A+ for H7); for a benchmark trade, the median over all development years. Trades in the first development year sit out of threshold tests.

## Hypotheses (one-sided; the favoured side is named in advance)

Continuation (every grade), outcome `ledger_bracket` R:

| id | condition | favoured side |
|---|---|---|
| H1 | trend | `direction == trend20` (with the 20-session trend) |
| H2 | overnight move | `direction == sign(gap)` (continuing the overnight move) |
| H3 | opening candle | `body / atr` at or above its walk-forward median |
| H4 | overnight compression | `overnight_range / atr` at or below its walk-forward median |
| H5 | open outside the prior session | longs: `open > prev_high`; shorts: `open < prev_low` |
| H6 | extension at the signal | `abs(distance_from_fv) / atr` at or below its walk-forward median (less already spent) |

Reversion, grade A+ only (his funded trigger), outcome `ledger_bracket` R:

| id | condition | favoured side |
|---|---|---|
| H7 | room to fair value | `abs(distance_from_fv) / atr` at or above its walk-forward median |
| H8 | trend | `direction == trend20` |
| H9 | gap fill | `direction == -sign(gap)` (trading back across the overnight move) |

Power, stated in advance: about 3,280 development continuation entries give a standard error of roughly 0.04 R on a half-against-half difference; about 780 reversion A+ entries give roughly 0.08 R, so H7 to H9 can only detect large effects.

## Test and decision rule

- Statistic: the development difference in mean R, favoured minus other side, pooled over trades. Its standard error is the root sum of the two sides' squared standard errors, each clustered by day. One-sided p-value from the normal distribution.
- Multiplicity: Holm's step-down procedure across all nine hypotheses at a family-wise 0.05.
- Consistency: the share of development years in which the favoured side's mean R exceeds the other side's, counting only years with at least 10 trades on each side.
- A condition **passes** only if it is Holm-significant and its difference is positive in at least 60% of the eligible development years.
- A passing condition becomes a candidate filter and goes, with provenance, through the B3 firm scoring (on the favoured side) and the research engine's re-simulation. A failing condition is reported and dropped, and is not re-cut into another threshold, window or combination on these data.
- No combination of conditions is tested here. Any combination is a new registration.

## Reported beside the tests

For every hypothesis: trades and mean R on each side, in development and in the benchmark; the difference, its standard error, raw and Holm p-values, and year consistency; and for continuation, the secondary outcome on each side. Volatility terciles are shown descriptively, flagged as seen. Aggregates only are committed; the per-trade conditions stay private.

## Clarifications, 2026-10-07, before any run on real data

Prompted by the independent review of the tool on synthetic bars (no real data has been touched). They change how three context values are computed around contract switches and fix two readings the text left open; nothing else changes.

1. **Contract switches.** The continuous series switches contract at 00:00 UTC, the evening of the excluded roll date, so the next Globex session holds bars of two contracts and is not excluded. Every cross-session comparison is therefore made in the contract of D's 09:30 bar: `prev_close`, `prev_high` and `prev_low` come from the previous session's bars in that contract (undefined if it has none, which is the switch session itself), and `overnight_range` is undefined when D's bars before 09:30 are not all in that contract. On the switch session `gap`, the H5 comparison and `overnight_range` are thus undefined, and its trades sit out of H2, H4, H5 and H9 under the undefined-value rule.
2. **`trend20` without the switch jump.** `trend20` is the sign of the price change over the 20 sessions D-20 to D-1, that is from the close of session D-21 to the close of session D-1 (the reading the text left open), summed bar by bar within each contract: at a bar where the contract changes, only that bar's own open-to-close move counts, so the calendar spread never enters. No price series is back-adjusted. The first 21 sessions have no `trend20`.
3. **`atr` stays as registered** (`research.anatomy.daily_context`, shared with B1-B3). Its true range on the switch session includes the spread, so the ATR of the following 14 sessions is slightly inflated (about the spread over 14); this is accepted and stated, not corrected.
4. **Pinned.** The tool runs only on this file (sha256 checked against the value pinned in the code) and only at the registered cut (development through 2025-10-05, benchmark from 2025-10-06), and prints both. Synthetic tests may use another cut through an explicit flag that stamps the report as not the registered run.
5. **Reported beside, not tested.** For each hypothesis, the number of development days on which both sides trade (the registered standard error ignores the covariance between sides on such days), and the benchmark difference's standard error. The volatility table uses the replayed bracket R flat at 16:00 on replayed entries, with terciles from sessions that have a 09:30 bar, so its numbers differ slightly from the anatomy's.
6. **Alignment refused, not assumed.** An entry whose Globex session is not its New York date, or that enters before 09:31, stops the tool.
