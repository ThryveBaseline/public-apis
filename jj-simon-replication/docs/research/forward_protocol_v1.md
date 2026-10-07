# Forward paper test, version 1: S3 frozen, S4 beside it

Decided by Chris on 2026-10-07. Written and committed before any trading day after 2026-10-05 has been scored. The commit that adds this file freezes it. Any change after that is version 2, recorded beside version 1, which keeps running unchanged.

**Purpose.** "The backtest gave us permission to try it; the forward test is earning permission to risk a little money." The forward test checks that the frozen rules behave on unseen days as they did historically, and it records every trade exactly as the rules would have taken it. It cannot confirm the edge in any practical time: at about 220 trades a year, a year pins the mean to roughly ±0.09 R. It can show whether something is obviously wrong.

## What is frozen

- **S3, the main candidate.** The frozen engine's rules, Baseline 0 (f585bfb), run through `research/engine.py`, which takes one position at a time as a live bot would. Continuation entries only.
  - **Configuration:** `ResearchConfig(reversion_end="09:30", continuation_atr_k=0.4, continuation_rr=2.0, flat_time="16:00", one_contract=True)`.
  - **Stop:** 0.4 × the previous Globex session's daily ATR, tick-rounded, at least 2 points.
  - **Target:** 2 × the stop.
  - **Exit:** flat at the close of the last bar before 16:00 ET, less 0.25 point.
  - **Costs:** as the replay.
  - **Why this bracket:** it is the link S3's walk-forward chain chose on all 16 development years. It is the same link the chain used every year from 2021, and in the benchmark year.
  - **R:** per contract. The whole-micro sizing used in B3–B5 is recorded beside each trade (the largest count whose full stop-out fits $1,000 in the evaluation and $500 funded).
- **S4, the challenger.** S3 plus the reversion entries of grade A+, at the sealed 25/38 bracket, flat at 16:00.
  - **Configuration:** `ResearchConfig(allow_grade_a_reversion=False, continuation_atr_k=0.4, continuation_rr=2.0, flat_time="16:00", one_contract=True)`.
- **Data.**
  - **The series:** `GLBX.MDP3` `NQ.n.0` continuous `ohlcv-1m`, bought, transcoded and prepared exactly as the sealed file (`docs/DATA_DECISION.md`, symbol := instrument_id). The first unseen day is 2026-10-06.
  - **Roll dates** are excluded as in the sealed run: New York dates on which the instrument changes.
  - **Completeness:** a date is scored only when its bars reach the close of the 15:59 ET bar.
  - **Hashes:** every forward file's sha256 is recorded.
- **The firm view.** For the record, one paper Topstep 50K path from $2,000, one account at a time, whole micros, both payout policies, B5's mechanics. It is driven by S3's forward trades, and S4's beside it. It is bookkeeping, not a test.

## How it runs

- **The baseline (once, before scoring any forward day).** `research/forward.py baseline` runs both configurations over the sealed history through 2026-10-05.
  - It reports their trades and statistics by period.
  - It fixes the checkpoint thresholds below from development trades only.
  - The baseline report's sha256 is recorded, and every daily run checks it.
- **Each trading day.** `research/forward.py day` reruns the frozen configurations over the sealed history plus the forward bars, in one pass.
  - It appends each completed forward date's trades to the forward ledger.
  - It refuses if any trade already recorded would change. History is never rewritten.
  - It writes a status report with the checkpoint flags.
  - The per-trade ledger stays private. The status report is a public aggregate.
- **No edits during the test.** S3 and S4 are not changed, and no third candidate joins before the 30-setup checkpoint. A bug fix becomes version 2 and runs beside version 1; both are recorded.

## Checkpoints, fixed now

All thresholds come from the baseline's development trades. Windows are blocks of consecutive trades or sessions, every start counted (overlapping).

1. **After 10 forward trading days: does it behave like history?**
   - Checks, flagged when outside the development 1st–99th percentile:
     - S3's and S4's trade counts over the 10 sessions, against all 10-session windows;
     - the share of stops, targets and 16:00 exits;
     - the long and short split.
   - Also checked:
     - a deterministic rerun reproduces the ledger exactly;
     - no day was skipped for data reasons without being recorded as such.
2. **At 20 and at 30 forward S3 setups: is anything obviously wrong?** Each is flagged against development S3 trades over windows of the same length:
   - mean R per trade below the 2.5th percentile;
   - the deepest cumulative-R drawdown beyond the 99th percentile;
   - the target-hit share below the 1st percentile.

   S4 is reported the same way beside it. A flag means stop and look, not a verdict.

**Healthy after 30 S3 setups** means no flag, and no unresolved data or engine fault. Healthy is the condition under which Chris has said he would discuss one cheap real evaluation. That also requires the independent audit of the Topstep economics, which runs in parallel and does not block the paper test.

## The MBO sidecar

For forward days with MBO data (subject to its own quote), each S3 and S4 trade is annotated with two things: whether a microstructure-timed entry would have filled better, and whether book state at the signal pointed to a skip. These annotations are recorded beside the ledger. They never change a trade, a checkpoint or the candidates during version 1.

## Clarifications before the first forward day

Written 2026-10-07, after the runner's independent review and before any bar after 2026-10-05 was bought or seen. The text above left some things underspecified. These clarifications say how it is carried out. They change no candidate, rule, threshold method or checkpoint.

1. **A session** is a New York date with a 09:30 ET bar, both in the baseline (the thresholds' 10-session windows) and forward. Sunday evenings and closed holidays are not sessions. "10 forward trading days" means the first 10 scored sessions.
2. **Completeness.** A forward session is scored once the file holds a bar on a later New York date. This replaces "its bars reach the close of the 15:59 ET bar". That rule would never score an early close (13:15 ET), and it would score a date before its evening roll could be seen.
   - Roll dates are still excluded.
   - Every forward weekday that is not scored is listed with its reason: a roll date, or no 09:30 bar (market closed or data missing).
3. **Continuity.**
   - The forward bars must continue the sealed file within 30 minutes. The sealed file ends at 2026-10-05 23:59 UTC; the forward request starts at 2026-10-06 00:00 UTC.
   - A stretch of over 30 minutes without a bar inside a weekday's 09:30–16:00 session stops the run as missing data.
   - Overnight stretches can be genuine, since a one-minute bar exists only when a trade occurred. They are reported, not refused.
   - The baseline reports how often each kind would have occurred in the benchmark year.
   - The raw forward file must have unique, increasing timestamps and an instrument on every bar.
4. **The record.** The forward ledger is a private state file, written atomically. It holds:
   - the scored dates;
   - every trade, with its signal time and the ambiguous-bar flag;
   - a run log, each entry carrying the previous state's hash;
   - the sha256 of the code that produces the trades: `research/engine.py`, `anatomy.py`, `bracket_replay.py`, `candidates.py` and the `fpt` modules they use.

   A change to that code stops the test. It would be version 2.
5. **Public and private.**
   - The public status gives counts, hashes, scored and unscored dates and, at each checkpoint, which checks were flagged.
   - A private status holds the values behind the checks, the forward R, the exit mix and the paper account.
6. **S4's setup checks** are taken at S4's own 20th and 30th setups, against S4's own development thresholds.
