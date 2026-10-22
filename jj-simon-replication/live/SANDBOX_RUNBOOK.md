# Ironbeam sandbox session runbook

Exact commands for the first real broker session, in order. Nothing here has been run against
Ironbeam: every step below is unexercised until a credential exists. Production orders are
`LIVE_DISABLED` throughout and no step in this runbook can place a production order.

Prerequisite: Ironbeam has issued a native API credential. Until then step 0 fails closed with
`CREDENTIAL_FILE_UNAVAILABLE`, which is the correct answer, not a defect.

```
HOST   buddy2 (GB10), via: ssh buddy2-tail
REPO   /home/buddy2/public-apis/jj-simon-replication
PY     ~/.local/share/jj-live/venv/bin/python
```

## 0. Enter the credential (owner, interactive terminal only)

Must be a real TTY. The command refuses a pipe, refuses argv, and writes `0600` with `O_EXCL`.
Nothing is transmitted during setup.

```
ssh -t buddy2-tail
cd /home/buddy2/public-apis/jj-simon-replication
~/.local/share/jj-live/venv/bin/python -m live setup --credentials ~/.config/jj-live/ironbeam-demo.json
```

Three hidden prompts:

1. `API username:` the Ironbeam-issued API username.
2. `API key (standard) or API password (Enterprise):` for a standard account, **the issued API key
   goes here**. This is the Ironbeam contract, not a workaround: a standard account authenticates
   with the key in the `password` field.
3. `Enterprise API key (leave empty for a standard account):` press Enter unless Ironbeam
   explicitly issued a separate Enterprise key. An empty value is omitted from the request
   entirely, because the server validates `apikey` whenever the field is present.

Send only the file path. Never the values.

## 1. Read-only probe, no order and no mutation

```
$PY -m live probe --environment demo
```

Expect `SELECT_AND_VERIFY_MATCHING_NQ_MNQ_EXPIRIES` with the discovered contract list. Read the
listed NQ and MNQ symbols, pick the matching front expiries, then re-probe them explicitly:

```
$PY -m live probe --environment demo --symbol XCME:NQ.<EXP> --symbol XCME:MNQ.<EXP>
```

Verifies auth, account enumeration, a USD balance, security definitions, tick size 0.25, tick value
0.50 for MNQ, a non-expired contract, trading-allowed and margin availability. Then:

```
$PY -m live probe --environment demo --symbol XCME:MNQ.<EXP> --stream
```

Adds one trade sample and reports `observed_send_time_age_seconds`. **A fresh send time on a
delayed feed is not a live exchange trade.** `real_time_signal_timing` stays `BLOCKED` by design.

## 2. Record the account and the broker terms

Copy the example config to a private path outside the repository and fill in only broker-confirmed
values. Leave every qualification flag false until its own step passes.

```
cp live/config.example.json ~/.config/jj-live/demo.json
chmod 600 ~/.config/jj-live/demo.json
```

Required before sizing can be trusted: `risk_terms.fee_round_trip`, `slippage_points`,
`margin_per_contract`, `margin_cushion`, `max_drawdown_dollars`, then `confirmed: true`. Test
values are not broker terms. Set `account` to the id the probe returned.

## 3. Bounded broker mechanics, where demo orders begin

```
$PY -m live demo-smoke --config ~/.config/jj-live/demo.json --output ~/evidence/demo-smoke.json
```

Requires `environment: demo` and `mode: demo-mechanics`. A smoke pass does **not** authorize
strategy routing. Then work `live/DEMO_TRIAL.md` in its stated order, capturing a separate receipt
per step:

1. Native bracket. Record the exact accepted MARKET and STOP payloads both sides, GTC encoding,
   parent and child ids, active child prices and quantities. An entry that returns an order id
   without native protection **fails** and triggers recovery.
2. Amend the active child stop by its own `orderId` with unchanged quantity. Verify the sibling
   target is untouched and child ids are stable. Never fall back to amending the parent.
3. Lose the amendment acknowledgement. Interrupt the client before and after broker acceptance,
   restart against the same private ledger. Require no repeated PUT and no second entry.
4. Kill only the client process with an accepted amended bracket live. Confirm from the portal that
   the stop and target persist, observe a broker-side fill and OCO cancellation, then reconcile
   exactly once on a **new** stream id.
5. Cutoff and emergency exit with protection impaired. Independently confirm the account is flat
   with no working orders.
6. Paced recovery under real event load. Use a broker-approved throttle exercise for real 429
   behaviour, never an uncontrolled flood.

Then the attended wall-clock day: the 18:00 Eastern reopen through the following session and the
broker cutoff, flat through the daily break.

## 4. If something fails mid-session

```
$PY -m live recover --config ~/.config/jj-live/demo.json
```

`recover` ignores entry-session and parity gates, monitors only an existing demo ledger, closes
known exposure and keeps the entry halt. It is the correct response to a halt. It is not a way to
resume trading.

## 5. Confirm orders remain disabled

```
$PY -m live status
```

Must print `"live": "LIVE_DISABLED"` and `"frozen_strategy": "CLEAR"`.

## What cannot be answered without the broker

Bracket acceptance timing, server-side OCO persistence, partial-fill semantics, cash and fee
posting lag, real disconnect recovery, cutoff behaviour, and feed timestamp meaning. Mock receipts
are never broker evidence. Keep broker receipts in a directory distinct from the `live/evidence`
mock receipts.
