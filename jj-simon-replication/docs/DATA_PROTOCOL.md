# Real-data protocol: Databento quote, freeze, seal, run, review

The order is fixed: **quote -> approve -> freeze and seal -> run once -> independent review**. Nothing in the strategy or the evaluator changes between the freeze and the sealed first result.

## 0. Environment

`pip install numpy 'pandas>=3' tabulate pytest` (all four are declared in `requirements.txt`; `tabulate` is easy to forget and its absence fails one test).

## 1. Credential handling (Surface)

The Databento key lives in the local `access.txt`. It is read into the client at run time and is never printed, echoed, logged, copied into a notebook, committed, pasted into a chat, or sent to any other model or machine. If a command would display it, the command is wrong.

```python
key = open("access.txt").read().strip()          # never print this variable
import databento as db
client = db.Historical(key)
```

## 2. Quote first, buy nothing

```python
client.metadata.get_dataset_range("GLBX.MDP3")      # available date range for CME Globex
client.metadata.get_cost(dataset="GLBX.MDP3", symbols=["NQ.n.0"], stype_in="continuous",
                         schema="ohlcv-1m", start="2010-06-06", end=END)   # USD, no purchase
client.metadata.get_record_count(... same arguments ...)                    # rows
client.metadata.get_cost(dataset="GLBX.MDP3", symbols=["NQ.n.0"], stype_in="continuous",
                         schema="ohlcv-1d", start="2010-06-06", end=END)   # roll cross-check, dates only
```

Report before any download: available range, proposed range, dataset and schema, symbol method, roll treatment, row count and approximate size, the quoted price, the development window and the untouched out-of-sample window. The user approves; only then `client.timeseries.get_range(...)` with the same arguments.

## 3. What to buy

| item | choice | why |
|---|---|---|
| dataset | `GLBX.MDP3` | CME Globex, the venue NQ trades on; full-depth derived bars, history from June 2010 |
| schema | `ohlcv-1m` | the strategy is defined on 1-minute bars; `ohlcv-1s` is not needed and is 60x larger |
| symbol | `NQ.n.0` with `stype_in="continuous"` (open-interest roll) is the only 1-minute purchase; the roll cross-check is `NQ.n.0` at `ohlcv-1d` over the same range, dates only | continuous series stitched from the front contract with **no price adjustment**; every bar carries the underlying contract in `symbol`, so the roll days of the purchased series are read from the data itself; the daily series of the same symbol confirms them independently for five cents. `NQ.c.0` is the calendar roll and rolls on different dates, so it would identify the wrong days (caught in the Surface session's review of the quote, 2026-10-06) |
| span | all available history to the latest date, at least 2015 onward | several regimes: 2015-16 range, 2017 trend, 2018 and 2020 shocks, 2021 melt-up, 2022 bear, 2023-24 trend, 2025-26 current |
| extras | none | the strategy uses OHLC only; volume is kept for regime analysis |

**Roll policy, pre-registered.** Databento's continuous symbols switch contracts without adjusting prices, so the first bars after a roll compare one contract's open with another contract's close. The evaluator excludes every roll date (the New York date on which `symbol` changes in the purchased `NQ.n.0` series) from signal generation and reports how many trades that removed. No back-adjusted series is used anywhere: a back-adjusted price would shift the opening price that fair value is anchored to and could manufacture or erase an "unfair move". Calendar-roll (`.c.0`) and volume-roll (`.v.0`) dates are not excluded: the purchased series has no discontinuity on them, and excluding expiry days would be a strategy choice, not a data-integrity one. (Earlier wording said both `.n.0` and `.c.0` dates would be excluded; corrected on 2026-10-06 before any download.)

**Size.** One symbol at 1-minute resolution over the 23-hour Globex day is about 1,380 bars a day, roughly 350,000 rows a year, 25-35 MB a year as CSV. Fifteen years is on the order of 5 million rows.

**Symbol column, corrected 2026-10-06.** For a continuous request Databento writes the requested name (`NQ.n.0`) into `symbol` on every bar; the underlying contract is identified by `instrument_id`. The evaluator's input is therefore prepared with `symbol := instrument_id` (as text), which is what the roll filter keys on; see `docs/DATA_DECISION.md`.

**Timezone.** `ts_event` is UTC nanoseconds. The loader parses the `Z` suffix as UTC and converts to America/New_York; Databento fixed-point prices (1e-9 units, present when `rtype` is in the file) are rescaled automatically. Export with `df.to_csv(path)` from the client's DataFrame (`to_df()`), keeping the `symbol` column (`map_symbols=True`).

## 4. Windows, pre-registered

* **Development window**: everything up to 12 months before the last available bar. Any diagnostic, any future rule proposal, any parameter discussion uses this window only.
* **Untouched out-of-sample window**: the final 12 months. `evaluate --oos-months 12` reports it separately; its numbers are read once, after the development numbers, and never used to choose anything. If the available history is short, the OOS window is the final 6 months and that choice is recorded in the manifest.

## 5. Freeze and seal

The strategy and evaluator are frozen at the git tag named in `docs/FROZEN.md`. The canonical run is produced by

```
python3 scripts/seal_run.py --csv data/nq_1min_databento.csv --source-tz UTC --out sealed/run1 --oos-months 12
```

which refuses to run on a modified tree, writes `report.md`, `trades.csv` and `manifest.json` (data hash, rows, range, commit, tag, fpt/ tree hash, options, output hashes, roll dates excluded, ambiguous-bar count) and a `SEALED` marker. The sealed directory is committed as is. Nobody edits it.

The nine primary measurements, in the report in this order: P(50K evaluation pass) in sample; the same on the untouched OOS window; standard errors for both; the R distribution and expectancy; continuation vs reversion; stability by year, quarter and volatility regime; funded-to-first-payout probability; $2,000 bootstrap survival; median trading days to first payout.

**Same-bar ambiguity.** When one 1-minute bar contains both the stop and the target, the data cannot say which printed first. The frozen rules resolve every such bar as a stop (worst case) and the report states how many trades that touched. They are never resolved in the strategy's favour, and no later rule may change that without a separate proposal.

## 6. Review after sealing

Only after `sealed/run1` exists may anyone analyse why it worked or failed. Reviewers (Claude, the GB10's local models, Jev, Laya) receive the same `report.md` and nothing else, answer the four questions in `docs/REVIEW_PROMPT.md` independently, and their answers are compared by a person. Reviewers may propose checks and challenge inferences; they do not change the canonical rules or the evaluator. A change to either is a new proposal with its own approval, a new tag and a new sealed run; the first run stays.
