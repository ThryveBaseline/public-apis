# Pre-registration: a trend exit for continuation

Registered 2026-10-07, before the tool exists and before any of these brackets has been replayed on any data. The commit that adds this file is the registration; any later change to it is a new registration and must say so.

## Why

B3 (`docs/reviews/run1_b3_read.md`) found that continuation's direction call carries information beyond the market's drift. Held to 16:00, continuation entries beat the same-direction trade from the same minute by +0.035 daily ATR per trade in development, in 14 of 16 years, longs and shorts alike. The brackets keep little of it: +0.013 R per trade for the sealed 25/38 and about +0.04 R for the walk-forward ATR bracket with a target (S3). The hypothesis is that a protective stop with no target, held to the firms' end-of-day flat, keeps more of the move.

## What has been seen

Already reported, on development and benchmark:
- ATR-scaled stops with targets at 1.0, 1.52 and 2.0 times the stop, k from 0.03 to 0.70 (B1, B2, B3);
- the hold to 16:00 with no stop (B1);
- the hold-minus-drift by year (B3).

Not computed on any data: an ATR-scaled stop with no target. The choice of this family was made after seeing those results; that is why its test is paired against S3 on the same entries and years, and why only data after 2026-10-05 can confirm it.

## Population, bracket and outcome

- **Entries.** The sealed continuation entries (every grade), roll dates excluded, restricted to the entries the B2 replay covers.
- **Bracket.** Stop = k × the previous Globex session's daily ATR (`research.anatomy.daily_context`), tick-rounded, at least 2 points, as `research/bracket_replay.py`'s ATR family. No target. Flat at the close of the last bar before 16:00, less slippage. Same-bar ambiguity is not possible without a target. Costs as the replay: 0.25 point of slippage on the stop and on the flat, $5 per round trip.
- **k.** One of {0.2, 0.3, 0.4, 0.5, 0.7, 1.0}.
- **Outcome.** R per trade on the trade's own stop, (points × 20 − 5) / (stop × 20). Under the firms' fixed risk per trade this is the dollar outcome per unit of risk, so it compares across stop sizes.

## Choosing k

The pooled walk-forward of B1 and B3, within this family only:
- For each development year Y from the fourth development year on (2013), k is the value with the best pooled, trade-weighted expectancy over all earlier development years.
- Before 2013 no trend trade is taken.
- Benchmark trades take the k chosen on all development years.

S3's chain (the ATR family with targets, in `research/run1_b3.md`) is the comparison, on the same entries and years.

## The test

- **Statistic.** The paired difference per entry, trend-exit R minus S3's R, each with its own chain's choice for the entry's year. It is averaged over development entries from 2013 to the cut, with a standard error clustered by day, and a one-sided normal p-value (trend exit better).
- **Pass.** p < 0.05, and the mean difference positive in at least 60% of the chain's development years (2013 to 2025).
- **Single hypothesis.** One test, no multiplicity adjustment. Any other k set, stop base, exit time or management rule is a new registration.

## Reported beside, not tested

- The chain's choice per year.
- The trend exit's development and benchmark R per trade, by direction, against S1 (sealed bracket) and S3.
- Its share of stops and of 16:00 exits.
- If it passes, the stream "S5 continuation, walk-forward trend exit" and "S6 S5 plus reversion A+, sealed bracket" go through:
  - the B3 firm scoring: summary, TopstepX size sensitivity, whole micro contracts;
  - B4's lifetime EV, at the presets, sizes and horizons B4 uses.

  If it fails, they are reported once for the record and dropped.
- The benchmark year is reported beside and never used.
