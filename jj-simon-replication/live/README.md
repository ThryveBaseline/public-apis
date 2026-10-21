# JJ V1 Ironbeam execution integration

**LIVE_DISABLED. This implementation cannot send production orders.** It is installed alongside JJ on GB10. Existing paper jobs, strategy files, forward ledgers, and their Python environment are untouched. The transport supports authenticated production reads and verified simulation-account writes only. There is no environment variable or approval file that bypasses that boundary.

Implementation request: [issue #1](https://github.com/ThryveBaseline/jj-simon-sources/issues/1), including [START IMPLEMENTATION NOW](https://github.com/ThryveBaseline/jj-simon-sources/issues/1#issuecomment-6324227839). Operational reliability, not profitability research, is the priority. See [operational status and defects](STATUS.md), [streaming translation declaration](PARITY.md), and [demo trial procedure](DEMO_TRIAL.md).

## What is implemented

- REST authentication, account verification, instrument/margin probes, market/account WebSockets, and a fresh stream ID after every disconnect.
- Completed-minute feed validation and a causal JJ adapter emitting order/management intents. The frozen completed-day engine is never used to generate runtime orders.
- MNQ native bracket requests, stop/target verification against actual fills, break-even modifications, partial-fill reconciliation, pending-order cancellation, and guarded demo liquidation.
- Durable order intent before each entry request; a timeout or interrupted process never causes an automatic repeat submission. Account-wide process locking prevents two runtimes using different state directories.
- Separate SQLite ledgers for mock, dry-run, and demo accounts. Actual fills drive brokerage cash, FIFO realized P&L, fees, open quantity and optional marked P&L. JJ's virtual position results never become account cash.
- Whole-contract sizing under 3% per trade and 6% aggregate reserved stop risk, including pending entries, configured fees, two slippage allowances, margin and cushion. Unrealized gains cannot increase sizing; open losses can reduce capacity. A 50-point MNQ stop does not fit the initial $60 risk allowance. Stops cannot guarantee a maximum loss through gaps.
- Recovery monitoring keeps entries halted after disconnects, reconciles broker state, checks protection, and attempts emergency demo exits for confirmed protection/margin/risk failures. Unknown submissions require manual resolution.

## GB10 commands

Run from `/home/buddy2/public-apis/jj-simon-replication`.

```sh
PY=/home/buddy2/.local/share/jj-live/venv/bin/python
$PY -m live status
$PY -m pytest live/tests -q
$PY -m live mock-demo --output /home/buddy2/.local/share/jj-live/mock-receipt.json
$PY -m live mock-day --output /home/buddy2/.local/share/jj-live/mock-day-receipt.json
```

Receipts refuse overwrite. Mock fixtures contain invented prices and failure events. They are execution tests, not historical market studies or profit forecasts. `mock-day` advances an injected clock through 23 hours; it is not a wall-clock broker trial.

The separate runtime reuses packages read-only from `/home/buddy2/jj-venv` and installs only `websocket-client==1.9.2` into its own environment. To recreate it, use `/home/buddy2/jj-venv/bin/python live/install.py`. No service, timer, cron entry, container or trading daemon is installed.

## API setup once Ironbeam issues access

Ironbeam's [official access rules](https://www.ironbeam.com/knowledge-base/ironbeam-api-access/) require a funded account of at least $1,000 even for simulation API access. An initiated transfer does not confirm funds availability. The standard simulation feed is delayed by 10 minutes. Initial-month pricing, whether MNQ micros count toward the five-contract threshold, and account-specific entitlements still need Ironbeam's confirmation. No paid feature has been requested or purchased.

The owner can ask the existing account representative:

> Please enable the standard Ironbeam simulation API for my funded individual account, with the usual delayed feed for broker-mechanics testing. Please confirm any first-month API cost before activation, MNQ counting toward the activity threshold, NQ/MNQ data entitlements, all-in MNQ fees, API intraday and overnight margin, required flatten cutoff, and permission for unattended personal Linux ARM64 execution. Please also confirm server-side bracket/OCO persistence, partial-fill handling, and the supported emergency close procedure.

We can handle the GB10 configuration. Enter issued credentials through an owner-controlled interactive terminal; never send their values through chat, GitHub or command-line arguments:

```sh
cd /home/buddy2/public-apis/jj-simon-replication
/home/buddy2/.local/share/jj-live/venv/bin/python -m live setup
```

This creates `/home/buddy2/.config/jj-live/ironbeam-demo.json` with owner-only permissions and hidden input. It refuses a non-interactive terminal and never overwrites an existing secret. It does not authenticate or send orders. Tell the assistant only the saved path.

Then run the read-only probe:

```sh
$PY -m live probe
$PY -m live probe --account ACCOUNT_ID --symbol XCME:NQ.Z26 --symbol XCME:MNQ.Z26 --stream
```

The symbols above are examples, not an automatic contract choice. Discover and verify the current matching expiries first. Production read-only probing uses `--environment live-readonly` with the separately confirmed credential path. Receiving a trade sample or a recent server send timestamp does not validate exchange-time signal timing.

## Demo configuration and execution

Copy `config.example.json` to a private path outside the repository, fill confirmed account/instrument/cost/session terms, and keep the evidence flags false until qualified. Never use synthetic test fees or margins as broker facts. `starting_cash` is the actual allocated account cash, not virtual JJ results.

- `demo-smoke`: set `mode` to `demo-mechanics`, `environment` to `demo`, and use a new private state directory. Requires confirmed fees/margin/cutoff and a flat verified simulated account. Accepts explicitly configured delayed quotes for broker mechanics. Sends at most one MNQ entry, verifies its native stop/target, disconnects/reconnects, then attempts a confirmed cleanup close. It never qualifies real-time timing or a whole trading day.
- `run` with `mode: dry-run`: evaluates the streaming path without order routing. It requires valid current context, calendar and account settings. `probe` can inspect access while those are pending.
- `run` with `mode: demo`: requires qualified feed timestamp/sequence semantics, strategy parity and bracket evidence. It validates matching NQ/MNQ instruments and expiration against the broker. A delayed feed cannot pass strategy routing qualification.

```sh
$PY -m live demo-smoke --config /home/buddy2/.config/jj-live/mechanics.local.json --output /home/buddy2/.local/share/jj-live/demo-smoke-receipt.json
$PY -m live run --config /home/buddy2/.config/jj-live/demo.local.json
```

`CLEAR` from `demo-smoke` covers only its named checks. It is never live authorization. A blocked or uncertain trial must be reconciled before another state directory or trial is used. Do not reset a simulator account to hide unknown orders or discrepancies.

## Kill and recovery

Create `KILL` in the configured state directory. The runtime stops accepting new entries and attempts a guarded demo liquidation when connectivity permits. Removing the file does not clear the durable halt. Do not clear SQLite halt/unknown fields by hand or rerun an uncertain submission.

On a timeout, shutdown, rejected stop, cash mismatch or uncertain flatten: inspect the broker portal, independently confirm all working orders and positions, preserve the private ledger, and reconcile actual executions. A local zero position alone is not proof that the broker is flat. If GB10 is unavailable, the owner must use Ironbeam's independent access/support route. Native bracket persistence and unattended cutoff protection during a complete GB10 outage are **unverified release blockers**.

After GB10 returns, `recover` can monitor the existing demo ledger even if its configured session/cutoff is already past or strategy qualification is incomplete. It cannot restore entry routing or create a fresh ledger:

```sh
$PY -m live recover --config /home/buddy2/.config/jj-live/demo.local.json
```

This creates fresh account streams, reconciles protection, and attempts a close when the old cutoff has passed. An unknown order remains a manual broker-reconciliation case. Do not repeatedly interrupt the recovery monitor while exposure remains.

Production activation requires all broker and timing gates, the full demo day, an independent review of the financial/authority boundaries, and explicit owner authorization. This revision deliberately has no production order switch. Monday October 26 remains conditional.
