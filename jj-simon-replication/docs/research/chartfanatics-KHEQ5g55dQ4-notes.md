# Chart Fanatics episode KHEQ5g55dQ4 - second-hand notes (verify against the transcript)

Source: "STEAL The 1-Minute Strategy That Made Him $1.8M+ (Works Every Session)", Chart Fanatics, uploaded 2026-10-04, runtime 1:42:24, 21,988 transcript words. sha256 of the header-plus-transcript text as committed on the GB10 (branch claude/jj-simon-sources, commit f638a1f): 17c0041ef52d73cc54c0c0dd59103bfc33d1df5fca83cc837ce7b1777ae6c17c.

Companion: aCOgfvL6lK8, "The Genius Who Outsmarted The Prop Firm Game, And Made $1.5M In Payouts", Titans Of Tomorrow, 16,917 words, sha256 8abdeeb8494a7c5b2d8d6ea1e46337fd85efefb2de063dbadc39e1cbe2c2caea.

These points were reported by the GB10 session that holds the transcript. They are its reading, not verbatim quotes. Every item must be checked against the transcript (KHEQ_timestamped.txt gives per-cue timestamps) before it is promoted into DOSSIER.md as JJ's own words.

## Rules reported (JJ speaking unless noted)

| item | reported content | status |
|---|---|---|
| stop/target | 25-point stop and 38-point target in normal volatility | matches the 7-20 ATR tier already modelled |
| big opening range | contracts cut in half when the open exceeds 25 points | matches the big-open-candle rule already modelled |
| R:R by account type | 1:1.5 on evaluations and on consistency-rule accounts; 100-point targets on funded accounts without a consistency rule | NEW: the paired stop for the 100-point target is not yet known |
| stop rule | three losses in a row in a session ends that session | NEW: per-session, not per-day |
| session | sessions are 90 minutes; the 9:30 fair price is invalid after 11:00 | matches the 09:30-11:00 window already modelled |
| eval example | 50k account with -$2k drawdown and +$3k target | matches Topstep/E8/Tradeify 50k parameters |
| accounts | says 45 accounts at 0:01:21 and 0:58:50, and "if I'm trying to get through 40 accounts" earlier | he never breaks the count down by firm |
| firm choice | which firm does not matter, only that risk is optimised to that firm's rules | principle, not a list |
| firms he names himself | "Lucid or Tradeify" (0:50:51, live-account bonuses); captions "tops of lucid" at 0:24:02, probably "Topstep or Lucid" | Apex is mentioned five times, every time by the host as a sponsor read, never by JJ: do not attribute Apex figures to him |
| eval cost | evaluation price divided by pass rate | matches the formula already in risk.py |
| risk of ruin passage | at 1:14:48 he multiplies pass rate by payout rate; the captions render "0.09% 09% chance of getting a payout", which is garbled: in context it is about 9%, with 91% as its complement | check against audio before citing any number from this passage |

## Consequences for the replication

- The dossier's "45 accounts = sum of firm caps" statement is an inference, not his breakdown; keep it marked as such.
- Add a per-session consecutive-loss stop (three losses) to the strategy config and simulators.
- Add a funded-account mode with a 100-point target for accounts without a consistency rule once the paired stop is known; until then model it as an open parameter.
