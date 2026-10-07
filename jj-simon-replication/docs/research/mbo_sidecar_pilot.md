# MBO sidecar pilot: what it measures, fixed before any order-book day is read

Written 2026-10-07. MBO day 1 (2026-10-06) had been bought and its integrity checked, but no book had been rebuilt or read. Chris approved the pilot for exactly the first 10 forward trading days. The tool is `research/mbo_sidecar.py`.

**Role.** Annotate only. It never changes a trade, a checkpoint or a candidate of forward protocol v1. Raw MBO stays read-only on the GB10, and everything derived from it is private.

## Per day: rebuild and admit

- **Read.** The DBN file is read as is: version 3, `GLBX.MDP3` `mbo`, ESZ6 and NQZ6 with one instrument each. It must hold whole MBO records and nothing else; any other content is refused.
- **Rebuild.** The NQZ6 book is rebuilt by order from the midnight snapshot, with Databento's MBO semantics: trades and fills leave the book alone, and the following cancel or modify reduces the resting order.
- **Read the book.** It is read at every regular-session minute boundary, 09:30 to 16:00 ET. The state used at boundary T is the one after every record received before T.
- **Admit.** A day is admitted only if all of these hold:
  - the 1-minute NQ bars rebuilt from its trades (exchange time) equal the forward bar file's bars, OHLCV exactly, on at least 99% of regular-session minutes;
  - the book is never crossed or locked at a boundary;
  - neither side of the book is empty at a boundary.

  Cancels or modifies of unknown orders are counted and reported.

## Per trade: three annotations

Each S3 or S4 trade on an admitted day is annotated. The trade enters at the start of minute T, at the signal bar's close. The engine assumes a fill at that minute's open plus one tick.

| Annotation | Definition (ticks against the engine's entry; positive is better) |
|---|---|
| **E1 market fill** | The far touch at T: the offer for a long, the bid for a short. |
| **E2 passive entry** | A limit at the near touch at T. It fills only if a trade prints through it before T + 60 s; no queue position is assumed. Otherwise it is a market order at the far touch at T + 60 s. The fill rate is reported. |
| **S skip signals** | At T, each signed in the trade's direction: the five-level depth imbalance, the NQ aggressor flow over the minute before T, and the ES flow over the same minute. Each is flagged when it falls strictly below the 20th percentile of the reference distribution. A trade is **skip-flagged** when both NQ imbalance and NQ flow are flagged. |

**The reference distribution.** Every boundary of the admitted round-1 sessions, 2026-09-17 to 10-02, bought before the forward test. Both directions are counted, so a long's adverse value is a short's favourable one.

**The reference trades.** S3's and S4's trades on those sessions come from the baseline's private trade list. They are annotated the same way and reported separately from the forward trades.

## Day 10: how the four questions will be read

- **The sample is small.** About 5 S3 and 14 S4 forward trades, plus a similar number on the reference sessions. Nothing here can be a statistical verdict.
- **Did S3 and S4 behave as expected?** The forward protocol's 10-session checkpoint answers this, not the sidecar.
- **Did the order book improve entries?** Read from E2's mean ticks and fill rate. An entry effect is per trade and far less noisy than outcomes. For example, +1 tick on a 25-point stop is +0.01 R.
  - **"Obvious"** means E2 better than E1 by at least one tick on average, on both the reference and the forward trades, with a fill rate of at least 60%.
  - E1 also shows whether the engine's own one-tick slippage assumption was fair.
- **Did it identify trades to skip?** The skip-flagged trades' R is listed against the rest. With so few trades this is anecdote, and it will be called that. A skip rule could only be tested on a much larger set, such as the round-1 corpus and later forward days, under its own registration.
- **Is it worth $2.30 a day?** The data cost buys measurement, not the entry itself: a live passive entry needs only the platform's own book. So the question is whether ten more days would sharpen E2 enough to decide.

If the order book adds nothing obvious, the purchases stop, as Chris set.
