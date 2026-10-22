# JJ V1 operational readiness — 2026-10-21

**Not ready for live orders. LIVE_DISABLED is enforced in code.**

The isolated implementation is installed at `/home/buddy2/public-apis/jj-simon-replication/live` on GB10. Following the [bounded Ironbeam API review](IRONBEAM_API_REVIEW.md), verification passed **124 tests** (the original 114 plus ten focused regression cases, with existing amendment checks strengthened). The end-to-end synthetic workflow and a **23-hour accelerated operational day** also passed. No real Ironbeam authentication, market stream or simulated broker order has yet been exercised because API credentials are pending.

The owner reports the account is established, the bank is linked and a transfer was initiated. Amounts and dates stay in the owner's private account record. Cleared/available funds have not been verified. Monday October 26 remains conditional.

| Area | Status | Evidence or missing requirement |
|---|---|---|
| Frozen JJ engine/config/dependency preservation | CLEAR | Startup hash/config checks pass; no frozen source changed. |
| Streaming decisions on synthetic fixtures | CLEAR | Session, causal-prefix, management and restart fixtures pass. This is not complete live parity sign-off. |
| API adapter and separate brokerage ledger | CLEAR | Implemented and exercised against documented-shape mock responses. |
| Risk, margin and failure guards in mocks | CLEAR | 124-test suite includes concurrent reservations, uncertain submission/amendment, real process death, partial fills, rate limiting and recovery. |
| Accelerated full-day operational trial | CLEAR | 16,561 synthetic ticks across 18:00–17:00 Eastern; evening, overnight book, midnight, simultaneous signals and cutoff; ends with zero positions and working orders. |
| Actual API credentials/entitlements | BLOCKED | Owner confirms credentials pending; funding availability unconfirmed. |
| Actual native bracket/OCO persistence and broker reconciliation | BLOCKED | Requires the real demo account, including partial fills and cancel races. |
| Actual wall-clock trading-day trial | BLOCKED | Not run. A 23-hour simulated clock is not an overnight broker soak. |
| Exchange-time live signal timing and full parity | BLOCKED | Timestamp/sequence semantics, startup/gap completeness and declared translation boundaries unresolved. |
| Production orders | LIVE_DISABLED | Production mutations rejected before network calls; no enabling flag exists in this revision. |

## 2026-10-22 real broker access attempt (Claude Code took over from Codex)

Codex credits were exhausted; nothing was rebuilt. The inherited suite was independently
re-run first and passed 124 tests in 7.78s, so the handoff artifact is sound.

**Sandbox access today: NO. One blocker, and it is on the broker side.** Ironbeam requires a
live funded account holding at least the published funding minimum *cleared* before it issues any API credential,
simulation included. The owner's deposit has posted but available funds read zero; amounts and dates are in the owner's private account record, not here. No API
credential exists on GB10 and none was found in account onboarding mail.

What was established against the real broker, not a mock:

| Check | Result |
|---|---|
| GB10 reaches demo.ironbeamapi.com | CLEAR. DNS 81ms, TLS 134ms, /auth answers. |
| Credential present on host | None. Searched the configured path and the filesystem. |
| Auth contract shape | Mapped empirically with four junk-credential probes. |
| Any endpoint usable without a key | None. /info/trader, symbol search, security definitions and /stream/create all return 401. |
| Account/entitlement/market data/brackets | Untestable today. All sit behind the credential. |

**A real defect was caught before it could burn the first connection.** The credential loader and
the owner setup prompt both demanded username, password *and* apikey as non-empty strings, and the
adapter transmitted that dictionary verbatim. A standard retail account is issued a username plus
ONE key, which the official contract places in the `password` field, with `apikey` reserved
for Enterprise. The owner could not have loaded a standard credential without inventing an
`apikey` value, and the server validates `apikey` whenever present. Both shapes are now
accepted, an absent key is omitted from the request rather than sent empty, and an empty key is a
named block. Two independent model reviewers reached this diagnosis and the same minimal patch
separately. Verification is now 128 tests, the 124 inherited plus four credential-shape
regressions. Every existing protection was kept: owner-only file mode, O_EXCL creation,
terminal-only entry, no secrets in argv.

Both reviewers and this operator agree the probes do **not** settle whether a junk `apikey`
alongside a valid standard key would be rejected. That stays open and only a real credential
settles it, which is why the fix omits the field instead of relying on the server to ignore it.

**Broker terms now confirmed from the official account-open email** (previously unknown): the API
username is the account number itself (value kept out of this repository); the account carries
broker-confirmed per-contract commissions and a broker-side start-of-day auto-liquidation
threshold, both recorded in the owner's private account record; ACH clears in about three business
days while a wire is available immediately on receipt. Exchange and NFA fees per side are still **unconfirmed by Ironbeam**, so
`risk_terms.confirmed` stays false and sizing stays blocked on it.

### Two broker-process findings that change the route to Monday

**The credential route is the platform setup form, not the website API form.** The public
"Request an API Key" form on ironbeam.com is a three-field sales lead capture (name, phone,
email). The real route for an existing account holder is the platform setup form linked from the
account-open email, and Ironbeam's own knowledge base states only a **$500 account balance
minimum to have the setup processed**. That is a lower bar than the $1,000 cleared figure on the
API access page, and the two have not been reconciled by Ironbeam. The owner should submit that
form today and let the broker resolve the discrepancy in writing.

**Live API credentials require a broker conformance test on the demo account first.** Ironbeam
staff state in their own community forum: "For live, we will first need to pass you through a
conformance test on your demo account." This gate was not in the plan and it sits directly in
front of the first real-money trade. It must be scheduled, not discovered later. Demo credentials
are described as issued up front for development, on a separate demo account number.

Caveat on that forum thread: the credential fields it lists (operator ID, account password, TCP
host, port, version) describe a socket API rather than the v2 REST service this integration
targets, so the conformance requirement may attach to a different Ironbeam API product. It is
reported here as a broker statement to confirm, not as an established fact about v2 REST.

[Evidence receipt](evidence/20261022-claude-takeover/broker-access-attempt.json)

Production orders remain LIVE_DISABLED. No order, demo or otherwise, was placed.

## Defects found and fixed during this implementation

| Defect | Fix | Verification |
|---|---|---|
| Parent bracket amendments conflict with staff guidance and reported destructive behavior | Amend verified active child orders with unchanged quantity; check both legs after each PUT; persist unknown amendments before transmission | Destructive parent mock, lost stop/target despite HTTP success, accepted/unaccepted amendment timeout and restart. |
| Account-event REST bursts could exceed the published rate limit | Pace all client requests; coalesce balance events; honor 429 cooldown without queuing or retrying mutations | Request spacing, blocked requests during cooldown, stale WS status and cutoff reached during pacing. |
| Cash/fee posting lag could hide a missing protective stop | Check known exposure's protection before failing the cash comparison | Missing stop plus shifted fill price and cash lag triggers protective recovery; cash discrepancy remains blocked. |
| A timeout/restart could invite a second order | Durable pre-submit reservation and UNKNOWN state; no automatic retry | Accepted-then-timeout entry/exit tests; subprocess exits without orderly SQLite close, before/after acknowledgement. |
| A stop could exist with the wrong quantity, side, price, duration or status | Require exactly the accepted opposite-side GTC stop and target for each actual exposure; reject extra working children | Rejected/cancelled/mis-sized/wrong-side/wrong-price/day-duration/extra-child cases. |
| Protection could disappear after the stream had already failed | Recovery independently checks REST state and immediately attempts emergency demo liquidation | Stop-cancelled-after-disconnect regression. |
| Partial exit could cancel the remaining position's stop | Halt and close the remaining quantity; accept only correctly resized surviving protection | Partial target with cancelled sibling, and with correctly resized sibling. |
| Cancellation could race a stop fill and reverse the account | Confirm cancellations, ingest intervening fills, then calculate close quantity | Cancel/fill race confirms zero extra reversing order. |
| Overnight cancellation missed a partially filled parent's unfilled remainder | Cancel working parent remainder while verifying protection for the filled contracts | Partial overnight-book cancellation test. |
| Unrealized losses or a large simulator balance could overstate risk capacity | Cap sizing by realized cash and lower current broker equity; pin a separate simulated allocation offset | Open-loss capacity and large-simulator-balance versus small-allocation tests. |
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
5. **Unknown entry/exit/amendment acknowledgement needs broker reconciliation.** The documented API provides no client idempotency key or proven atomic reduce-only flatten. Cancel-then-close has an exposure window: a disconnection after protective orders are cancelled can leave an open position without a stop. The safe current behavior for uncertain requests is a durable halt and independent resolution, not guessing or retrying. This requires an exercised operator/broker recovery procedure before live use; it is not solved by the passing mock cancellation tests.
6. **Unattended operations remain unqualified.** No production daemon or alert service was installed. Authentication expiry/reauthentication, response latency near cutoff, restart supervision and reliable owner notification need verification in the existing GB10 operating setup before unattended activation. Recovery currently keeps failed authentication blocked; it does not silently refresh credentials and resume trading.
7. **Account terms and final parity approval are pending.** Confirm first-month API cost, MNQ activity counting, exchange data/fees, API margin through evening/overnight, cutoff/holidays, unattended ARM64 permission, slippage/cushion/drawdown settings, and the boundaries documented in `PARITY.md`. Test values are not broker terms.

No known failing automated test is being waived. These open items are not represented by passing mocks. No statement of operational reliability for real money is justified yet.

## Saved evidence

- [Current 124-test JUnit receipt](evidence/20261021-forum-review/tests.xml)
- [Causal signal through mock execution/recovery receipt](evidence/20261021-forum-review/mock-workflow-final.json)
- [Accelerated 23-hour operational trial receipt](evidence/20261021-forum-review/mock-day-final.json)
- [Prior-code reproduction of the three repaired gaps](evidence/20261021-forum-review/prior-defects.json)
- [Earlier 114-test candidate receipt](evidence/20261021-candidate/tests.xml)

Receipts identify mock evidence and include implementation hashes. Earlier receipts are retained as earlier revisions, not substituted for the final run. The existing paper status files had unrelated working-tree changes before this work; they remain outside this integration's commit.

## Needed from the owner

Let us know when funds are available and Ironbeam enables API access. Credentials belong in the private GB10 file through hidden terminal input; send only its path. We can handle configuration and demo testing. Ironbeam must confirm its account-specific terms before any paid activation. No approval for real trading is requested now.

The next brokerage work is the read-only probe, the delayed-feed mechanics smoke test, and the full actual trading-day failure trial in `DEMO_TRIAL.md`. Production remains disabled until the remaining defects/gates are resolved and the owner explicitly authorizes activation after reviewing the evidence.
