# Frozen implementation

The canonical strategy rules (`fpt/strategy.py`, `fpt/structure.py`, `fpt/fair_value.py`, `fpt/indicators.py`, `fpt/risk.py`) and the evaluator (`fpt/evaluate.py`, `fpt/propfirm.py`, `fpt/bootstrap.py`, `fpt/portfolio.py`, `fpt/data.py`, `scripts/seal_run.py`) are frozen at git tag **`jj-frozen-v1`**, which is commit **`f585bfb`** on branch `claude/replicate-researcher-work-lhd1rm`, for the first real-data run. The commit hash is the authoritative identifier (the hosting proxy may not list tags); `scripts/seal_run.py` records it in every manifest.

Rules of the freeze:

* `scripts/seal_run.py` refuses to produce a sealed result from a tree that differs from the commit it was run on; the manifest records the commit, the tag and the hash of the `fpt/` tree.
* Reviewers (other models on the GB10, people) may read, probe, criticise and propose. They do not edit the frozen files. A proposal becomes a change only with an explicit separate approval, a new tag (`jj-frozen-v2`, ...) and a new sealed run; earlier sealed runs are never overwritten.
* No parameter is tuned on the out-of-sample window. The development window is the only place where a future proposal may be studied.
* Same-bar stop/target ambiguity is always resolved against the strategy and reported.

What the frozen defaults are, in his words, is recorded row by row in `docs/ASSUMPTIONS.md`; the sources are in `docs/DOSSIER.md` and `docs/research/EXTRACTED.md`.
