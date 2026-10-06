# Phase 1 data decision (2026-10-06)

Inventory of the GB10 performed over the Surface bridge session, read-only, no credentials. Full report kept on the GB10 as `~/nq_inventory.md`; it is not committed here because it lists local paths.

| Candidate | What it is | Verdict |
|---|---|---|
| Databento batch pilot (GLBX.MDP3, `mbo`, ESZ6 + NQZ6) | 12 weekdays 2026-09-17 to 2026-10-02, each 00:00 to 20:10 UTC, 6.77 GiB, 415,304,978 records, raw fixed-point prices, UTC ns timestamps, symbol recoverable per record | unsuitable for Baseline 0: order-book schema, not 1-minute bars; 12 days, not multi-year; one contract month, so no roll observable; 20:10 cutoff omits the Globex open and the last 50 minutes before the 21:00 close; tape completeness gate pending in the project's own report. Kept as an asset for Phase 6 microstructure work. |
| 100 ms top-of-book grids derived from the pilot | 13:30 to 20:00 UTC, no OHLC, no volume | unsuitable |
| FirstRate free samples (AAPL, EURUSD, ES, SPY) | sample-length 1-minute CSVs | unsuitable: no NQ, no coverage |
| crypto wallet `ohlcv.parquet` | not futures | unsuitable |
| `bars/` directory | empty | unsuitable |

**Decision:** no suitable NQ 1-minute data exists on the GB10. Proceed to the Databento quote on the Surface per `docs/DATA_PROTOCOL.md` (NQ.n.0 at ohlcv-1m as the purchase; NQ.c.0 at ohlcv-1d as the roll cross-check). Quote first; nothing is downloaded until Chris approves the price.

Environment notes for the sealed run: the GB10 system Python has no pandas or numpy, the pilot virtualenv has only the DBN decoder, and the root filesystem has about 42 GiB free against a 35 GiB floor reserved by the pilot project. Run the frozen evaluator on the Surface, or in a fresh environment on the GB10 after the disk question is settled.
