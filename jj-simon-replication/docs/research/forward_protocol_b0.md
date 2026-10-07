# Forward paper test: JJ's full rules (Baseline 0) as a third stream

Decided by Chris on 2026-10-07, under `FORWARD_POLICY.md`. The commit that adds this file freezes it.

**Why.** JJ's full rules are what this project set out to investigate. The historical work narrowed them to S3 (continuation only, about 0.9 trades a session) and S4. From here, all three run forward side by side, and only new trades decide which parts of JJ's system work.

**What runs.** Baseline 0 exactly as frozen at commit f585bfb: the research engine with every hook at its default (`ResearchConfig()`).
- That engine rebuilds `sealed/run1/trades.csv` byte for byte (`research/engine_check.py`).
- Continuation and reversion entries, both grades.
- JJ's risk sizing, his three-loss session stop, and positions held to the day's last bar.
- R per trade, the same as one contract's.

No filter, re-selection or optimisation, now or later. A change is a new version, judged on later forward data.

**How it runs.** `research/forward_b0.py` is the forward runner of `forward_protocol_v1.md`, imported unchanged and run with this one candidate, named B0. It shares with S3 and S4:
- the forward bars and the data-condition gate;
- the session and completeness rules, the gap rules and the holiday calendar;
- roll-date exclusion.

It has its own:
- baseline, with checkpoint thresholds from B0's development trades, reported as context;
- pinned hash, in `research/forward_b0_baseline.sha256`;
- state file, ledger, status and paper account.

S3 and S4 are not changed or restarted, and their state is never read or written by this stream.

**Checkpoints.** The same as version 1's: the first 10 sessions, and B0's first 20 and 30 trades. They are flagged against B0's own development distribution. A flag means stop and look, not a verdict.

**Comparison.** The three streams are compared only on trades taken after their forward start. None is ranked or dropped on history.
