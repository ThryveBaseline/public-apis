# Brief for the Surface session (Databento step)

We are ready for the real-data phase of the JJ Simon replication. The repository is `ThryveBaseline/public-apis`, branch `claude/replicate-researcher-work-lhd1rm`, folder `jj-simon-replication`; the strategy and evaluator are frozen at tag `jj-frozen-v1` (see `docs/FROZEN.md`). Follow `docs/DATA_PROTOCOL.md` exactly.

1. Locate the local `access.txt` with the Databento access key. Use it locally only: never print, echo, log, commit, copy, transmit to another model, or otherwise expose it.
2. **Quote only.** Using the Databento metadata API, report before any purchase or download:
   * available date range of `GLBX.MDP3`
   * proposed date range (all available history to the latest date, at least 2015 onward)
   * dataset and schema (`GLBX.MDP3`, `ohlcv-1m`)
   * symbol and contract method (`NQ.n.0`, `stype_in="continuous"`, unadjusted; `NQ.c.0` cross-check for roll dates)
   * rollover treatment (roll dates excluded by the evaluator; no price adjustment anywhere)
   * record count and approximate size
   * Databento price from `metadata.get_cost`
   * proposed development window and the untouched final out-of-sample window (final 12 months)
   Do not download until the quote is approved.
3. After approval: download with the same arguments, export to CSV keeping the `symbol` column (`map_symbols=True`), save as `jj-simon-replication/data/nq_1min_databento.csv` (not committed; the folder is ignored), and record the file's sha256 and row count.
4. Run the frozen evaluator once, exactly as:
   ```
   cd jj-simon-replication && python3 scripts/seal_run.py --csv data/nq_1min_databento.csv --source-tz UTC --out sealed/run1 --oos-months 12
   ```
   Commit `sealed/run1` unchanged. Do not read it for tuning. Do not alter anything under `fpt/` or `pine/` while obtaining or preparing the data; the script refuses to seal a modified tree.
5. You may consult the GB10 and its local models for technical review of the data step (dataset choice, roll handling, timezone, file integrity). They are reviewers: they may identify problems, propose checks, or challenge assumptions; they must not change the canonical rules or evaluator.
6. After `sealed/run1` exists, give each reviewer `docs/REVIEW_PROMPT.md` plus `sealed/run1/report.md` and nothing else, collect their four answers independently, and hand them to Jev to compare.

The primary measurements, in the report in this order: P(50K evaluation pass); the same on the untouched OOS window; the uncertainty of both; expectancy and the R distribution; continuation vs reversion; year, quarter and volatility-regime stability; funded-to-first-payout probability; $2,000 bootstrap survival; median trading days to first payout. The report also states how many trades hit a bar that contained both stop and target; those are resolved as stops, never in our favour.
