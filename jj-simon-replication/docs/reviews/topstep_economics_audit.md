# Independent audit: does Topstep's structure pay a zero-edge trader?

Run 2026-10-07 by an independent reviewer. It used no code of ours until its own simulator was written from the rules. The question: is the finding "the rules themselves have positive value for a zero-edge trader" (B4, B5, `research/run1_structure.md`) real, and how large is it? Asked by Chris before any money is spent.

## Verdict

**The finding is real, and our code computes it correctly, but it overstates the size by about 2–3×.**

- **Under our model's conventions** our code and the independent simulator agree within one Monte-Carlo standard error. On a zero-mean synthetic stream: +$91 / +$106 / +$111 at 60 / 120 / 250 days for ours, against +$90.5 / +$104.9 / +$109.1 for the independent one, with P(pass) 0.208 and about $900 paid per funded account in both.
- **With what we leave out,** a zero-edge trader makes about **+$35 to +$70 per evaluation**, not +$90 to +$160. The omissions:
  - intraday dips to the loss limit;
  - TopstepX's real micro fees;
  - a sealed-style 1.52 R target;
  - the Live call-up.
- **The margin is thin.** A further −0.05 R per trade, of edge, slippage or cost, removes it.

**The mechanism** was confirmed by an exact identity. With zero edge, expected gross payouts equal the loss the firm absorbs when it closes the account. 62% of funded accounts die before any payout, at an average balance of −$1,485. The trader holds a free put on the trailing loss limit. The payout fraction and cap hardly matter. The fees, the risk per trade, the call-up and costs per trade do.

## The rules, checked against Topstep as of October 2026

The checks were made through search-engine summaries of Topstep's help centre and 2026 third-party pages; the sites themselves are blocked from the container.

**Match the model:**
- the Combine at $49 a month, with a $3,000 target;
- the $2,000 end-of-day trailing limit, locking at the start;
- the 55% consistency rule;
- no daily loss limit on TopstepX;
- the $149 activation on the Standard path;
- the Express Funded Account's limit locking at $0;
- five winning days of $150 or more;
- payouts of 50% of profit, capped at $2,000, with a $125 minimum and a 90/10 split;
- the loss limit set to $0 after a payout;
- later payouts needing net profit since the last;
- no platform or data fee on TopstepX.

**Different:**
- **Micro fees.** TopstepX charges $1.22 per micro round trip, deducted from the balance since 12-Apr-2026. Ours charged $0.50.
- **Payout transfer.** $30 by ACH or wire; $0 by Wise, Aeropay or to Topstep's brokerage.
- **Purchases.** There is no Combine purchase limit (2 resets per account per day), not "20 a month". This has no effect at one account at a time.

**Not modelled:**
- **The scaling plan.** On a 50K Express Funded Account: 2 lots below a $1,500 balance, 3 from $1,500, 5 from $2,000. It binds only for stops under about 12.5 points traded in micros.
- **Inactivity closure** after 30 days.
- **Back2Funded:** $599 to reactivate an account lost before its first payout.
- **The Live call-up.** Discretionary, and it closes all Express Funded Accounts. Third parties say "typically about 5 payouts".

**Allowed.** One account at a time at fixed risk is not prohibited. Topstep's "account stacking" rule targets aggressive attempts that hit the loss limit, then switching accounts and repeating. The risks are Topstep's discretion (the call-up and payout review) and rule changes; there were four in 2026.

## The discrepancies in our model, and their effect on the zero-edge EV

1. **Intraday dips are not modelled (high).** The account is checked only on closed trades, but a winning trade can touch the loss limit first. This matters most right after a payout, when the cushion is under one stop-out. Effect: about −$37. Fix: fail the account on each trade's worst excursion, taken from the bar replay.
2. **Micro fees (medium).** Ours were $0.50 against $1.22 per round trip. Effect: about −$19 at 25-point stops, and −$40 to −$50 at 10-point stops.
3. **No Live call-up in B4 or the structure control (medium).** Effect: −$37 for a call-up at the 3rd payout with the Live account worth $0, and −$104 at the 1st. B5 has it.
4. **Lower:**
   - the scaling plan;
   - the $30 ACH transfer fee, avoidable;
   - the cap varying by pricing path (±$1);
   - our Combine trading on after its target, which is conservative (about +$13);
   - the split depending on Chris's join date: before 12-Jan-2026 the first $10,000 is paid at 100%.

## Sensitivities

Zero edge, our convention, 250 days, baseline +$107:

| Change | EV per evaluation |
|---|---|
| Activation fee $0 / $299 | +$138 / +$76 |
| Express Funded risk per trade $250 / $750 | +$52 / +$136 |
| Call-up after the 1st / 3rd / 5th payout, Live worth $0 | +$3 / +$70 / +$92 |
| Extra cost of 0.014 / 0.025 / 0.040 R per trade | +$88 / +$74 / +$56 |
| Intraday dips counted | +$70 |
| Edge of −0.041 / −0.08 / −0.12 R per trade | +$57 / +$24 / −$3 |

**Realistic combination:** the 1.52 R target, +0.014 R per trade of micro fees, and dips counted. That gives about +$68 at 250 days, and about +$49 with a call-up at the 3rd payout. It breaks even at about −0.05 R per trade.

**It vanishes if Topstep moves to any of:**
- an activation fee of about $660 or more;
- a monthly price of about $155 or more;
- a payout split of about 40% or less;
- a call-up after the first payout.

## What this means for S3 and S4

The same corrections apply to the streams with an edge. S3's and S4's development EVs (about +$210–$290 per evaluation at H 250) carry the same structural overstatement. Their edge's part (about +$110–$165) shrinks by the extra cost per trade.

Their realistic EV per evaluation therefore needs to be recomputed before any money is spent, with:
- TopstepX's micro fees;
- the trade's worst excursion against the loss limit;
- the call-up.

That is bounded follow-up work. It does not block the paper test.
