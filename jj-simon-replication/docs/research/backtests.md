# JJ Simon replication research: Angle 1 - independent backtests, indicators, critiques, reviews

Research date: 2026-10-05. Tool: WebSearch only (57 queries for this angle; page fetches blocked by network policy, so every fact below comes from search-result text and is marked with its source). 'JJ own words' marks statements attributed to JJ Simon himself via transcript or his own posts; everything else is a third party.

Already-known baseline (from the task brief, not re-researched): reversion to the 09:30 open during 09:30-11:00 after a short continuation phase; BOS + displacement entry (counter-wick < 20%); ATR-tier stops (>20 ATR 50 pts/1 ct, 7-20 ATR 25 pts/2 ct, <7 ATR 16.5 pts/3 ct, ~$1,000 risk); fixed 1.5R. fxreplay: 150-158 trades, 52-54% WR, PF 1.66-1.76, streaks 8W/5L, +46R raw. 365-day test: 289 trades, +$48,700 (49%), PF 1.7.

## Facts

- **fxreplay codes fair value as two fixed reference prices: the 9:30 ET NQ open price and the 2:00 PM ET price.** Quote: "For the NQ ... JJ has identified two price levels that consistently act as fair value: the 9:30 AM market open price and the 2:00 PM NY afternoon price." ([JJ Simon's Fair Value Theory Strategy (FX Replay strategy page)](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29 (listed publish date on fxreplay.com/learn); confidence high)
- **fxreplay restricts the strategy to the 1-minute chart in two windows: 09:30-11:00 and 14:00-15:00 ET.** Quote: "The strategy is traded exclusively on the 1-minute chart during two New York sessions: 9:30-11:00 AM and 2:00-3:00 PM." ([FX Replay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence high)
- **fxreplay's phase split: continuation setups in the first 10-15 minutes of each window, mean-reversion to fair value for the remainder.** Quote: "In the first 10-15 minutes, traders look for continuation moves ... For the remainder of the window, the focus shifts to mean-reversion setups." ([FX Replay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence high)
- **Entry trigger as coded by fxreplay: a Market Structure Break (MSB) or Break of Structure (BOS) confirmed by a strong displacement candle; fixed 1.5R target, no management, no partials.** Quote: "All entries require the same two-condition trigger: a Market Structure Break (MSB), or Break of Structure (BOS), confirmed by a strong displacement candle. ... trades target a fixed 1.5R with no active trade management." ([FX Replay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence high)
- **fxreplay distinguishes BOS (trend continuation) from MSB (potential reversal).** Quote: "A BOS, Break of Structure, signals trend continuation, while an MSB, Market Structure Break, signals a potential trend reversal." ([FX Replay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence medium)
- **fxreplay's ATR-tiered stop/target table: above 20 ATR = 50 pt SL / 75 pt TP; 7-20 ATR = 25 / 37.5; below 7 ATR = 16.5 / 24.75; 1, 2 or 3 NQ contracts per tier for roughly $1,000 risk. The ATR period is not stated in any indexed excerpt.** Quote: "Above 20 ATR: 50 point SL, 75 point TP; 7-20 ATR: 25 point SL, 37.5 point TP; Below 7 ATR: 16.5 point SL, 24.75 point TP ... Using 1, 2, or 3 NQ contracts at the appropriate ATR tier equates to approximately $1,000 of risk per trade." ([FX Replay strategy page](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence high)
- **Search-engine excerpt of the fxreplay page states 'one point = $1 on NQ'. This is wrong for the full-size NQ contract ($20/pt) and would match MNQ ($2/pt) only loosely; treat as a summarizer error or an MNQ framing.** Quote: "(one point = $1 on NQ)" ([FX Replay strategy page (search excerpt)](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy); strategy page / third-party writeup; third party; 2026-04-29; confidence low)
- **fxreplay published a companion PDF titled 'JJ Simon's Fair Value Theory NQ Strategy Backtesting Reimagined' on its CDN.** Quote: "JJ Simon's Fair Value Theory NQ Strategy Backtesting Reimagined" ([FX Replay PDF](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf); pdf; third party; 2026 (undated); confidence high)
- **fxreplay also maintains an author page for JJ Simon, implying the strategy write-up was published with/for him.** ([FX Replay author page: JJ Simon](https://fxreplay.com/author/jj-simon); strategy page / third-party writeup; third party; 2026; confidence medium)
- **fxreplay's video backtest: aggregate validation set of 158 trades (continuations + reversions), 54% win rate, profit factor 1.76, max win streak 8, max loss streak 5; continuation setups had a slightly higher win rate than reversions.** Quote: "Across 158 trades (continuations + mean reversions combined) ... 54% win rate and 1.76 profit factor, with a maximum win streak of 8 and maximum loss streak of 5." ([Video Summary - Backtesting JJ Simon's NQ Strategy (youtubesummary.com)](https://youtubesummary.com/summary/SNO1wqJTq5A); video summary; third party; 2026; confidence high)
- **fxreplay's pre-filter sample: 150 trades, 52% win rate, PF 1.66, +46R. Post-filter: about 62% win rate and PF 2.46.** Quote: "Before filters: 150 trades, 46R, 52% win rate, 1.66 profit factor. After filters: ~62% win rate, 2.46 profit factor." ([Backtesting JJ Simon's NQ Strategy (FX Replay YouTube)](https://www.youtube.com/watch?v=SNO1wqJTq5A); video; third party; 2026; confidence high)
- **fxreplay's filters: skip the first ~3 minutes after 09:30 for continuations; take mean reversions only within the first ~30 minutes of the NY open (i.e. avoid 10:00-11:00 reversions).** Quote: "the presenter suggests avoiding the first ~3 minutes after 9:30 a.m. for continuations and limiting mean reversions to within the first ~30 minutes of the NY open." ([youtubesummary.com summary of FX Replay video](https://youtubesummary.com/summary/SNO1wqJTq5A); video summary; third party; 2026; confidence high)
- **fxreplay sub-sample: a half-month February 2026 subset of 43 trades returned 58% win rate and +19R.** Quote: "the February 2026 subset showed 43 trades with a win rate of 58% and generated 19R total profit (representing only half of February)." ([youtubesummary.com summary of FX Replay video](https://youtubesummary.com/summary/SNO1wqJTq5A); video summary; third party; 2026-02 (data window); confidence medium)
- **fxreplay's presenter explicitly says JJ's payout claims are not independently verified and reports JJ's claim at the time as $1.2M over roughly 12-13 months across Topstep, E8 and Funded Next.** Quote: "JJ is said to claim $1.2M in payouts over approximately 12-13 months across futures prop firms (Topstep, E8, Funded Next), but the presenter notes it's 'not fully verified.'" ([youtubesummary.com summary of FX Replay video](https://youtubesummary.com/summary/SNO1wqJTq5A); video summary; third party; 2026; confidence high)
- **fxreplay's presenter notes results are timing-dependent and that multiple sample periods were tested.** Quote: "reporting strong performance across multiple sample periods ... results can be timing-dependent" ([youtubesummary.com](https://youtubesummary.com/summary/SNO1wqJTq5A); video summary; third party; 2026; confidence medium)
- **The 365-day custom-indicator backtest (YouTube 'Is JJ Simons Method Profitable? We Backtested 365 Days With a Custom Indicator') defines fair price as the pre-open candle, i.e. the last 1-minute candle before 09:30 ET.** Quote: "The fair price is just the price of the candle right before the NASDAQ opens, the pre-open price, before all that institutional volume hits." ([sozai.app transcript: Is JJ Simons Strategy Profitable? I Backtested 365 Days With a Custom Indicator](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); transcript; third party; 2026; confidence high)
- **The 365-day test's phase split differs from fxreplay: continuation only in the first 5 minutes, then reversion-only for the remaining 85 minutes of a 90-minute session.** Quote: "take a continuation away from fair price in the first 5 minutes, and after that only looking for reversion for the following 85 minutes to make a 90-minute session total." ([sozai.app transcript (365-day backtest)](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); transcript; third party; 2026; confidence high)
- **365-day test, un-optimized: profit factor about 1.2. Optimized: 49% return on a $100K micro-Nasdaq (MNQ) account, PF 1.7, 55% win rate; max drawdown about 2.5% of account.** Quote: "a profit factor of about 1.2 initially ... Optimization improved performance to a 49% return on a $100K micro Nasdaq account with a 1.7 profit factor and 55% win rate. ... max drawdown around 2.5% of the account." ([sozai.app transcript (365-day backtest)](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); transcript; third party; 2026; confidence high)
- **The same 365-day video is elsewhere summarized as '52% return' / 'nearly $52,000 on a 100k account' - a second tuned variant mentioned in the video, not a separate study.** Quote: "One tuned version made nearly $52,000 on a 100k account with a 52% return without breaching prop firm drawdown limits." ([Is JJ Simons Method Profitable? We Backtested 365 Days With a Custom Indicator](https://www.youtube.com/watch?v=Esv74mEfTFY); video; third party; 2026; confidence medium)
- **Conclusion of the 365-day tester: mechanically profitable but modest, regime-dependent, best used as a testable framework.** Quote: "JJ Simon's method is mechanically profitable but not extraordinarily so, yielding consistent modest returns. ... The method is regime-dependent and past results do not guarantee future performance." ([sozai.app transcript (365-day backtest)](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); transcript; third party; 2026; confidence high)
- **The 365-day video's hook quotes JJ's own framing that 'one candle' (the pre-open candle) made him $1.3M.** Quote: "JJ Simon claims one candle made him $1.3 million - one line on a chart, the price of a single candle right before the NASDAQ opens." ([sozai.app transcript (365-day backtest)](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/); transcript; third party; 2026; confidence medium)
- **A paid Pine 'JJ SIMONS STRATEGY (Indicator & Strategy Pack)' (NAS100 Continuation + Reversion) exists on ATSLibrary and resellers for about $97. The seller states it is not made by JJ Simon and not part of his mentorship.** Quote: "This is not an indicator made by JJ Simon, nor is it part of the mentorship. It's code from someone who implemented the strategy and made an indicator based on it." ([JJ SIMONS STRATEGY (Indicator & Strategy Pack) FULL PINECODE - ATSLibrary](https://atslibrary.com/product/jj-simons-strategy-indicator-strategy-pack-full-pinecode/); product page; third party; 2026; confidence high)
- **Pack features: continuation and reversion off the pre-open fair line; open-candle bias filter; wick-based or rolling break of structure; session and time-window controls; adjustable stop/target/management; one-reversion-per-session and cooldown options; indicator + automated strategy with editable Pine source.** Quote: "Continuation and reversion off the pre open fair line, open candle bias filter, wick based or rolling break of structure, session and time window controls, adjustable stop, target and management, one reversion per session and cooldown options." ([ATSLibrary product page](https://atslibrary.com/product/jj-simons-strategy-indicator-strategy-pack-full-pinecode/); product page; third party; 2026; confidence high)
- **Pack's advertised backtest: NAS100 (CFD, not NQ futures), last 365 days, $100K account: net +$51,893 (+51.89%), PF 1.94, win rate 56.69% (178 of 314 trades), max drawdown $3,207 (2.38%). Vendor-reported, not independent.** Quote: "Backtested on NAS100, last 365 days, 100K account: Net profit: +$51,893 (+51.89%), Profit factor: 1.94, Win rate: 56.69% (178 of 314), Max drawdown: $3,207 (2.38%)." ([Download JJ Simon (tradingaz.top mirror of product description)](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/); product page (mirror); third party; 2026; confidence medium)
- **Pirated copies of the pack circulate (jjsimonindicator.blogspot.com, tradingaz.top); do not rely on them.** ([JJ Simon: Trading View Indicator Strategy [DOWNLOAD]](https://jjsimonindicator.blogspot.com/); pirate mirror; third party; 2026; confidence medium)
- **joetroyer's 'Fair Price Theory - NQ Reversion / Continuation' anchors a fair-price line to each session open (NY AM, NY PM, London, Asia) and plots Reversion (orange diamonds) and Continuation (blue triangles) setups on the NQ 1-minute chart.** Quote: "anchors a 'fair price' line to each session open, then reads price structure around it to plot two setup types: Reversion (orange diamonds) ... and Continuation (blue triangles)" ([Fair Price Theory - NQ Reversion / Continuation - Indicator by joetroyer](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/); tradingview indicator; third party; 2026; confidence high)
- **joetroyer Reversion definition: price extends to the edge of a +/-38-point premium/discount band around fair price and a displacement candle closes back through toward the fair line.** Quote: "Reversion (orange diamonds) where price extends to the edge of the +/-38-point premium/discount band, and a displacement candle closes back through toward the fair line" ([joetroyer indicator](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/); tradingview indicator; third party; 2026; confidence high)
- **joetroyer Continuation definition: price closes through the fair line with a break of structure, retraces to the line, and continues in the break direction.** Quote: "Continuation (blue triangles) where price closes through the fair line with a break of structure, retraces to the line, and continues in the break direction." ([joetroyer indicator](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/); tradingview indicator; third party; 2026; confidence high)
- **joetroyer grades signals with a mechanical 4-of-5 confluence check, confirms on bar close (non-repainting), has a live confluence panel, a Learning Mode that draws swing pivots, BOS and displacement candles, and alerts for both setups.** Quote: "Each signal is graded on a mechanical 4-of-5 confluence check and confirmed on bar close (non-repainting). ... optional Learning Mode that draws swing pivots, break-of-structure, and displacement candles" ([joetroyer indicator](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/); tradingview indicator; third party; 2026; confidence high)
- **joetroyer's selectable fair-value sources: candle before the volume spike, session open, 9:29 line, VWAP, previous-day close, or a manual line.** Quote: "The fair-value source can be the 'candle before the volume spike, session open, 9:29 line, VWAP, prev-day close, or a manual line.'" ([joetroyer indicator](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/); tradingview indicator; third party; 2026; confidence medium)
- **AndrewFXTD's 'Fair Value Theory + Sessions + Fib' is built for 1m NQ, windows 9:30-11:00 and 2:00-3:00 NY, fib levels 0 / 0.2 / 1 (the 0.2 encodes the 20% counter-wick rule), continuation first ~10-15 min then reversion, entries = displacement candle + BOS/MSB.** Quote: "Fib retracement settings use 0, 0.2, and 1 ... looks for continuations away from fair value the first ~10-15 minutes, then mean reversions back to fair value ... displacement candle + BOS or MSB" ([Fair Value Theory + Sessions + Fib - Indicator by AndrewFXTD](https://www.tradingview.com/script/jfW4Vilk/); tradingview indicator; third party; 2026; confidence high)
- **AndrewFXTD's default risk: 25 pt SL / 37.5 pt TP most commonly, 50 / 75 in volatile conditions, ATR-adjusted.** Quote: "Most commonly uses 25 point SL and 37.5 point TP for 1.5R, or 50 point SL and 75 point TP in volatile times, with adjustments based on ATR levels" ([AndrewFXTD indicator](https://www.tradingview.com/script/jfW4Vilk/); tradingview indicator; third party; 2026; confidence high)
- **microupnup's 'Fair Price Strategy' (FPS) is a third TradingView implementation centered on the 9:29 candle, marking its range and flagging mean-reversion and continuation after liquidity sweeps and structure breaks.** Quote: "a structure-based intraday trading indicator centered around the 9:29 fair price candle ... automatically marks the fair price range created by the 9:29 candle" ([Fair Price Strategy - Indicator by microupnup](https://www.tradingview.com/script/mpU3gOF5-Fair-Price-Strategy/); tradingview indicator; third party; 2026; confidence high)
- **ethanforgotten's 'JJSimon strat' is a closed-source but free TradingView indicator that marks breaks of structure and the displacement candle that triggered each long/short.** Quote: "includes displacement and break of structure (BOS) shows that display different breaks of structure into the market and what displacement candle caused a short/long to happen" ([JJSimon strat - Indicator by ethanforgotten](https://www.tradingview.com/script/9jDxlxC6-JJSimon-strat/); tradingview indicator; third party; 2026; confidence high)
- **No public GitHub repository implementing JJ Simon's strategy was found; the only 'open' Pine code is the paid ATSLibrary pack.** ([GitHub search (negative result)](https://github.com/topics/pinescript-strategies); negative search result; third party; 2026-10-05; confidence medium)
- **'JJ Simon Strategy Backtest: 40 Trades Proves This Works (Or ...)' (earlier title 'Testing JJ Simons' Fair Value Strategy (40 Trades Later...)') frames the test as whether a mechanical strategy survives a full-time job plus prop-firm rules. No statistics surfaced in indexed text.** Quote: "whether a mechanical trading strategy can survive the reality of a full-time job and strict prop firm requirements" ([JJ Simon Strategy Backtest: 40 Trades Proves This Works (Or ...)](https://www.youtube.com/watch?v=c61c4CxTpYI); video; third party; 2026; confidence medium)
- **'Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?' tests the strategy in a prop-firm simulation; uploaded about 38 days before 2026-10-05. Verdict not available in indexed text.** Quote: "JJ Simon claims he made over $1.5 million trading his strategy. So I tested his strategy and tried to pass a prop firm simulation using it." ([Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?](https://www.youtube.com/watch?v=JcW8Wjnw8ck); video; third party; ~2026-08-28; confidence medium)
- **'Win Rate vs. Edge: JJ Simon Strategy vs. Mechanical Fair Value Gap - 52 Trades' compares JJ's higher-win-rate strategy with a mechanical FVG strategy over 52 completed trades. Figures not indexed.** Quote: "comparing JJ Simon's strategy with higher win rate versus a mechanical Fair Value Gap strategy after 52 completed trades" ([Win Rate vs. Edge: JJ Simon Strategy vs. Mechanical Fair Value Gap - 52 Trades](https://www.youtube.com/watch?v=6xZw32_Jp7U); video; third party; 2026; confidence medium)
- **'JJ Simons Strategy Exposed: Profitable or Impossible?' asks whether a part-time trader can hold the edge.** Quote: "explores whether you can actually trade the JJ Simmons strategy and maintain a profitable edge if you don't trade full-time" ([JJ Simons Strategy Exposed: Profitable or Impossible?](https://www.youtube.com/watch?v=FVS85GQGaT0); video; third party; 2026; confidence medium)
- **A YouTube Short 'The Truth About JJ Simons' Strategy' (about 97 days before 2026-10-05) raises the same 9-to-5 / family practicality objection.** Quote: "questioning whether it actually works in practice if you have a 9-5 job or a family" ([The Truth About JJ Simons' Strategy](https://www.youtube.com/shorts/SsDNK-XaMjo); video (short); third party; ~2026-06-30; confidence medium)
- **'I Will Trade JJ Simon's Fair Value Strategy In Real Time Since No One Else Will.' (about 103 days before 2026-10-05) takes one continuation and one reversion live.** Quote: "trades a continuation setup and a mean reversion setup that is based on JJ Simon's Fair Value" ([I Will Trade JJ Simon's Fair Value Strategy In Real Time Since No One Else Will.](https://www.youtube.com/watch?v=IYRtWZHb7Ws); video; third party; ~2026-06-24; confidence medium)
- **'This Strategy Generates 1,500,000? My Take On JJ Simon's Fair Market Value' (about 82 days before 2026-10-05) is an explainer with an idealized example, not a backtest.** Quote: "explains how the creator understands JJ Simon's Fair Value Strategy, then shows an ideal example" ([This Strategy Generates 1,500,000? My Take On JJ Simon's Fair Market Value](https://www.youtube.com/watch?v=2mDNljz-1dU); video; third party; ~2026-07-15; confidence medium)
- **'Can JJ Simon's Trading Strategy Really Make Money?' is another backtest video; no figures indexed.** ([Can JJ Simon's Trading Strategy Really Make Money?](https://www.youtube.com/watch?v=KaYc0m3fcdo); video; third party; 2026; confidence low)
- **faketrades.in lists JJ Simon with one strategy tested ('My $1,300,000 Trading Strategy (Explained in 10 Minutes)'), rating 1.0 star, marked '1 busted'. Its tests run on Indian market data, so it is not a valid NQ test.** Quote: "1 strategy tested with an average rating of 1.0 star ... marked as 1 busted ... backing every verdict with a real backtest on Indian market data" ([JJ Simon - strategies backtested (faketrades.in)](https://app.faketrades.in/guru/jj-simon); backtest aggregator; third party; 2026; confidence medium)
- **X user Joey (@WhizzTrades) reports forward-testing 'JJ Simon's strategy (or similar to it)' for May 2026 and calls it easy, mechanical and algo-able. No numbers.** Quote: "I tested JJ Simon's strategy (or similar to it) for the month of May 2026 - Super easy - Pretty mechanical - Can easily make this into an algo TBH" ([Joey on X](https://x.com/WhizzTrades/status/2066967293033103835); social post; third party; 2026-06-16; confidence high)
- **JJ's displacement-candle rule (own words via transcript): decisive close with counter-wick under 20% of the open-to-counter-wick-extreme distance.** Quote: "A displacement candle must close decisively, with a counter-wick measuring less than 20% of the distance from the candle's open to the counter-wick high or low." ([sozai.app transcript: The Strategy Behind My $1.6M in Prop Firm Payouts](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08 (sozai page ~66 days before 2026-10-05); confidence high)
- **JJ grades setups: A+ = break of structure, A = displacement, B = never take.** Quote: "An A+ setup is a break of structure. An A setup is a displacement. A B setup is something you would never take. Just don't take a B setup." ([sozai.app transcript ($1.6M strategy)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08; confidence high)
- **JJ's own two-week sample: 80 trades over 8 days (10/day), 57.5% win rate at 1:1.5.** Quote: "2 weeks of data showing 80 trades across 8 days with 10 trades per day, demonstrating a 57.5% win rate" ([sozai.app transcript ($1.6M strategy)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08; confidence high)
- **JJ's 1.5R rationale: eval accounts with -$2K max loss and +$3K target make 1:1.5 'automatically optimal'; he demonstrates 25 pt SL / 38 pt TP.** Quote: "evaluation accounts have a maximum loss of -$2K and a profit target of +$3K, making 1:1.5 automatically optimal ... a 25-point stop loss with a 38-point take profit" ([sozai.app transcript ($1.6M strategy)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08; confidence high)
- **JJ stops trading the AM session at 11:00 ET (own words).** Quote: "Unfortunately, I end trading at 11:00 and after 11:00, it reverted all the way back up here." ([sozai.app transcript ($1.6M strategy)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08; confidence high)
- **JJ selects which prop-firm account to trade a given setup on based on displacement size and distance from fair price; aggressive risk to get funded, conservative to stay funded; cycles one trade across multiple funded accounts.** Quote: "adjusting which prop firm account to trade based on the market displacement and points away from fair price ... aggressive risk to get funded and then conservative risk management to stay funded" ([sozai.app transcript ($1.6M strategy)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/); transcript; JJ own words; ~2026-08; confidence medium)
- **JJ (TikTok) concedes that over the last 5 years the simplest continuation model beat the simplest mean-reversion model - a counter-point to a reversion-first replication.** Quote: "the most simple continuation model outperformed the most simple mean reversion model the last 5 years. if you made mean reversion profitable, how did you do it?" ([TikTok discover page: Jj Simon Trading Review (quoting @itsjjsimon)](https://www.tiktok.com/discover/jj-simon-trading-review); social post; JJ own words; 2026; confidence medium)
- **JJ (TikTok) on sizing philosophy: maximize EV, then adjust variance, keeping variance low at first.** Quote: "max EV then mess with variance, but keep variance low to start" ([JJ Simon (@itsjjsimon) TikTok](https://www.tiktok.com/@itsjjsimon); social post; JJ own words; 2026; confidence medium)
- **JJ published his own backtest video, 'Watch Me Backtest My $1,500,000 Trading Strategy'. Statistics not indexed.** ([Watch Me Backtest My $1,500,000 Trading Strategy](https://www.youtube.com/watch?v=MVP7X-3v8xk); video; JJ own words; 2026; confidence medium)
- **allpros.io: JJ's Mentorship rated 4.6/5 from 5 verified reviews; 100% said worth the money; strengths community support 80%, practical content 80%, fast results 60%, real experience 60%; quoted learner: 'I got my first ever payout thanks to JJ.' Pricing not public (pirate sites list $2,500).** Quote: "JJ's Mentorship may be useful for traders who already understand futures basics ... Its strength is risk management and funded-account discipline rather than signal dependency. ... payout claims are not guaranteed" ([JJ's Mentorship Reviews 2026 (allpros.io)](https://allpros.io/course/jjs-mentorship); review site; third party; 2026; confidence high)
- **Whop: JJ's Mentorship rated 4.9 from 46 reviews; tagline 'Learn profitable prop firm futures trading'; a separate 'JJ's Pre Recorded Workshop' product also exists.** Quote: "4.9 rating with 46 reviews" ([JJ's Mentorship (Whop)](https://whop.com/jj-s-mentorship-ba4a/); review site / storefront; third party; 2026; confidence high)
- **No Trustpilot page for JJ Simon / jjsimontrades.com surfaced; Trustpilot results were for unrelated 'Simon' businesses.** ([Trustpilot (negative result)](https://www.trustpilot.com/); negative search result; third party; 2026-10-05; confidence medium)
- **No Reddit, futures.io, EliteTrader or ForexFactory threads about JJ Simon surfaced via site-restricted search.** ([Reddit / forums (negative result)](https://www.reddit.com/); negative search result; third party; 2026-10-05; confidence medium)
- **No dedicated 'scam' exposé of JJ Simon was found; critiques centre on (a) modest edge after mechanization, (b) practicality for part-time traders, (c) unverified payout totals.** ([aggregate of critique videos](https://www.youtube.com/watch?v=FVS85GQGaT0); analysis; third party; 2026-10-05; confidence medium)

## Numbers

| Name | Value | Context | Source |
|---|---|---|---|
| fxreplay validation trades | 158 | continuations + reversions combined | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |
| fxreplay validation win rate | 54% | 158-trade set | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |
| fxreplay validation profit factor | 1.76 | 158-trade set | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |
| fxreplay max win streak / max loss streak | 8 / 5 | 158-trade set | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |
| fxreplay pre-filter trades / WR / PF / R | 150 / 52% / 1.66 / +46R | before time filters | [link](https://www.youtube.com/watch?v=SNO1wqJTq5A) |
| fxreplay post-filter WR / PF | ~62% / 2.46 | skip first 3 min for continuations; reversions only in first ~30 min | [link](https://www.youtube.com/watch?v=SNO1wqJTq5A) |
| fxreplay Feb-2026 subset | 43 trades, 58% WR, +19R | half of February 2026 | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |
| fxreplay ATR tiers (SL/TP pts) | >20 ATR: 50/75; 7-20: 25/37.5; <7: 16.5/24.75 | ATR period unspecified | [link](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) |
| fxreplay contracts per tier | 1 / 2 / 3 NQ | approx $1,000 risk per trade | [link](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) |
| fxreplay page publish date | 2026-04-29 | fxreplay.com/learn listing | [link](https://fxreplay.com/learn) |
| 365-day test initial PF | ~1.2 | un-optimized custom indicator | [link](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) |
| 365-day test optimized return | 49% on $100K MNQ | after optimization | [link](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) |
| 365-day test optimized PF / WR | 1.7 / 55% | after optimization | [link](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) |
| 365-day test max drawdown | ~2.5% | of account | [link](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) |
| 365-day test alt variant | +~$52,000 (52%) on $100K | second tuned variant | [link](https://www.youtube.com/watch?v=Esv74mEfTFY) |
| 365-day test prior-known figures | 289 trades, +$48,700 (49%), PF 1.7 | from task brief; consistent with 49%/1.7 | [link](https://www.youtube.com/watch?v=Esv74mEfTFY) |
| 365-day test continuation window | first 5 minutes | then 85 min reversion-only | [link](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) |
| ATSLibrary pack net profit | +$51,893 (+51.89%) | NAS100 CFD, 365 days, $100K | [link](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/) |
| ATSLibrary pack PF | 1.94 | vendor-reported | [link](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/) |
| ATSLibrary pack WR | 56.69% (178 of 314) | vendor-reported | [link](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/) |
| ATSLibrary pack max DD | $3,207 (2.38%) | vendor-reported | [link](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/) |
| ATSLibrary pack price | $97 | reseller thread | [link](https://clubbingbuy.exchange/threads/jj-simons-strategy-indicator-strategy-pack-full-pinecode-97.4954/) |
| joetroyer band | +/-38 points | premium/discount band around fair price | [link](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/) |
| joetroyer confluence | 4 of 5 | mechanical grading | [link](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/) |
| AndrewFXTD fib levels | 0 / 0.2 / 1 | 0.2 = 20% counter-wick | [link](https://www.tradingview.com/script/jfW4Vilk/) |
| AndrewFXTD default SL/TP | 25/37.5 (50/75 volatile) | points | [link](https://www.tradingview.com/script/jfW4Vilk/) |
| microupnup anchor | 9:29 candle | fair price range | [link](https://www.tradingview.com/script/mpU3gOF5-Fair-Price-Strategy/) |
| faketrades.in rating | 1.0 star, 1 busted | Indian market data | [link](https://app.faketrades.in/guru/jj-simon) |
| allpros rating | 4.6/5, 5 reviews | 100% worth the money | [link](https://allpros.io/course/jjs-mentorship) |
| Whop rating | 4.9, 46 reviews |  | [link](https://whop.com/jj-s-mentorship-ba4a/) |
| Mentorship list price (pirate sites) | $2,500 | unverified | [link](https://wsotradingcourses.com/product/jj-simon-trades-trading-mentorship-course/) |
| JJ own sample | 80 trades / 8 days / 57.5% WR | 1:1.5 R:R | [link](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) |
| JJ eval math | -$2K max loss, +$3K target -> 1:1.5 | 25 pt SL / 38 pt TP example | [link](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) |
| JJ AM cutoff | 11:00 ET | own words | [link](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) |
| JJ displacement wick rule | <20% | counter-wick vs open-to-extreme | [link](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) |
| JJ claim per fxreplay presenter | $1.2M over ~12-13 months | not independently verified | [link](https://youtubesummary.com/summary/SNO1wqJTq5A) |

## Contradictions

- Continuation window: fxreplay/AndrewFXTD say first 10-15 minutes; the 365-day custom-indicator test uses first 5 minutes; fxreplay's filtered variant also drops the first 3 minutes.
- Fair value anchor: fxreplay says the 9:30 open price; the 365-day test and microupnup use the 9:29 (pre-open) candle; joetroyer offers six selectable sources (volume-spike candle, session open, 9:29 line, VWAP, prev-day close, manual).
- Reversion window: fxreplay's filtered version takes reversions only in the first ~30 minutes, whereas JJ's own rule (and the 365-day test) trades reversions through 11:00.
- Point value: a search excerpt of the fxreplay page says 'one point = $1 on NQ'; NQ is $20/pt and MNQ $2/pt. The 365-day test explicitly used micro Nasdaq.
- Profit factor range across tests: 1.2 (raw 365-day) -> 1.66 (fxreplay raw) -> 1.7 (365-day optimized) -> 1.76 (fxreplay validation) -> 1.94 (vendor NAS100 CFD) -> 2.46 (fxreplay filtered). The higher figures all follow filtering/optimization on the same data.
- Trades per day: JJ's own transcript sample is ~10/day; the Chart Fanatics title says 30/day; Words of Rizdom says 20+ scalps/day; the 365-day test produced ~1.2/day (289 trades / 250 days) and the vendor pack ~1.3/day (314 trades). Mechanized rule sets fire far less often than JJ trades.
- Instrument: the vendor pack's 314-trade result is on NAS100 CFD, not NQ futures; fxreplay and the 365-day test used NQ/MNQ.
- JJ's own TikTok statement that the simplest continuation model beat the simplest mean-reversion model over 5 years sits uneasily with a reversion-dominant strategy; fxreplay also found continuations had the slightly higher win rate.
- faketrades.in's '1.0 star / busted' verdict is on Indian market data and should not be weighed against NQ results.

## Open questions

- ATR period and timeframe used for the 20 / 7 ATR tier thresholds (none of the indexed sources state it).
- Exact swing-pivot definition (lookback bars) used for BOS/MSB in fxreplay's test and in each TradingView script.
- Whether 'fair value' at 2:00 PM is the 2:00 PM 1-minute open, the 13:59 close, or something else.
- Full statistics of the 40-trade, 52-trade, 'prop firm challenge' and 'Really Make Money' videos (not in any indexed text).
- Contents of the fxreplay PDF beyond its title (not fetchable under the network policy).
- Monthly and by-setup breakdowns for the 365-day test and fxreplay test; only aggregate numbers surfaced.
- Slippage/commission assumptions in every backtest (none stated in indexed excerpts).
- Whether the 'one reversion per session' and 'open candle bias filter' options in the ATSLibrary pack were on for its advertised 314-trade result.
- Rationale for joetroyer's +/-38-point band and whether it scales with ATR.

## Sources by kind

### JJ marketing page

- [How To Get Consistent Prop Firm Payouts Using The Fair Pricing Theory (jjwebinar.com)](https://jjwebinar.com/) (2026)
- [The Quant Trading Strategy Behind My $2,000,000 In Prop Firm Payouts (jjsimontrades.com)](https://jj.jjsimontrades.com/schedule-call) (2026)

### backtest aggregator

- [JJ Simon - strategies backtested (faketrades.in)](https://app.faketrades.in/guru/jj-simon) (2026)

### pdf

- [JJ Simon's Fair Value Theory NQ Strategy Backtesting Reimagined (PDF)](https://cdn.prod.website-files.com/668852f921e36c3365b91d03/69f277ffef6be0e125ad6a90_JJ%20Simon%20Fair%20value%20theory.pdf) (2026)

### pirate mirror

- [Download JJ Simon (tradingaz.top mirror)](https://tradingaz.top/jj-simon-trading-view-indicator-strategy/) (2026)
- [JJ Simon: Trading View Indicator Strategy [DOWNLOAD]](https://jjsimonindicator.blogspot.com/) (2026)
- [JJ Simon Trades: Trading Mentorship (pirate course listing)](https://wsotradingcourses.com/product/jj-simon-trades-trading-mentorship-course/) (2026)

### product page

- [JJ SIMONS STRATEGY (Indicator & Strategy Pack) FULL PINECODE - ATSLibrary](https://atslibrary.com/product/jj-simons-strategy-indicator-strategy-pack-full-pinecode/) (2026)

### product page / reseller

- [Realised - JJ SIMONS STRATEGY ... FULL PINECODE 97$ (clubbingbuy)](https://clubbingbuy.exchange/threads/jj-simons-strategy-indicator-strategy-pack-full-pinecode-97.4954/) (2026)

### review site

- [JJ's Mentorship Reviews 2026 (allpros.io)](https://allpros.io/course/jjs-mentorship) (2026)
- [JJ's Mentorship (Whop)](https://whop.com/jj-s-mentorship-ba4a/) (2026)

### social post

- [Joey (@WhizzTrades) on X](https://x.com/WhizzTrades/status/2066967293033103835) (2026-06-16)
- [TikTok discover: Jj Simon Trading Review](https://www.tiktok.com/discover/jj-simon-trading-review) (2026)
- [JJ Simon (@itsjjsimon) TikTok](https://www.tiktok.com/@itsjjsimon) (2026)

### storefront

- [JJ's Pre Recorded Workshop (Whop)](https://whop.com/jj-s-pre-recorded-workshop-73/) (2026)

### strategy page

- [JJ Simon's Fair Value Theory Strategy](https://fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy) (2026-04-29)
- [FX Replay author page: JJ Simon](https://fxreplay.com/author/jj-simon) (2026)
- [FX Replay Trading Blog (listing)](https://fxreplay.com/learn) (2026)

### tradingview indicator

- [Fair Price Theory - NQ Reversion / Continuation (joetroyer)](https://www.tradingview.com/script/j4BFY7JW-Fair-Price-Theory-NQ-Reversion-Continuation/) (2026)
- [Fair Value Theory + Sessions + Fib (AndrewFXTD)](https://www.tradingview.com/script/jfW4Vilk/) (2026)
- [Fair Price Strategy (microupnup)](https://www.tradingview.com/script/mpU3gOF5-Fair-Price-Strategy/) (2026)
- [JJSimon strat (ethanforgotten)](https://www.tradingview.com/script/9jDxlxC6-JJSimon-strat/) (2026)

### transcript

- [sozai.app transcript of the 365-day backtest](https://sozai.app/transcript/jj-simons-strategy-backtest-365-days/) (2026)

### transcript (JJ)

- [The Strategy Behind My $1.6M in Prop Firm Payouts - Transcript (sozai.app)](https://sozai.app/transcript/strategy-behind-1-6m-prop-firm-payouts/) (~2026-08)

### video

- [Backtesting JJ Simon's NQ Strategy (FX Replay)](https://www.youtube.com/watch?v=SNO1wqJTq5A) (2026)
- [Is JJ Simons Method Profitable? We Backtested 365 Days With a Custom Indicator](https://www.youtube.com/watch?v=Esv74mEfTFY) (2026)
- [JJ Simon Strategy Backtest: 40 Trades Proves This Works (Or ...)](https://www.youtube.com/watch?v=c61c4CxTpYI) (2026)
- [Can JJ Simon's $1.5M Trading Strategy Really Pass a Prop Firm Challenge?](https://www.youtube.com/watch?v=JcW8Wjnw8ck) (~2026-08-28)
- [Win Rate vs. Edge: JJ Simon Strategy vs. Mechanical Fair Value Gap - 52 Trades](https://www.youtube.com/watch?v=6xZw32_Jp7U) (2026)
- [JJ Simons Strategy Exposed: Profitable or Impossible?](https://www.youtube.com/watch?v=FVS85GQGaT0) (2026)
- [The Truth About JJ Simons' Strategy (Short)](https://www.youtube.com/shorts/SsDNK-XaMjo) (~2026-06-30)
- [I Will Trade JJ Simon's Fair Value Strategy In Real Time Since No One Else Will.](https://www.youtube.com/watch?v=IYRtWZHb7Ws) (~2026-06-24)
- [This Strategy Generates 1,500,000? My Take On JJ Simon's Fair Market Value](https://www.youtube.com/watch?v=2mDNljz-1dU) (~2026-07-15)
- [Can JJ Simon's Trading Strategy Really Make Money?](https://www.youtube.com/watch?v=KaYc0m3fcdo) (2026)

### video (JJ)

- [Watch Me Backtest My $1,500,000 Trading Strategy (JJ Simon)](https://www.youtube.com/watch?v=MVP7X-3v8xk) (2026)

### video summary

- [Video Summary - Backtesting JJ Simon's NQ Strategy](https://youtubesummary.com/summary/SNO1wqJTq5A) (2026)
