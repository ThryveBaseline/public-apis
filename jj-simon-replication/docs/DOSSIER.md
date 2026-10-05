# JJ Simon: Fair Pricing Theory, risk model and multi-account prop-firm operation

A replication dossier. Everything below is reconstructed from public
material: JJ Simon's own videos and landing pages (marked **JJ**), podcast
appearances, and third-party codifications and backtests (marked **3rd**).
Where sources disagree, both versions are shown. Nothing here is affiliated
with or endorsed by JJ Simon. Section 10 lists what is still unverified.

Evidence files: `docs/research/EVIDENCE.md` (merged, deduplicated facts
with URLs), `docs/research/*.md` (per-angle reports), `docs/research/sources.csv`.

## 1. Who he is (professional profile)

| Item | What the sources say | Status |
|---|---|---|
| Name, handles | JJ Simon; YouTube `@itsjjsimon`, X `@itsjjsimon`; sites jjsimontrades.com, jjwebinar.com | **JJ** |
| Credential | Quantitative finance degree, University of Washington ([channel / schedule-call page](https://jj.jjsimontrades.com/schedule-call)) | **JJ** |
| Experience | "full-time futures trader with 16 months of experience" at the $1.5M mark ([$1.6M video transcript summary](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)) | **JJ** |
| Payout claims over time | $1.3M, $1.5M ("over $1,500,000 in verified prop firm payouts across E8, Topstep, Tradeify and more", [jjwebinar.com](https://jjwebinar.com/)), $1.6M, $1.8M, $1.9M ([video HlWSP7ajgpQ](https://www.youtube.com/watch?v=HlWSP7ajgpQ)), $2,000,000+ ([schedule-call page](https://jj.jjsimontrades.com/schedule-call)) | **JJ**; figures rise with time and differ by platform bio |
| Payouts by firm (his $1.6M breakdown) | Topstep ~$292,000; E8 ~$222,000; Funded Engineer ~$180,000; MyFundedFutures ~$92,000 ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)); a third-party summary attributes ~$129,500 to Funded Next; Tradeify, Lucid, Alpha Futures, Bulwark also named | **JJ** / **3rd** |
| Business | Mentorship (NQ execution structure, risk management, funded-account consistency, trade recaps, psychology, mean reversion, fair pricing theory; AllPros rating 4.6/5, [allpros.io](https://allpros.io/course/jjs-mentorship)); free webinar funnel ([jjwebinar.com](https://jjwebinar.com/)); Discord | **3rd** (review site) |
| Appearances | Chart Fanatics podcast: "This Kid Printed $2M In Payouts Trading 30 Times/Day" ([-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg)); "The Genius Who Outsmarted The Prop Firm Game, And Made $1.5M In Payouts" ([aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8)); "Leap in with Captain Green Podcast" ([PCDHJBdj-Z4](https://www.youtube.com/watch?v=PCDHJBdj-Z4)); Titans of Tomorrow; Words of Rizdom | **3rd** |

## 2. The Fair Pricing Theory model

**Premise (JJ).** When the market has no new information to price in,
price is likely to revert toward a reference level he calls fair value /
fair price. For NQ the reference is the price at the 09:30 ET cash open:
"the price of a single candle right before the NASDAQ opens, the pre-open
price, before institutional volume hits" ([transcript summary](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)).
A second anchor is the 14:00 ET price for the afternoon
([fxreplay codification](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy)).
He has said the open is fair price in roughly 95% of cases; his mentorship
has separate "understanding fair price" and "identifying fair price"
modules plus VWAP and volume-analysis modules for the rest (3rd-party
course listings; the exact alternates are not public).

**Window (JJ).** 09:30 to 11:00 ET, "a 90-minute window"; an afternoon
session 14:00-15:00 in earlier videos; videos from September 2026
("$400,000 in 90 Days") add 18:00 and 20:00 sessions that no public
codification covers yet.

**Two phases.**

| Phase | JJ's own description | fxreplay / AndrewFXTD codification |
|---|---|---|
| Continuation | only the first ~5 minutes: trade with the opening push away from fair price | "first 10-15 minutes"; fxreplay's optimisation also skips the first 3 minutes |
| Reversion | the remaining ~85 minutes to 11:00: trade back to fair price | same, but fxreplay's filtered test keeps only reversions in the first ~30 minutes and avoids 10:00-11:00 |

**Premium / discount band.** joetroyer's TradingView indicator draws a
+/-38-point band around the fair line and fades price back to the line
after a displacement candle closes back toward it ("sell above, buy below",
[indicator page](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/)).
No statement by JJ of a fixed band has been found; treat 38 as the
indicator author's choice (`require_band_touch=False` by default).

**A caveat in his own words.** On TikTok he has said the simplest
continuation model outperformed the simplest mean-reversion model over the
last five years, even though his flagship method is reversion to fair
price. Read with Section 8: the third-party tests found reversions the
stronger half of his rules in the first 30 minutes and weak after 10:00.

## 3. Entry rules

| Rule | Detail | Status |
|---|---|---|
| Chart | NQ, 1-minute | **JJ** |
| Trigger | a Market Structure Break (MSB) or Break of Structure (BOS) confirmed by a strong displacement candle | **JJ** via fxreplay |
| Displacement candle | closes decisively; counter-wick less than 20% of the distance from the candle's open to the counter-wick extreme | **3rd** (fxreplay wording of his rule) |
| Setup grades | A+ = break of structure; A = displacement; B = avoid | **JJ** ([transcript summary](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)) |
| Direction, continuation | with the opening push, away from fair value | **JJ** |
| Direction, reversion | back toward fair value from premium (short) or discount (long) | **JJ** |
| Cadence | "around 10 trades per day" in the $1.6M video; 20 (Titans of Tomorrow), 20+ (Words of Rizdom), 30 (Chart Fanatics title) in later appearances | **JJ**, varies |
| Management | none: fixed target, no partials | **JJ** via fxreplay |
| Entry timing | on the displacement close (code: next bar open) | **JJ**; fill timing is an assumption |

Unpublished and therefore assumptions in the code (see `ASSUMPTIONS.md`):
the swing definition behind BOS/MSB (the commercial indicator pack offers
"wick-based or rolling" BOS, which shows the ambiguity), a size threshold
for "strong" displacement, whether grade-A entries are taken, one position
at a time, and whether open trades are flattened at 11:00.

## 4. Risk model

| Rule | Detail | Status |
|---|---|---|
| Stop by volatility | 1-minute ATR above 20: 50-point stop; 7-20: 25-point stop; below 7: 16.5-point stop | **3rd** (fxreplay codification) |
| Size by tier | 1 / 2 / 3 NQ contracts respectively, so every tier risks about $1,000 (NQ = $20/point) | **3rd** (fxreplay) |
| Target | 1.5R fixed | **JJ** via fxreplay |
| Losing weeks | "optimal risk management to ensure payouts even during losing weeks by adjusting contract size and stop loss based on candle size and market volatility" | **JJ** (transcript summary) |
| ATR period | not published; code uses Wilder 14 | assumption |

**The arithmetic the method rests on.** At the third-party-measured 52-54%
win rate and 1.5R the expectancy is +0.3 to +0.35R per qualifying trade;
the breakeven win rate is 40%. Full Kelly on the drawdown allowance is
about 23%; $1,000 on a $3,000 Topstep drawdown is 33%, i.e. more than
Kelly, which is why his operation needs many accounts rather than one.
`python -m fpt.cli edge` reproduces these numbers; `python -m fpt.cli
evaluation` shows the pass-probability curve versus fixed risk per trade
(it peaks near 25-30% of the drawdown for a 54% / 1.5R edge at 1.5
qualifying trades a day).

**Calibration warning.** Ten trades a day at 54% / 1.5R would be +3.5R per
account per day. His own reported results imply far less: "$105,700 in 3
weeks" across ~40 accounts is about $176 per account per trading day,
~0.18R at $1,000 risk, which matches the third-party backtests (about one
qualifying trade per day, Section 8). The simulators therefore default to
1.5 qualifying trades per day.

## 5. Multi-account operation

| Item | What the sources say | Status |
|---|---|---|
| Account count | 20-30 (his X posts), 40 ("if JJ has 40 accounts", transcript), "45+" (Chart Fanatics blurb) | **JJ**, grows over time |
| Firms | Topstep, E8, Funded Engineer, MyFundedFutures, Tradeify, plus Lucid, Alpha Futures, Bulwark, Funded Next in some sources | **JJ** / **3rd** |
| Why many accounts | "being able to get through so many accounts and diversify risk across all of them thanks to fair pricing theory"; "different prop firm accounts used depending on market conditions" | **JJ** (transcript summary) |
| Why prop firms | "prop firms offer more profitability due to their evaluation rules, drawdown limits, and profit targets"; an aggressive high-frequency NY-session method with risk tailored to prop-firm rules | **JJ** |
| Income target | "$100,000 per month on prop firms" (video title) | **JJ** |
| Execution stack | copier tooling not confirmed in public sources (TopstepX copier, Tradovate group trading, Replikanto, Tradecopia are the candidates) | unverified |

`fpt/portfolio.py` reproduces the economics: identical signals copied to N
accounts, each under its firm's rules, with evaluation fees, resets,
activation fees, consistency gates, payout caps and monthly cadence. With
45 accounts (20 Topstep 100k, 15 Tradeify Select 100k, 10 MFFU 100k),
$1,000 risk, 54% / 1.5R and 1.5 qualifying trades a day, the six-month
median net cash is in the $800k range (about $90k a month once accounts are
funded) with a 5th percentile near +$60k, and about 95 account breaches per
simulated run, i.e. roughly two breaches per account per six months. The
firm presets are templates (`verified=False`) until Section 9 is confirmed.

## 6. Stop-trading rules and discipline

Published statements are qualitative ("knowing exactly when to stop
trading", Chart Fanatics blurb; losing weeks handled by sizing). The
reconstruction used in the code:

* **Time stop**: the window ends at 11:00 (and 15:00 for the afternoon session).
* **Statistical daily stop**: the loss at which the day has fallen outside what the edge statistically produces. For 54% / 1.5R and 1.5 qualifying trades a day the 5th-percentile day is about -2R (-$2,000 at $1,000 risk); for 10 trades a day it is about -3R. `python -m fpt.cli edge` prints it for any parameters.
* **Streak stop**: over 200 trades at 54% the median longest losing streak is 6 and the 99th percentile 12; a stop after N consecutive losses should be set from these quantiles, not from feel (`risk.losing_streak_quantiles`).
* **Trade-count stop**: max trades per day (10 by his own statement).

Section 10 lists what the research sessions were asked to pin down from
his own words.

## 7. Reported results timeline

| When (approx.) | Claim | Source |
|---|---|---|
| ~12-13 months in | $1.2M payouts | third-party summary |
| mid-2026 | $1.5M, "16 months of experience"; "Road to $1M" series goal: $1.5M to $2.5M | [Road to $1M Ep. 2 summary](https://sozai.app/transcript/made-105700-3-weeks-day-trading-nq-futures/) |
| Ep. 2 | $105,700 in 3 weeks of NQ trading across his accounts | same |
| 2026 | $1.6M (video: "The Strategy Behind My $1.6M in Prop Firm Payouts") | [transcript](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) |
| 2026 | $1.9M ("I Hit $1.9M In Prop Firm Payouts (My Trades This Week LIVE)") | [HlWSP7ajgpQ](https://www.youtube.com/watch?v=HlWSP7ajgpQ) |
| Sept 2026 | "$400,000 in 90 Days" (adds 18:00 / 20:00 sessions) | his channel |
| 2026 | $2,000,000+ | [schedule-call page](https://jj.jjsimontrades.com/schedule-call) |

## 8. Independent backtests and critiques

| Study | Rules coded | Result | Notes |
|---|---|---|---|
| fxreplay, "Fair Value Theory NQ Strategy Backtesting Reimagined" ([page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy), [PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf)) | 09:30 and 14:00 anchors; continuation first 10-15 min, reversion after; MSB/BOS + displacement (<20% counter-wick); ATR tiers 50/25/16.5 with 1/2/3 contracts; 1.5R | 158 trades, 54% win rate, PF 1.76, max streaks 8 wins / 5 losses; another pass: 150 trades, +46R, 52%, PF 1.66 before filters | filters that helped: skip first 3 minutes for continuations; reversions only in the first ~30 minutes; avoid 10:00-11:00 |
| 365-day custom-indicator backtest ([transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/)) | same family, coded as an indicator | 289 trades in a year, +$48,700 on 100k (49%), PF 1.7 | about 1.2 trades a day |
| "Backtesting JJ Simon's NQ Strategy" ([SNO1wqJTq5A](https://www.youtube.com/watch?v=SNO1wqJTq5A), [summary](https://youtubesummary.com/summary/SNO1wqJTq5A)) | 1-minute scalp: fair value, BOS/MSB, displacement, ATR risk | see research files | |
| "JJ Simon Strategy Backtest: 40 Trades" ([c61c4CxTpYI](https://www.youtube.com/watch?v=c61c4CxTpYI)) | small sample | see research files | |
| "Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?" ([JcW8Wjnw8ck](https://www.youtube.com/watch?v=JcW8Wjnw8ck)) | forward test on an evaluation | see research files | |
| TradingView indicators: joetroyer ([link](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/)), AndrewFXTD ([link](https://www.tradingview.com/script/jfW4Vilk/)) | joetroyer: fair line anchored at session open with six selectable sources, +/-38-point band, displacement back toward the line; AndrewFXTD: sessions + fib, states "$1 per point" which is wrong for NQ ($20) | | |

Critiques to weigh: these are small samples (150-290 trades), sensitive to
the continuation window and to fills on 16.5-point stops with 3 contracts;
prop-firm payouts are gross of evaluation and reset spend; and the 10-30
trades-a-day cadence in his videos is not what the codified rules generate.

## 9. Prop-firm rule parameters

Templates live in `fpt/propfirm.py` (`FIRM_PRESETS`); `docs/research/firm_rules.json`
carries the researched values with URLs and dates once delivered. Confirm
every number on the firm's site before trusting a simulation: targets,
drawdown type and lock, daily loss limits, consistency %, payout minimum
days, caps and splits, copier policy and maximum accounts per person.

## 10. Contradictions, unknowns and verification status

Contradictions found so far:
1. Continuation phase length: ~5 minutes (JJ) vs 10-15 minutes (fxreplay, AndrewFXTD).
2. Reversion window: full 85 minutes to 11:00 (JJ) vs first ~30 minutes only (fxreplay's filtered result).
3. Fair value anchor: 09:30 open (fxreplay, AndrewFXTD) vs the candle right before the open (365-day backtester) vs six selectable sources (joetroyer).
4. Trades per day: 10 (JJ, $1.6M video) vs 20-30 (later appearances) vs ~1.2 qualifying (365-day backtest).
5. Account count: 20-30 vs 40 vs 45+.
6. Payout totals: every platform bio shows a different figure ($1.3M to $2M+), consistent with growth over time but not pinned to dates.
7. fxreplay statistics: 158 / 54% / PF 1.76 vs 150 / 52% / PF 1.66 (different passes of one study).
8. Firm naming: Funded Engineer (JJ) vs Funded Next (third-party summary).

Unknowns being researched (results land in `docs/research/`): the exact
BOS/MSB and displacement definitions in his own words; the ATR period; the
copier stack and per-firm account counts; his explicit daily stop and
consecutive-loss rules; the Chart Fanatics episode's statistics; current
firm rules.

## 11. Sources

Primary (JJ): his YouTube channel ([@itsjjsimon](https://www.youtube.com/@itsjjsimon)); [jjwebinar.com](https://jjwebinar.com/); [jj.jjsimontrades.com/schedule-call](https://jj.jjsimontrades.com/schedule-call); transcripts of "The Strategy Behind My $1.6M in Prop Firm Payouts", "Here's How You Can Make $100,000 Per Month On Prop Firms", "I Made $105,700 in 3 Weeks Day Trading NQ Futures (Road to $1M Ep. 2)" on [sozai.app](https://sozai.app/).
Podcasts: Chart Fanatics ([-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg), [chartfanatics.com](https://www.chartfanatics.com/)); [aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8); [PCDHJBdj-Z4](https://www.youtube.com/watch?v=PCDHJBdj-Z4).
Third-party tests and codifications: [fxreplay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) and [PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf); [365-day backtest transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); [youtubesummary.com](https://youtubesummary.com/summary/SNO1wqJTq5A); TradingView [joetroyer](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/) and [AndrewFXTD](https://www.tradingview.com/script/jfW4Vilk/).
Reviews: [allpros.io](https://allpros.io/course/jjs-mentorship).
Full list: `docs/research/sources.csv`.
