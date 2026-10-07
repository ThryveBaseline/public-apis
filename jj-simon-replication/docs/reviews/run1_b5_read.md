# Read: B5, the $2,000 bootstrap on replayed paths, and structure versus edge

**Provenance.** Runs on the GB10 at 6d6b39e, exit 0, no refusal. Results are in `research/run1_b5.md` (sha256 a947d173…) and `research/run1_structure.md` (0dc969be…), pushed in 0876d86 after Chris authorized it.

**Gates passed:**
- B3's eight sealed firm rows reproduce.
- B4's first-payout gate held on every selected stream.
- In every run, every evaluation and every first payout equals the frozen walk-forwards' result, where both are compared.
- The registration and its clarifications and amendment are at the pinned hash (10695c98…).

**Data.** Development runs from 2010-06 to 2025-10-05: 4,445 overlapping paths, 15.3 years. The benchmark is one path over 2025-10-06 to 2026-10-05, reported beside and choosing nothing.

## 1. The registered reading

Each path starts with $2,000 and runs for 12 months in whole micro contracts on TopstepX, development paths only. A configuration qualifies when, at one cap, both versions (without a call-up and with the call-up at the 3rd payout) have:
- P(ruin) at most 10%;
- median final cash above $2,000;
- 25th percentile of final cash at least $1,000.

**Verdict:** 14 of 16 stream-and-policy pairs go on to a forward test, every one at cap 1, one account at a time. The pairs are S1, S2, S3, S4 and H3's favoured side of S1, S3 and S4, each under both payout policies. S0r fails. At cap 5 nothing qualifies.

Cap 1, payouts asked for whenever eligible, development:

| stream | P(ruin) | final cash p10 / p25 / median (no call-up) | the same with the call-up | deepest fall below $2,000, median / p90 | called up within 12 months |
|---|---|---|---|---|---|
| S0r sealed brackets | 25.0% | $32 / $48 / $2,627 | $32 / $48 / $2,329 | $841 / $1,968 | 62% |
| S1 continuation, sealed bracket | 0.7% | $1,367 / $2,302 / $3,688 | $1,399 / $2,013 / $3,056 | $579 / $1,188 | 85% |
| S2 S1 + A+ reversion | 3.9% | $832 / $1,683 / $3,111 | $912 / $1,719 / $2,819 | $609 / $1,646 | 76% |
| S3 continuation, walk-forward ATR | 0.0% | $1,273 / $2,509 / $3,967 | $1,273 / $2,402 / $2,963 | $494 / $982 | 86% |
| S4 S3 + A+ reversion | 0.0% | $1,123 / $2,682 / $4,447 | $1,122 / $2,378 / $3,238 | $537 / $1,033 | 86% |
| S1 on H3's favoured side | 0.0% | $1,269 / $1,971 / $3,178 | $1,269 / $1,987 / $3,029 | $494 / $943 | 66% |

- **The waiting policy** (no payout until the loss limit reaches the starting balance) gives similar results. Without a call-up its medians are a little higher: S3 $4,780, S4 $4,594.
- **The call-up.** Most paths are called up to a Live account within the year, typically after about 145–205 trading days. The call-up version counts the Live account as nothing, so it bounds a called-up path's worth from below.
- **Cap 5 fails everywhere.** P(ruin) is 43–73% without a call-up. Five evaluations bought on consecutive days, taking the same trades, spend the cash before the payouts arrive. Their outcomes are bimodal: the paths that survive grow large, and most do not survive.
- **The benchmark year**, one path at cap 1 under "ask": S1 ended at $7,611, S2 $10,778, S3 $5,004 and S4 $5,377 (with the call-up $2,962, $3,783, $3,941 and $4,639). S0r was ruined after 34 evaluations and two passes, with no payout.
- **The frozen bootstrap** B3 used (independent accounts, one payout each) gives P(bust) of 0–2% for S1–S4 and 64% for S0r. The path replay agrees for S1–S4 and is kinder to S0r (25%). Among other things, the frozen version charges the evaluation fee once, so it is not simply more pessimistic.

## 2. Structure versus edge

The control measures how much of B4's development lifetime EV per evaluation at H 250 (TopstepX) the same trades would earn with zero edge. It uses two nulls:
- **Shift:** every R moved by the stream's development mean.
- **Re-label:** a share of trades moved to the other side's typical outcome, averaged over ten orders.

The two nulls agree within about $10–30.

| stream | dev R per trade | EV at 1.00, ask | EV with no edge: shift / re-label | the edge's part |
|---|---|---|---|---|
| S0r | −0.041 | +$36 | +$138 / +$111 | −$103 / −$75 |
| S1 | +0.013 | +$133 | +$96 / +$107 | +$37 / +$25 |
| S2 | +0.001 | +$102 | +$100 / +$100 | +$1 / +$1 |
| S3 | +0.042 | +$228 | +$107 / +$117 | +$121 / +$112 |
| S4 | +0.044 | +$211 | +$92 / +$93 | +$119 / +$117 |

At 0.95 of the budget, and under the waiting policy, the picture is the same: no edge earns +$99 to +$161, and S3/S4's edge adds +$112 to +$165.

- **What the structure pays.** With no edge at all, the same trades earn about +$90 to +$160 per evaluation under Topstep's rules as modelled. A funded account's loss is capped by the firm's drawdown, while half of every upswing can be withdrawn.
- **What continuation's edge adds.** For S3 and S4 the edge roughly doubles the EV.
- **What S0r's negative edge costs.** It costs $75–120 of the structure's value.
- **S2 is the clearest case.** Its edge is zero (+0.001 R per trade) and it still qualifies in B5. The registered test of surviving from $2,000 mainly tests the structure.

## 3. What this means

- **The research question has an answer in development.** A disciplined operation from $2,000, with one Topstep 50K account at a time, whole micro contracts, continuation entries, and payouts taken as the rules allow, survives and grows in development. For S3 and S4, no development path was ruined; the median after 12 months is $3,000–$4,450 depending on the call-up. The benchmark year agrees.
- **Most of that comes from the firm's structure, and it lasts only as long as the rules do.** Topstep changed its payout caps in April 2026. The modelled rules are the Standard path: 50% of profit up to $2,000 a request, five winning days of at least $150, a 90/10 split, and the loss limit reset to the starting balance after a payout. If they change, the value changes. The continuation edge adds about as much again, and the H3 filter more in development.
- **Untested here, and what a forward test should measure:**
  - real fills and slippage beyond the replay's 0.25 point and commission;
  - micro contract fees at today's rates;
  - platform and data fees, assumed $0;
  - Topstep's discretion over payouts and call-ups;
  - the Live account's value;
  - today's micro menu applied to 2010–2019;
  - the 20-purchases-a-month limit, which does not bind at cap 1.
  None of these is the edge, which forward data cannot confirm in any practical time.
- **Selection.** Fourteen of sixteen pairs qualify, so picking among them is not what drives the result. But every number here is from development data that the research has looked at many times.

**Next, if Chris wants it:** a pre-registered paper forward test of one configuration, S3 or S4 at cap 1. It would run on data after 2026-10-05, checking the replay's fills and costs and the operation's mechanics trade by trade. The data needs a Databento quote, for Chris to approve. If H3's favoured side were chosen, its re-simulation on the research engine, which its registration requires, comes first. No live money.
