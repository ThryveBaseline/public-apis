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
| Payouts by firm (his $1.6M breakdown) | Topstep ~$292,000; E8 ~$222,000; Funded Engineer ~$180,000; MyFundedFutures ~$92,000; Bulwark ~$55,000; Apex ~$60,000 ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)); a third-party summary attributes ~$129,500 to Funded Next; Tradeify, Lucid, Alpha Futures also named | **JJ** / **3rd** |
| Business | Mentorship operated by SIMON FUND LLC (entry model, trade recaps, risk-management dashboard, weekly 1-on-1 calls; price behind an application funnel; curriculum lists continuation and mean-reversion specifics, understanding and identifying fair price, expected value and variance, risk of ruin and bankroll management, prop-firm math, volume by session, VWAP, news days); Whop listing 4.9/5 from 46 reviews with 6,125 members; AllPros 4.6/5 from 5 reviews ([allpros.io](https://allpros.io/course/jjs-mentorship)); a $299.99 pre-recorded workshop; free mini-course and Discord; webinar funnel ([jjwebinar.com](https://jjwebinar.com/)); the free PropFirmEV calculator | **JJ** / **3rd** |
| Audience | about 32,800 YouTube subscribers, 17K Instagram, 18.1K TikTok (Oct 2026) | platform counts |
| Credential detail | LinkedIn: University of Washington; built options-pricing software (Black-Scholes and Cox-Ross-Rubinstein) as a student project | **JJ** |
| Appearances | Chart Fanatics (host Riz Iqbal): "This Kid Printed $2M In Payouts Trading 30 Times/Day, Here's How." ([-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg), uploaded 2026-09-18; no transcript is indexed anywhere, so "45+ accounts" and "30 times/day" exist only in its title and description); Titans of Tomorrow (host Waqar Asim), "The Genius Who Outsmarted The Prop Firm Game, And Made $1.5M In Payouts" / audio title "Quant Finance Graduate Reveals His $1.5M Prop Firm Strategy" ([aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8), 2026-06-22; chapters "Why High Risk-Reward Fails Evaluations" 7:23, "Taking 20 Trades A Day Without Tilting" 12:01, "JJ's Mean Reversion Trading Model" 16:00, "His Session Open Strategy Explained" 20:07); Words of Rizdom (Riz Iqbal's audio podcast; billed "$1.8+ Million in Payouts in JUST 18 Months", "20+ scalps a day", "3 fixed simple strategies", trades live on the episode). Not him: the "Leap in with Captain Green" podcast's JJ Simon is a Singapore environment official; the Trading Nut "JJ" and the Business Insider "Kane Simons" are other people. | **3rd** |

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

In his own words "the fair price is 95% of the time going to be the market
open" and "fair price again at the 9:30 a.m. open" ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/));
on news releases: "The spike off the number is the unfair move, fade it
back to fair price" ([X](https://x.com/itsjjsimon)). The FX Replay PDF adds
that "the best setups require displacement + break of structure on the
same candle", that mean reversions alone ran PF ~1.46 with 49-59% win rate
depending on filter, and that continuations had the higher win rate and
profit factor. Other codifiers anchor differently: krisskross18's
TradingView script uses the 09:29 candle open; the 365-day backtester
"the candle right before the NASDAQ opens"; joetroyer offers six sources.

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

Additional detail from the `entries` research angle (44 facts): the MSB is a
**close** past the wick high/low of the recent price leg (AndrewFXTD's
codification), BOS is the same test with the trend; the mechanical
displacement rule is only the wick test, measured with a fib set to
0 / 0.2 / 1, and candle size relative to its neighbours is "discretionary,
optional"; entries are market orders after the displacement close; he says
"aim to only take A+ setups" but also that on prop firms he takes
"literally any displacement entry seen towards fair price" to scale;
fxreplay's filtered variant (skip the first 3 minutes for continuations,
reversions only in the first ~30 minutes, avoid 10:00-11:00 and
15:00-16:00) reported about 62% win rate and PF 2.46; joetroyer's
continuation variant waits for a retrace to the fair line instead of
entering on the displacement close; a September 2026 video covers the
18:00 and 20:00 sessions ([GMDUiamqgig](https://www.youtube.com/watch?v=GMDUiamqgig)).

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

**His own reasoning for 1.5R (JJ, `risk-model` angle, 38 facts).**
Evaluations are "minus 2K max loss and plus 3K profit target, making it
automatically optimal to do a one to 1.5"; trading in 1:1.5 units raises
the pass rate "based on how the drawdown trails"; break-even is 40%; his
sample ran 57.5%. Posture: "aggressive risk to get funded and then
conservative risk management to stay funded"; "on the eval, optimize for
your pass rate; on the funded, maximize your expected value: probability
of getting a payout multiplied by how large that payout is". Sizing
exception: "when opening candles are larger than 25 points, he cuts the
size in half" and uses the 50-point stop. The business math he teaches:
cost to funded = fee / pass rate ($100 / 0.30 = $333); cost per dollar of
drawdown = fee / drawdown ($750 for $4,500); EV of an evaluation =
P(payout) x payout - P(no payout) x fee (10% x $2,000 - 90% x $100 =
+$110); "the optimal profit target on his accounts was $1,800 per day";
about 40 accounts "where all of your accounts end the day traded" is six
figures a month; he says he spent $550,000 on evaluations learning this.
Variance he reports: -$21,000 over seven days inside a +$48K month with a
$45K payout. `python -m fpt.cli evalmath` reproduces the arithmetic.

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
| Routing | "one account at a time and one trade per account per day"; evaluations: max risk, target in exactly two trades; funded: risk "coming right down" | **JJ** ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/), [jjwebinar.com](https://jjwebinar.com/)) |

`fpt/portfolio.py` reproduces the economics: identical signals copied to N
accounts, each under its firm's rules, with evaluation fees, resets,
activation fees, consistency gates, payout caps and monthly cadence. With
45 accounts (20 Topstep 100k, 15 Tradeify Select 100k, 10 MFFU 100k),
$1,000 risk, 54% / 1.5R and 1.5 qualifying trades a day, the six-month
median net cash is in the $800k range (about $90k a month once accounts are
funded) with a 5th percentile near +$60k, and about 95 account breaches per
simulated run, i.e. roughly two breaches per account per six months. The
firm presets are templates (`verified=False`) until Section 9 is confirmed.

**Operation details from the `accounts` angle (34 facts).** Payouts by
firm from his $1.6M breakdown: Topstep ~$292,000; E8 $222,122 (the one
firm-issued "Certificate of Performance" found); Funded Engineer ~$180,000
(a dashboard showing 48 payouts, $179,938, largest single payout $46,433 in
April 2026); Funded Next $129,500; Lucid ~$105,000; MyFundedFutures
~$92,000; Alpha Futures ~$75,000; Apex ~$60,000; Bulwark Prime ~$55,000.
Routine: "trade each account one at a time and get through all of his
accounts every day, though he sometimes copy trades two together"; "you
should not copy trade until you're making like 20k"; once funded "he
cycles one trade across multiple funded accounts"; a conservative
evaluation uses "a minimum of two trades, but most likely four". He buys
evaluations in bulk ("160 evals for 250 bucks each"), says he has spent
$550,000 on evaluations in total, and argues that "one trade a day ...
22 trades a month ... approximately 3K a month" cannot reach $100k, which
is why the account count matters more than the edge. He risks
"different on separate firms and accounts" and says his real edge is
"understanding the prop firms and having a different risk strategy per
prop firm", adding that the method is "optimized for prop firms and less
effective on live accounts". He has published a calculator, PropFirmEV,
that replays a trader's statistics through each firm's rulebook thousands
of times at one trade per day; `fpt/portfolio.py` is the same idea.
Monthly examples from his posts: a $48K month with a $45K payout; four
June payouts totalling $25,000; a record-month target of $90,000. He also
says he picks which account takes a given setup "based on the market
displacement and points away from fair price", and sizes by "max EV then
mess with variance, but keep variance low to start". His cost-per-drawdown
rule of thumb: above about $0.50 of fee per $1 of drawdown a firm is
"generally not profitable" to use. Note the arithmetic gap: the per-firm
figures he lists ($292K + ~$50K old Topstep dashboard + $222K + $180K +
$129.5K + $105K + $92K + $75K + $60K + $55K) sum to roughly $1.26M against
the $1.6M headline of the same video; the remainder is unexplained.
Unknown still: the copier stack, account sizes per firm, and spend versus
payouts per month.

## 6. Stop-trading rules and discipline

What his own material says (research angle `stop-rules`, 22 sourced facts):

| Rule | His statement | Source |
|---|---|---|
| Clock stop | "I end trading at 11:00 ... 'Done for this day'", even when the reversion completes after 11:00 | [Road to $1M Ep. 2](https://sozai.app/transcript/made-105700-3-weeks-day-trading-nq-futures/) **JJ** |
| Per-account cadence | "one account at a time and one trade per account per day as the optimal way to trade prop firms" | [$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) **JJ** |
| Total cadence | "there's no maximum amount of trades"; about 10 a day in the NY session, spread across accounts | same **JJ** |
| Evaluation posture | "maximum risk and clears the whole target in exactly two trades and then moves on"; a loss is "a cheap eval" and he moves on; at 50% win rate "roughly one in every four evals gets funded, and he just plays the numbers" | [jjwebinar.com](https://jjwebinar.com/) **JJ** |
| Funded posture | "The moment he is funded, he flips gears with risk coming right down"; sizing "around the daily loss limit and trailing drawdown so the rules stop taking traders out" | [jjwebinar.com](https://jjwebinar.com/) **JJ** |
| Losing weeks | risk per account tuned to volatility so "even red weeks still grant him payouts"; example: "not my best week, but I was still able to take $18,000 worth of payouts" | [jjwebinar.com](https://jjwebinar.com/), [Ep. 2](https://sozai.app/transcript/made-105700-3-weeks-day-trading-nq-futures/) **JJ** |
| Mechanics as discipline | fixed 1.5R, no management, no partials, skip the trade if the conditions are not met | [fxreplay](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) **3rd** |
| Psychology | mini-course lesson "The Lie About Psychology: Why Trading Psychology Is Fake", yet a mentorship module "The Killer In Trading: Emotions & Overtrading" | [mini-course](https://jj.jjsimontrades.com/mini-course) **JJ** |
| His own sample | 80 trades over 8 days, 57.5% win rate at 1.5R | [$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) **JJ** |

Not found in any indexed source: a dollar, R or loss-count daily stop, a
consecutive-loss rule, news-day rules. The "stop at one third of the daily
loss limit" rule that circulates online comes from generic prop-firm
guides, not from him. The statistical reconstruction used by the code
(`python -m fpt.cli edge`): the 5th-percentile day for his edge is about
-2R at 1.5 qualifying trades a day and -3R at 10; the median longest losing
streak over 200 trades at 57.5% is 5 and the 99th percentile about 11.

**How the pieces fit.** "One trade per account per day" plus "about 10
trades a day" means the day's signals are routed across accounts, not
copied to all of them, which is why 40 accounts produce ~$176 per account
per day rather than 10 trades' worth each. Evaluations take the first
signals at target/3 risk (two 1.5R wins = target, satisfying a 50%
consistency rule exactly); funded accounts take one signal a day at about
$1,000. `python -m fpt.cli portfolio --routing round_robin --eval-risk-mode
two_trade` simulates exactly this; with 40 accounts, 10 signals a day at
57.5% and template firm rules it yields a median of roughly $35-45k net per
month after the first month, with about 24 accounts funded at any time and
roughly two breaches per account per six months.

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
| fxreplay (published 2026-04-29, with an author page for JJ, so written with him), "Fair Value Theory NQ Strategy Backtesting Reimagined" ([page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy), [PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf), [video](https://www.youtube.com/watch?v=SNO1wqJTq5A)) | 09:30 and 14:00 anchors; continuation first 10-15 min, reversion after; MSB (close past the wick of the recent leg) or BOS + displacement (<20% counter-wick); ATR tiers 50/25/16.5 with 1/2/3 contracts; 1.5R | 158 trades, 54% win rate, PF 1.76, max streaks 8 wins / 5 losses, continuations slightly stronger; pre-filter pass: 150 trades, +46R, 52%, PF 1.66; post-filter about 62% and PF 2.46; a half-month February 2026 subset: 43 trades, 58%, +19R; reversion-only subset PF ~1.46 | filters: skip first 3 minutes for continuations; reversions only in the first ~30 minutes; avoid 10:00-11:00 and 15:00-16:00; presenter calls JJ's payout claims "not fully verified" |
| ATSLibrary paid Pine pack "JJ SIMONS STRATEGY (Indicator & Strategy Pack)" (~$97, not by JJ) | continuation and reversion off the pre-open fair line, open-candle bias filter, wick-based or rolling BOS, one-reversion-per-session and cooldown options | vendor-reported NAS100 CFD test: 314 trades, 56.69% win rate, PF 1.94, +$51,893, max drawdown $3,207 | CFD, not NQ futures; not independent |
| 365-day custom-indicator backtest ([transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/), [video Esv74mEfTFY](https://www.youtube.com/watch?v=Esv74mEfTFY)) | same family, coded as an indicator | baseline PF ~1.2; optimized 289 trades, +$48,700 on 100k (49%), PF 1.7, 55% win rate, MDD ~2.4%; an alternate run on the same page: 314 trades, 56.69% win rate, PF 1.94, +$51,893, MDD $3,207 | about 1.2 trades a day; "mechanically profitable but not extraordinarily so" |
| "Backtesting JJ Simon's NQ Strategy" ([SNO1wqJTq5A](https://www.youtube.com/watch?v=SNO1wqJTq5A), [summary](https://youtubesummary.com/summary/SNO1wqJTq5A)) | 1-minute scalp: fair value, BOS/MSB, displacement, ATR risk | see research files | |
| "JJ Simon Strategy Backtest: 40 Trades" ([c61c4CxTpYI](https://www.youtube.com/watch?v=c61c4CxTpYI)) | small sample | see research files | |
| "Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?" ([JcW8Wjnw8ck](https://www.youtube.com/watch?v=JcW8Wjnw8ck)) | forward test on an evaluation | see research files | |
| TradingView indicators: joetroyer ([link](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/)), AndrewFXTD ([link](https://www.tradingview.com/script/jfW4Vilk/)), microupnup "Fair Price Strategy" ([link](https://www.tradingview.com/script/mpU3gOF5-Fair-Price-Strategy/)), ethanforgotten "JJSimon strat" ([link](https://www.tradingview.com/script/9jDxlxC6-JJSimon-strat/)) | joetroyer: fair line anchored at each session open (NY AM, NY PM, London, Asia) with six selectable sources, +/-38-point band, displacement back toward the line, 4-of-5 confluence grading, continuation waits for a retrace to the line; AndrewFXTD: 09:30-11:00 and 14:00-15:00, fib 0/0.2/1 encodes the 20% wick rule, 25/37.5 default; microupnup: the 09:29 candle's range; ethanforgotten: closed source, marks BOS and the triggering displacement candle | | the "$1 per point on NQ" line that appears in search excerpts is a summarizer error (NQ is $20, MNQ $2) |

Mechanized versions of the rules fire about 1.2-1.3 trades a day (289-314
trades a year), an order of magnitude below the 10-30 a day he describes.
Critiques to weigh: these are small samples (150-314 trades), sensitive to
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
8. Firm naming: Funded Engineer (JJ) vs Funded Next (third-party summary); both appear in his own breakdown.
9. The per-firm payout figures he lists sum to roughly $1.26M, not the $1.6M headline of the same video.
10. Two of the podcast appearances in the original brief were wrong: the Captain Green podcast guest is a different JJ Simon, and the Titans of Tomorrow video and "The Genius Who Outsmarted The Prop Firm Game" are one episode.

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
