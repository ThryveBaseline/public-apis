# run1 B3 and the conditional-edge tests: read (Claude, cloud session, 2026-10-07)

Sources: `research/run1_b3.md` (sha256 b459827c…) and `research/run1_conditions.md` (3b9fcb2f…), both run on the GB10 at bb8d2ff and pushed unchanged in 127b6b1. The tools, `research/candidates.py`, `research/conditions.py` and `research/engine_check.py`, went through independent adversarial reviews and verification rounds before the run (commits 46dfae7 to bb8d2ff). The conditional-edge tests implement `docs/research/preregistration_conditional_edge.md` as registered in c0c7a15 and clarified in 26cb07a, both before any real data was touched.

## Gates

- **Research engine.** `research/engine.py` at its defaults rebuilds `sealed/run1/trades.csv` byte for byte from the sealed bar file (sha256 afd3fc4d…, 8,810 trades). Re-simulation is therefore anchored to Baseline 0.
- **B3.**
  - The sealed ledger, scored B3's way, reproduces all eight firm rows of the sealed report.
  - The trades, bars and report match the manifest's sha256.
  - The replay join is checked on 7,656 exits.
- **Conditional edge.**
  - The registration file and the cut match their pinned values.
  - 142 entries sit on sessions holding a contract switch; under clarification 1 they sit out of the gap-based tests.
- **Stale wording.** B3's summary says the monthly fee is counted "22 trading days a month". The computation bills every 30 calendar days (b54d18c), and the sentence has since been corrected; the numbers are right.

## 1. The continuation signal is real, and it is not the bull market

Held to 16:00, continuation entries beat the same-direction trade from the same minute, averaged over every day of their year, as follows.

| measure | development | benchmark |
|---|---|---|
| excess per daily ATR, long | +0.039 (0.015) | +0.068 (0.053) |
| excess per daily ATR, short | +0.031 (0.015) | +0.044 (0.050) |
| excess per daily ATR, both | +0.035 (0.011) | +0.055 (0.036) |
| development years positive, per daily ATR | 14 of 16 | |
| mean of the yearly means, per daily ATR | +0.034 (0.0095 across years) | |
| excess in R per 25 points, both | +0.260 (0.105) | +1.087 (0.702) |

- Shorts carry excess too, so the direction call carries information beyond drift; it is not just being long in a rising market. Counting each year as one observation, the signal is about 3.6 standard errors from zero. Only 2015 and 2017 are negative.
- The brackets keep little of it. The sealed 25/38 bracket makes +0.013 R per trade on continuation in development. The walk-forward ATR bracket makes about +0.04 R per trade; from 2021 it chose a 0.4 ATR stop with a 2:1 target, chosen on earlier years only.

## 2. Under the firm rules

Topstep 50K. TopstepX (`topstep_50k_x`) is the realistic preset for a new account; the frozen preset carries the legacy daily limit. "Frozen EV" is JJ's calculator. "Net EV" also charges the monthly evaluation billing and the $149 activation fee. Development first, benchmark after the slash.

| stream | P(pass), frozen preset 1.00 | P(payout) | frozen EV | net EV | net EV, TopstepX at 1.00 / 0.95 | net EV, TopstepX whole micros |
|---|---|---|---|---|---|---|
| S0r sealed brackets (control) | 18.0% / 7.7% | 44.4% / 13.2% | −2 / −31 | −33 / −45 | −34 / −33 | −36 / −45 |
| S1 continuation, sealed bracket | 29.6% / 25.6% | 54.6% / 63.6% | +40 / +82 | −7 / +43 | −9 / −6 | −11 / +65 |
| S3 continuation, walk-forward ATR | 29.3% / 22.8% | 63.4% / 70.1% | +44 / +36 | −2 / −0 | −3 / +0 | −7 / −30 |
| S4 S3 plus reversion A+ | 29.0% / 25.5% | 62.0% / 74.4% | +48 / +74 | +2 / +33 | +2 / +8 | −3 / +15 |

- **Continuation trades through an evaluation far better than Baseline 0.** It passes about 30% of the time against about 20%, and pays out from the funded account 55–66% against about 45%. That is the B2 finding, now in firm terms.
- **The fees take what JJ's calculator shows.** Monthly billing and the activation fee are about $50 per evaluation at these pass rates. They turn the calculator's +$40 to +$50 into −$11 to +$8 in development. On the realistic preset no stream is clearly profitable in development. S4 is the best at about breakeven.
- **Sizing.** On TopstepX, sizing at 0.95–0.98 of the budget (below the drawdown edge: two stop-outs at 1.02 R breach the $2,000 drawdown) adds 2–4 points of P(pass) and a few dollars of EV. Whole micro contracts cost a few dollars more, through rounding on ATR stops. The frozen daily-limit preset's numbers below 1.00 are an artefact and are not shown (assumption 39).
- **The frozen bootstrap is optimistic.** It shows 0% bust from $2,000 for S1, S3 and S4, but it charges one evaluation fee and no activation fee.
- **The calculator counts one payout per funded account.** That payout is the first, and it is small: a median of $430–$550, half the profit after five winning days, net of the split. A funded account trading a positive-drift stream keeps paying. This is now the largest conservative assumption left in the money estimate.

## 3. The conditional-edge tests (research step 4)

| id | condition, favoured side | development difference (se) | Holm p | years positive | benchmark difference (se) | result |
|---|---|---|---|---|---|---|
| H1 | continuation with the 20-session trend | +0.037 (0.038) | 1.00 | 10 of 16 | −0.084 (0.151) | fails |
| H2 | continuation with the overnight move | +0.021 (0.038) | 1.00 | 9 of 16 | +0.237 (0.151) | fails |
| H3 | continuation, opening candle at or above its median, relative to ATR | +0.101 (0.039) | 0.047 | 11 of 15 | −0.160 (0.154) | passes |
| H4 | continuation, compressed overnight range | −0.038 (0.039) | 1.00 | 4 of 15 | +0.198 (0.161) | fails |
| H5 | continuation, open beyond the prior session's extreme | +0.066 (0.054) | 0.88 | 11 of 16 | +0.171 (0.180) | fails |
| H6 | continuation, less extension at the signal | −0.078 (0.039) | 1.00 | 3 of 15 | +0.003 (0.158) | fails, opposite |
| H7 | reversion A+, more room to fair value | +0.016 (0.095) | 1.00 | 4 of 5 | +0.150 (0.188) | fails |
| H8 | reversion A+, with the 20-session trend | −0.179 (0.089) | 1.00 | 1 of 8 | +0.023 (0.174) | fails, opposite |
| H9 | reversion A+, gap fill | +0.013 (0.091) | 1.00 | 5 of 8 | +0.013 (0.176) | fails |

- **H3 passes, barely.** In development the favoured side makes +0.053 R and the other side −0.047 R. In the benchmark, under the bracket, it points the other way. On the secondary outcome (the hold minus the drift) the favoured side is ahead in both periods: +0.052 against +0.011 per ATR in development, +0.073 against +0.024 in the benchmark. Per the registration it becomes a candidate filter for firm scoring and re-simulation. It is not yet evidence of money.
- **Two fail in the opposite direction.**
  - H6: continuation does better when the price is further from fair value at the signal (+0.053 against −0.025).
  - H8: reversion A+ does worse with the 20-session trend (−0.136 against +0.043).

  The registration forbids adopting a re-cut on these data. With H3 they tell one story: continuation pays when the opening push is strong. A new registration, tested on unseen data, is the only way to use them.
- **Reversion A+.** No condition helps it, and the test has little power (about 780 entries).

## 4. What this means for the $2,000 question

- **The edge is in the signal, not yet in the account.** The direction call is real and persistent across years. The current exits and JJ's evaluation economics leave almost none of it after Topstep's fees.
- **Two levers remain, both measurable on the data we have:**
  1. **The lifetime value of a funded account.** Count every payout until bust over a fixed horizon, with all fees. The one-payout calculator is the largest conservative bias left.
  2. **Exits that keep more of the measured move.** For example, a continuation stop scaled to daily ATR, with no target and flat at 16:00. This must be pre-registered before it is computed.
- **H3 follows its registered path:** firm scoring on its favoured side, then re-simulation.
- **Clean proof must come from data after 2026-10-05.** The benchmark year has been seen through B1 to B3. S3's ATR family was also chosen after B1 and B2 had printed benchmark columns, so the benchmark is no longer a clean test for these candidates.

## Caveats

- Streams are built from the sealed entries. S2 to S4 cannot contain re-entries that an earlier exit would have freed; the research engine re-simulates whatever survives.
- Fractional sizing in the summary. The whole-contract rows assume $0.50 per micro round trip; real micro fees are higher, about 0.01–0.02 R per trade on a 25-point stop.
- The TopstepX rule (no daily loss limit since 2024-08-25) was read through a search engine, because the help centre is blocked from the research container.
- The account model books realised R. A winning trade's dip toward the drawdown before it wins is not modelled. That flatters every stream similarly, and matters more when the cushion is thin.
