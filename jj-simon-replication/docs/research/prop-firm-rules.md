# Prop Firm Rule Parameters for Replicating JJ Simon's Setup (Angle 2: prop-firm-rules)

Research date: 2026-10-05 (58 web searches for this angle). Machine-readable rows are in `firm_rules.json` (44 plan rows) and `prop-firm-rules.json`. "Official" = the firm's own help center or site; "3P" = third-party review site. Anything not from an official page is marked unverified in the JSON. Rules change often; re-check the official link before buying.

## 1. Summary table (one row per plan family; dollar figures for 50K / 100K / 150K unless noted)

| Firm / plan | Eval cost | Reset / activation | Profit target | Max drawdown (type) | Daily loss limit | Consistency | Payout timing & caps | Split | Max accounts | Copy trading | Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Topstep** Trading Combine -> Express Funded Account | $49 / $99 / $199 per month (Standard Path); $95 / $149 / $229 No-Activation path | reset = monthly fee; activation $149 (Standard) or $0 | $3,000 / $6,000 / $9,000 | $2,000 / $3,000 / $4,500 EOD-trailing, locks at starting balance | -$1,000 / -$2,000 / -$3,000 (Responsible Trading Program) | Combine: best day <= 55% of target. XFA: Standard none (5 winning days $150+) or Consistency path 40% | 5 winning days or 3 days+40%; min $125; 50% of balance up to $2,000/$3,000 (50K), $3,000/$4,000 (100K), $5,000/$6,000 (150K) per request | 90/10 | 5 active XFAs; unlimited Combines; 20 purchases/month | Yes, own accounts via TopstepX | Official |
| **E8 Futures** Signature (25K/50K/100K/150K) | $110 / $150 / $260 / $390 one-time | no activation; reset unconfirmed | - / $3,000 / $6,000 / $9,000 | 3% EOD-dynamic: $1,000 / $2,000 / $3,000 / $4,500 | none | eval none; funded 35% best-day | first after 14 days; then 5 profitable days (>=0.3%); caps 2.5% / 2.5% / 4.5% / 5.5% then $25k | 80/20 | unlimited evals (3P) | own accounts (3P conflict on multi-eval) | Pricing official; rest 3P |
| **E8 Futures** Zero (50K/100K/200K) | n/a | n/a | 6% | 3% EOD-dynamic, locks at initial balance | none | challenge 40% best-day; performance none | no min days; min $100; max 5 payouts | n/a | n/a | own accounts | Official (partial) |
| **Funded Engineer** | DEFUNCT | - | - | - | - | - | - | - | - | - | Bankrupt 15 Jul 2024 |
| **MyFundedFutures** Core (50K) | $77 / month | $0 activation | $3,000 | 3% EOD trailing | n/a | 40% (3P) | $5,000 per cycle (3P) | 80/20 | 5 small / 3 if 100K+ | Yes | 3P |
| **MyFundedFutures** Rapid | ~$129 / month (3P) | $0 activation | $3,000 (50K) | $2,000 intraday trailing (50K) | none | 50% intraday / 30% EOD | daily (24h); min $500; buffer $2,100 (50K) | 90/10 | 5 small / 3 if 100K+ | Yes | 50K official |
| **MyFundedFutures** Pro | $157 / $267 / $347 per month (3P) | $0 activation | $3,000 / $6,000 / $9,000 | $2,000 / $3,000 / $4,500 EOD trailing | none | 50% (official) vs none (3P) | every 14 days; min $1,000; max $100,000; buffer $2,100 / $3,100 / $4,600 | 80/20 | 5 small / 3 if 100K+ | Yes | mixed |
| **Tradeify** Growth | $145 / $255 / $369 one-time (promo $87 / $153 / $221) | reset $95 / $169 / $229; $0 activation | $3,000 / $6,000 / $9,000 | $2,000 / $3,500 / $5,000 EOD trailing | $1,250 / $2,500 / $3,750 (soft) | eval none; funded 35% | 5 winning days; min balance $53,000 / $104,500 / $156,500; caps $1,500-$3,000 / $2,000-$4,000 / $2,500-$5,000 | 90/10 | 5 sim-funded total | Yes, up to 5 own accounts | Official (params), 3P (price) |
| **Tradeify** Select (ex-Advanced) | $165 / $265 / $369 one-time (promo $99 / $159 / $221.40) | $0 activation | $2,500? / $6,000 / $9,000 | $2,000 / $3,000 / $4,500 EOD trailing | eval none; Select Daily funded $1,000 / $1,250 / $1,750; Flex none | eval 40%; funded none | Daily (no min days) or Flex 5-day; Daily 50K cap $1,000 -> $1,250 (after 2026-09-01); protected balance $52,100 | 90/10 | 5 sim-funded total | Yes | 100K/150K official |
| **Lucid** LucidFlex (25K-150K) | $89 ... $407 one-time (3P) | - | $1,250 / $3,000 / $6,000 / $9,000 | $1,000 / $2,000 / $3,000 / $4,500 EOD trailing, locks | optional | funded none | 5 profitable days; min $500; 50% of balance up to $1,000 / $2,000 / $2,500 / $3,000; 5 payouts then live | 90/10 | 10 eval / 5 funded per household | Yes, own accounts | Official |
| **Lucid** LucidPro (25K-150K) | $123 / $192 / $307 / $410 one-time (3P, 2026-09-16) | - | same as Flex | same as Flex | yes on 50K+ | funded 40% | min profit goal $250 / $500 / $750 / $1,000 per cycle | 90/10 | same | Yes | Official (payouts) |
| **Alpha Futures** Standard | $79 / $159 / $239 per month | activation $149 | $3,000 / $6,000 / $9,000 | $2,000 / $4,000 / $6,000 (4%) EOD trailing | eval none; qualified yes | qualified 40% | 5 winning days >= $200, up to 4/month; max $3,000 / $4,000 / $5,000 per request | 70/70/80/80/90 tiered | 5 | own external -> Alpha only | Official |
| **Alpha Futures** Advanced | $209 / $349 / $489 per month | reset $189 / $319 / $449 | $4,000 / $8,000 / $12,000 | $1,750 / $3,500 / $5,250 (3.5%) EOD trailing | none | qualified 40% | same cadence; max $15,000 per request | 90/10 from first | 3 | own external -> Alpha only | Official |
| **Apex** 4.0 (25K-150K) | Intraday $167 / $249 / $790 / $1,190; EOD $490 / $590 / $1,190 / $2,190 one-time (3P) | activation $69 (Intraday) / $119 (EOD) | n/a | 50K $2,500 / 100K $3,000 / 150K $4,000 trailing; safety net = DD + $100 | none | PA: no day >= 50% of net profit | 5 qualifying days; min $500; weekly; safety net for first 3 payouts | 100% of first $25k then 90/10 | 20 PAs per household | Yes, own PAs, same direction | Accounts/copy official; rest 3P |
| **FundedNext Futures** Flex (bonus) | $70 (50K, 3P) | - | - | $1,500-$4,000 EOD trailing | - | challenge 40%; funded none | 5 rewards then account ends; 24h guarantee | 95% | - | - | 3P |

## 2. Firm-by-firm detail with links

### Topstep
- Combine parameters: targets $3,000/$6,000/$9,000; MLL $2,000/$3,000/$4,500 ([Trading Combine Parameters](https://help.topstep.com/en/articles/8284197-trading-combine-parameters)).
- MLL is EOD-trailing, monitored in real time, locks permanently at starting balance ([What is the Maximum Loss Limit?](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit)); third parties add that after the first payout the MLL is set to $0 ([phidias](https://phidiaspropfirm.com/education/topstep-drawdown)).
- Daily Loss Limit -$1,000/-$2,000/-$3,000 under the Responsible Trading Program ([DLL article](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account)). Whether breach fails the account was not captured (3P: soft lockout).
- Consistency: best day <= 55% of target in the Combine ([Consistency at Topstep](https://help.topstep.com/en/articles/8284208-consistency-at-topstep)).
- XFA payouts: Standard path 5 winning days of $150+; Consistency path 3 trading days + largest day <= 40%; 90/10 ([Payout Policy](https://help.topstep.com/en/articles/8284233-topstep-payout-policy)); caps per request $2,000/$3,000 (50K), $3,000/$4,000 (100K), $5,000/$6,000 (150K), higher with DLL option ([XFA Parameters](https://help.topstep.com/en/articles/8284215-express-funded-account-parameters)).
- 3P payout details: 90/10 from dollar one for accounts created after 2026-01-12; min payout $125; no first-payout floor since 2026-04-28 ([proptradingvibes](https://proptradingvibes.com/blog/topstep-payout-rules)).
- Pricing: $49/$99/$199 per month + $149 activation, or $95/$149/$229 with $0 activation; reset = monthly fee ([propdatalab](https://propdatalab.com/firms/topstep/), [official pricing FAQ](https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions)).
- Accounts: 5 active XFAs; unlimited Combines; 20 purchases/month ([Account Purchase Limits](https://help.topstep.com/en/articles/10370307-account-purchase-limits)).
- Max position 5/10/15 minis via scaling plan ([Scaling Plan](https://help.topstep.com/en/articles/8284223-what-is-the-scaling-plan), [tradetanto](https://tradetanto.com/learn/topstep-rules)). Min trading days: none listed officially.
- Copy trading: allowed via TopstepX Settings -> Copy Trading, own accounts, copier auto-off during payout processing, independent evaluation per account, no cross-account hedging, no VPS/VPN ([proptradingvibes](https://proptradingvibes.com/blog/topstep-copy-trading-rules)).
- News: allowed; CPI window - no new opening transactions on ES/RTY/YM/NQ/NKD minis 5 min before/after ([Economic Releases](https://help.topstep.com/en/articles/8284211-economic-releases)).

### E8 Futures (E8 Markets)
- Signature pricing $110/$150/$260/$390 one-time, no activation or subscription ([All product overviews](https://help.e8markets.com/en/articles/13106558-all-product-overviews-e8-one-vs-e8-zero-vs-e8-pro-vs-e8-signature)).
- Signature rules (3P): 3% EOD-dynamic DD $1,000/$2,000/$3,000/$4,500; targets $3,000/$6,000/$9,000; no DLL; no min days; 4/8/12 minis; 80% split; 35% best-day rule once funded ([damnpropfirms](https://damnpropfirms.com/futures-prop-firms/e8-futures/), [tradetanto](https://tradetanto.com/learn/e8-futures-rules), [capitalcritic](https://www.capitalcritic.ai/blog/e8-futures-account-types-compared)).
- Payouts: first after 14 calendar days, then 5 profitable days >= 0.3%; caps 2.5%/2.5%/4.5%/5.5% then $25,000; buffer equal to EOD drawdown retained ([official caps article](https://help.e8markets.com/en/articles/11940573-payout-caps-and-buffers-for-e8-signature-explained), [proptrusted](https://proptrusted.com/e8-markets-payout-caps/), [proptradingvibes](https://proptradingvibes.com/blog/e8-markets-payout-rules)).
- Copy trading across your own accounts allowed ([Trading Policies](https://helpfutures.e8markets.com/en/articles/10209270-trading-policies-and-prohibited-trading-strategies)); one 3P says not between multiple E8 evals.
- E8 Zero: 6% target, 3% EOD-dynamic locks at initial balance, 40% best-day in challenge only, min payout $100, max 5 payouts ([E8 Zero article](https://helpfutures.e8markets.com/en/articles/15935817-e8-zero-starter-and-max), [40% rule](https://helpfutures.e8markets.com/en/articles/15936479-40-best-day-rule-challenge)).
- Other official pages: [max contract sizes](https://helpfutures.e8markets.com/en/articles/10155917-max-available-contract-sizes), [news trading](https://helpfutures.e8markets.com/en/articles/10209321-can-i-trade-news).

### Funded Engineer
- Filed for bankruptcy 15 July 2024 after FPFX revoked its licence (Feb 2024) alleging fraud; no futures product; no relaunch found ([FX News Group](https://fxnewsgroup.com/forex-news/retail-forex/exclusive-prop-firm-funded-engineer-closes-files-for-bankruptcy/), [Finance Magnates](https://www.financemagnates.com/forex/breaking-prop-trading-firm-funded-engineer-shuts-down/), [tradingfinder](https://tradingfinder.com/props/fundedengineer/), [Prop Firm Match delisting](https://propfirmmatch.com/unlisted-prop-firms/funded-engineer)). Cannot be part of a 2026 replication.

### MyFundedFutures
- Plan overhaul 2025-07-22: Starter/Starter Plus/Expert -> Core, Rapid, Pro; activation fees removed; Core $77/mo (50K only), Rapid $129/mo, Pro $229/mo ([tradecovex](https://tradecovex.com/guides/myfundedfutures-rules-2026)).
- Rapid 50K official: target $3,000; MLL $2,000 intraday trailing; 5 minis; buffer $2,100; daily payouts; min $500; 90/10 ([Rapid Plan 50k](https://help.myfundedfutures.com/en/articles/13134709-rapid-plan-50k-a-comprehensive-look)).
- Pro: $157/$267/$347 per month; targets $3,000/$6,000/$9,000; EOD trailing $2,000/$3,000/$4,500; 80/20; every 14 days; min $1,000; max $100,000; buffers $2,100/$3,100/$4,600 ([thetraderstack 50K](https://www.thetraderstack.com/reviews/myfundedfutures-pro-50k), [official Pro page](https://myfundedfutures.com/plans/pro)).
- Consistency (official): 30% Rapid EOD, 50% Rapid Intraday and Pro ([Consistency Rule](https://help.myfundedfutures.com/en/articles/11994562-consistency-rule-at-myfunded-futures-core-scale-and-pro-plans)).
- Copy trading allowed on all account types; 5 active sim-funded (25K/50K) or 3 if any 100K/150K ([Copy Trading at MFF](https://help.myfundedfutures.com/en/articles/10771500-copy-trading-at-myfundedfutures)).
- News: Tier-1 (FOMC, minutes, NFP, CPI) flat 2 min before/after on Rapid and Pro sim-funded; evals unrestricted ([News Trading Policy](https://help.myfundedfutures.com/en/articles/8230009-news-trading-policy)).

### Tradeify
- Growth eval official: 50K $3,000 / DLL $1,250 / DD $2,000 / 4 minis; 100K $6,000 / $2,500 / $3,500 / 8; 150K $9,000 / $3,750 / $5,000 / 12; pass in 1 day ([Growth Evaluation Accounts](https://help.tradeify.co/en/articles/10495915-growth-evaluation-accounts)).
- Growth funded payouts: 5 winning days; 35% consistency; min balance $53,000/$104,500/$156,500; caps 50K $1,500-$3,000, 100K $2,000-$4,000, 150K $2,500-$5,000; 90% ([Growth Funded Payout Policy](https://help.tradeify.co/en/articles/11083796-growth-funded-account-payout-policy)).
- Select eval: 40% consistency (50% add-on), 3 days min, no DLL, EOD DD $3,000 (100K)/$4,500 (150K) ([Select Evaluation Accounts](https://help.tradeify.co/en/articles/12853921-select-evaluation-accounts)); funded: Select Daily (DLL $1,000/$1,250/$1,750, daily payouts) or Select Flex (5-day, no DLL) ([Select payout policies](https://help.tradeify.co/en/articles/12853966-select-flex-and-select-daily-payout-policies)).
- Prices one-time, no activation: Growth $145/$255/$369 (promo $87/$153/$221), resets $95/$169/$229; Select $165/$265/$369 (promo $99/$159/$221.40); 5 sim-funded max; copy trading across up to 5 own accounts; Select Daily 50K cap $1,000 -> $1,250 after 2026-09-01 ([propdatalab](https://propdatalab.com/firms/tradeify/), [tradetanto](https://tradetanto.com/learn/tradeify-rules-explained-what-every-trader-should-know)).
- News: no restriction ([traderssecondbrain comparison](https://traderssecondbrain.com/guides/futures-prop-firms-news-trading)).

### Lucid Trading
- Limits: 10 active evals and 5 active funded per household, 10 total ([Maximum Number of Accounts](https://support.lucidtrading.com/en/articles/11404617-maximum-number-of-accounts)).
- LucidFlex payouts: 90/10, 5 profitable days, min $500, 50% of balance up to $1,000/$2,000/$2,500/$3,000, 5 payouts then live ([LucidFlex Payouts](https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts)); funded Flex: EOD trailing, optional DLL, no consistency, no buffer ([LucidFlex Funded Account](https://support.lucidtrading.com/en/articles/12945795-lucidflex-funded-account)).
- LucidPro payouts: min profit goal $250/$500/$750/$1,000 per cycle ([LucidPro Payouts](https://support.lucidtrading.com/en/articles/12890092-lucidpro-payouts)); Pro has DLL on 50K+ and 40% funded consistency (3P).
- Prices: LucidPro $123/$192/$307/$410 (2026-09-16), LucidFlex $89-$407; targets $1,250/$3,000/$6,000/$9,000; MLL $1,000/$2,000/$3,000/$4,500 ([proptradingvibes FAQ](https://proptradingvibes.com/blog/lucid-trading-faq), [tradingtoolshub](https://tradingtoolshub.com/blog/lucid-trading-pricing-guide-2026/)).
- Copy trading: copiers permitted between your own eval/funded accounts; copying others or signal services prohibited ([Other Activities](https://support.lucidtrading.com/en/articles/11404728-other-activities)). News allowed (3P).

### Alpha Futures
- Standard: $79/$159/$239 per month; 6% target; 4% MLL ($2,000/$4,000/$6,000); $149 activation; split 70/70/80/80/90; scaling ([Standard Plan Is Back](https://alpha-futures.com/posts/alpha-futures-standard-plan-is-back-rules-fees-what-s-new)).
- Advanced: 50K $4,000 / $1,750 / $209 mo / $189 reset; 100K $8,000 / $3,500 / $349 / $319; 150K $12,000 / $5,250 / $489 / $449; no DLL; no scaling; 90% from start; $15,000 max per request ([Advanced Account Overview](https://help.alpha-futures.com/en/articles/11634907-advanced-account-overview)).
- Payouts: up to 4 per month after 5 winning days >= $200 ([Payout Policy](https://help.alpha-futures.com/en/articles/9492051-payout-policy)); max withdrawal Standard $3,000/$4,000/$5,000, Zero $1,000/$1,500/$2,500 ([Maximum Withdrawal Request](https://help.alpha-futures.com/en/articles/10491202-maximum-withdrawal-request)).
- Accounts: Zero 5, Direct 5, Standard 5, Advanced 3 ([Maximum Allocation](https://help.alpha-futures.com/en/articles/9492088-maximum-allocation)). Copy trading only from your own external account into Alpha ([Terms](https://alpha-futures.com/terms-and-conditions)).

### Apex Trader Funding
- Max 20 PAs per household; copy trading across own PAs (personal + business), same direction, no hedging ([How Many Accounts](https://support.apextraderfunding.com/hc/en-us/articles/4406804554779-How-Many-Paid-Funded-Accounts-Am-I-Allowed-to-Have), [PA and Compliance](https://support.apextraderfunding.com/hc/en-us/articles/31519788944411-Performance-Account-PA-and-Compliance)).
- Apex 4.0 (March 2026, 3P): one-time eval fees Intraday $167/$249/$790/$1,190, EOD $490/$590/$1,190/$2,190; activation $69/$119; 50% consistency in PA; 5 qualifying days; $500 min; 100% of first $25k then 90/10 ([damnpropfirms](https://damnpropfirms.com/futures-prop-firms/apex-trader-funding/), [proptradingvibes](https://proptradingvibes.com/blog/apex-trader-funding-rules-overview)); safety net = DD + $100 (50K $2,500, 100K $3,000, 150K $4,000) for first 3 payouts ([phidias](https://phidiaspropfirm.com/education/apex-trader-funding-4-0-explained)). Official PA pages: [EOD PA](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/), [Intraday PA](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/).

### FundedNext Futures (bonus: JJ reported $129,500 here)
- Flex 50K $70; EOD trailing DD $1,500-$4,000; 40% consistency in challenge only; 95% split; 5 performance rewards then account concludes; 24h payout guarantee ([damnpropfirms](https://damnpropfirms.com/futures-prop-firms/fundednext/)).

## 3. Same trades on multiple accounts (replication-critical)
Every firm above permits copying between accounts you own (Topstep, E8, MFF, Tradeify, Lucid, Apex explicitly; Alpha only from an external master into Alpha). Hard caps per firm on funded/sim-funded accounts: Topstep 5, MFF 5 (3 if 100K+), Tradeify 5, Lucid 5, Alpha 5 (Advanced 3), Apex 20, E8 unverified. Summing the official caps across Topstep + MFF + Tradeify + Lucid + Alpha + Apex gives roughly 45 funded accounts, which matches JJ's stated 20-45 account range. Evaluations are far less constrained (Topstep unlimited, Lucid 10, E8 unlimited).

## 4. Contradictions
1. Funded Engineer bankrupt July 2024 vs ~$180k credited to it in JJ's July 2026 video.
2. E8 copy trading: official "own accounts allowed" vs 3P "not between multiple E8 evals".
3. E8 buffer: "equal to EOD drawdown" vs "4% profit buffer".
4. E8 reset fee: $0 / $88 setup (3P, unconfirmed) vs official "no activation or subscription fees".
5. MFF Pro consistency: 50% (official article) vs none (thetraderstack).
6. MFF Rapid payouts: daily (official) vs every 5 winning days with $1,250 cap (tradecovex).
7. MFF Pro price: $157/$267/$347 vs $229/mo vs $227-$477.
8. Alpha Advanced price: official $209/$349/$489 vs 3P $139/$279/$419.
9. Tradeify Select 50K target: $2,500 (one 3P) vs $3,000.
10. Apex drawdown: dollar figures ($2,500/$3,000/$4,000) vs "5% EOD trailing".
11. Topstep min trading days: none (official) vs 2 or 5 (3P).
12. Topstep DLL consequence (fail vs daily lockout) not captured.

## 5. Open questions
- E8 Zero futures pricing; E8 Signature reset availability.
- MFF Rapid 100K/150K parameters; Core exact drawdown and consistency.
- Tradeify Select 50K official target; Select Flex caps for 100K/150K.
- LucidPro per-request caps and DLL amounts.
- Alpha qualified-account DLL amounts.
- Apex per-size payout caps and contract limits; 20-PA cap wording (person vs household).
- Identity of JJ's "Funded Engineer".
- Official news-trading pages for Tradeify, Lucid, Alpha, Apex (only a 3P comparison captured).

## 6. Full source list

### Official
- https://help.topstep.com/en/articles/8284197-trading-combine-parameters
- https://help.topstep.com/en/articles/8284215-express-funded-account-parameters
- https://help.topstep.com/en/articles/8284233-topstep-payout-policy
- https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit
- https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account
- https://help.topstep.com/en/articles/8284208-consistency-at-topstep
- https://help.topstep.com/en/articles/10370307-account-purchase-limits
- https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions
- https://help.topstep.com/en/articles/8284211-economic-releases
- https://help.topstep.com/en/articles/8284223-what-is-the-scaling-plan
- https://help.e8markets.com/en/articles/13106558-all-product-overviews-e8-one-vs-e8-zero-vs-e8-pro-vs-e8-signature
- https://help.e8markets.com/en/articles/11940573-payout-caps-and-buffers-for-e8-signature-explained
- https://helpfutures.e8markets.com/en/articles/15935817-e8-zero-starter-and-max
- https://helpfutures.e8markets.com/en/articles/15936479-40-best-day-rule-challenge
- https://helpfutures.e8markets.com/en/articles/10209270-trading-policies-and-prohibited-trading-strategies
- https://helpfutures.e8markets.com/en/articles/10155917-max-available-contract-sizes
- https://helpfutures.e8markets.com/en/articles/10209321-can-i-trade-news
- https://help.myfundedfutures.com/en/articles/13134709-rapid-plan-50k-a-comprehensive-look
- https://help.myfundedfutures.com/en/articles/10771500-copy-trading-at-myfundedfutures
- https://help.myfundedfutures.com/en/articles/11994562-consistency-rule-at-myfunded-futures-core-scale-and-pro-plans
- https://help.myfundedfutures.com/en/articles/8230009-news-trading-policy
- https://myfundedfutures.com/plans/pro
- https://myfundedfutures.com/plans/builder
- https://help.tradeify.co/en/articles/10495915-growth-evaluation-accounts
- https://help.tradeify.co/en/articles/12853921-select-evaluation-accounts
- https://help.tradeify.co/en/articles/11083796-growth-funded-account-payout-policy
- https://help.tradeify.co/en/articles/12853966-select-flex-and-select-daily-payout-policies
- https://help.tradeify.co/en/articles/10468320-rules-consistency-rule
- https://help.tradeify.co/en/articles/10468321-rules-daily-loss-limit
- https://support.lucidtrading.com/en/articles/11404617-maximum-number-of-accounts
- https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts
- https://support.lucidtrading.com/en/articles/12890092-lucidpro-payouts
- https://support.lucidtrading.com/en/articles/12945795-lucidflex-funded-account
- https://support.lucidtrading.com/en/articles/12890069-lucidpro-funded-account
- https://support.lucidtrading.com/en/articles/11404728-other-activities
- https://alpha-futures.com/posts/alpha-futures-standard-plan-is-back-rules-fees-what-s-new
- https://help.alpha-futures.com/en/articles/11634907-advanced-account-overview
- https://help.alpha-futures.com/en/articles/9492051-payout-policy
- https://help.alpha-futures.com/en/articles/10491202-maximum-withdrawal-request
- https://help.alpha-futures.com/en/articles/9492088-maximum-allocation
- https://alpha-futures.com/terms-and-conditions
- https://support.apextraderfunding.com/hc/en-us/articles/4406804554779-How-Many-Paid-Funded-Accounts-Am-I-Allowed-to-Have
- https://support.apextraderfunding.com/hc/en-us/articles/31519788944411-Performance-Account-PA-and-Compliance
- https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-performance-accounts-pa/
- https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-performance-accounts-pa/

### News (Funded Engineer closure)
- https://fxnewsgroup.com/forex-news/retail-forex/exclusive-prop-firm-funded-engineer-closes-files-for-bankruptcy/
- https://www.financemagnates.com/forex/breaking-prop-trading-firm-funded-engineer-shuts-down/
- https://tradingfinder.com/props/fundedengineer/
- https://propfirmmatch.com/unlisted-prop-firms/funded-engineer

### Third-party review sites used for prices and restatements
- https://propdatalab.com/firms/topstep/ ; https://proptradingvibes.com/blog/topstep-payout-rules ; https://proptradingvibes.com/blog/topstep-copy-trading-rules ; https://tradetanto.com/learn/topstep-rules ; https://phidiaspropfirm.com/education/topstep-drawdown
- https://damnpropfirms.com/futures-prop-firms/e8-futures/ ; https://tradetanto.com/learn/e8-futures-rules ; https://proptrusted.com/e8-markets-payout-caps/ ; https://proptradingvibes.com/blog/e8-markets-payout-rules ; https://www.capitalcritic.ai/blog/e8-futures-account-types-compared ; https://tradeinformer.com/broker-news/e8-markets-scraps-activation-fees-including-for-futures-accounts
- https://tradecovex.com/guides/myfundedfutures-rules-2026 ; https://www.thetraderstack.com/reviews/myfundedfutures-pro-50k ; https://www.thetraderstack.com/reviews/myfundedfutures-pro-150k ; https://thepropjournalist.com/reviews/my-funded-futures/ ; https://www.futureshive.com/blog/myfundedfutures-review-2026
- https://propdatalab.com/firms/tradeify/ ; https://tradetanto.com/learn/tradeify-rules-explained-what-every-trader-should-know ; https://damnpropfirms.com/futures-prop-firms/tradeify/
- https://proptradingvibes.com/blog/lucid-trading-faq ; https://tradingtoolshub.com/blog/lucid-trading-pricing-guide-2026/
- https://saveonpropfirms.com/blog/alpha-futures-standard-plan ; https://tradetanto.com/learn/alpha-futures-rules-every-plan-rule-and-limit
- https://damnpropfirms.com/futures-prop-firms/apex-trader-funding/ ; https://proptradingvibes.com/blog/apex-trader-funding-rules-overview ; https://phidiaspropfirm.com/education/apex-trader-funding-4-0-explained
- https://damnpropfirms.com/futures-prop-firms/fundednext/
- https://traderssecondbrain.com/guides/futures-prop-firms-news-trading
