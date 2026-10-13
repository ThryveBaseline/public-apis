# The JJ system, version 1: his whole trading day as one forward paper stream

Decided by Chris on 2026-10-13: run JJ's entire system every day as the JJ stream. It must be his exact system:
- nothing simplified;
- nothing adjusted because of a backtest;
- nothing dropped to make it easier.

Code: `research/jj_system.py`, run nightly by `research/forward_jj.py`.

**Freezing.** It is frozen by the commit that records this file's sha256 in `research/forward_jj.py` (`SPEC_SHA256`). Until then the runner refuses to start.

**Sources.** Every rule below comes from his own videos: the 58 transcripts in `docs/research/extracted/` and the dossier built from them.
- Where his statements changed over time, his **latest** version is used. The date is when he said it, where that is known, otherwise the upload date. Three videos were recorded before they were uploaded:
  - KHEQ5g55dQ4, uploaded 2026-10-04, was recorded in July and August.
  - -lxNWJGWtbg is a clip of a June video.
  - PN1UKQMPb5M (late September) is the latest recording.
- Where he gives no number, the value is the one his own words imply, listed below with the quote.
- Where his words give no way to tell when a clause applies, it is listed under "Not run yet", with the reason.

No rule was chosen, tuned or dropped on historical results, and no historical result of this stream is computed.

This replaces Baseline 0 (B0) as the JJ stream:
- B0 was only his 09:30 session.
- B0's record, 4 sessions from 2026-10-06, stays in `research/private/forward_b0_state.json`.
- S3, S4 and the tournament are unchanged.

## The stream

**What a position is.** The stream is his whole signal stream: every trade his rules take across the day. He runs many accounts and puts each new entry on another one ("one account per successive structure break"), so each position stands for one account and positions can overlap.

**Instrument and costs.**
- Data: NQ front month, 1-minute bars, the same finalized forward bars and data checks as the other streams.
- Sizing: his evaluation sizing at the same dollar risk:
  - two NQ on 25/38;
  - four on 12.5/19 ("double the contracts");
  - one on 50/76 ("cut my contracts in half").
- Costs: $2.50 a side per contract, and 0.25 points of slippage on market fills and stops, as every stream here.
- R is the trade's result over its stop risk.

**The trading day** is the exchange's: 18:00 ET the evening before to 17:00 ET. His evening sessions and overnight orders belong to the next morning's day. Positions run to their stop or target and are closed at 16:10 ET at the latest. That is the firm's end of day: Topstep closes positions at 3:10 PM CT.

## Sessions

| Session | Window (signal bars) | Fair value | Continuation | Reversion |
|---|---|---|---|---|
| 18:00 reopen (Sun-Thu evenings) | 18:00-19:59 | the 18:00 open | first 5 minutes; one only; never away from the gap (the 18:00 open vs the previous 16:59 close) | one attempt |
| 20:00 Asia | 20:00-21:29 | the 20:00 open if its first move (first break of structure, first 5 minutes) goes away from the 18:00 fair value; otherwise the 18:00 one | first 5 minutes; one only | one attempt |
| Overnight book | placed at 21:30, cancelled at 09:29 | 9:30 of that morning | - | an order at every live swing between the price and 9:30 of that morning, in that direction; it fills when price trades through |
| 08:30 news (a USD red or orange folder release at 08:30 or 08:15) | the release minute to 09:29 | the pre-news price (the release bar's open; the earlier of two releases) | none ("I don't really do continuation of news anymore") | to the pre-news price |
| 09:30 New York | 09:30-10:59 | the 09:30 open. News days: the pre-news price stays fair if the opening move (to 09:34) heads back to it. A 10:00 release: the pre-10:00 price from 10:00 | first 5 minutes; follow up on each further break | to fair value |
| 14:00 New York PM | 14:00-15:29 ("first 90 minutes") | the 14:00 open if its first move goes away from the morning's fair value; otherwise the morning's. FOMC days: the pre-FOMC price | first 5 minutes; follow up on each further break | to fair value |
| Friday's last hour | 15:00-15:59 | the 15:00 open | - | one reversal, on a break of structure |

London (03:00) is not traded: "I'm not going to talk about London because I don't operate there."

## Entries

**Structure.**
- A swing high (low) is a wick above (below) the one candle before and the one after. It counts once the next bar has closed.
- It stays live until a candle closes beyond it; a wick does not consume it.
- Structure counts from the previous 09:30 open ("every single piece of structure to the left all the way back down to 9:30").
- A **break of structure** is a close beyond a live swing.

**Displacement.** All three of these:
1. the body is larger than the previous candle's body;
2. it closes beyond the previous candle's wick;
3. the previous candle is the opposite colour.

Two or three same-colour candles may count together against the one before them. Two exclusions:
- Not right after a break of structure the other way ("I would not be taking this green candle ... because it did break structure short").
- Not when the candle reached a live swing and failed to close through it ("it failed to break structure ... which kind of invalidates the displacement").

**Grades.**
- **A+** is a break of structure.
- **A** is a displacement alone.
- **B**, never traded, is when the biases are opposed: the higher-time-frame bias points against the trade.

**Higher-time-frame bias.** "Inverting whatever happened for the previous 6 to 12 hours."
- Daytime: the opposite of the net move over both the last 6 and the last 12 hours. Neutral when the two disagree.
- Evening: toward "9:30 of that morning", his evening reading.

**Continuation.**
- Direction: the session's opening 1-minute candle's colour.
- Trigger: a close through prior structure in that direction ("as long as it breaks structure of the previous candles").
- The phase: the first 5 minutes, ending early after two opposite-colour candles.
- Against a clear higher-time-frame bias, at 09:30 and 14:00 only, it also needs a displacement ("you can go against that if the opening candle is so strong").
- It is not added to while an earlier one is in drawdown.

**Reversion.** Toward fair value, on a grade A+ or A signal, once price has first moved away:
- **Room of 30 points or more**, after a move away of more than 38 points: 25/38 ("I waited until we had a move of more than 38 points ... so I could look for 38-point reversals"; "I need at least 30 points in my favor").
- **Room of 15 points or more**, after a move away of more than 15 points: 12.5/19 ("If there are 15 to 30 points in my favor ... 19 points"; "every time it moves more than 15 points from the right price ... I'm going to send a reversal").
- **Under 15 points:** none (14.75 rejected).
- **Re-arming:** once price closes within 15 points of fair value, a fresh move away is needed.

Filters, all from his statements:
- After two losing reversion attempts in a row, breaks of structure only.
- At an all-time high, shorts only on a break of structure ("I don't want to short off displacement").
- Three losing reversion attempts in a row end that session's reversions ("I lose three in a row, then I'm done"; per session).
- After a losing attempt, fair value moves to the middle of the last 30 minutes ("I'll be adjusting fair price to this consolidation now"; "There's the 30 minutes of consolidation").

**Layering.** A further position in the same direction is taken on a new signal only when the latest one is at least halfway to its target ("After the first one is halfway to take profit, boom, there goes the next one"). It is never at the same level, and it belongs to the same attempt.

**Brackets.**
- 25/38 on evaluations ("Evaluations always going to be a 1 to 1.5").
- A session's opening candle body over 25 points: its continuation uses 50/76 at half the contracts ("I do 76 instead of 75 because there are commissions and fees").
- The 12.5/19 bracket for 15 to 30 points of room.
- On his bank holidays, 38 and never 76.
- Entries fill at the next bar's open after the signal candle closes ("Always waiting for candle closes"). The overnight orders fill where price trades through.

## Management

- **Reversions are static:** no partials, and no break-even except as below ("Leaving runners and partials is probably one of the worst things you can do on prop firms").
- **Break-even at a new session or a release:** any position in profit moves its stop to break-even at the close of the bar before:
  - a session opens;
  - a release at 08:15, 08:30, 09:45, 10:00 or 14:00.

  A position in drawdown is left to play out ("I would move stop to break even, but I'm in draw down").
- **Continuation exits:**
  - It closes at the next open after a break of structure or a displacement against it ("as soon as we got displacement long, I exited the short").
  - At the end of its phase, if the opening move never reached 38 points and the trade is in profit, it goes to break-even ("didn't make my 38 point unfair move").
- **Evening 38-point trades** go to break-even when structure breaks against them while in profit ("If you do a 38, make sure you go to the break-even point, especially when it breaks structure against your position").

## Days

- **News:** a red (High) or orange (Medium) folder USD release, from Forex Factory's calendar ("red folder", "orange folder if it moves"; the room rules test whether it moved).
  - The snapshot used is the latest fetched before the trading day began.
  - FOMC: a High release at 14:00 named FOMC or Federal Funds Rate.
  - A High-impact scheduled speech ("Speaks", "Testifies", "Press Conference") stops new entries in any session open at that time, for the rest of it ("the dude is speaking. So, probably not going to be taking any trades").
- **Bank holidays** (2026-10-12, 2026-11-11 and the exchange's early-halt holidays): the 09:30 session runs only when its opening candle's range is larger than the median of the day's candles so far ("the 9:30 a.m. candle that's larger than most of these candles").
- **Sundays:** the 18:00 and 20:00 sessions run as on any evening ("I do the same thing on Sundays").

## Where he gives no number: the value his words imply

| Clause | His words | Value used |
|---|---|---|
| 14:00 session length | "First 90 minutes of every single session" | 14:00-15:29 |
| End of the 08:30 news window | "going break even if the market's going to open" | 09:29 |
| How far back structure counts | "every single piece of structure to the left all the way back down to 9:30" | from the previous 09:30 open |
| The consolidation fair value moves to after a loss | "There's the 30 minutes of consolidation"; "There's the middle of it" | the middle of the last 30 minutes' range |
| Higher-time-frame lookback | "the previous 6 to 12 hours" | both; neutral when they disagree |
| A 20:00 or 14:00 open's first move | "The first move was down. Uh, so 6 p.m. is fair" | the first break of structure in its first 5 minutes |
| Friday's last hour | "every Friday in the last hour" | 15:00-15:59 |
| "Halfway to take profit" | his words | 50% of the target |
| "Larger than most of these candles" | his words | above the median of the day's candles so far |
| The overnight book's orders | "an eval short at every single piece of structure to the left all the way back down to 9:30" | every live swing between the price and 9:30 of that morning, at the 25/38 or 12.5/19 bracket its room allows |
| A news-day open "heading back" to the pre-news price | "if the opening move heads to the pre-news price" | the 09:34 close nearer the pre-news price than the 09:30 open was |

## Not run yet, and why

These clauses are his, but his words give a computer no way to know when they apply, or they need data the stream does not have yet. Each goes in, as a new version, once there is a number from him or the data.

| His clause | Why it cannot run yet |
|---|---|
| The opening 1-second candle's colour must match the 1-minute's ("1 second green, 1 minute green") | needs 1-second bars (Databento ohlcv-1s; the cost is being checked) |
| News and opening reversions entered on the 5- or 15-second chart | needs 1-second bars; he gives no window for "opening reversions" |
| A mid-candle entry when waiting for the close would cost the room | a computer can't know at that moment what the close will be. Deciding afterwards would be using hindsight, and his latest word is "Should have waited for the close, so don't do that" |
| The 11:00-14:00 "longer trade" and with-trend trades after 11:00 | no entry, direction, stop or target given (said once, in June) |
| A continuation of the 08:30 news candle "unless it's a huge candle" | no size given (he skipped 92 points and took 157 on an FOMC) |
| No continuation into a "huge" 18:00 gap; the 18:00 open not fair when it gaps "far" | no size given |
| Moving fair value after "enough of a move away" from a consolidation | no size given; only the after-a-loss move above is defined |
| An open "not fair" when its first move runs through a pre-open consolidation; the 9:24 candle on a 9:25 volume spike; pre-open entries | no size for a spike or a consolidation |
| A displacement with a "huge wick" is not one | no size given |
| Ambiguous fair values: trade between them | no test for ambiguity given |
| Unscheduled news (tweets, unscheduled speeches): no fade, done for the day | no feed of them; scheduled speeches are handled |
| His discretionary skips ("some days I'm going to skip 6 p.m.") | no rule given; the stream takes the session |

## The paper account

One Topstep 50K evaluation from $2,000, following his evaluation playbook.
- **Evaluation phase:**
  - It takes the stream's trades one at a time, every kind of entry ("Evaluations as well will be all of my displacement candle entries").
  - It stops for the day at +$1,500 ("I'm just going to go for 1500").
  - After a loss it takes the next one ("I like my accounts to either be at profit target or gone").
- **Funded phase:** it takes breaks of structure only, never a continuation ("continuations are only for evaluations").
- **Firm rules, fees, sizing in whole micros and payouts:** the frozen bookkeeping's (TopstepX).

## Scoring and versions

**Scoring.**
- A trading day is scored once the forward file holds a bar of a later trading day.
- The day must have a 09:30 bar, no contract roll inside it, and a calendar snapshot fetched before it began.
- A day that can never be scored is recorded with the reason.
- History is never rewritten.

**Version 1:**
- starts on the first trading day that began after this file was committed (`FIRST_DAY` in `research/forward_jj.py`);
- is compared with the other streams only on its own forward trades;
- has a one-time `init` check on the sealed bars that only confirms the trades do not depend on how much history is loaded (trade counts, no results).

**Changes:** a change is a new version, frozen before its first day and judged only on the forward days after it.
