# What to do when a connection or a protective order fails

Operational response for the demo trial and, later, for live. The broker-side contact card is
`ops/IRONBEAM_EMERGENCY_CARD.md` in `ThryveBaseline/jj-simon-sources`; this file is the software
side. Account identifiers and credentials appear in neither.

**The governing rule: an uncertain order is never retried.** Every uncertain mutation becomes a
durable `UNKNOWN` plus a halt. The API offers no client idempotency key and no proven atomic
reduce-only flatten, so a second attempt can double a position. Resolve by reading broker truth,
never by guessing.

## Triage by symptom

| Symptom | What the system does | What the operator does |
|---|---|---|
| Auth rejected or expired | Fails closed. Recovery does **not** silently re-authenticate and resume. | Re-check the credential file. Do not re-enter a key while a position is open; reconcile first. |
| `BROKER_REJECTED` | Ironbeam returned a 200-shaped envelope with `status: ERROR`. Caught, never mistaken for success. | Read the reported reason. Do not resend. |
| `HTTP_429` or `RATE_LIMIT_COOLDOWN` | All traffic paced at 250ms; a cooldown blocks requests without queuing and never retries a mutation. | Wait out the cooldown. Check cutoff headroom before resuming. |
| Submission times out | Durable pre-submit reservation plus `UNKNOWN`. No automatic retry. | Confirm from the portal that exactly one parent exists, then reconcile. |
| Stop or target missing, rejected, or mis-sized | Entries halt. Emergency close is attempted, or unconfirmed exposure is reported. | If the close is unconfirmed, flatten through the broker and treat the position as unprotected until confirmed. |
| Amendment acknowledgement lost | Persisted before transmission; both legs re-checked after each PUT. | Verify the new protection independently, or leave the amendment blocked. Never re-PUT. |
| Partial fill, remainder unprotected | Halts and closes the remaining quantity; accepts only correctly resized surviving protection. | Confirm the broker position equals the protected quantity. |
| Cancel racing a fill | Cancellation is confirmed and intervening fills ingested **before** any close quantity is computed. | Verify no reversing order exists. |
| Stream drops | A new `streamId` per reconnect; fills seen while offline reconcile exactly once. | Confirm the reconciled fill count matches the portal. |
| Client process dies | Journal replay on restart, no duplicate order. | Run `live recover`, then verify flat. |
| **Whole GB10 outage** | Nothing local runs. Broker-native GTC children are the only protection. | See the hard limit below. |

## The hard limit, stated plainly

**If GB10 dies, this system cannot flatten anything.** Broker-native GTC stop and target orders are
the only remaining protection, and a stop is not a guaranteed maximum loss: a gap can fill it
anywhere. The account auto-liquidation threshold is a broker risk control, not a timed cutoff, and
must not be treated as one.

Until an independent cutoff route is confirmed for this account and actually exercised,
**unattended live trading stays BLOCKED.** Owner intervention is not an independent cutoff: it
requires a person to be awake and reachable.

Two things must be established with Ironbeam before that status can change:

1. That our exact API-placed bracket persists server-side after amendment, verified while the
   client is deliberately offline.
2. Whether this account may use the web or mobile platform **concurrently** with the native API.
   Ironbeam staff have previously stated that an account may trade through only one platform at a
   time. If that holds here, the platform is **not** an emergency fallback and the 24-hour trade
   desk is the only independent route. Verify before relying on either.

## Escalation order

1. Stop new entries. The halt is already durable; do not clear it to try again.
2. Read broker truth over REST and the portal. Reconcile before acting.
3. If exposure is unprotected and the software cannot confirm a close, flatten through whichever
   broker channel is actually permitted for this account.
4. If the platform route is unavailable or uncertain, call the 24-hour trade desk and flatten by
   voice. Record order ids and times.
5. Only once flat and reconciled, diagnose. Re-run the affected scenario plus the full workflow
   before resuming.

An unresolved fill, a cash or fee discrepancy, missing protection, or a cutoff failure is a defect.
None of them is an acceptable pass.
