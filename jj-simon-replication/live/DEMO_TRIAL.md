# Required actual Ironbeam operational trial

Status: **BLOCKED - API credentials pending.** Reconfirmed against the real broker on
2026-10-22: GB10 reaches https://demo.ironbeamapi.com/v2 and /auth answers, but every other
endpoint returns 401 without a token, so none of the checks below can start. Ironbeam requires a
funded account before issuing any API credential and available funds read zero. Two broker-side
gates were identified the same day and are prerequisites to this trial: submitting the platform
setup form from the account-open email, and a broker conformance test on the demo account before
live credentials are issued. See STATUS.md for both. No actual Ironbeam order was attempted. The only real traffic sent was unauthenticated auth-endpoint probes with junk values, to map the credential contract. Standard delayed simulation data is acceptable for the broker-mechanics checks below. Real-time signal timing is a separate gate.

Use the existing GB10 runtime and a verified simulation account with no external positions or orders. Confirm any API charge, fees, margin, contract, account reset behavior and broker cutoff first. Begin with the read-only probe and the bounded `demo-smoke` harness. A smoke pass does not authorize automated strategy routing.

The [bounded API review](IRONBEAM_API_REVIEW.md) identified the following priority sequence. These are attended, actual-broker checks; none has been run yet:

1. **Establish the native bracket contract.** Record exact accepted MARKET and STOP entry payloads on both sides, GTC encoding, parent/child IDs, active child prices/quantities and fills. Resolve absolute-price versus offset documentation with a bounded comparison only if needed; verify units and price basis. A successful entry response without native protection fails qualification and requires recovery.
2. **Modify the active child stop.** Use that child's `orderId`, unchanged `quantity` and `stopPrice`; alignment of the LIMIT child uses `limitPrice`. Inspect REST and the independent portal after each amendment. Require unchanged sibling target, matching exposure and eventual execution of the amended stop. Test partial entry, partial exit and child-ID stability. Never fall back to updating the parent when a child is inactive. Observe/reconcile an amendment that races a fill.
3. **Lose the amendment acknowledgement.** Interrupt the demo client's connection before and after broker acceptance. Restart against its same private ledger. Require no repeated PUT, no second entry, and either independently confirmed new protection or a clearly blocked unresolved amendment. Confirm emergency recovery for a missing leg even if balances lag.
4. **Make the demo client disappear with an accepted, amended bracket.** Kill only its process or isolate only its broker connection; do not stop GB10 paper jobs or globally disable networking. Keep the independent broker portal available. Demonstrate stop/target persistence, a broker-side fill and OCO cancellation while the client cannot act, followed by exact reconciliation after restart. This tests broker independence from the client; whole-host restart durability and cutoff action while the host is absent remain separate checks.
5. **Prove cutoff and emergency exit while protection/recovery is impaired.** Confirm account-specific margin transition and cutoff/holiday schedule. Exercise cancel/fill races, rejected close and loss between cancel and close. Independently verify the broker account is flat with no working orders. Demonstrate the owner/broker recovery route while GB10 is unavailable. Do not treat broker auto-liquidation or the existence of a GTC stop as a timed cutoff guarantee.
6. **Observe paced recovery under real event load.** Capture status disagreements and REST convergence; verify a balance-message burst does not flood REST. Use a broker-approved throttle exercise for actual HTTP 429 behavior, not an uncontrolled request flood. Confirm cooldown, no mutation retry and sufficient cutoff headroom. A single snapshot needs multiple requests; real latency and concurrent clients count.

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
