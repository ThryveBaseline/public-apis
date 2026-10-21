# JJ V1 operational readiness — 2026-10-21

**Not ready for live orders. LIVE_DISABLED is enforced in code.**

The isolated implementation is installed at `/home/buddy2/public-apis/jj-simon-replication/live` on GB10. The final local verification run passed **114 tests**. The end-to-end synthetic workflow and a **23-hour accelerated operational day** also passed. No real Ironbeam authentication, market stream or simulated broker order has yet been exercised because API credentials are pending.

The owner reports the account is established, the bank is linked and a $2,000 transfer was initiated. Cleared/available funds have not been verified. Monday October 26 remains conditional.

| Area | Status | Evidence or missing requirement |
|---|---|---|
| Frozen JJ engine/config/dependency preservation | CLEAR | Startup hash/config checks pass; no frozen source changed. |
| Streaming decisions on synthetic fixtures | CLEAR | Session, causal-prefix, management and restart fixtures pass. This is not complete live parity sign-off. |
| API adapter and separate brokerage ledger | CLEAR | Implemented and exercised against documented-shape mock responses. |
| Risk, margin and failure guards in mocks | CLEAR | 114-test suite includes concurrent reservations, uncertain submission, real process death, partial fills and recovery. |
| Accelerated full-day operational trial | CLEAR | 16,561 synthetic ticks across 18:00–17:00 Eastern; evening, overnight book, midnight, simultaneous signals and cutoff; ends with zero positions and working orders. |
| Actual API credentials/entitlements | BLOCKED | Owner confirms credentials pending; funding availability unconfirmed. |
| Actual native bracket/OCO persistence and broker reconciliation | BLOCKED | Requires the real demo account, including partial fills and cancel races. |
| Actual wall-clock trading-day trial | BLOCKED | Not run. A 23-hour simulated clock is not an overnight broker soak. |
| Exchange-time live signal timing and full parity | BLOCKED | Timestamp/sequence semantics, startup/gap completeness and declared translation boundaries unresolved. |
| Production orders | LIVE_DISABLED | Production mutations rejected before network calls; no enabling flag exists in this revision. |

## Defects found and fixed during this implementation

| Defect | Fix | Verification |
|---|---|---|
| A timeout/restart could invite a second order | Durable pre-submit reservation and UNKNOWN state; no automatic retry | Accepted-then-timeout entry/exit tests; subprocess exits without orderly SQLite close, before/after acknowledgement. |
| A stop could exist with the wrong quantity, side, price, duration or status | Require exactly the accepted opposite-side GTC stop and target for each actual exposure; reject extra working children | Rejected/cancelled/mis-sized/wrong-side/wrong-price/day-duration/extra-child cases. |
| Protection could disappear after the stream had already failed | Recovery independently checks REST state and immediately attempts emergency demo liquidation | Stop-cancelled-after-disconnect regression. |
| Partial exit could cancel the remaining position's stop | Halt and close the remaining quantity; accept only correctly resized surviving protection | Partial target with cancelled sibling, and with correctly resized sibling. |
| Cancellation could race a stop fill and reverse the account | Confirm cancellations, ingest intervening fills, then calculate close quantity | Cancel/fill race confirms zero extra reversing order. |
| Overnight cancellation missed a partially filled parent's unfilled remainder | Cancel working parent remainder while verifying protection for the filled contracts | Partial overnight-book cancellation test. |
| Unrealized losses or a large simulator balance could overstate risk capacity | Cap sizing by realized cash and lower current broker equity; pin a separate simulated allocation offset | Open-loss capacity and $100,000 simulator/$2,000 allocation tests. |
| Multiple simultaneous signals could compete for the same risk budget | SQLite immediate transaction reserves risk/margin before submission | 16 concurrent reservations across separate connections respect $60/$120 initial limits. |
| Restarting after the configured session expired blocked recovery setup | Dedicated `recover` command ignores entry-session/parity requirements and monitors only an existing demo ledger | Next-day recovery closes known exposure and retains entry halt. |
| A changed margin requirement could prevent recognizing an already-flat account | Separate confirmed broker position state from entry eligibility | Flat-after-target recovery with changed margin. |
| Partial first minute or late historical insertion could corrupt causal state | Discard partial startup minute; reject late insertion/revision instead of silently changing replay | Aggregation and late-bar regression tests. |
| Account/host changes could retain authority | Revoke verification before rebind; pin hosts and order account; lock account across state directories | Production-write, host/account override and lock tests. |

## Open defects and release blockers

1. **Actual broker behavior remains unverified.** Bracket acceptance timing, server persistence, OCO and partial-fill semantics, order/fill retention, cash/fee posting timing, disconnect recovery and cutoff behavior need real demo evidence. Native children are requested; their server persistence is not yet proven.
2. **The feed is not yet qualified for real-time decisions.** The API calls `st` send time; contiguous per-symbol sequence semantics are not established. A delayed feed with a fresh send timestamp is not proof of a live exchange trade. The implementation deliberately blocks qualification.
3. **Automatic context backfill is incomplete.** Recent, verified context can be seeded and the minute journal replayed, but an arbitrary mid-minute startup or unscheduled gap cannot currently be repaired automatically. This remains a functional blocker for unattended strategy routing. No candles are fabricated.
4. **Whole-GB10 outage safety is not established.** Actual process-kill durability is tested in isolated subprocesses. GB10 was not powered off or disconnected globally, which would disturb the existing paper system. Broker-native stop persistence and a cutoff liquidation route independent of the failed GB10 must be confirmed. Recovery after restart cannot substitute for action while power is off.
5. **Unknown entry/exit acknowledgement needs broker reconciliation.** The documented API provides no client idempotency key or proven atomic reduce-only flatten. The safe current behavior is a durable halt and manual resolution, not guessing or retrying. This requires an exercised operator/broker recovery procedure before live use.
6. **Unattended operations remain unqualified.** No production daemon or alert service was installed. Authentication expiry/reauthentication, response latency near cutoff, restart supervision and reliable owner notification need verification in the existing GB10 operating setup before unattended activation. Recovery currently keeps failed authentication blocked; it does not silently refresh credentials and resume trading.
7. **Account terms and final parity approval are pending.** Confirm first-month API cost, MNQ activity counting, exchange data/fees, API margin through evening/overnight, cutoff/holidays, unattended ARM64 permission, slippage/cushion/drawdown settings, and the boundaries documented in `PARITY.md`. Test values are not broker terms.

No known failing automated test is being waived. These open items are not represented by passing mocks. No statement of operational reliability for real money is justified yet.

## Saved evidence

- [Final 114-test JUnit receipt](evidence/20261021-candidate/tests.xml)
- [Causal signal through mock execution/recovery receipt](evidence/20261021-candidate/mock-workflow.json)
- [Accelerated 23-hour operational trial receipt](evidence/20261021-candidate/mock-day.json)

Receipts identify mock evidence and include implementation hashes. Earlier receipts are retained as earlier revisions, not substituted for the final run. The existing paper status files had unrelated working-tree changes before this work; they remain outside this integration's commit.

## Needed from the owner

Let us know when funds are available and Ironbeam enables API access. Credentials belong in the private GB10 file through hidden terminal input; send only its path. We can handle configuration and demo testing. Ironbeam must confirm its account-specific terms before any paid activation. No approval for real trading is requested now.

The next brokerage work is the read-only probe, the delayed-feed mechanics smoke test, and the full actual trading-day failure trial in `DEMO_TRIAL.md`. Production remains disabled until the remaining defects/gates are resolved and the owner explicitly authorizes activation after reviewing the evidence.
