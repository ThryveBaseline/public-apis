# MBO sidecar pilot: what it measures, fixed before any order-book day is read

Written 2026-10-07. MBO day 1 (2026-10-06) had been bought and its integrity checked, but no book had been rebuilt or read. Chris approved the pilot for 10 forward sessions. On 2026-10-07 he set these as the first 10 sessions that pass the data-condition gate (`forward_data_log.md`). The tool is `research/mbo_sidecar.py`.

**Role.** Annotate only. It never changes a trade, a checkpoint or a candidate of forward protocol v1. Raw MBO stays read-only on the GB10, and everything derived from it is private.

## Per day: rebuild and admit

- **Read.** The DBN file is read as is: version 3, `GLBX.MDP3` `mbo`, ESZ6 and NQZ6 with one numeric instrument each, nothing partial or missing. It must hold whole MBO records and nothing else, with NQ's records in receive-time order. Anything else is refused.
- **Rebuild.** The NQZ6 book is rebuilt by order from the day's clear and snapshot, with Databento's MBO semantics: trades and fills leave the book alone, and the following cancel or modify reduces the resting order. A modify of an unknown order is an add, as in Databento's example.
- **Read the book.** It is read at every regular-session minute boundary T, 09:30 to 16:00 ET, after every NQ record received before T. Flow is taken over [T − 60 s, T) and the trade range over [T, T + 60 s). Prints without an aggressor side are left out of both.
- **Admit.** A day is admitted only if all of these hold:
  - the 1-minute NQ bars rebuilt from its trades equal the bar file's bars, OHLCV exactly, on at least 99% of regular-session minutes. They are bucketed by exchange time or by receive time; both are recorded, because which one Databento's bars use is not documented beyond doubt;
  - the book starts from a clear followed by snapshot records;
  - no cancel of an unknown order, and no record flagged as a possibly bad book;
  - at every boundary, the book is never crossed or locked, and neither side is empty.
- **Which bar file.** Forward days are checked against the forward bar file. Reference days are checked against the sealed bar file. A day whose contract is absent from its bar file is not admitted, and the check says so.

## Per trade: three annotations

Each S3 or S4 trade on an admitted day is annotated. The trade enters at the start of minute T, at the signal bar's close. The engine assumes a fill at that minute's open plus one tick.

| Annotation | Definition |
|---|---|
| **E1 market fill** | The far touch at T: the offer for a long, the bid for a short. |
| **E2 passive entry** | A limit at the near touch at T. It fills only if a trade prints through it before T + 60 s; no queue position is assumed. Otherwise it is a market order at the far touch at T + 60 s. If there is no bar before 16:00 to enter on, it never trades (R 0). |
| **S skip signals** | At T, each signed in the trade's direction: the five-level depth imbalance, the NQ aggressor flow over the minute before T, and the ES flow over the same minute. Each is flagged when it falls strictly below the 20th percentile of the reference distribution. A trade is **skip-flagged** when both NQ imbalance and NQ flow are flagged. |

- **Measured in ticks and in R.** Ticks are measured against the engine's entry (positive is better). For R, each trade's bracket (the same stop and target distances) is replayed on the 1-minute bars from each entry, with the engine's exits:
  - the stop is checked first and filled a tick through, then the target;
  - otherwise the trade is flat at the last bar before 16:00, a tick through;
  - for a passive fill inside the entry minute, the target is not checked on that bar.
- **The check.** The engine's own entry is replayed first. It must give the recorded R and exit; any trade that does not is set aside and counted.
- **Set aside.** Trades on days that were not admitted are also set aside and counted.

**The reference distribution.** Every boundary of the admitted round-1 sessions, 2026-09-17 to 10-02, bought before the forward test. Both directions are counted, so a long's adverse value is a short's favourable one.

**The reference trades.** S3's and S4's trades on those sessions come from the baseline's private trade list. They are annotated the same way and reported separately from the forward trades.

## Day 10: how the four questions will be read

- **The sample is small.** About 5 S3 and 14 S4 forward trades, plus a similar number on the reference sessions. Nothing here can be a statistical verdict.
- **Did S3 and S4 behave as expected?** The forward protocol's 10-session checkpoint answers this, not the sidecar.
- **Did the order book improve entries?** Read from the R of each trade replayed from the passive entry, against the market fill. That replay counts the trades the passive order misses or enters late, and the adverse selection of the ones it fills.
  - **"Obvious"** means the passive entry beats the market fill in R on average and on a majority of trades, in both the reference and the forward sets.
  - The split by filled and unfilled trades is reported beside it.
  - E1 also shows whether the engine's own one-tick slippage assumption was fair.
- **Did it identify trades to skip?** The skip-flagged trades' R is listed against the rest. With so few trades this is anecdote, and it will be called that. A skip rule could only be tested on a much larger set, such as the round-1 corpus and later forward days, under its own registration.
- **Is it worth $2.30 a day?** The data cost buys measurement, not the entry itself: a live passive entry needs only the platform's own book. So the question is whether ten more days would sharpen the passive-entry result enough to decide.

If the order book adds nothing obvious, the purchases stop, as Chris set.

## Amendment before any book was read

Written 2026-10-07, after the tool's independent review and before its first run on real data. MBO day 1 had been bought and its integrity checked, but no book had been rebuilt or read.

The review found four things, now fixed above:
- the bar-match rule assumed exchange time;
- book integrity was not part of admission;
- the reference days could not be checked against the forward bar file;
- the "obvious" test was nearly true by construction: a filled passive entry beats the market fill by the spread, by definition.

The test is now in R, replayed from each entry.

## Forward only, from 2026-10-07

Under `FORWARD_POLICY.md` the sidecar uses forward data only:
- **The round-1 reference.** The historical sessions and the baseline's historical trades are dropped.
- **The flags.** Calibrated at the 20th percentile of the admitted forward sessions' own boundaries, both directions. These are context, not trade outcomes.
- **What is annotated.** Only forward trades.
- **"Obvious" at day 10.** The passive entry beats the market fill in R on average, and on a majority of the forward trades.

Any change the sidecar suggests is a new, frozen version, judged on later forward data.
