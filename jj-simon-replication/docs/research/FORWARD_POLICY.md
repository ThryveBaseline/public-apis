# Research policy: forward only

Set by Chris on 2026-10-07. It replaces the historical research programme in `docs/RESEARCH_PLAN.md` and governs all work from here.

## The rule

S3 is the starting production hypothesis. It runs forward exactly as frozen in `docs/research/forward_protocol_v1.md`. We observe new trades only and learn from what actually happens.

```
S3 v1 -> forward trades -> learn -> S3 v2 -> new forward trades -> learn -> ...
```

Not `idea -> backtest -> tweak -> backtest -> tweak`, forever.

## What stops

- **No more historical strategy work.** That covers:
  - strategy backtests;
  - historical optimization and parameter searches;
  - retrospective candidate ranking;
  - attempts to further validate or invalidate S3 on old market data.
- **Cancelled:**
  - H3's re-simulation on the research engine;
  - further reads of the task-15 economics and the zero-edge control.

  Those reports stand as records of what was learned. Nothing is chosen on them.

## What historical data may still be used for

- Data-quality checks.
- Implementation debugging, for example proving that code reproduces a frozen run.
- Firm-rule verification.
- Factual context.

It may not be used to optimize trading performance or to choose strategy rules.

## How S3 changes

When forward evidence reveals a weakness or an opportunity:

1. Document what happened, from the forward record.
2. Form a specific hypothesis.
3. Make the smallest justified change, as a new version.
4. Freeze that version, with its own protocol, baseline and state. The existing tooling allows this: a version-2 protocol beside version 1, with its own code hashes.
5. Judge it only on forward data that arrives after the freeze.

- Never go backward to select a change because it improves old results.
- Preserve every version and its forward record. A superseded version is kept, not rewritten.
- Version 1's checkpoint thresholds come from history. They answer one question only: is the implementation behaving as designed? A later version's thresholds may come from history for the same purpose, never to justify the change.

## Notes on version 1

- **S4** stays in version 1's runner. Removing it would change frozen code. It has no role in decisions.
- **The paper Topstep account** in the private status is version 1's bookkeeping, at B5's $0.50 fee with dips ignored. Accounting for forward trades at TopstepX's real $1.22 fee, with dips counted, may be added from the forward record. It uses forward trades only.
- **The MBO sidecar** observes forward sessions and forward trades only. Its flags are calibrated on the forward sessions' own order-book states. Anything it suggests becomes a new version, judged on later forward data.

## What remains in scope

Work needed to start and keep the forward test running:
- the forward runner;
- the data-condition gate;
- the daily runs and their checkpoints;
- data-quality handling, such as `docs/research/forward_data_log.md`;
- the forward-only MBO observation.

The first real-money step still waits for about 20 to 30 forward S3 setups with no checkpoint flag. Then Chris decides whether to buy one cheap evaluation.
