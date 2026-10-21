# The personal cash account: assumptions, sources and limits

Written before the figures were computed, and reviewed adversarially before the code was built
(Codex, 2026-10-21; the blocking findings it raised are each answered below).

The question this account answers is **"what would my own $2,000 be worth?"** The prop-firm
figures answer a different question — what the evaluations have cost and paid — and the two are
now kept apart on the dashboard because they are not comparable dollar for dollar.

This is a **hypothetical accounting view** reconstructed over forward days already collected and
scored. It is not a claim that this account was operating from 2026-10-15. Nothing here alters,
rescores or re-derives a recorded signal, fill, R or outcome; the engine and its state files are
read-only inputs.

## What the recorded data actually says

Established from `research/private/jj_system_v1_state.json`, not assumed. Each of these was
checked in code against all 87 trades of the first four scored days.

1. **The existing `pnl_dollars` field is not money.** `pnl_dollars == 1000 * r` holds on every
   row, as an identity. It is a flat $1,000-per-R bookkeeping convention. This
   account therefore computes dollars from the recorded **entry and exit prices** only, and never
   touches `pnl_dollars`.
2. **Exit slippage is already inside the recorded fills.** All 39 stop exits fill exactly one
   tick adverse to the stop; all 45 target exits fill exactly at the target; the one breakeven
   exit fills one tick adverse to entry. Charging exit slippage again would double-count it, so
   this account does not.
3. **The engine's R already charges a tick on top of the fill.** `r == (signed points - 0.25) /
   stop_points` on all 87 rows. So the engine's own cost convention is one tick per trade. This
   account charges one tick of **entry** slippage on its market entries — the same magnitude,
   once — and then the commission, which R does not model at all.
4. **Stop distances take three values**: 12.5 points (9 trades), 25.0 (75), 50.0 (3). At $2 a
   point that is $25 / $50 / $100 of raw risk per micro.
5. **`stop_points` is the initial stop distance, `stop` is not.** Two trades carry a `stop` moved
   to entry (breakeven) while keeping `stop_points` 25.0. Sizing must read `stop_points`; reading
   `stop` would size those two as zero-risk.
6. **All recorded holds are intraday**: 0 to 52 minutes, median 6. None spans the 16:55–18:00 ET
   settlement break. The check stays in the code rather than being assumed for future days.
7. **The raw stream reaches 7 positions open at once** (2026-10-18 21:33). Margin alone would
   permit that at one micro each ($700); it is this account's risk limits that decline it.
8. **Two exits are `exit_signal` fills with no reference price in the record**, so their execution
   cost cannot be verified from it. They are counted at their recorded price and reported.

## The contract and cost inputs, with sources

| input | value | source |
|---|---|---|
| MNQ point value | $2.00 per index point | CME contract spec; matches `MNQ_POINT_VALUE` already in this repo |
| tick | 0.25 point = $0.50 per contract | CME contract spec |
| commission, all-in round turn | **$1.90 per micro** | retail all-in: broker commission + CME exchange/clearing (~$0.35/side) + NFA (~$0.01/side); reported retail range $1.82–$1.90, and the higher end is taken. The repo's existing $0.50 is an old replay convention the repo itself flags as too low; TopstepX is $1.22 |
| intraday margin | **$100 per micro** | NinjaTrader and AMP $100, Tradovate $50; the more conservative figure is taken |
| overnight margin | **~$3,800 per micro** | above the whole account, so overnight holding is forbidden outright rather than priced |

Margin and fee schedules move with volatility and by broker. These are the figures as of
2026-10-21 and they are constants in one place in `research/personal_account.py`.

## The sizing and risk policy

The central fact: **$2,000 is below the size at which these stop distances can be risked at a
textbook 1–2% per trade.** One micro on the typical 25-point stop risks $52.90 all in, which is
2.645% of $2,000. That is the arithmetic minimum per-trade cap that admits his main setup at all.

| knob | value | why |
|---|---|---|
| starting cash | $2,000.00 | the owner's figure |
| max risk per trade | **3.0% of equity**, both slippages and commission included | a **policy choice**, made after seeing these stops, taken for headroom above the 2.645% arithmetic minimum as equity moves. Not a figure the data forced — the report reruns the whole account at 2.0 / 2.5 / 2.645 / 3.0 / 5.0% so the choice is visible, not buried |
| max total open risk | 6.0% of equity across all open positions | two full-size ideas at once. **This, not the position count, is what governs concurrency at this account size**: sizing spends the per-trade cap, and the allowance is twice it, so two full-sized positions are the norm |
| max concurrent positions | 3 | a backstop. It binds only when a trade sizes below its full per-trade cap and leaves risk slack — on the first four scored days that happened 3 times. The raw stream reaches 7; a $2,000 account should not carry that |
| open day-margin cap | 50% of cash | never tie the account up; at $2,000 that is 10 micros, so margin is not the binding constraint here — risk is |
| overnight holding | forbidden | overnight margin exceeds the account |
| no new entry | 16:40–18:00 ET | a forward policy, so the flatten rule never needs to see a trade's exit |
| flatten by | 16:55 ET | if a taken position is ever still open then, it is FLAGGED, never given an invented liquidation price |
| trading floor | $500, latched | below this the account cannot fund one micro responsibly; once off it stays off |
| equity for sizing | realised cash at the moment of entry | no mark-to-market, no look-ahead |
| sizing rule | largest whole micro count whose full stop-out fits the cap, minimum 1, else not taken | mirrors `research/candidates.whole_contracts` and `forward_jj.sized` |

Planned risk per micro, used for sizing:
`(stop_points + 0.25 entry slip + 0.25 exit slip) * $2.00 + $1.90` — $52.90 on a 25-point stop,
$27.90 on 12.5, $102.90 on 50 (so 50-point stops are declined until equity reaches $3,430).

Realised P&L per trade, from recorded prices only:
`((exit - entry) * direction) * $2.00 * micros - $1.90 * micros - $0.50 * micros`,
with the commission and entry slippage debited **at the entry** and the gross credited at the
exit, so no decision ever sees its own outcome.

## Causality, and why the skips are split in two

Every entry decision reads only cash returned by trades that had already closed and positions
already open at that moment. A trade's own `exit_time` is never consulted to decide whether to
take it.

Skips are reported in two kinds, deliberately:

- **`infeasible`** — the account could not have placed the trade (below the trading floor, day
  margin cap).
- **`policy`** — its own risk limits declined it (per-trade cap, open-risk cap, concurrency, the
  no-entry window). A larger account, or a looser limit, would have taken it.

Calling a policy skip "unexecutable" would claim more than the record supports. No skipped trade
is counted as profit or loss in either kind.

Where several candidates share one entry minute and the account cannot take them all, they are
offered in the order the engine emitted them — the order a live trader would have seen them fire.
That tie cannot be settled from the record, so the report also reruns the identical account with
the order reversed and prints both, which bounds how much of the result rests on it.

## Drawdown: two numbers, because one is not enough

- **Closed-balance drawdown** moves only when a trade closes. With up to three positions open it
  understates what the account went through, and says nothing about margin survival. The opening
  $2,000 counts as the first peak.
- **Marked-to-market drawdown** marks every open position on each minute's close from the same
  forward 1-minute bars the engine scored, and also at each minute's adverse extreme as an
  intra-minute bound. This is the number that answers "did this account stay alive", and it also
  reports how many minutes equity sat below the day-margin the open positions required.

## Not modelled — every one adverse to this account

So the figures here are **optimistic, not conservative**: session and news margin increases,
trading halts, partial fills, rejected orders, fills worse than one tick, forced-liquidation
charges, and the two `exit_signal` fills whose execution cost the record cannot establish.

## What this view does not do

It does not test whether the strategy has an edge, and four scored days cannot. It is a dollar
translation of the recorded R stream and inherits every property of that stream. Do not annualise
it. What it fixes is the measurement: whether $2,000 of the owner's own money could have placed
these trades, at what size, at what cost, and what it would be holding now.
