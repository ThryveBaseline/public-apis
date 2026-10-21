# Streaming translation declaration: jj-v1-stream-1

Date: 2026-10-21. Scope: implementation equivalence of frozen JJ V1 rules. **No parameter optimization, historical performance study or rule change.** Synthetic correctness fixtures compare causal decisions with the pinned batch implementation and assert specific session behavior.

Frozen engine SHA-256: `5bf01d24ec9f5e2c6a677786168ab0dda341920243e20a4b28767ec35633f40d`.

Frozen specification SHA-256: `928fb99da33f67c4b6e4aae26d5bc35c406b0ec871fdacda32d8fcf7f3ede456`.

Startup also verifies the exact configuration and dependency hashes in `research/jj_system_v1_init.json`. The new module imports frozen configuration/state types and reads the existing calendar/session helpers. It does not modify those files.

## Preserved rules and evidence

`tests/test_strategy.py` uses hand-authored candles, not recorded market history. Coverage includes 18:00/20:00, overnight book placement/cancellation, news/FOMC/speeches, 09:30/14:00/Friday, pivots and break of structure, displacement, higher-time-frame direction, 25/38 and 12.5/19 brackets, wide opening brackets, holiday behavior, layering, all-time-high exclusion, consecutive-loss state/reanchoring, break-even management, and deterministic restart decision IDs.

Decisions are emitted after the completed signal minute, before a future candle or exit is available. Shortening an input prefix does not create the batch engine's artificial terminal close. `verification.mock_demo` exercises synthetic trades through aggregation, causal JJ entry, MNQ bracket, restart replay, disconnect fill, and reconciliation.

## Explicit translation decisions and unresolved limits

| Boundary | Implementation | Live qualification |
|---|---|---|
| Batch session end can inspect the next available bar | Streaming uses known session clock boundaries; missing unscheduled minutes halt entry routing | Sparse/missing-bar equivalence is not assumed. Verified gap repair and timestamp semantics remain required. |
| Batch order filled at next bar's open plus fixed slippage | Emit a market intent at the signal minute close; use actual fills for cash and align protection to accepted average fill | Actual delay/slippage distribution has not been measured. Excess allowance halts/attempts emergency demo close. |
| Overnight strict trade-through at a swing | Native STOP trigger one MNQ tick beyond the swing; preserve frozen stop/target distances from actual fill | Requires actual Ironbeam trigger and partial-fill qualification. The model's theoretical price is not booked as cash. |
| Multi-account virtual JJ positions | Keep frozen virtual state for subsequent JJ signal rules; record executable personal orders separately | A risk-skipped or oppositely directed candidate is logged rather than converted into account P&L. Opposing brackets cannot be silently netted in one account. |
| Pre-10:00 wording vs pinned code | Follow the pinned code's 10:00 candle-open anchor when that candle completes | Wording/code timing ambiguity remains declared; no alternative rule was silently selected. Final parity sign-off is still BLOCKED. |
| Starting mid-minute | Discard the initial incomplete minute; require completed context and previous 09:30 state | An arbitrary fresh start cannot bridge that missing minute automatically. No validated history/backfill endpoint has been implemented. Continuous qualified capture or verified context repair is required. |
| Missing calendar | Pin latest eligible pre-session snapshot and verify its hash; reject absent, old or revised input | Unknown calendar is not treated as no news. |
| NQ signals and MNQ execution | Matching explicit expiries; NQ points, MNQ $2/point and $0.50 tick | Broker entitlements, tick values, calendar and mapping must be verified. No automatic roll. |
| Break-even and exits | Translate causal management to broker modification/exit; verify actual position and accepted child orders | Real fills can differ from virtual fills. Actual demo behavior remains unverified. |
| Broker cutoff vs frozen 16:10 | Preserve the frozen 16:10 signal event and separately enforce an earlier broker-required cutoff if applicable | Actual account/API margin schedule and cutoff are unknown; configuration blocks routing until confirmed. |

The synthetic tests are useful evidence, not complete equivalence proof across every possible tick ordering, sparse market interval, broker fill sequence or economic-calendar condition. `parity_qualified` remains false in the example. Unresolved translation or timing discrepancies block production activation.
