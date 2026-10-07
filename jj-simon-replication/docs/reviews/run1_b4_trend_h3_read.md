# Read: B4 (lifetime value), the trend exit, and H3 through firm scoring

Runs on the GB10 at b6a7732; results in `research/run1_b4_lifetime.md` (sha256 26d5d2b6…), `research/run1_trend_exit.md` (38120983…) and `research/run1_h3.md` (1f01445c…), pushed in 59578b6 after Chris authorized it. Every gate passed: B3's eight sealed firm rows reproduced, every first payout equal to the frozen walk-forward's, both registrations at their pinned hashes, and the trend replay equal to B2's wherever B2's target never filled (37,753 pairs). Development is 2010-06 to 2025-10-05; the benchmark year is beside and chose nothing.

## 1. B4: with every payout and fee, every stream is positive in development, the losing baseline included

Development lifetime EV per evaluation at H 250 (about 42 weeks), net of the evaluation's monthly fees and the activation fee, with the benchmark year beside:

| stream | R per trade, development | TopstepX 0.95, ask | TopstepX 0.95, wait | frozen topstep_50k 1.00, ask | benchmark, TopstepX 0.95 ask / wait |
|---|---|---|---|---|---|
| S0r sealed brackets | −0.041 | +43 | +49 | +35 | −39 / −39 |
| S1 continuation, sealed bracket | +0.013 | +148 | +182 | +142 | +441 / +707 |
| S2 S1 + A+ reversion | +0.001 | +108 | +130 | +106 | +107 / +113 |
| S3 continuation, walk-forward ATR | +0.042 | +246 | +293 | +232 | +85 / +53 |
| S4 S3 + A+ reversion | +0.044 | +236 | +274 | +209 | +147 / +268 |

What carries these numbers:

- **The first payout is a small part.** For S4 at TopstepX 0.95, the first payout alone is worth +$26 per evaluation; every payout by H 250 is worth +$236. Under Topstep's rules a payout moves the loss limit to the starting balance. Half the profit stays in the account as its cushion, and a later payout needs net profit since the previous one.
- **Almost every funded account dies.** P(breach by 250) is 99.9–100% for every stream in development. An account pays what it pays and then breaches, and most of its value comes within 120 days.
- **S0r is the warning.** Its trades lose 0.041 R on average, yet its development EV is +$35 to +$49 per evaluation. A funded account's loss is capped by the firm's drawdown, while half of every upswing can be withdrawn. A trader with no edge, or a small negative one, is therefore paid by the structure itself. On a synthetic pattern with its edge removed, the model pays about +$66 per evaluation.
- **Where the edge shows.** Mostly in P(pass): 18–20% for S0r against 29–33% for S3 and S4. It also shows in the size of the upswings. The benchmark year shows the cost of a weak year: S0r's pass rate falls to 8–9% and its EV to −$39.

How much of each stream's EV is the structure and how much the edge is now measured directly. `research/structure_control.py` (f28fb72) shifts each stream's R by its development mean and reruns B4 on the copy with zero edge. It runs on the GB10 with B5.

What this rests on:
- **Topstep's rules being modelled right.** Checked against 2026 sources: on the Standard path a 50K Express Funded account pays 50% of profit up to $2,000 a request, after five winning days of at least $150, at a 90/10 split, with the loss limit reset to the starting balance after a payout. Topstep lowered some caps in April 2026, so the rules can move against this.
- **The move to a live account.** Topstep moves Express Funded traders to a live account after about 30 winning days. That is not modelled, so long horizons overstate.
- **Payout policy.** Waiting for the loss limit to reach the starting balance (Topstep's advice) beats asking at once in development for every stream at H 250.

## 2. The trend exit fails its registered test

- **The test.** The paired difference per entry, trend exit minus S3, is +0.0002 R (standard error 0.0138), one-sided p 0.49, positive in 7 of 13 chain years. The rule needed p < 0.05 and 60% of years.
- **Same expectancy as S3.** The trend exit makes +0.047 R per trade against S3's +0.047.
- **But worse under the firm's rules.** Without a target its outcomes are more spread out: 68% of its development trades end flat at 16:00. Its P(pass) on the frozen preset falls from 31.8% (S3 on the same span) to 24.0%, and its first-payout EV from +$13 to −$19.

Per the registration, S5 and S6 are reported once and dropped. A finer point is that a strategy's value to a prop account is not only its R per trade: for the same expectancy, a fixed target that passes evaluations quickly is worth more.

## 3. H3 passes its test and improves the streams in development; the benchmark year is mixed

H3 (continuation after an opening candle at least the walk-forward median of its body over ATR) passed its registered test: +0.101 R, Holm p 0.047, 11 of 15 years. Each stream is scored from 2011, where H3 is defined, on its favoured side against all continuation entries where H3 is defined.

| stream | development lifetime EV, TopstepX 0.95, H 250, ask / wait: all → favoured | benchmark, same: all → favoured | whole micros, first payout only, development: all → favoured | benchmark: all → favoured |
|---|---|---|---|---|
| S1 | +159 / +197 → +183 / +270 | +441 / +707 → +236 / +284 | −10 → −12 | +65 → +23 |
| S3 | +263 / +315 → +335 / +438 | +85 / +53 → +106 / +109 | −5 → +16 | −30 → −46 |
| S4 | +252 / +295 → +354 / +435 | +147 / +268 → +202 / +230 | −1 → +18 | +15 → +34 |

- **Development.** The favoured side raises the lifetime EV of all three streams, by roughly a third to a half for S3 and S4. It does so while trading on only about 60% of the days.
- **Benchmark year.** It helps S4 under "ask" and S3 slightly, and hurts S1 sharply.
- **Next step, by its registration.** H3 is re-simulated on the research engine: the ledger replay cannot add the entries the frozen engine skipped while a position was open.

## 4. What follows

- **B5**, the $2,000 bootstrap on replayed market paths, is pre-registered (df2bc28, clarified 1995b2c) and under independent review.
  - Its candidates are every configuration with positive development lifetime EV at H 250. By the tables above that is every stream, the losing baseline included, plus H3's favoured side.
  - Its reading rule is fixed: in whole micros, P(ruin within 12 months) at most 10%, median cash after 12 months above $2,000, and its 25th percentile at least $1,000.
- **The structure control** runs alongside B5.
- **Forward data.** Forward data cannot confirm edges of +0.04 R per trade in any practical time: at about 220 trades a year, a year of data pins the mean to roughly ±0.09 R. It can confirm that live fills match the replay and catch a gross failure. Whether this is worth money rests on the development evidence, the firm's rules holding, and how much loss is acceptable. B5 measures that loss.
