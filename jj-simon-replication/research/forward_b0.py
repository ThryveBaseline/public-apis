"""JJ's full rules (Baseline 0) as a third forward paper stream (docs/research/forward_protocol_b0.md).

research/forward.py is imported unchanged and run with one candidate, B0 = the research engine at its defaults
(Baseline 0 exactly as frozen), its own protocol, baseline pin, state and outputs. S3 and S4 (protocol v1) are
untouched: they run through research/forward.py itself, with their own state.

usage (the same modes and arguments as research/forward.py):
  python research/forward_b0.py baseline --csv data/nq_1min_databento.csv --source-tz UTC --manifest sealed/run1/manifest.json \\
      --protocol docs/research/forward_protocol_b0.md --out research/forward_b0_baseline.md \\
      --private-out research/private/forward_b0_baseline_trades.csv
  python research/forward_b0.py day --csv data/nq_1min_databento.csv --forward-csv data/forward/nq_1min_forward.csv --source-tz UTC \\
      --manifest sealed/run1/manifest.json --protocol docs/research/forward_protocol_b0.md --baseline research/forward_b0_baseline.md \\
      --state research/private/forward_b0_state.json --out research/forward_b0_status.md \\
      --private-out research/private/forward_b0_status_private.md
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research import forward as fw  # noqa: E402
from research.engine import ResearchConfig  # noqa: E402

PROTOCOL_SHA256 = "4bdd5c737c9c4647240ece64bb159a72c7dcc92de65d27ba80e51ae4f3006aa5"  # docs/research/forward_protocol_b0.md
BASELINE_PIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forward_b0_baseline.sha256")
CANDIDATES = {"B0": ResearchConfig()}  # Baseline 0: every hook at its default


def configure() -> None:
    fw.CANDIDATES = CANDIDATES
    fw.PROTOCOL_SHA256 = PROTOCOL_SHA256
    fw.BASELINE_PIN = BASELINE_PIN
    if "research.forward_b0" not in fw.TRADE_MODULES:
        fw.TRADE_MODULES = fw.TRADE_MODULES + ("research.forward_b0",)


def main() -> int:
    configure()
    return fw.main()


if __name__ == "__main__":
    raise SystemExit(main())
