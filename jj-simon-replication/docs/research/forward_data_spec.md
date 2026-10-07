# Forward data: how the unseen NQ bars are bought and assembled

This is for the forward paper test (`docs/research/forward_protocol_v1.md`). It applies once Chris approves the bar quote of 2026-10-07: $0.0113 per trading day for `NQ.n.0` at `ohlcv-1m`. The bridge on the GB10 runs it, with the local Databento credential, which is never printed or transmitted. `research/forward.py` reads only the prepared cumulative file described below.

## Daily, after 17:15 ET

1. **The increment.** Request `GLBX.MDP3`, `NQ.n.0`, `stype_in="continuous"`, `ohlcv-1m`.
   - **Start:** 15:00 ET on the last stored complete trading day. That is the last regular-session hour, so the overlap is dense.
   - **End:** the `available_end` that the API's 422 reports at that moment. The range endpoint lags by hours.
   - **Storage:** each raw `.dbn.zst` gets its own dated, read-only name and its sha256. None is ever overwritten.
2. **The overlap check.**
   - Every bar of the increment inside the overlap window must equal the stored bar exactly: `ts_event`, open, high, low, close, volume and `instrument_id`.
   - The window must contain at least one bar, so the check can never pass on an empty window.
   - On any difference, stop, report it and append nothing.
   - A change of `instrument_id` there can be Databento revising the continuous series' resolution. That is the check doing its job, to be reported, not a pipeline bug.
3. **Rebuild the prepared file** `data/forward/nq_1min_forward.csv` from the stored increments, in order:
   - transcode exactly as run1 (the databento-dbn Transcoder, CSV, map_symbols, decimal prices);
   - set `symbol := instrument_id`;
   - de-overlap, with the stored copy winning: an increment's rows in the overlap are discarded.

   Record the file's sha256, its row count, and its first and last `ts_event`.
   - The first increment's request starts at exactly 2026-10-06T00:00:00Z, the minute after the sealed file's last bar.
   - The runner refuses a file:
     - whose first bar comes more than 30 minutes after the sealed file's last bar;
     - that repeats or reorders a timestamp;
     - with a bar whose symbol is not its instrument_id;
     - with a gap of over 30 minutes inside a 09:30–16:00 session, or across 00:00 UTC.

     A gap running from a scheduled halt (the 17:00 daily break, or a 13:00 holiday halt or 13:15 early close on a date in the runner's calendar) to the 18:00 reopen is exempt. So is a gap a person records as an exchange halt, with its source (`--accept-gap`).
   - The prepared file and the increments stay under `data/forward/`, which git ignores.
4. **The daily bar** (`NQ.n.0`, `ohlcv-1d`) is fetched the same way, for the roll cross-check only. Its absence does not hold up the daily run: it is published on another path and may lag a day.

## Data condition, before any date is fetched

Added 2026-10-07, before any forward bar was bought. That afternoon the MBO file for 2026-10-06 carried Databento's possibly-bad-book flag on every non-snapshot record, ES and NQ alike. Databento's condition report gave the reason: from 2026-09-15 on, 2026-10-06 was the only GLBX.MDP3 date reported "degraded". Its last-modified date was the day itself. Every other date had been revised the day after its session. The condition is per dataset and date, so it covers the bars as well as MBO.

1. **Check first, for free.** Before fetching a date, bars or MBO, query `metadata.get_dataset_condition` for `GLBX.MDP3`.
2. **What counts as ready.** Fetch a date only if both hold:
   - its condition is "available";
   - its last-modified date is later than the date itself, meaning it was published after its session. The current day can read "available" while still incomplete.
3. **Record it.** Store each fetched date's condition and last-modified date with the increment's sha256.
4. **Otherwise wait.** A date that is degraded, pending or missing is not fetched. The runner needs bars that continue from 2026-10-06 00:00 UTC, so the daily run waits and the wait is reported. The test's first scored day, 2026-10-06, waits for its revision.
5. **Recheck stored dates.** At every daily run and at the monthly audit, recheck the condition and last-modified date of every stored date.
   - If a stored date's last-modified date has advanced, refetch it and compare it bar for bar before the next daily run.
   - Any difference is reported.
   - If the difference touches a scored date, the runner's history check stops the test. That is what the check is for.
6. **If a date stays degraded,** Chris decides what to do then. It is never handled by relaxing a check.

For the MBO pilot, each day is bought only when it meets point 2. The degraded 2026-10-06 file is kept, and the sidecar's admission rule rejects it. Re-buying it after its revision, about $2.30, is Chris's call.

## Monthly audit

Once a month, refetch the whole forward range for both schemas. Transcode it and set `symbol := instrument_id` exactly as for the prepared file, then compare it bar for bar with the prepared file. Comparing a raw transcode would differ on every row's symbol. Any difference is reported before the next daily run.

## Cost

Daily increments cost about $0.011 a trading day, about $2.85 a year. The monthly audit adds about $18.50 a year. Refetching the whole range every day would have cost the triangular sum, about $360 a year, and is not done.

## Decisions, 2026-10-07 (Chris)

- **Bars:** the forward NQ 1-minute and daily bars are approved, bought as above. The order is:
  1. the runner's review clears;
  2. the sealed-data baseline is run and pinned;
  3. the bars are bought from 2026-10-06 on;
  4. the daily paper runs start.
- **MBO sidecar:** approved as a pilot for exactly the first 10 forward trading days, about $23 in total.
  - **What:** `GLBX.MDP3` `mbo`, `ESZ6` and `NQZ6`, full session 00:00–21:00 UTC.
  - **Purchase:** each complete day once, quoted before buying.
  - **Storage:** raw files read-only and hashed, on the GB10 only.
  - **Limits:** no long-term commitment, and no model files cleared.
  - **Disk:** for the pilot only, 25 GiB of free space on the GB10 is a reported line, not a hard stop. Chris chose warn-and-proceed in the bridge window.
    - The tooling reports the projected free space before each download.
    - It refuses to start, and aborts mid-stream, only if a download would take the root filesystem under 2 GiB.
    - Nothing is ever deleted, and the line is revisited at day 10.
- **At day 10, Chris asks four questions:**
  - Did S3 and S4 behave as expected?
  - Did the order book improve entries?
  - Did it identify trades that should have been skipped?
  - Is that worth $2.30 a day?

  If the order book adds nothing obvious, the purchases stop.
