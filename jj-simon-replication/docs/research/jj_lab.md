# The JJ learning lab

**What Chris asked for, 2026-10-17:** keep the JJ system running exactly as it is. Beside it, something should:
- take everything JJ's system does;
- learn what went well, what didn't, and what it could have done;
- build off the entire thing, testing it in the background.

The live JJ system (`jj_system_v1.md`) is never touched: its files, pins and record are unchanged. Everything below runs on paper beside it, forward only.

## The loop

1. **Journal** (`research/jj_lab_engine_b2.py`). Every trading day the system has scored is rerun with a copy of its engine that also records every decision:
   - each session's opening and every change of its fair value, with the reason;
   - every signal its rules saw: a break of structure or a displacement toward fair value inside a session, or a continuation break. Each is recorded as taken or not; if not, with the rule that stopped it ("biases opposed", "under 15 points of room", "last one not halfway", "three losses in a row", ...);
   - every overnight order placed;
   - every break-even move and early exit, with the reason.

   At its defaults the copy gives exactly the live system's trades, with or without the journal (`tests/test_jj_learn.py`). Each night it is checked against the live ledger; if they ever differ, the report says so and stops.

2. **What it could have done** (`research/jj_whatif.py`). Every signal, taken or passed, is replayed on the real bars:
   - with every stop in 12.5, 25, 50 against every target in 19, 38, 76, 100;
   - held to the day's end;
   - with how far it went for and against.

   For a trade with no management, the replay of its own bracket gives exactly its result (tested).

3. **The nightly learning report** (`research/jj_learn.py`), with no Claude and no cost. From the forward record only, it covers:
   - **what went well and badly**, by session, setup, grade, direction, hour, bias, news day, weekday and layer;
   - **what each rule did**: what the signals it passed on would have made, so a rule that kept the system out of losers earns its place and one that kept it out of winners costs;
   - **what other exits would have made** for the same trades, overall and by session;
   - **how far trades went first**: stops that were first halfway to their target, and targets with twice as much more to give;
   - **moves it missed**: sessions where price went more than 38 points from fair value and came back with no reversion taken, and why not;
   - **findings**: the largest of these in plain sentences, each with its number of trading days.

   A day's trades move together, so the sample is days. Anything under 10 days is marked early.

4. **The weekly builder.** Every Saturday a Claude session reads the report, the forward record and the lab. It writes what went well, what didn't, and what the system could have done. Then it **builds the next challenger, "JJ+ generation N"**:
   - the whole JJ system with every change the evidence supports, all at once;
   - **one ablation per change**: the challenger without that change, so each change's share is measured.

   The challenger and its ablations are a batch file (`research/jj_lab/batch_NN.json`), frozen before their first trading day. A change the settings cannot express is built as a new engine file: a copy of the latest, at whose defaults the live system's trades come out exactly (tested), never an edit to a frozen one.

5. **Judging.** Every version is compared with the live JJ system on the trading days both have scored: the version's day R minus the live system's, so the same market is on both sides.
   - A version **beats JJ** once it has at least 20 such days and the one-sided lower bound of that daily difference is above zero, at 5% divided by the number of versions tried so far. Every new idea raises the bar for all of them.
   - Earlier generations keep running, and their records are kept.

6. **Promotion is Chris's.** A version that beats JJ comes to him as a candidate for JJ system v2. If he approves, it is frozen and judged only on the days after it, beside v1's record.

**No backtests.** Learning uses only the forward days already scored. A version is judged only on days after its own freeze, never on the days it learned from.

## The settings a challenger can use (engine b2)

Each setting's default is the live system:
- **The one-setting dials of batch 1**: continuation window, evening brackets, a fourth attempt, re-anchoring, overnight-order count, the news-candle and evening-gap sizes, the 14:00 length, the bias lookback, displacement entries, layering, 12.5/19 in New York, the continuation bias.
- **`sessions_off`**: not trading a session at all: 18:00, 20:00, book, news, 09:30, 14:00, fri.
- **`filters_off`**: switching a rule off: grade B, all-time high, after two losses, three losses, the gap rule, the strong-opening rule, continuation drawdown, the band.
- **`mgmt_off`**: switching a management rule off: break-even at opens or releases, the unfair-move break-even, the evening 38 break-even, the bias-flip exit.
- **`rev_bracket` and `cont_bracket`**: a session's own stop and target.
- **Every number** in JJConfig.

## Batch 1: single-setting components (frozen 2026-10-17, first day 2026-10-19)

Fifteen versions of the whole system, each with one setting from JJ's own earlier or alternative statements, or a value tried for a clause where he gives no number. They measure single components; the challengers build on everything.

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
