# The background lab

Asked for by Chris on 2026-10-17: keep the JJ system running exactly as it is, and have something in the background learning how it could improve and testing those ideas.

**What it is.**
- Versions of the JJ system, each with one setting changed, run every night beside it on paper.
- They use the same bars, data checks, calendar and scoring rules. Each version keeps its own ledger, which never rewrites a scored day.
- The live JJ system (`jj_system_v1.md`) is never touched. Its engine and pins are unchanged.
- The lab runs a copy of that engine with extra settings (`research/jj_lab_engine_b1.py`). At its defaults the copy gives exactly the live system's trades; `tests/test_jj_lab.py` checks this.

**How a version is judged.**
- On each trading day both have scored, the version's total R minus the JJ system's: a paired comparison on the same market, which removes most of the day-to-day noise.
- A version **beats JJ** once it has at least 20 such days and the one-sided lower bound of its mean daily difference is above zero. The bound is at 5% divided by the number of versions tried in all batches so far, so every new idea raises the bar for all of them.
- It **trails JJ** when the upper bound is below zero.
- Before 20 days it is "too early".

**What happens when one beats JJ.** Nothing automatic. It is a proposal for Chris. If he approves, it becomes JJ system version 2: frozen, and judged only on the trading days after it, beside the record of version 1.

**Batches.**
- Each batch is a file `research/jj_lab/batch_NN.json`, committed before its first trading day. A batch's first run pins its file and its engine, and a change refuses.
- A new idea is a new batch, judged only from its own first day.

**Batch 1** (frozen 2026-10-17; first day 2026-10-19, which begins at 18:00 ET on 2026-10-18). Fifteen versions, from:
- his own earlier or alternative statements;
- the clauses where he gives no number, with a value tried;
- two part checks: no overnight orders, and no layering.

| version | what changes | where it comes from |
|---|---|---|
| L01 | continuation window 15 minutes | his June videos; his latest is 5 |
| L02 | evening reversions take 12.5/19 | "take profits of 19 points instead of 38" (6 Sep) |
| L03 | a fourth reversion attempt on a break of structure | "Sometimes a fourth trade only if it's like an A+ setup" (April) |
| L04 | fair value moves after the first losing attempt | losing reversions move fair value; the live system waits for the second |
| L05 | no overnight orders | part check |
| L06 | only the 10 nearest overnight levels | "at least 10 evals placed" |
| L07 | continue the news candle when its body is over 50 points | "unless it's a huge candle" (no size given) |
| L08 | no 18:00 continuation into a gap over 50 points | "I would not be taking continuations into the huge gap" (no size given) |
| L09 | 14:00 session ends at 15:00 | his earlier 14:00-15:00 session |
| L10 | bias from the last 6 hours only | "look back 6 hours" |
| L11 | bias from the last 12 hours only | "the previous 6 to 12 hours" |
| L12 | reversions on breaks of structure only | his funded posture |
| L13 | no layering | part check |
| L14 | no 12.5/19 in the New York sessions | "Never less than 25 points in the New York session" |
| L15 | continuations only with the higher-time-frame bias | his July version |

**The weekly review.** Every Saturday a Claude session:
- reads the forward record and the lab;
- writes a short dated note: what the JJ system's sessions are doing, what the lab shows, and what to try next;
- may add a new batch that uses the existing settings, committed before its first day.

A new kind of setting needs new engine code. That is built and reviewed as a new engine file, never by editing a batch's frozen one.

**No backtests.** The lab runs forward only. No version is chosen, tuned or ranked on historical data.
