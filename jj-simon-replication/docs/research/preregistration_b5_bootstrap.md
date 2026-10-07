# Pre-registration: B5, the $2,000 bootstrap on replayed market paths

Registered 2026-10-07. The tool did not exist yet, B4 had not run on the real data, and no B5 number had been computed. The commit that adds this file is the registration. Any later change to it is a new registration and must say so.

B5 is an estimate, not a hypothesis test. What is fixed here: which configurations run, the mechanics, what is reported, and how the result will be read.

## Why

B3 ran the frozen bootstrap (`fpt.bootstrap.simulate_his_stats`) at each stream's measured rates and found no bust from $2,000 for S1, S3 and S4. That simulation is optimistic in four ways:

- Every account is an independent draw. Real accounts take the same signals on the same days.
- The evaluation fee is paid once, though Topstep bills it monthly.
- There is no activation fee.
- Payouts are gross, and each funded account pays once.

B4 measures what a funded account is worth over its life, with every fee and every payout. B5 asks what is left: starting with $2,000 of cash, on the market's real sequence of days, how often does the operation run out of money, and where is the cash after twelve months?

## Which configurations run

A configuration is a stream, a preset and size, and a payout policy, as B4's lifetime rows score them. The streams:
- B3's S0r and S1 to S4 (`research/lifetime.py`);
- S5 and S6, if the trend exit passes its registered test (`research/trend_exit.py`);
- H3's favoured-side streams (`research/h3_filter.py`).

B5 runs every configuration whose development lifetime EV per evaluation at H 250 is positive. If none is positive, B5 reports that and stops.

Each configuration runs twice:
- at its B4 size (fractional sizing, as B3 and B4);
- in whole micro contracts within the same budgets (as `research/candidates.whole_contracts`). This is what real money would trade.

Every configuration that runs is reported. None is dropped for its B5 result.

## Mechanics

**Paths**
- Each path uses the stream's own trading-day calendar, from its span start, and covers 365 calendar days.
- Development paths: every development trading day whose path ends on or before the cut is a start. The paths overlap, as in the walk-forward.
- Benchmark: one path from the first benchmark day, reported beside.

**Accounts**
- The Topstep 50K Trading Combine and Express Funded account, at the configuration's preset:
  - `topstep_50k_x`: TopstepX, no daily loss limit;
  - `topstep_50k`: the frozen preset.
- Evaluation sizing as B3: the two-trade posture, $1,000 of risk per trade.
- Funded sizing: $500 per trade.
- Both are scaled by the configuration's size, or in whole micros within those budgets.
- Funded accounts are `research.lifetime.LifetimeAccount`, with Topstep's Express Funded rules and the configuration's payout policy.
- Every live account takes all of the stream's trades of the day. Every account sees the same market.
- An evaluation still open after 30 trading days is abandoned. B3 counts the same case as not passed.

**Purchases**
- Before each trading day, at most one new evaluation is bought.
- A purchase needs cash of at least $49, and fewer live evaluations plus live Express Funded accounts than the cap. Counting both means a pass can always be activated.
- Two caps run:
  - 1: one account at a time;
  - 5: Topstep's limit on simultaneous Express Funded accounts.
- A failed evaluation is replaced by a new purchase, never a reset. Both cost the same.

**Fees**
- $49 at purchase, and again every 30 calendar days while the evaluation stays live.
- An evaluation whose monthly fee falls due when cash is short is cancelled.
- $149 activation on a pass.
- No other platform or data fee is charged. That is an assumption to check before any money is spent.

**Payouts**
- Credited net of the split, 5 trading days after the payout day. Topstep processes payouts in 1 to 3 business days, plus the transfer.

**Ruin**
- Cash below $49, with no live account and no payout pending.
- No income is taken out and no new money is added.

## Gates

Before anything is reported, on every configuration and period:
- Every evaluation's outcome (pass, fail or open at 30 days) equals the frozen pass walk-forward's outcome for its start day. That is `fpt.evaluate.walk_forward_pass_probability`, at the same rules, risk, sizing and calendar.
- Every Express Funded account's first-payout outcome within 60 days equals the frozen payout walk-forward's, for the day after its pass.
- B4's own gate holds.

## Reported, per configuration, sizing, cap and period

- **Ruin:** P(ruin within 12 months) and the median day of ruin.
- **Cash at 12 months**, payouts pending included:
  - the mean and the 10th, 25th, 50th, 75th and 90th percentiles;
  - P(above $2,000) and P(above $4,000).
- **Money at risk:** the deepest fall of cash below $2,000, as a median and a 90th percentile.
- **Activity, as means:** evaluations bought, passes, Express Funded accounts breached, payouts, total fees and total payouts.
- **First payout:** its median day, and the share of paths without one.
- **Effective sample:** the number of non-overlapping years of development data behind the paths.
- **Comparison:** beside each stream, the frozen bootstrap's row from B3 at $2,000.

## How it will be read

B5 is a feasibility check on development paths. It confirms nothing.

A configuration goes on to a forward test only if all three of these hold on development paths, in whole micros, at either cap:
- P(ruin within 12 months) is at most 10%.
- The median cash at 12 months is above $2,000.
- The 25th percentile of cash at 12 months is at least $1,000.

The benchmark path is reported beside and decides nothing. Clean proof comes only from data after 2026-10-05.

## Caveats, stated now

- The candidates are the best of many configurations on development data, so their development numbers are biased upward.
- Overlapping paths share most of their days. Development covers about a dozen independent years.
- Topstep may move an Express Funded trader to a Live account. B5 does not model this, and neither does B4.
- TopstepX's lack of a daily loss limit dates from 2024-08-25. Earlier paths apply today's rules to past markets.

## Clarifications, 2026-10-07, before any B5 number

These were written while building the tool on synthetic data, before B5 had touched real data. They settle four points the text left open; nothing else changes.

1. **The funded gate under "wait".** The frozen payout walk-forward has no wait policy. Under "wait", each Express Funded account's first payout is therefore compared with B4's walk-forward of the same policy (`research.lifetime.walk_forward_lifetime`). That walk-forward is itself checked against a one-account scalar reference. Under "ask" the gate is the frozen walk-forward, as registered.
2. **A pass that cash cannot activate.** If cash is below $149 at a pass, the account is not activated and the pass is lost. It is counted and reported as a lost pass. Cash never goes below zero.
3. **The end of a path.** On the path's last day, accounts still live are cut off: their balances are not cash and count for nothing. Payouts already earned but not yet credited count in the final cash. Cut-off accounts are left out of the gates.
4. **Days.** The payout delay and the 30-day limit on an evaluation count the stream's own trading days (New York dates with bars, as every walk-forward here). The monthly fee and the path's 365 days count calendar days.

## Clarifications, 2026-10-07 (second), before any B5 number

Prompted by the independent review of the tool on synthetic data. B5 has still not touched real data. Nothing else changes.

5. **Whole micros run on TopstepX only.** The frozen `topstep_50k` preset's soft daily loss limit is not usable below the sealed sizing (`docs/ASSUMPTIONS.md` row 39). It cuts a loss that carries the day past the limit to the room left, but credits a win in full. Whole micros size below 1.00, so on that preset they would carry the artifact into the decisive reading. On synthetic data it turned failing configurations into qualifying ones. New Combines are also TopstepX only.
   - For every stream and payout policy with a selected configuration on any preset, the whole-micro runs are on `topstep_50k_x`, and the reading uses those.
   - A selected `topstep_50k` configuration runs at its B4 size only. It is reported for the record and decides nothing.
6. **H3's streams** run when H3 passes its registered test on the inputs. It did on the registered run (Holm p 0.047).
7. **Not modelled: Topstep's limit of 20 account purchases a month.** See `docs/research/prop-firm-rules.md`. At cap 5 it binds on part of the paths. In the review's probe on synthetic data, enforcing it moved P(ruin) by under one point and left the cash percentiles unchanged. The report states it as a caveat.
8. **The frozen bootstrap beside each row** is computed on that period's own B3 row: development beside development, benchmark beside benchmark. The full row is printed: P(bust), the median days to the first payout, and the funded accounts at month 12.
9. **A period in which no trade fits one phase's budget** still runs. That phase's account then never trades: an evaluation stays open, and an Express Funded account pays nothing. The gates compare with that phase's walk-forward on an empty stream, where every start with the full horizon is open. Both phases share one calendar.

## Amendment, 2026-10-07: the call-up to a Live account (a change, before any B5 number)

This is a change to the registration, not a clarification. It was made after B4 had run and before B5 had run on any real data. It was prompted by a rule found after the registration was written.

**The rule.** Topstep's risk team calls an Express Funded trader up to a Live Funded Account at its discretion, typically between the trader's 3rd and 5th Express Funded payout. At the call-up every Express Funded account closes. Their combined balances move into the Live account: 20% available, at least $10,000, and 80% held in a reserve released at profit thresholds. Daily payouts unlock after 30 winning days. Sources: Topstep's Live Funded Account pages, read through a search engine because the help centre is blocked from the research container; third-party guides agree.

**Why it matters here.** The registered paths keep up to five Express Funded accounts paying for twelve months. Once payouts accumulate, a real operation would not get that.

10. **The call-up as a lower bound.** Every run is repeated with a call-up at the path's 3rd payout request, counted across all of its accounts. That is the early end of the typical range, so the more conservative choice.
    - At the end of that day every account of the path closes, Combines included, and nothing more is bought.
    - The path's final cash is its cash plus the payouts already requested.
    - The Live account counts for nothing. That understates the truth: a Live account's losses are the firm's, and it can pay.
    - Accounts closed by the call-up are left out of the gates, as cut-off accounts are.
    - Reported per run: the share of paths called up within the 12 months, and the median day of the call-up.
11. **The reading** now requires both versions. A configuration goes on to a forward test only if, on development paths in whole micros on TopstepX, at one cap, the registered thresholds hold both without a call-up and with the call-up at the 3rd payout:
    - P(ruin within 12 months) at most 10%;
    - median final cash above $2,000;
    - its 25th percentile at least $1,000.

    One that qualifies only without the call-up is reported as depending on the Live account's value, and is not carried forward on this evidence.
