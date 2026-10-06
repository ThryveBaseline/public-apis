# run1 first read: Claude (cloud session), 2026-10-06

Written from the five verbatim lines of `sealed/run1/report.md` and `manifest.json` relayed by the Surface session, before reading any other reviewer and before the full report was pushed. Preserved unchanged; a second read on the full report follows in a separate file.

## The five numbers

| measure | value |
|---|---|
| OOS Topstep 50K evaluation pass rate (30-day horizon, one start per trading day) | 8.7% |
| Newey-West standard error | ± 4.0% |
| independent OOS opportunities | about 18 (310 starts, median 17 days to resolve) |
| OOS expectancy | −0.071 R per trade after costs; 1,258 trades; 37.5% win rate; profit factor 0.89; 4.02 trades per day |
| ambiguous bars | 7 of 8,689 trades (0.1%), all resolved as stops |

Other firm rows, OOS: FundedNext 50K flex 2.6% ± 1.8% pass, 7.7% payout; Topstep 100K 8.1% ± 3.5% pass, 12.3% payout; Tradeify 100K growth 27.7% ± 3.9% pass in a median of 2 days, 5.2% payout. Payout rates are per funded start within 60 days. Hygiene: 121 trades on 66 roll dates excluded; evaluator at commit bd2be64 with `fpt/` identical to f585bfb; data sha256 d2e4ebf9…; 65 tests passed.

## Verdict

Weak as a mechanical baseline. The breakeven win rate for a fixed 25/38 bracket after $2.50 per side commission and 0.25 points slippage is about 41%; the untouched year shows 37.5%. The monetized chain, P(pass) × P(payout before breach), is about 0.087 × 0.132 ≈ 1.1% per Topstep 50K evaluation against the 10.9% his calculator assumes; expected payout per evaluation ≈ $21 against a fee near $49. Firm rules move the evaluation stage by an order of magnitude (2.6% to 27.7%) for the same trade sequence, but the funded stage fails everywhere. This is a measurement, not a kill: see "not justified".

## 1. What is wrong with this experiment, if anything?

1. **Scope: one session.** The manifest shows `pm_session: false` and `extra_sessions: []`. Baseline 0 trades only the 09:30 session. He describes five sessions (08:30 news, 09:30, 14:00, 18:00, 20:00). The opportunity count and the trade mix are a fraction of what he trades.
2. **Fixed-point parameters across a 17x price range.** The 25/38 bracket, the 25-point big-open threshold and the 38-point band are 2024-26 calibrations; the data runs from NQ ≈ 1,800 to ≈ 31,000. The OOS year trades 4.02 times per day against about 1.9 in-sample, which says the same point thresholds describe a different strategy at older price levels. Consequence: the in-sample years are not the same experiment, and the effective test at his price regime is one year with about 18 independent evaluation windows. The pass-rate confidence interval (roughly 1% to 17%) is correspondingly wide.
3. **Firm rules are research presets, not verified contracts.** Trailing drawdown type, daily-loss handling, consistency rule, payout caps and fees per firm come from public research, not from current firm terms (class D risk in the mission's taxonomy). The firm ranking is therefore indicative only.
4. **Evaluation sizing is our construction.** `two_trade` sets evaluation risk so two winners reach the target (Topstep 50K: $1,000 per trade). It is one reading of "attack the evaluation aggressively", not a sizing he stated.
5. **Interpretation parameters that are ours, not his**: consolidation re-anchoring (`consolidation_bars` 8, `consolidation_atr_mult` 1.5), `continuation_stall_candles` 2, room rule 0.8, structure as one-candle swing, A+ grading. Any of these could account for the 3.5-point win-rate gap to his claim (class C).
6. **Costs may be light at the open.** 0.25 points slippage on 1-minute stops at 09:30 is plausible on average, optimistic on volatile opens. The direction of this error is against us if anything, which is acceptable for a baseline, but a 0.5-point sensitivity should be reported.
7. **Data hygiene is sound.** Roll exclusion worked once the symbol column carried the contract; ambiguity is negligible; open starts were counted as not passed; the OOS tail was untouched.

## 2. What conclusions are justified?

* Under the frozen literal reading, one session, one untouched year at his price regime, the rule set has negative expectancy after costs (−0.07 R per trade; profit factor 0.89) and a 37.5% win rate.
* The 33% pass and 33% payout assumptions in his calculator are not reproduced by this reading; the measured chain is near 1% per 50K evaluation, so evaluation fees would be lost at a high rate under these rules.
* The evaluation stage is highly firm-dependent, and aggressive sizing can raise pass probability (Tradeify growth 27.7%) without producing payouts; the binding constraint is expectancy, not evaluation mechanics.
* The data pipeline, roll handling and seal are fit for purpose; subsequent runs can be compared against this one exactly.

## 3. What conclusions are not justified?

* That his method does not work: his trading includes four more sessions, discretion in structure reading, and position management the literal rules do not capture.
* That the in-sample years corroborate anything: fixed-point brackets at 2010-2019 prices are a different strategy, as the trades-per-day drift shows.
* Any definitive firm ranking, or any bootstrap conclusion built on the preset firm rules before they are checked against current contracts.
* Anything about the 14:00, 18:00, 20:00 or 08:30 sessions.
* That the 3.5-point win-rate gap to his claim is a genuine weakness rather than an interpretation difference. It has not been located yet.

## 4. What should be tested next?

Pre-registered on the development window only, with walk-forward and the untouched year used once per candidate:

* **B1 Volatility-scaled bracket.** Express 25/38 as multiples of recent ATR at 2025-26 levels and apply the multiples across history. Makes 2010-2024 comparable and tests whether the fixed-point choice is the drift.
* **B2 His other sessions.** Add 14:00 first, then 08:30 (news), 18:00 and 20:00, each anchored to its own session open as he describes.
* **B3 Continuation versus reversion separately.** Read the split in the full report; condition or drop the weaker leg.
* **B4 Interpretation sweep.** Alternatives for displacement, structure and re-anchoring (the documented LEGACY variants), classified as C, to locate the win-rate gap.
* **B5 Evaluation and funded policy as separate objects.** Per-firm sizing, stop-after-first-win (his one trade per account per day), and measured days-to-payout; firm presets verified against current contracts first.
* **B6 Cost sensitivity.** Slippage 0.5 points, commission variants.
* **B7 Regime gating.** ATR terciles and opening-gap size (room-rule variants) as conditions, not fits.
* **Direct check against his own examples.** Replay the trades he narrates in the transcripts against our signal stream to see whether the literal rules fire where he fires.

Bootstrap with these measured inputs (P(pass) 8.7%, P(payout | funded) 13.2%, payout $1,800, fee ≈ $49): expected value per evaluation ≈ −$28; a $2,000 bankroll buys about 40 attempts with roughly a 37% chance of at least one payout before exhaustion. The report's own bootstrap section supersedes this back-of-envelope.
