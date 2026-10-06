# run1 anatomy: what the ledger says about where the edge lives (Claude, cloud session, 2026-10-06)

Source: `research/run1_anatomy.md` as run on the GB10 against the sealed ledger (tool at feed760; population 8,689 after the same 121 roll-date exclusions as the sealed report; the period rows reproduce the sealed "all" rows exactly). Benchmark = the sealed report's out-of-sample year, now inspected; nothing below is selected on it.

## 1. The bracket's meaning moved by a factor of fifteen

| year | median price | daily ATR (pts) | 09:30-09:35 range (pts) | 25-pt stop / daily ATR | 38-pt target / opening range | stop as % of price |
|---|---|---|---|---|---|---|
| 2010 | 1,953 | 35 | 5.5 | 0.72 | 6.9 | 1.28% |
| 2014 | 3,800 | 47 | 8.1 | 0.53 | 4.7 | 0.66% |
| 2018 | 6,944 | 134 | 22.5 | 0.19 | 1.7 | 0.36% |
| 2022 | 12,664 | 379 | 69.0 | 0.07 | 0.55 | 0.20% |
| 2025 | 22,222 | 409 | 69.8 | 0.06 | 0.54 | 0.11% |
| 2026 | 28,829 | 518 | 106.5 | 0.05 | 0.36 | 0.09% |

In 2010-2014 the stop was more than half a day's range and the target was five to seven opening ranges away: trades rarely resolved intraday. In 2025-26 the stop is a twentieth of the day's range and the target is a third of the first five minutes. These are not the same strategy, and the development-era results (47-52% win rates, pass rates of 20-39%) describe the first one.

## 2. The early-era trades were held into the evening session

Development has 893 `session_end` exits (838 continuation, 55 reversion), concentrated in the early years where the bracket was unreachable; the benchmark year has none (continuation 150 stops, 122 targets; reversion 636 stops, 350 targets). On full-Globex data the frozen evaluator's day key is the New York calendar date, so its last bar is 23:59 ET and an unresolved position is held through the 18:00-23:59 evening session. That is not his rule (positions run past 11:00, not overnight). Classification: B, implementation, affecting development-era numbers only; the benchmark year is untouched because every trade there resolved intraday. The research branch gets an explicit flat time (16:00 ET); `fpt/` on the baseline branch stays as sealed, and this is recorded in `docs/ASSUMPTIONS.md`.

## 3. Reversion grade A is the single largest drag

| period | setup | grade | trades | win rate | expectancy R | profit factor |
|---|---|---|---|---|---|---|
| development | continuation | A | 1,272 | 42.8% | −0.010 | 0.98 |
| development | continuation | A+ | 2,009 | 44.9% | +0.039 | 1.08 |
| development | reversion | A | 3,367 | 36.8% | −0.090 | 0.86 |
| development | reversion | A+ | 783 | 38.6% | −0.049 | 0.92 |
| benchmark | continuation | A | 95 | 50.5% | +0.257 | 1.51 |
| benchmark | continuation | A+ | 177 | 41.8% | +0.038 | 1.06 |
| benchmark | reversion | A | 770 | 34.2% | −0.156 | 0.77 |
| benchmark | reversion | A+ | 216 | 40.3% | −0.001 | 1.00 |

Reversion A is 45% of development trades and 61% of benchmark trades, negative in both. Removing it on paper (no re-simulation, so sequencing effects ignored) leaves development at about +0.007 R per trade and the benchmark at about +0.06 R. Continuation A versus A+ flips sign between periods on small benchmark counts (95 trades), so grade is not a continuation lever yet.

## 4. Entry time: the later the reversion, the worse

| period | entry bucket | trades | expectancy R |
|---|---|---|---|
| development | 09:30-09:35 | 3,187 | +0.020 |
| development | 09:35-09:45 | 418 | +0.013 |
| development | 09:45-10:00 | 941 | −0.069 |
| development | 10:00-10:30 | 1,657 | −0.083 |
| development | 10:30-11:00 | 1,200 | −0.117 |
| benchmark | 09:30-09:35 | 261 | +0.114 |
| benchmark | 09:35-10:00 | 367 | −0.124 |
| benchmark | 10:00-11:00 | 626 | −0.111 |

Monotone in development with large counts. A reversion window that closes at 09:45 or 10:00 is a pre-registrable condition with a direction known before testing.

## 5. Excursions at today's volatility: the signal is often right, the stop is inside the noise

Benchmark winners: median MFE through 16:00 of 186 points against a 38-point target; 93% ran at least 12 points past the target and 80% to twice it. Benchmark losers: median MFE while held 8.5 points (most never approached the target: 27% reached half of it, 5% reached 90%), but median MFE through 16:00 of 97 points: half of the stopped trades later moved 97 points or more in the intended direction. Winners came within 60% of the stop 26% of the time. Development (earlier regime) shows the same shape at smaller magnitudes. This is the geometry hypothesis in excursion form: at a 518-point daily ATR a 25-point stop is hit by noise before the move it was placed for.

## What this changes in the research design

**B1, bracket replay on frozen entries.** Keep the sealed entries (time, price, direction, setup, grade) fixed and replay the bars from entry through 16:00 ET under alternative brackets, so geometry is isolated from signal: the fixed 25/38 (must reproduce the ledger apart from the evening-session effect), stop as a multiple of daily ATR, of the opening range, and of price, each with the 1.52 reward-to-risk kept, plus a few wider-stop variants suggested by the loser excursions. Same-bar ambiguity resolved as a stop. Grid pre-registered; selection by walk-forward across development years; the benchmark year reported beside, never selected on. Caveat: replay ignores sequencing (a longer hold blocks later entries), so shortlisted variants go to full re-simulation on the research branch afterwards.

**B2, reversion as he trades it.** Filters on the frozen ledger first, then full re-simulation: reversion A+ only; reversion entries before 09:45, then before 10:00; the two combined; continuation untouched. Expected direction known from the tables above; the test is whether it holds year by year in development.

**Research-branch config additions, with provenance:** `flat_time` (16:00 ET) and a reversion entry cutoff; both documented as class B / class C corrections, neither applied to the sealed baseline.
