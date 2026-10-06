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
| Experience | "full-time futures trader with 16 months of experience" at the $1.5M mark ([jjwebinar.com](https://jjwebinar.com/); repeated in the Road to $1M Ep. 2 transcript and the channel about-text); the Words of Rizdom episode bills "$1.8+ Million in Payouts in JUST 18 Months" | **JJ** / **3rd** |
| Payout claims over time | $1.3M, $1.5M ("over $1,500,000 in verified prop firm payouts across E8, Topstep, Tradeify and more", [jjwebinar.com](https://jjwebinar.com/)), $1.6M, $1.8M, $1.9M ([video HlWSP7ajgpQ](https://www.youtube.com/watch?v=HlWSP7ajgpQ)), $2,000,000+ ([schedule-call page](https://jj.jjsimontrades.com/schedule-call)) | **JJ**; figures rise with time and differ by platform bio |
| Payouts by firm (his $1.6M breakdown) | Topstep ~$292,000; E8 ~$222,000; Funded Engineer ~$180,000; MyFundedFutures ~$92,000; Bulwark ~$55,000; Apex ~$60,000 ; Funded Next $129,500; Lucid ~$105,000; Alpha Futures ~$75,000 ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/)); Tradeify is named as a payout source elsewhere but is absent from this breakdown | **JJ** |
| Business | Mentorship operated by SIMON FUND LLC (entry model, trade recaps, risk-management dashboard, weekly 1-on-1 calls; price behind an application funnel; curriculum lists continuation and mean-reversion specifics, understanding and identifying fair price, expected value and variance, risk of ruin and bankroll management, prop-firm math, volume by session, VWAP, news days); Whop listing 4.9/5 from 46 reviews with 6,125 members; AllPros 4.6/5 from 5 reviews ([allpros.io](https://allpros.io/course/jjs-mentorship)); a $49/month community tier on Whop and a $299.99 pre-recorded workshop; free mini-course and Discord; webinar funnel ([jjwebinar.com](https://jjwebinar.com/)); the free PropFirmEV calculator | **JJ** / **3rd** |
| Business, funnel detail | The application asks for a monthly income band (from under $1,000 to $5,000-$7,500); pirate resellers claim an "original price" of $2,500, $6,000 or $6,500 (unverified, likely invented); a free live webinar was dated 2026-08-25 19:00 ET; advertised student results: Connor $0 to $40,000 in 2.5 months, Kyle $0 to $25,000, Dillon $30k/month, Mitch $10k/month in 3 months, $0 to $56,900 in 4 months, $22,000+ in 30 days on Tradeify, $40,000+ on Lucid Live; three student-scaling videos exist (r5AhmGaFujU, VY-bO35-tjE, MIWsdldzJgQ) | **JJ** marketing / **3rd** |
| Audience | about 32,800 YouTube subscribers, 17K Instagram, 18.1K TikTok (Oct 2026) | platform counts |
| Credential detail | LinkedIn: University of Washington; built options-pricing software (Black-Scholes and Cox-Ross-Rubinstein) as a student project | **JJ** |
| Appearances | Chart Fanatics (host Riz Iqbal): "STEAL The 1-Minute Strategy That Made Him $1.8M+" ([KHEQ5g55dQ4](https://www.youtube.com/watch?v=KHEQ5g55dQ4), uploaded 2026-10-04; the episode behind the reel that started this dossier, whose blurb promises "statistics, risk models and account strategies ... optimal risk and R:R ... 45+ accounts ... knowing exactly when to stop trading"; a 22,000-word transcript exists in the GB10 corpus, see Section 11); Titans of Tomorrow clip "This Kid Printed $2M In Payouts Trading 30 Times/Day, Here's How." ([-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg), 2026-09-18, nine minutes cut from the June episode below; the research sessions mis-attributed it to Chart Fanatics from search snippets); Titans of Tomorrow (host Waqar Asim), "The Genius Who Outsmarted The Prop Firm Game, And Made $1.5M In Payouts" / audio title "Quant Finance Graduate Reveals His $1.5M Prop Firm Strategy" ([aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8), 2026-06-22; chapters "Why High Risk-Reward Fails Evaluations" 7:23, "Taking 20 Trades A Day Without Tilting" 12:01, "JJ's Mean Reversion Trading Model" 16:00, "His Session Open Strategy Explained" 20:07); Words of Rizdom (Riz Iqbal's audio podcast; billed "$1.8+ Million in Payouts in JUST 18 Months", "20+ scalps a day", "3 fixed simple strategies", trades live on the episode). Not him: the "Leap in with Captain Green" podcast's JJ Simon is a Singapore environment official; the Trading Nut "JJ" and the Business Insider "Kane Simons" are other people. | **3rd** |

## 2. The Fair Pricing Theory model

**Premise (JJ).** When the market has no new information to price in,
price is likely to revert toward a reference level he calls fair value /
fair price. For NQ the reference is the price at the 09:30 ET cash open;
the 365-day backtester paraphrases him as "the price of the candle right
before the NASDAQ opens, the pre-open price, before all that institutional
volume hits" ([365-day backtest transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/), **3rd**; see contradiction 3 in Section 10 for the open-vs-pre-open-candle difference).
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

**His own words on the anchor and its drift (Titans of Tomorrow clip, Sept 2026).**
"First fair price that I will assume is just 9:29 Eastern before the market
opens. And then from there, if there's consolidation and then more
breakouts, I'll just treat the most recent consolidation as a fair price."
On why the open is exploitable: "Whenever the session opens obviously
increase in volatility ... it creates an unfair move. So just because
volume came into the market and it moved a specific direction that
shouldn't change the fair underlying price of the stocks." On news:
"news most of the time is going to be priced in pretty fairly so that when
news comes out there's a huge candle, I'll just trade a continuation of
that candle for my first trade of the day. And then after that I'll take
usually like three to four trades trying to revert that move ... back to
the pre-news price." On cycles: "Not from session to session ... But within
a session, I do believe there are unfair moves and if you are able to
revert those unfair moves, then you have a positive expectancy."
`rolling_fair_value=True` implements the consolidation re-anchor.

**His full day (same clip).** 08:30 news: one continuation, three or four
reversions. 09:30 New York: "one continuation, three or four reversions."
Then "a longer trade ... going into lunch hour like 11:00 a.m. ... I'm
trying to play it out from 11:00 all the way until 2:00." 14:00: "one
continuation, three to four reversions." 18:00: "same thing." 20:00 Asian
session: "one more time." That is the arithmetic behind "20-30 trades a
day": five sessions of four or five trades. `--all-sessions` enables the
08:30, 18:00 and 20:00 windows.

**Window (JJ).** 09:30 to 11:00 ET, "a 90-minute window"; an afternoon
session 14:00-15:00 in earlier videos; the 18:00 and 20:00 sessions appear
from May 2026 ("How I Trade the 6PM & 8PM Session", GMDUiamqgig,
2026-05-18) and are the subject of the September 2026 "$400,000 in 90 Days"
video; no public codification covers them yet.

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
price. Read with Section 8: the fxreplay tests found continuations the
stronger half (higher win rate and profit factor); reversions ran PF ~1.46
and only held up in the first ~30 minutes, weak after 10:00, which is
consistent with his TikTok remark.

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

In his own words (Titans of Tomorrow clip): phase one is time, "the minute
any session opens, I'm ready to take a continuation"; phase two starts
"when volume starts dying out, it will usually start to consolidate ... I
will trade when it breaks structure back towards the opening price", "as
long as it's before 11:00 a.m."; the signal is binary, "Either it broke
structure or it didn't. I try to take the discretion out of it just
because I'm trying to take so many trades"; execution: "as long as it
closes below the structure that it broke, I'm good with entering". He does
not use chart patterns ("most of it is artificial when market makers are
balancing their inventory") or institutional-footprint signals.

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
entering on the displacement close; a May 2026 video (2026-05-18) covers the
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
| Target | 1.5R fixed; second-hand from the Chart Fanatics episode: 1:1.5 on evaluations and consistency-rule accounts, 100-point targets on funded accounts without a consistency rule (unverified) | **JJ** via fxreplay; Chart Fanatics notes |
| Losing weeks | Week-13 video description: risk management "to ensure payouts even during losing weeks"; the Ep. 2 summary paraphrases him as adjusting contract size and stop by candle size and volatility (summariser wording, not verbatim) | **JJ** description / **3rd** paraphrase |
| ATR period | not published; code uses Wilder 14 | assumption |

**Static risk, in his words (Titans of Tomorrow clip).** "The stop loss
take profit are static ... on prop firms, it is infinitely better to use
static risk in terms of like exactly 1,000, exactly 500." Asked whether a
structure-based stop would be better: "No. No. I found infinitely better to
have a static stop loss." On management: "I never go break even ... unless
there is a new session opening ... Or, if we have news coming out ... like
95% of my trades I'm not going to go break even. I find it better to just
let it play out." And the thesis in one line: "a small bias is like
extremely profitable on prop firms if you have good risk management."

**His own reasoning for 1.5R (JJ, `risk-model` angle, 38 facts).**
Evaluations are "minus 2K max loss and plus 3K profit target, making it
automatically optimal to do a one to 1.5"; trading in 1:1.5 units raises
the pass rate "based on how the drawdown trails"; break-even is 40%; his
sample ran 57.5%. Posture: "aggressive risk to get funded and then
conservative risk management to stay funded"; "on the eval, optimize for
your pass rate; on the funded, maximize your expected value: probability
of getting a payout multiplied by how large that payout is". The sizing
exception, "when opening candles are larger than 25 points, he cuts the
size in half" with the 50-point stop, is the fxreplay presenter's wording
(**3rd**, via youtubesummary), reported again second-hand from the Chart
Fanatics episode. The business math he teaches:
cost to funded = fee / pass rate ($100 / 0.30 = $333); cost per dollar of
drawdown = fee / drawdown ($750 for $4,500); EV of an evaluation =
P(payout) x payout - P(no payout) x fee (10% x $2,000 - 90% x $100 =
+$110; strictly the fee is paid either way, so with a gross $2,000 payout
the EV is +$100); "the optimal profit target on his accounts was $1,800 per day";
about 40 accounts "where all of your accounts end the day traded" is six
figures a month; he says he spent $550,000 on evaluations learning this.
Variance he reports: -$21,000 over seven days inside a +$48K month with a
$45K payout. `python -m fpt.cli evalmath` reproduces the arithmetic.

**Reported second-hand from the Chart Fanatics episode** (KHEQ5g55dQ4,
uploaded 2026-10-04; the reading of the GB10 session that holds the
transcript, see `docs/research/chartfanatics-KHEQ5g55dQ4-notes.md`; every
item is to be checked against the transcript before it is promoted to his
own words): a 25-point stop and 38-point target in normal volatility;
contracts halved when the opening range exceeds 25 points; 1:1.5 targets on
evaluations and consistency-rule accounts but 100-point targets on funded
accounts without a consistency rule (`--target-points`, stop pairing not yet
known); the 50k example of a $2,000 drawdown against a $3,000 target; 45
accounts, never broken down by firm; and cost to funded = evaluation price
divided by pass rate.

**The arithmetic the method rests on.** At the third-party-measured 52-54%
win rate and 1.5R the expectancy is +0.3 to +0.35R per qualifying trade;
the breakeven win rate is 40%. Full Kelly on the drawdown allowance is
about 23%; $1,000 on a $3,000 Topstep drawdown is 33%, i.e. more than
Kelly, which is why his operation needs many accounts rather than one.
`python -m fpt.cli edge` reproduces these numbers; `python -m fpt.cli
evaluation` shows the pass-probability curve versus fixed risk per trade
under the preset's own drawdown rule. For Topstep 100k (EOD-trailing limit
locked at the start balance, $2,000 soft daily limit) at a 54% / 1.5R edge
and 1.5 qualifying trades a day it peaks near 20-30% of the drawdown at a
73-75% pass probability (4,000 sims); a static-drawdown scan would say 80%,
which is why the firm's rule matters.

**Calibration warning.** Ten trades a day at 54% / 1.5R would be +3.5R per
account per day. His own reported results imply far less: "$105,700 in 3
weeks" across ~40 accounts is about $176 per account per trading day,
~0.18R of payout at $1,000 risk. At 0.35R expectancy per trade that is what
about 0.5 R-producing trades per account per day would yield if payouts
equalled P&L; payouts are net of splits, caps, breaches and unfunded
accounts, and the third-party backtests log about 1.2 qualifying signals a
day (Section 8). The simulators default to 1.5 qualifying signals per day
per account in copy mode, an upper bound on his cadence rather than a fit
to his payouts.

## 5. Multi-account operation

| Item | What the sources say | Status |
|---|---|---|
| Account count | 20-30 (his X posts), 40 ("runs approximately 40 accounts", Road to $1M Ep. 2), "45+" (Chart Fanatics blurb; 45 said twice in the episode per second-hand notes) | **JJ**, grows over time |
| Firms | His own list on X: Topstep, MFF, E8, TickTick Trader, FFF, Bulenox, Tradeify, Futures Elite, Apex, TPT, Funding Futures, BGF, Phidias, FXIFY, Alpha, TopOneFutures, FundedNext (17); LinkedIn names a subset; payouts itemised for Topstep, E8, "Funded Engineer", MyFundedFutures, Funded Next, Lucid, Alpha, Apex, Bulwark Prime; also Fundedseat (a live-bonus product, bonus achieved on 2 of 3 accounts, Sept 2026) | **JJ** |
| Why many accounts | "being able to get through so many accounts and diversify risk across all of them thanks to fair pricing theory"; "different prop firm accounts used depending on market conditions" | **JJ** (transcript summary) |
| Why prop firms | "prop firms offer more profitability due to their evaluation rules, drawdown limits, and profit targets"; an aggressive high-frequency NY-session method with risk tailored to prop-firm rules | **JJ** |
| Income target | "$100,000 per month on prop firms" (video title) | **JJ** |
| Execution stack | copier tooling not confirmed in public sources (TopstepX copier, Tradovate group trading, Replikanto, Tradecopia are the candidates) | unverified |
| Routing | "one account at a time and one trade per account per day"; evaluations: max risk, target in exactly two trades; funded: risk "coming right down" | **JJ** ([$1.6M video](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/), [jjwebinar.com](https://jjwebinar.com/)) |

`fpt/portfolio.py` reproduces the economics: identical signals copied to N
accounts, each under its firm's rules, with evaluation fees, resets,
activation fees, consistency gates, payout caps and monthly cadence. With
the cap-feasible 45-account mix of Section 9 (Topstep 5, Tradeify Growth 5,
MFFU Pro 3, Lucid 5, Alpha 5, Apex 20, E8 2), $1,000 risk, 54% / 1.5R and
1.5 qualifying trades a day (1,000 sims, seed 0), the six-month median net
cash is about $1.17M (roughly $230-260k a month once accounts are funded)
with a 5th percentile near $240k and about 112 account breaches per run,
each re-bought the next trading day (a cap-ignoring 20 Topstep / 15 Tradeify
Select / 10 MFFU run gives a $1.06M median, $330k 5th percentile and 154
breaches). Treat these as the model's upper bound:
every account receives 1.5 qualifying signals a day with no execution
differences. Seven of the twelve presets (Topstep x3, MyFundedFutures Rapid,
Tradeify Growth and Select, Alpha Standard) are backed by the firms' help
centers; the rest are third-party placeholders (Section 9).

**Operation details from the `accounts` angle (34 facts).** Payouts by
firm from his $1.6M breakdown: Topstep ~$292,000; E8 $222,122 (the one
firm-issued "Certificate of Performance" found); "Funded Engineer" ~$180,000
(an unnamed firm's dashboard on jjwebinar.com shows 48 payouts totalling
$179,938, $123,901 disbursed as of April 2026, largest $46,433, rolling
monthly payouts of $47,300 plus $17,250 lump sums; the matching total is the
only basis for linking it to the "Funded Engineer" line); Funded Next $129,500; Lucid ~$105,000; MyFundedFutures
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
"different on separate firms and accounts" ([jjwebinar.com](https://jjwebinar.com/));
the 365-day backtester's reading is that "his real edge is understanding the
prop firms and having a different risk strategy per prop firm" and that the
method is "optimized for prop firms and less effective on live accounts"
(**3rd**). He has published a calculator, PropFirmEV,
that replays a trader's statistics through each firm's rulebook thousands
of times at one trade per day; `fpt/portfolio.py` is the same idea.
Monthly examples from his posts: a $48K month with a $45K payout; four
June payouts totalling $25,000; $90,000 made toward a $175,000 record-month
target. He also
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

Not found in any indexed snippet: a dollar or R daily stop or news-day
rules. A consecutive-loss rule (three in a row end the session) and the
rule that the 9:30 fair price is invalid after 11:00 are reported
second-hand from the Chart Fanatics episode (Section 4 note). The "stop at one third of the daily
loss limit" rule that circulates online comes from generic prop-firm
guides, not from him. The statistical reconstruction used by the code
(`python -m fpt.cli edge --p 0.575`): the 5th-percentile running loss for
his edge is -2R at 1.5 qualifying trades a day and -4R at 10 (the quantile of
the day's closing P&L is -2R at both cadences); the median longest losing
streak over 200 trades at 57.5% is 5 and the 99th percentile 10. The
backtester's `stop_scope="session"` resets these stops at each session start
to match the reported per-session rule.

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
| start ~Feb 2025 (implied: $1.5M at "16 months" in June 2026) | first payouts; two early Topstep payouts of $4,500 each | his $1.6M video |
| 2026-03-08 | "$100 to $1M in 2 Years / Here's How" | [aBVn6IUAjnM](https://www.youtube.com/watch?v=aBVn6IUAjnM) |
| 2026-03-28 | $1.2M "in the Last 12 Months" (his title; fxreplay's presenter restates "over 12-13 months") | [3L8xdh3oPm4](https://www.youtube.com/watch?v=3L8xdh3oPm4) |
| 2026-04-03 / 04-09 | "$52,392.04 THIS WEEK"; "$56,893.28 in ONE Day (My Biggest Day Ever)" | [Lep139B5EbU](https://www.youtube.com/watch?v=Lep139B5EbU), [RnwOqmEF6Rk](https://www.youtube.com/watch?v=RnwOqmEF6Rk) |
| 2026-04-12 | $1.3M: "I Ranked Every Futures Prop Firm After $1,300,000 in Payouts" (also PropFirmEV, old X bio) | [5RzMu2B2E_0](https://www.youtube.com/watch?v=5RzMu2B2E_0) |
| 2026-05-18 / 05-22 | 6PM & 8PM session video; news-trading strategy video ("$1,300,000 in 12 Months") | [GMDUiamqgig](https://www.youtube.com/watch?v=GMDUiamqgig), [8lbkj0PF1uM](https://www.youtube.com/watch?v=8lbkj0PF1uM) |
| 2026-06-06 / 06-10 | $1.5M: "How I turned $0 into $1,500,000" roadmap; "Watch Me Backtest My $1,500,000 Trading Strategy" (80 trades, 57.5%) | [C-_0QhKZmA4](https://www.youtube.com/watch?v=C-_0QhKZmA4), [MVP7X-3v8xk](https://www.youtube.com/watch?v=MVP7X-3v8xk) |
| mid-2026 | $1.5M, "16 months of experience"; "Road to $1M" series goal: $1.5M to $2.5M | [Road to $1M Ep. 2 summary](https://sozai.app/transcript/made-105700-3-weeks-day-trading-nq-futures/) |
| 2026-06-15 | Road to $1M Ep. 1: "$87,000 From Prop Firms in 2 Weeks" | [gjWiGBiVis0](https://www.youtube.com/watch?v=gjWiGBiVis0) |
| 2026-06-21 | Ep. 2: $105,700 in 3 weeks across ~40 accounts | [xTxrtFKlQfc](https://www.youtube.com/watch?v=xTxrtFKlQfc), [transcript](https://sozai.app/transcript/made-105700-3-weeks-day-trading-nq-futures/) |
| 2026-06-22 | Titans of Tomorrow full episode "The Genius Who Outsmarted The Prop Firm Game, And Made $1.5M In Payouts" | [aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8) |
| 2026-06-28 | Ep. 3: "I Lost $30,000 in Prop Firm Profits in One Day" | [CzxSgYujDxs](https://www.youtube.com/watch?v=CzxSgYujDxs) |
| 2026-07-05 / 07-13 | Ep. 4 "From $1.5M To $2.5M" payout breakdown; Ep. 5 "Road to $2,500,000" | [EyR3i2GxwyA](https://www.youtube.com/watch?v=EyR3i2GxwyA), [q8PXXvY9lS0](https://www.youtube.com/watch?v=q8PXXvY9lS0) |
| 2026-07-20 / 07-27 | Ep. 6 "$12,500 Week - Why I'm Not Satisfied"; Ep. 7 students trading live in Miami | [7KJOh2NF-lQ](https://www.youtube.com/watch?v=7KJOh2NF-lQ), [MIWsdldzJgQ](https://www.youtube.com/watch?v=MIWsdldzJgQ) |
| 2026-07-25 | $1.6M: "The Strategy Behind My $1.6M in Prop Firm Payouts" (per-firm breakdown, A+/A/B grades, 80-trade sample) | [KN7j6NXXAio](https://www.youtube.com/watch?v=KN7j6NXXAio) |
| 2026-07-30 | "Here's How You Can Make $100,000 Per Month On Prop Firms" | [AxP-cg50TdM](https://www.youtube.com/watch?v=AxP-cg50TdM) |
| 2026-08-02 / 08-09 | "$37,500" week, every trade filmed; Ep. 9 "$50,000+" week | [pwO9IAu7FUQ](https://www.youtube.com/watch?v=pwO9IAu7FUQ), [g68HHbrIBBg](https://www.youtube.com/watch?v=g68HHbrIBBg) |
| 2026-08-23 / 08-27 | $1.8M: strategy breakdown; "How I Scaled To $1.8M In Prop Firm Payouts" | [74CRg-mID5c](https://www.youtube.com/watch?v=74CRg-mID5c), [4BXpI-hYqe0](https://www.youtube.com/watch?v=4BXpI-hYqe0) |
| 2026-09-06 / 09-08 | Ep. 11 "Why You Pass Evaluations But Never Get A Payout"; "The Prop Firm Strategy That Made $1.8M" | [KhooqEQK9bA](https://www.youtube.com/watch?v=KhooqEQK9bA), [DEkzU8gqX-o](https://www.youtube.com/watch?v=DEkzU8gqX-o) |
| 2026-09-13 | $1.9M: "I Hit $1.9M In Prop Firm Payouts (My Trades This Week LIVE, Ep. 12)" | [HlWSP7ajgpQ](https://www.youtube.com/watch?v=HlWSP7ajgpQ) |
| 2026-09-15 / 09-17 | "Why I Can't Show You My Risk Management"; "The ONE Setup That Made Me $400,000 in 90 Days (6 & 8PM Session)" | [sWJa8vRfPb8](https://www.youtube.com/watch?v=sWJa8vRfPb8), [BLvsYJ4sqn8](https://www.youtube.com/watch?v=BLvsYJ4sqn8) |
| 2026-09-18 | Titans of Tomorrow clip ($2M, "30 times/day"), nine minutes of the June episode | [-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg) |
| summer-autumn 2026 | TikTok daily series "day N trading to my second million" (day 4 ... day 77, day 80), which dates the start of the second-million count to about July 2026 | TikTok @itsjjsimon (video 7621017448963132702) |
| 2026-10-04 | Chart Fanatics: "STEAL The 1-Minute Strategy That Made Him $1.8M+" (1:42:24) | [KHEQ5g55dQ4](https://www.youtube.com/watch?v=KHEQ5g55dQ4) |
| 2026-09-20 / 09-22 | "How I Made Money Trading Prop Firms On A Bad Week (Week 13)"; "I spent $550,000 on prop firm evaluations and learned this" | [l6iq0ljhxIo](https://www.youtube.com/watch?v=l6iq0ljhxIo), [dJdBnSBJlgQ](https://www.youtube.com/watch?v=dJdBnSBJlgQ) |
| 2026-10-04 | $2,000,000+: "I Hit $2,000,000 In Prop Firm Payouts (Week In My Life)", channel bio, sales page | [PN1UKQMPb5M](https://www.youtube.com/watch?v=PN1UKQMPb5M), [schedule-call page](https://jj.jjsimontrades.com/schedule-call) |

The run from $1.5M (June) to $2M+ (early October) implies about $500k in
three and a half months; the weekly episodes above itemise parts of it
($87k, $105.7k, -$30k day, $12.5k, $37.5k, $50k+ weeks) but no complete
ledger was found. Dates are the YouTube upload dates from the transcript
index (`docs/research/transcript-index.md`); Ep. 8, 10 and Weeks 1-12 of the
later series were not captured.

## 8. Independent backtests and critiques

| Study | Rules coded | Result | Notes |
|---|---|---|---|
| fxreplay (published 2026-04-29, with an author page for JJ, which implies it was published with or for him), "Fair Value Theory NQ Strategy Backtesting Reimagined" ([page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy), [PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf), [video](https://www.youtube.com/watch?v=SNO1wqJTq5A)) | 09:30 and 14:00 anchors; continuation first 10-15 min, reversion after; MSB (close past the wick of the recent leg) or BOS + displacement (<20% counter-wick); ATR tiers 50/25/16.5 with 1/2/3 contracts; 1.5R | 158 trades, 54% win rate, PF 1.76, max streaks 8 wins / 5 losses, continuations slightly stronger; pre-filter pass: 150 trades, +46R, 52%, PF 1.66; post-filter about 62% and PF 2.46; a half-month February 2026 subset: 43 trades, 58%, +19R; reversion-only subset PF ~1.46 | filters: skip first 3 minutes for continuations; reversions only in the first ~30 minutes; avoid 10:00-11:00 and 15:00-16:00; presenter calls JJ's payout claims "not fully verified" |
| 365-day custom-indicator backtest ([transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/), [video Esv74mEfTFY](https://www.youtube.com/watch?v=Esv74mEfTFY)), later sold as the ATSLibrary Pine pack "JJ SIMONS STRATEGY" (~$97, not by JJ) | continuation and reversion off the pre-open fair line, open-candle bias filter, wick-based or rolling BOS, one-reversion-per-session and cooldown options | one indicator, two reported runs: raw 314 trades, 56.69% win rate, PF 1.94, +$51,893 (+51.9%), MDD $3,207 (2.38%) on NAS100 CFD; optimized 49% return, PF 1.7, 55% win rate, MDD ~2.5% on MNQ; baseline PF ~1.2 before optimisation (the "289 trades, +$48,700" figures in the task brief are unsourced) | CFD, not NQ futures; about 1.2 trades a day; "mechanically profitable but not extraordinarily so"; the creator stresses it is not JJ's indicator |
| "Win Rate vs. Edge: JJ Simon Strategy vs. Mechanical FVG - 52 Trades" ([6xZw32_Jp7U](https://www.youtube.com/watch?v=6xZw32_Jp7U), 2026-08-04) | 52 trades | run on EURUSD, not NQ | a commenter objects that the point-based 25/38 and 50/75 stops do not transfer to EURUSD; not a valid test |
| Forward tests: @WhizzTrades (X, 2026-06-16) forward-tested "JJ Simon's strategy (or similar)" for May 2026, "easy, mechanical and algo-able", no numbers; "I Will Trade JJ Simon's Fair Value Strategy In Real Time" ([IYRtWZHb7Ws](https://www.youtube.com/watch?v=IYRtWZHb7Ws), ~2026-06-24) takes one continuation and one reversion live | as traded | anecdotal | |
| "JJ Simon Strategy Backtest: 40 Trades" ([c61c4CxTpYI](https://www.youtube.com/watch?v=c61c4CxTpYI)) | small sample | see research files | |
| "Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?" ([JcW8Wjnw8ck](https://www.youtube.com/watch?v=JcW8Wjnw8ck)) | forward test on an evaluation | see research files | |
| TradingView indicators: joetroyer ([link](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/)), AndrewFXTD ([link](https://www.tradingview.com/script/jfW4Vilk/)), microupnup "Fair Price Strategy" ([link](https://www.tradingview.com/script/mpU3gOF5-Fair-Price-Strategy/)), ethanforgotten "JJSimon strat" ([link](https://www.tradingview.com/script/9jDxlxC6-JJSimon-strat/)) | joetroyer: fair line anchored at each session open (NY AM, NY PM, London, Asia) with six selectable sources, +/-38-point band, displacement back toward the line, 4-of-5 confluence grading, continuation waits for a retrace to the line; AndrewFXTD: 09:30-11:00 and 14:00-15:00, fib 0/0.2/1 encodes the 20% wick rule, 25/37.5 default; microupnup: the 09:29 candle's range; ethanforgotten: closed source, marks BOS and the triggering displacement candle | | the "$1 per point on NQ" line that appears in search excerpts is a summarizer error (NQ is $20, MNQ $2) |

Mechanized versions of the rules fire about 1.2-1.3 trades a day (314
trades in the one-year test), an order of magnitude below the 10-30 a day he
describes. Critiques to weigh: these are small samples (150-314 trades),
sensitive to the continuation window and to fills on 16.5-point stops with 3
contracts; fxreplay found the choppy April 2023 regime performed "not as
good"; ZenomTrader (X) calls the technique automatable and hard to lose with
enough accounts but with tiny ROI, "5-10 accounts pay almost monthly while
buying challenges constantly"; faketrades.in rates the strategy 1.0 star
with one "bust", on Indian market data, so not a valid NQ test; prop-firm
payouts are gross of evaluation and reset spend; and the 10-30 trades-a-day
cadence in his videos is not what the codified rules generate.

## 9. Prop-firm rule parameters (as of 2026-10-05)

Researched in `docs/research/prop-firm-rules.md` (58 queries, official help
centers where marked) and encoded in `fpt/propfirm.py` (`FIRM_PRESETS`,
each with `verified` and `source`). Presets cover 8 of the 17 firms he
names; Bulwark Prime ($55,000 of his payouts), TickTick Trader, FFF, Bulenox,
Futures Elite, Take Profit Trader, Funding Futures, BGF, Phidias, FXIFY and
TopOneFutures have no preset or research row yet. Highlights for a 100K
account:

| Firm / plan | Cost | Target / drawdown | Daily limit | Consistency | Payouts | Split | Funded cap |
|---|---|---|---|---|---|---|---|
| Topstep Combine -> XFA | $99/mo + $149 activation | $6,000 / $3,000 EOD-trailing, locks at start | $2,000 soft | 55% of target in the Combine | 5 winning days of $150+, $125 min, $3,000-$4,000 per request | 90/10 | 5 XFAs |
| E8 Signature | $260 one-time | $6,000 / $3,000 EOD-dynamic | none | 35% best-day once funded | first after 14 days then every 5 profitable days; caps 2.5% / 2.5% / 4.5% / 5.5% of account size for payouts 1-4, then up to $25,000; EOD-drawdown buffer retained | 80/20 | n/a |
| MyFundedFutures Pro | $267/mo | $6,000 / $3,000 EOD-trailing | none | 50% | every 14 days, $1,000 min, buffer $3,100 | 80/20 | 3 if any 100K+ |
| Tradeify Growth | $255 one-time, reset $169 | $6,000 / $3,500 EOD-trailing | $2,500 soft | 35% funded | 5 winning days, balance above $104,500, $2,000-$4,000 | 90/10 | 5 |
| Tradeify Select | $265 one-time | $6,000 / $3,000 EOD-trailing | none (eval) | 40% eval | daily (Select Daily) or 5-day (Flex) | 90/10 | 5 |
| Lucid Flex | $89-$407 | $6,000 / $3,000 EOD-trailing, locks | optional | none funded | 5 profitable days, $500 min, up to $2,500, 5 payouts then live | 90/10 | 5 per household |
| Alpha Standard | $159/mo + $149 | $6,000 / $4,000 EOD-trailing | none | 40% qualified | 5 winning days of $200+, up to 4/month, $4,000 max | 70-90% tiered | 5 |
| Apex 4.0 Intraday | $790 one-time + $69 (third-party) | n/a / $3,000 trailing, safety net +$100 | none | 50% in PA | 5 qualifying days, $500 min, weekly | 100% of first $25k then 90/10 | 20 per household |

Two facts matter most for replication. Every firm allows copying between
accounts you own (Alpha only from an external master). And the official
funded-account caps (Topstep 5, MyFundedFutures 3-5, Tradeify 5, Lucid 5,
Alpha 5, Apex 20) sum to about 45, matching the "45+ accounts" in the
Chart Fanatics blurb. That match is this dossier's inference, not his
statement: in the episode he says 45 accounts twice but never splits them by
firm, says the firm does not matter as long as risk is tuned to its rules,
and names only Lucid, Tradeify and (probably) Topstep himself; every Apex
mention there is the host's sponsor read. "Funded Engineer", credited with ~$180,000 in
his July 2026 video, was an FX prop firm that filed for bankruptcy on 15
July 2024, before his trading career began; the transcript almost
certainly mishears another firm's name (candidates on his own list: FFF,
Funding Futures; outside it, Funded Futures Network). The caps of these six
firms sum to 43-45 (Alpha's cap is per plan type, MFFU's is 3 with any 100K
account); E8, FundedNext, Bulwark, Fundedseat and the other firms he lists
are not in the sum. The simulator's cap-feasible 45-account mix:
`--account topstep_100k:5 --account tradeify_100k_growth:5 --account
mffu_100k_pro:3 --account lucid_100k_flex:5 --account alpha_100k_standard:5
--account apex_100k_intraday:20 --account e8_100k_signature:2`.

**News and operating constraints that bear on the method** (official help
centers unless noted; `fpt/propfirm.py` models none of them): MyFundedFutures
funded accounts may hold no positions or orders two minutes either side of
FOMC, FOMC minutes, the employment report and CPI, so the 08:30 news trade is
unavailable there; Topstep allows news but bars new opening transactions on
the index minis for five minutes either side of CPI (from 2026-09-11);
Tradeify has no news restriction; Apex allows news trading with brackets
(third-party comparison). Topstep sells at most 20 Combines a month per
trader, switches the copier off while a payout is processed, and sets the
loss limit to $0 (the start balance) after the first payout; Apex requires
copied accounts to trade the same direction with no hedging; Lucid caps a
household at 10 evaluations and 5 funded accounts; Alpha allows copying only
from an external master into Alpha.

## 10. Contradictions, unknowns and verification status

Contradictions found so far:
1. Continuation phase length: ~5 minutes (JJ) vs 10-15 minutes (fxreplay, AndrewFXTD).
2. Reversion window: full 85 minutes to 11:00 (JJ) vs first ~30 minutes only (fxreplay's filtered result).
3. Fair value anchor: 09:30 open (fxreplay, AndrewFXTD) vs the candle right before the open (365-day backtester) vs six selectable sources (joetroyer).
4. Trades per day: 10 (JJ, $1.6M video) vs 20-30 (later appearances) vs ~1.2 qualifying (365-day backtest).
5. Account count: 20-30 vs 40 vs 45+.
6. Payout totals: every platform bio shows a different figure ($1.3M to $2M+), consistent with growth over time but not pinned to dates.
7. fxreplay statistics: 158 / 54% / PF 1.76 vs 150 / 52% / PF 1.66 (different passes of one study).
8. Firm naming: "Funded Engineer" and Funded Next are both named in his own breakdown; only the former conflicts with the 2024 bankruptcy (item 10), and the $179,938 dashboard is linked to it only by its total.
9. The per-firm payout figures he lists sum to roughly $1.26M, not the $1.6M headline of the same video.
10. "Funded Engineer" (~$180,000 in his breakdown) went bankrupt in July 2024, before he started; the firm name is almost certainly misheard in the transcript.
11. Two of the podcast appearances in the original brief were wrong: the Captain Green podcast guest is a different JJ Simon, and the Titans of Tomorrow video and "The Genius Who Outsmarted The Prop Firm Game" are one episode.
12. Evaluation sizing: $1,000 per trade on a $2,000-drawdown 50k evaluation is half the drawdown, so two losses bust it; his "higher pass rate" claim and the two-trade evaluation model (Section 6) assume this, but his actual evaluation risk figure is not published (risk-model angle).
13. Firm-rule source conflicts (prop-firm-rules angle, twelve items): Topstep's daily loss limit soft vs hard and its minimum days (none / 2 / 5); MFFU Pro consistency 50% (official) vs none (thetraderstack) and Rapid payouts daily vs every 5 winning days; MFFU Pro and Alpha Advanced pricing; E8 eval-to-eval copying allowed (official) vs prohibited (third party), its payout buffer (drawdown-sized vs 4%) and reset fee; Apex drawdown as dollar figures vs "5% EOD trailing"; Tradeify Select 50K target $2,500 vs $3,000. Section 9 cells that depend on an unresolved one: Topstep "$2,000 soft", MFFU Pro "50%", Apex "$3,000 trailing", "every firm allows copying between accounts you own".
14. Experience: "16 months" at $1.5M (his pages) vs "$1.8+ Million in JUST 18 Months" (Words of Rizdom billing).
15. Income promise differs by platform: "scale to $10K+/month" (Instagram) vs "$30K+/month" (YouTube, TikTok).
16. An evaluation-vs-funded tweet in the evidence is dated before the account it refers to existed (profile angle).
17. "Verified payouts" is self-asserted: one firm certificate (E8, $222,122) was found; every other figure is his own screenshot or restatement.
18. Tradeify is named as a payout source ("E8, Topstep, Tradeify and more") but is absent from the $1.6M per-firm breakdown.
19. Routing: "one account at a time, one trade per account per day" (JJ) vs "trade copiers across dozens of smaller funded accounts" (third-party summary); he says he sometimes copies two accounts together and advises no copier until ~$20k earned.
20. Entry quality: A+ (break of structure) preferred and B avoided (his grading) vs "literally any displacement entry" in a third-party reading of the same video.

Unknowns still open: the exact BOS/MSB and displacement definitions in his
own words; the ATR period; the copier stack and per-firm account counts
(he gives none); the stop he pairs with the reported 100-point funded
target; verbatim confirmation of the per-session three-loss stop and the
other Chart Fanatics statements (the transcript sits on the GB10, Section
11); the rules in the news-trading video (8lbkj0PF1uM, 2026-05-22, not yet
extracted); the current pricing of the third-party-sourced presets.

## 11. Sources

**Primary corpus on the GB10.** Your machine's session collected 58
verbatim transcripts (296,678 words) of his channel and the podcast
episodes, plus the usable pages, at `~/jj-simon-sources` and committed them
on branch `claude/jj-simon-sources` (commit f638a1f) without pushing, since
redistributing full transcripts is a publication decision for you. Highest
value items for a replicator: KHEQ5g55dQ4 (Chart Fanatics, 21,988 words),
aCOgfvL6lK8 (Titans of Tomorrow, 16,917), MVP7X-3v8xk ("Watch Me Backtest
My $1,500,000 Trading Strategy", 9,091), 74CRg-mID5c ("How I Made $1.8M
Trading Prop Firms (Strategy Breakdown)", 8,864), AxP-cg50TdM ("$100,000
Per Month", 7,463), dJdBnSBJlgQ ("$550,000 on evaluations", 7,628),
KN7j6NXXAio ("$1.6M", 6,577), BLvsYJ4sqn8 (6 & 8PM session, 6,923),
GMDUiamqgig (6PM & 8PM on funded accounts, 2,681), sWJa8vRfPb8 ("Why I
Can't Show You My Risk Management", 5,148), and the Road to $1M / weekly
episodes 1-13. A local Qwen 35B model on that machine can extract the rules
from all of them in one pass once you allow the batch run.

Primary (JJ): his YouTube channel ([@itsjjsimon](https://www.youtube.com/@itsjjsimon)); [jjwebinar.com](https://jjwebinar.com/); [jj.jjsimontrades.com/schedule-call](https://jj.jjsimontrades.com/schedule-call); transcripts of "The Strategy Behind My $1.6M in Prop Firm Payouts", "Here's How You Can Make $100,000 Per Month On Prop Firms", "I Made $105,700 in 3 Weeks Day Trading NQ Futures (Road to $1M Ep. 2)" on [sozai.app](https://sozai.app/).
Podcasts: Chart Fanatics ([KHEQ5g55dQ4](https://www.youtube.com/watch?v=KHEQ5g55dQ4), 2026-10-04, [chartfanatics.com](https://www.chartfanatics.com/)); Titans of Tomorrow ([aCOgfvL6lK8](https://www.youtube.com/watch?v=aCOgfvL6lK8), full episode 2026-06-22, and the clip [-lxNWJGWtbg](https://www.youtube.com/watch?v=-lxNWJGWtbg), 2026-09-18); Words of Rizdom (episode not indexed). Not him: PCDHJBdj-Z4 (Captain Green podcast, a different JJ Simon; video now unavailable). Rows in `EVIDENCE.md` and `sources.csv` that label -lxNWJGWtbg as Chart Fanatics are mislabelled.
Third-party tests and codifications: [fxreplay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) and [PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf); [365-day backtest transcript](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); [youtubesummary.com](https://youtubesummary.com/summary/SNO1wqJTq5A); TradingView [joetroyer](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/) and [AndrewFXTD](https://www.tradingview.com/script/jfW4Vilk/).
Reviews: [allpros.io](https://allpros.io/course/jjs-mentorship).
Full list: `docs/research/sources.csv`.
