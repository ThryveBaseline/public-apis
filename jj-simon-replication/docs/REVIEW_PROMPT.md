# Independent review of a sealed evaluation report

Give each reviewer this file and `sealed/<run>/report.md`. Nothing else: no other reviewer's answer, no transcript, no code. Collect the answers before anyone sees another's.

You are reviewing the sealed result of a frozen trading-rule evaluator run once on real NQ 1-minute data. The rules reconstruct a public trader's method (fair-price continuation and reversion on the 1-minute chart, fixed 25-point stop and 38-point target, prop-firm evaluation economics). The report is the only evidence. Do not propose changes to the rules; you are judging the experiment and the inference, not improving the strategy.

Answer these four questions, each in its own section, with the report's own numbers quoted where they bear on the answer:

1. **What is wrong with this experiment?** Data, leakage, sample size, overlapping starts, censoring, roll handling, same-bar ambiguity, out-of-sample discipline, anything that would make a careful statistician distrust a number in the report.
2. **What conclusions are justified** by the numbers as reported, with their uncertainty?
3. **What conclusions are not justified**, including ones the report's own wording might invite?
4. **What would you test next**, in order, and what result of each test would change your mind?

Keep to the evidence in the report. Where you must assume something, say so in one sentence.
