# JJ SIMON REAL-DATA + IMPROVEMENT MISSION

Operating brief for every session and model working on this project (Claude on the Surface, Claude in the cloud, the GB10 models, Laya, Jev). Written by Chris; the frozen Baseline 0 is commit `f585bfb` (`docs/FROZEN.md`), the data rules are in `docs/DATA_PROTOCOL.md`, the review questions in `docs/REVIEW_PROMPT.md`, the Databento session's steps in `docs/SURFACE_BRIEF.md`.

We are moving from reconstruction into real-data testing and then, if necessary, systematic improvement.

The objective is not merely to determine whether our exact reconstruction of JJ Simon's published strategy works unchanged. The objective is: start with JJ Simon's strategy, prop-firm mathematics, and trading framework as Baseline 0, reproduce it faithfully, measure it honestly, then discover and validate whatever changes, additions, combinations, or policies are required to build a robust profitable process for us.

The frozen JJ implementation is commit `f585bfb`. That commit remains permanently preserved as Baseline 0. `sealed/run1` must be produced from that frozen implementation before any strategy optimization begins.

## PHASE 1 — FIND OR ACQUIRE THE DATA

Before buying new Databento data, inspect the GB10 for NQ 1-minute data already acquired for other trading work. Do not assume existing data is suitable just because it contains NQ. Existing GB10 data may be used only if you can verify:

* trustworthy provenance
* NQ 1-minute OHLCV
* timestamp source and timezone known, preferably UTC source timestamps
* contract or symbol identity preserved
* enough historical coverage for multi-year study
* no unknown price adjustment; no hidden back-adjusted continuous-series transformation
* roll behavior can be identified
* no preprocessing that could alter session opens, gaps, highs, lows, stops, targets, or fair-value calculations
* data can be converted into the frozen evaluator's expected format without changing trading logic

If existing GB10 data satisfies the frozen protocol, report that fact and its provenance before using it. If anything material is unknown, ambiguous, transformed, insufficient, or unsuitable, do not try to save time by forcing it to fit. Use Databento instead.

### Databento path

On the Surface, locate the local `access.txt` containing the Databento credential. The credential may be used locally only. Never print it, echo it, log it, commit it, include it in a report, transmit it to GB10 models, or expose it to another model.

Before purchasing or downloading data, obtain a quote only. Frozen preferred data specification: dataset `GLBX.MDP3`; schema `ohlcv-1m`; primary series `NQ.n.0`; cross-check series `NQ.c.0`; unadjusted prices; symbol column retained; enough history to span materially different NQ regimes; final 12 months reserved as untouched out-of-sample data.

Report before purchase: available date range; proposed date range; dataset; schema; symbol methodology; roll methodology; whether any prices are adjusted; approximate rows; approximate file size; Databento cost; development period; walk-forward period; untouched 12-month OOS period. Do not download until Chris approves the quote. Once approved, download the data and preserve the original/raw copy.

## PHASE 2 — DATA HYGIENE

The frozen loader already supports Databento `ohlcv-1m`. Preserve `ts_event`, UTC time, open, high, low, close, volume if available, symbol/contract identity. The evaluator already detects contract-roll dates from the symbol field and excludes those dates from signal generation. No back-adjusted price series is permitted for Baseline 0. Roll gaps must never be allowed to manufacture false fair-value moves, displacement events, continuation moves, or reversion trades.

Same-bar stop/target ambiguity must remain conservative. If both the stop and target occur inside the same 1-minute bar and the ordering cannot be established: `ambiguous_bar = true` and the trade is resolved as a loss/stop, never in our favor. Report the ambiguity count. Do not improve the baseline by resolving ambiguity optimistically.

## PHASE 3 — FREEZE AND SEAL BASELINE 0

Before running: verify the repository is clean and the evaluator corresponds to frozen commit `f585bfb`. Do not alter `fpt/` or `pine/`. Do not change entries, exits, fair-value logic, displacement, structure, continuation rules, reversion rules, stops, targets, sizing, session logic, or account logic. If a data-loading problem or objectively incorrect implementation problem prevents the frozen specification from being executed as intended, document it separately. Do not silently change trading behavior.

Then run:

```
cd jj-simon-replication
python3 scripts/seal_run.py --csv data/nq_1min_databento.csv --source-tz UTC --out sealed/run1 --oos-months 12
```

`seal_run.py` must produce and preserve: report, trades, manifest, data hash, row count, date range, commit, `fpt/` tree hash, runtime options, output hashes, roll dates excluded, ambiguity count, `SEALED` marker. Never overwrite `sealed/run1`. Commit `sealed/run1` unchanged.

## PHASE 4 — FIRST READ OF RUN1

Before optimizing anything, read the sealed result exactly as produced. The first measurements that matter:

1. **OOS 50K evaluation pass probability**: P(profit target reached before max drawdown) under the exact evaluation rules.
2. **OOS uncertainty**: use the report's Newey-West estimate. Consecutive evaluation starts overlap and are not independent; do not interpret the raw number of starts as the number of independent experiments. As an intuition check compare OOS trading days / median days to resolution; do not substitute that for the formal estimate.
3. **OOS net expectancy in R**: the `all` row of the OOS R-distribution table.
4. **Hygiene**: ambiguous bars, excluded roll dates, missing periods, malformed rows, any timezone or calendar problems.
5. **Stability**: by year, quarter, volatility regime, continuation, reversion, session/time, drawdown behavior, days to resolution.

## PHASE 5 — INDEPENDENT REVIEW

Do not let models influence each other before their first review. Claude receives `docs/REVIEW_PROMPT.md` and the sealed `report.md` and nothing from GB10 reviewers; GB10 reviewers receive the same sealed evidence independently. Each reviewer answers: What is wrong with this experiment, if anything? What conclusions are justified? What conclusions are not justified? What should be tested next? Preserve each reviewer's original answer. Do not allow a reviewer to rewrite its critique after seeing another model's answer. Then give the independent reviews to Jev for synthesis and adjudication: agreement, disagreement, real methodological problems, unsupported objections, useful next experiments, whether the baseline result is economically interesting.

**RUN1 IS NOT A KILL GATE.** A disappointing Baseline 0 result does not mean "JJ failed, stop." It means: find out why. Baseline 0 exists so we know precisely where we started. The broader mission is JJ Baseline -> diagnose -> hypothesize -> modify -> test -> retain or reject -> repeat. Baseline is a measurement. Failure is a research direction.

## PHASE 6 — IF JJ BASELINE IS NOT GOOD ENOUGH, MAKE THE PROCESS BETTER

After `sealed/run1` exists, create a separate research branch. Never overwrite or modify Baseline 0. Candidate systems become B1, B2, B3, ... Each candidate must have explicit provenance: what changed; why; which weakness it targets; what data was used to invent it; what data was used to test it; result versus Baseline 0.

Claude, GB10 models, Laya, Jev, and other approved research workers may now actively search for ways to improve the process. They are not executioners; their task is to discover a system that works. If the baseline is weak, investigate why before declaring the idea dead. Areas to explore include: continuation and reversion separately; session effects; time-of-day effects; volatility, trend and chop/range regimes; opening-candle properties; fair-value definitions and alternative anchors; re-anchoring logic; displacement and structure definitions; entry confirmation and entry delay; stop and target geometry; dynamic and volatility-scaled brackets; position sizing; daily-loss behavior; number of attempts; evaluation-specific and funded-account-specific policy; firm-specific policies; payout timing; drawdown geometry; order flow, microstructure, volume, momentum, mean-reversion context, liquidity, market breadth where relevant; other discoveries from our trading research; combinations of individually weak signals. Do not assume a signal must be strong by itself: search for Signal A + Signal B + Context C where the combination creates an edge none of the components has alone.

### Constructive research rule

When something appears to fail, classify the failure first:

* **A. Data failure** (bad timestamps, corrupted bars, contract-roll artifact): fix the data problem.
* **B. Implementation failure** (code does not implement the intended published rule): correct the implementation.
* **C. Interpretation failure** (JJ's wording was misunderstood): return to the source evidence and determine the most defensible interpretation.
* **D. Evaluation/account-model failure** (payout logic, trailing drawdown, daily-loss logic, or a firm rule modeled incorrectly): correct the model.
* **E. Genuine strategy weakness** (a correctly implemented setup loses money in a particular environment): that becomes a research target.

Do not kill the strategy because of A-D. Fix A-D and rerun cleanly. For E, search for modifications or conditions that improve it.

### Do not overfit

"Make it work" does not mean tweak history until the equity curve looks beautiful. Every proposed improvement must: solve an identified weakness; be developed only on permitted research/development data; produce measurable improvement there; survive walk-forward testing; survive unseen data; include realistic costs and slippage; respect prop-firm mechanics; survive ambiguity treatment; avoid relying on one lucky quarter; beat the previous candidate honestly. If an improvement disappears outside the period where it was invented, reject it.

### Primary optimization objective

Do not optimize mainly for win rate. Win rate, profit factor, Sharpe and R expectancy are diagnostic. The operation exists to generate withdrawable money while controlling bankruptcy risk. Primary outputs: P(evaluation pass); P(first payout | funded); E[withdrawable dollars per evaluation dollar]; P(bankroll survival); median time to first payout; time to recover the original bankroll; time to self-funded expansion. Evaluation policy and funded-account policy do not have to be identical; if different behavior maximizes each state's economics, model them separately.

## PHASE 7 — $2,000 BOOTSTRAP

Do not use JJ's assumed numbers once our measured numbers exist. Feed our measured pass probability, funded-to-payout probability, payout size, days to evaluation resolution, days to payout, failure distribution and firm rules into the bootstrap simulator. Model $2,000 -> evaluation attempts -> funded accounts -> payouts -> reinvestment. Produce: probability of total bankroll loss; probability of at least one payout; probability of recovering the original $2,000; median days to first payout; median days to recover initial capital; median capital after 30/60/90 trading days; downside and upside percentiles.

## REAL-MONEY PROGRESSION

Chris is not going to sit on paper for 60 days if the evidence is already becoming strong; design around that. The operating rule: move fast on experimentation, scale slowly on exposure. Real capital unlocks progressively as evidence earns it. Do not require an arbitrary calendar period if statistical and economic evidence becomes strong sooner; do not scale merely because an early streak looks exciting. Exposure increases are driven by predefined evidence gates, for example: historical OOS survives -> live paper behavior agrees -> tiny real evaluation pilot -> funded account -> first payout -> repeated payout evidence -> larger rollout. The exact gate thresholds come from the measured system and the bootstrap results.

## MODEL BEHAVIOR

Claude and GB10 models should be optimistic about search, not optimistic about results. The attitude is "There may be a workable edge here. Search hard, test carefully, and keep improving while credible avenues remain." Not "find a reason this cannot work", and not "make the numbers look good". The standard: **give the idea every fair opportunity to work without lying to ourselves.** If hundreds of sensible variants, combinations, regimes and policies eventually fail genuinely unseen testing, Jev may conclude that the branch is exhausted; that conclusion comes after serious discovery work, not after one disappointing JJ baseline.

## IMMEDIATE NEXT ACTION

First determine whether the GB10 already has suitable NQ 1-minute data. If it does, verify it against the protocol and report its provenance. If it does not, use the Surface Databento credential to obtain the quote. Once the data source is approved: run frozen Baseline 0, create `sealed/run1`, preserve the result, perform independent reviews, then begin the improvement program if needed. Do not build anything else before the data decision and the sealed baseline run.

The frozen JJ run protects us from fooling ourselves; the research branch protects us from prematurely giving up on something that could be made much better. We get both.
