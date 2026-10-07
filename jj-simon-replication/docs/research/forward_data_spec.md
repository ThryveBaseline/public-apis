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

   Record the file's sha256, its row count, and its first and last `ts_event`. The first `ts_event` must be 2026-10-06T00:00:00Z or later, and there must be no duplicate timestamp.
4. **The daily bar** (`NQ.n.0`, `ohlcv-1d`) is fetched the same way, for the roll cross-check only. Its absence does not hold up the daily run: it is published on another path and may lag a day.

## Monthly audit

Once a month, refetch the whole forward range for both schemas. Transcode it and set `symbol := instrument_id` exactly as for the prepared file, then compare it bar for bar with the prepared file. Comparing a raw transcode would differ on every row's symbol. Any difference is reported before the next daily run.

## Cost

Daily increments cost about $0.011 a trading day, about $2.85 a year. The monthly audit adds about $18.50 a year. Refetching the whole range every day would have cost the triangular sum, about $360 a year, and is not done.
