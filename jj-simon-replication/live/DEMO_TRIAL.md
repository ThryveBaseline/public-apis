# Required actual Ironbeam operational trial

Status: **BLOCKED — API credentials pending.** No actual Ironbeam connection or order was attempted during this implementation. Standard delayed simulation data is acceptable for the broker-mechanics checks below. Real-time signal timing is a separate gate.

Use the existing GB10 runtime and a verified simulation account with no external positions or orders. Confirm any API charge, fees, margin, contract, account reset behavior and broker cutoff first. Begin with the read-only probe and the bounded `demo-smoke` harness. A smoke pass does not authorize automated strategy routing.

Run an attended wall-clock trading-day trial from the 18:00 Eastern reopen through the following overnight/day sessions and broker cutoff, then verify flat through the daily break. Capture UTC and Eastern timestamps, API acknowledgement latency, order IDs in the private ledger, actual fills, accepted child quantities/prices, broker cash and final working orders. Repeat after any material execution fix. Do not use fixture prices, flags or mocked receipts as broker evidence.

| Deliberate failure | Required evidence before CLEAR |
|---|---|
| Disconnect before/after submit | Exactly one accepted parent or a durable unresolved intent; never an automatic repeat request. Reconcile broker truth before resuming. |
| Disconnect with an open position | Native stop and target persist at Ironbeam; observe fills/cancels while client is offline and reconcile them exactly once on a new stream ID. |
| Missing/rejected/wrong-sized stop | Entries halt; emergency close succeeds or the system clearly reports unconfirmed exposure for independent broker action. No quiet unprotected position. |
| Partial entry and partial target | Protective remaining quantities match the actual open exposure; unfilled parent remainder is cancelled at the book cutoff; no orphan or reversed position. Actual partial fills must be observed, not assumed from a one-contract fill. |
| Cancel/fill race and bracket replacement | A fill racing cancellation is ingested before any exit quantity is computed. Rejected/uncertain replacement blocks entries. Confirm server OCO semantics. |
| API timeout/restart | Unknown placement/exit remains durable across process death; no second entry/exit appears. Restore from the same private journal. |
| Simultaneous JJ signals | Sum of accepted and pending risk never exceeds 6%; each new position fits 3%, fees/slippage and available margin. Whole contracts only. |
| Margin change/negative availability | Current broker requirements override stale settings; no further entries; protective recovery executes or reports a blocker. |
| Session cutoff without incoming market trades | Independent recovery clock attempts cancel/close and confirms broker flat; measure timeout behavior close to the cutoff. |
| Stale/delayed/missing/revised ticks or calendar | Strategy routing halts. Delayed-demo mechanics may run only in their explicitly separate harness. |
| GB10 process and machine failure | Test actual restart journal reconciliation; separately demonstrate native protection during a GB10 outage and an independent method to flatten by cutoff. A process-kill unit test does not prove whole-machine cutoff safety. |

Keep a separate timing receipt from a genuinely real-time, exchange-time-correct feed: verify what `st` and `sq` mean, final-minute completeness, duplicate/gap detection, clock agreement, actual arrival-to-decision latency, and matching NQ/MNQ expiries. The API describes `st` as send time; a recent send time on delayed data is not proof of a current exchange trade. Do not buy live simulation data automatically.

Unresolved fills, cash/fee discrepancies, missing protection, or cutoff failures are defects, not acceptable passes. No test may be marked CLEAR solely because the request returned an order ID. Record repaired defects and rerun the affected scenario plus the complete workflow.

After the full broker trial and timing/parity checks are CLEAR, give the owner a plain-language readiness report and obtain explicit authorization for production activation. Until then, **LIVE_DISABLED**.
