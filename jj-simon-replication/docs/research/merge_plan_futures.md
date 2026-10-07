# One futures program: JJ Simon's framework and the MBO microstructure lane

Written 2026-10-07, when Chris handed the futures/minis lane (built with Codex and ChatGPT) to this session.

**The mission.** Find small, repeatable, observable ES/NQ states where the odds turn favourable enough to exploit after realistic execution, long or short, continuation or reversion, with abstention always allowed. JJ Simon's framework is one hypothesis family inside that search, not the whole of it. No live money: Chris decides when anything advances.

## What each lane has measured

**The JJ lane** (this repository). It covers 1-minute NQ from 2010-06 to 2026-10, with a sealed baseline and walk-forward tools.
- **Continuation.** Continuation's direction call carries information beyond drift, in 14 of 16 years. With an ATR-scaled bracket it makes about +0.04 R per trade on stops of roughly 25–150 points (100–600 ticks). Costs there are about 1–2% of R.
- **One condition passed.** H3, continuation after a large opening candle, is the only one of nine pre-registered conditions to pass.
- **Prop-firm economics, with every fee:**
  - Topstep's payout structure alone pays roughly +$90–160 per evaluation, even with no edge.
  - Continuation's edge adds about as much again.
  - From $2,000, one account at a time survives the development paths. The details are in `docs/reviews/run1_b5_read.md`.

**The MBO lane** (round 1). It covers 12 ESZ6/NQZ6 GLBX MBO sessions, 2026-09-17 to 10-02, with 415M events; 10 sessions pass reconstruction.
- **Every test was negative before fees.** That covers 1,832 one-second rules and 720 candidate × delay × exit settings, all taker trades with 2-tick stops, 2–4-tick targets and 10–30 s horizons.
- **The best conditioning** moved ES SHORT from −0.77 to −0.37 gross ticks per trade, at the cost of falling frequency.
- **The best mid-price drifts** are about +0.3 to +0.43 ticks.
- **Other results:**
  - A progressive search improved one branch over two generations, from −2.64 to −2.42 net ticks, still negative.
  - Qwen as a forecaster did no better than chance. It stays useful for proposing hypotheses.
  - No local LLM qualified as a reviewer.

## The fact that joins them: cost against move size

A mini round trip costs about 1.5 ticks on ES and 2.1 on NQ: provisional fees plus one adverse tick, with the spread crossed at entry. Against 2–4-tick targets that is half the target or more. Against a 100–600-tick stop it is 1–2% of the risk.

Round 1's best signals move the mid-price by a fraction of a tick. That makes them unlikely to pay as standalone 2-tick scalps, but potentially valuable in three other roles:
1. **Timing for larger trades.** Entering or exiting a JJ-scale trade 1–2 ticks better is worth +0.01 to +0.02 R on a 100-tick stop. That is a quarter to a half of continuation's whole edge.
2. **State classification.** Telling continued displacement from the start of reversion before a 1-minute candle shows it.
3. **Abstention.** Not trading when the book says the move is already spent, or the spread and stop geometry are hostile.

Short-duration trades are not ruled out. The measurement they need is the frontier: how the conditional move grows with horizon and target size, against cost, per state. A short horizon is worth trading only where that move clears about 1.5–2 ticks after costs.

## The program

**1. A shared state layer.** One causal feature set, computed the same way at every resolution, from raw events to 1-minute bars:
- JJ's state variables:
  - the 09:30 reference (fair value) and the distance from it, in ticks and in ATR;
  - time since the open, and the initial displacement;
  - the continuation window, reversion attempts, failed reversions, and the drift of the value area;
  - H3's opening candle;
  - scheduled-news windows.
- Round 1's microstructure features:
  - imbalance at levels 1 and 5, OFI and signed flow;
  - depletion and refill, the microprice and the spread;
  - ES/NQ agreement and lead/lag, normalised by volatility.

**2. A first bridge, on data already bought.** The sealed ledger covers 2026-09-17 to 10-02, so JJ's own entries on the 10 admitted MBO sessions are known: roughly 40–60 trades.
- For each one, from the MBO data:
  - the book state in the seconds before the signal minute closes;
  - whether a microstructure-timed entry would have filled better;
  - whether book state separated the winners from the losers.
- It is too small to decide anything. It shows, on real trades, whether the timing and state roles above are visible at all, and which features to carry forward.

**3. The cost frontier.** On the 10 sessions, for long, short and abstain: the first-passage outcome (target before stop) is measured across a grid of target and stop sizes, from 2 to 40 ticks, and horizons from 5 seconds to 15 minutes. It is measured overall and conditioned on JJ states and round 1's best features. This finds the scale at which conditional moves first outrun costs, if any does.

**4. The specialist colony.** Cheap models come first; each model's output becomes a feature for the others.
- **First, on the CPU:**
  - logistic and boosted-tree baselines;
  - an EBM for readable interactions;
  - competing-risk hazards for first passage (target, stop or timeout);
  - Hawkes intensities for event clustering;
  - a queue and adverse-selection model, kept out of any fill claim until maker fills are qualified.
- **Then, on the GB10's GPU:** order-book models (TLOB, MLPLOB, a BiN-style compact model) on event-sampled 10-level books, as specialists, not a winner-take-all contest.
- **For each model, a specialization map:** where it helps and where it fails, long and short, continuation and reversion, its regimes, its sensitivity to delay, and its useful abstentions.
- **Then a search over model outputs** with round 1's progressive engine.
- **Validation** walks forward by day. Nothing is called validated on the sessions it was chosen on.

**5. The daily loop,** once new sessions arrive. The day runs observe, predict and seal; then score and diagnose; then challengers. Today's frozen model runs today, and its challenger runs beside it tomorrow. No prediction is ever rewritten. This needs forward MBO data, which needs a Databento quote that Chris approves.

## Rules carried over

- Pre-registration before any number that decides anything.
- Walk-forward selection, a benchmark beside that never chooses, and independent adversarial review of every tool before it touches real data.
- Numerical code owns the arithmetic. No language model has authority over evidence.
- Discovery classifies concerns as fatal, a measurement, or an experiment. Only frozen candidates get the hostile treatment.
- Raw and reconstructible data stay on the GB10. The heavy computation runs there.
- No purchase without a quote that Chris approves. No credential is ever printed or transmitted.
