"""The paper test's status page (STATUS.md on the private repo's forward-v1-status branch), written by the daily job.

Plain and short: what state the test is in, whether a person is needed, the numbers so far, the next milestones,
and the latest trades. It reads only the forward record; it computes nothing new about the strategy.

usage (by the daily job, after research/forward.py day or after the gate decides to wait):
  python research/status_page.py --state research/private/forward_v1_state.json --public-status research/forward_v1_status.md \\
      --headline "OK" --readings "2026-10-07 available 2026-10-08; 2026-10-08 available 2026-10-08" --out STATUS.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from research.forward import SESSION_WINDOW, SETUP_CHECKS, paper_account  # noqa: E402

NY = "America/New_York"
MEANING = {
    "OK": "Ran normally. Nothing for you to do.",
    "WAITING": "Waiting for market data to be final. Nothing for you to do.",
    "REFUSED": "The runner stopped itself. Nothing is scored until a person looks: open the bridge window.",
    "FLAG": "A checkpoint is outside its historical range. Stop and look before anything else.",
}


def _when(ts: str) -> str:
    t = pd.Timestamp(ts)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return t.tz_convert(NY).strftime("%a %d %b %Y, %H:%M ET")


def _summary(t: pd.DataFrame) -> list[str]:
    r = t["r"].astype(float)
    reason = t["exit_reason"].astype(str)
    n = len(t)
    if not n:
        return ["0", "-", "-", "-", "-"]
    return [str(n), f"{(r > 0).sum()} / {(r <= 0).sum()}", f"{(reason == 'target').sum()} / {(reason == 'stop').sum()} / {(reason == 'flat').sum()}",
            f"{r.sum():+.2f}", f"{r.mean():+.3f}"]


def _account(led: pd.DataFrame, dates: list, name: str) -> str:
    if not len(led[led["candidate"] == name]):
        return "no trade yet"
    p = paper_account(led, [pd.Timestamp(d) for d in dates], name, "wait")
    state = "ruined" if p["ruined"] else f"{p['evals']:.0f} evaluation(s) bought, {p['passes']:.0f} passed, {p['payouts']:.0f} payout(s)"
    return f"${p['final_cash']:,.0f} ({state})"


def page(state: dict | None, headline: str, readings: str, flags: list[str], now: str) -> str:
    kind = headline.split(":", 1)[0].strip().upper()
    s = ["# S3 paper test", "", f"**Status: {headline}**", "", MEANING.get(kind, ""), "", f"Last run: {_when(now)}", ""]
    dates = state["dates"] if state else []
    led = pd.DataFrame(state["trades"]) if state and state["trades"] else pd.DataFrame(columns=["candidate", "r", "exit_reason"])
    s += [f"Sessions scored: {len(dates)}" + (f" ({dates[0]} to {dates[-1]})" if dates else ""), ""]
    s += ["| | S3 (decides) | S4 (watched only) |", "|---|---|---|"]
    rows = list(zip(*[_summary(led[led["candidate"] == c]) for c in ("S3", "S4")]))
    for label, row in zip(("Trades", "Up / down", "Target / stop / 4 pm exit", "Total R", "R per trade"), rows):
        s.append(f"| {label} | {row[0]} | {row[1]} |")
    s.append(f"| Paper account from $2,000 | {_account(led, dates, 'S3')} | {_account(led, dates, 'S4')} |")
    n3 = int((led["candidate"] == "S3").sum()) if len(led) else 0
    s += ["", "## Next milestones", "",
          f"- First {SESSION_WINDOW}-session check: " + ("reached" if len(dates) >= SESSION_WINDOW else f"{SESSION_WINDOW - len(dates)} session(s) to go"),
          *[f"- {n} S3 trades: " + ("reached" if n3 >= n else f"{n - n3} to go") for n in SETUP_CHECKS],
          "- After about 20 to 30 S3 trades with no flag: Chris decides on one $49 evaluation", "",
          "## Checkpoints", ""] + ([f"- {f}" for f in flags] or ["- none reached yet"])
    s3 = led[led["candidate"] == "S3"].sort_values("entry_time").tail(10) if n3 else led.iloc[:0]
    if len(s3):
        s += ["", "## Latest S3 trades", "", "| date | side | exit | R |", "|---|---|---|---|"]
        for _, t in s3.iloc[::-1].iterrows():
            s.append(f"| {t['date']} | {t['direction']} | {t['exit_reason']} | {float(t['r']):+.2f} |")
    if readings:
        s += ["", "## Market data status (Databento)", "", readings]
    s += ["", "R is the result per contract in units of the trade's stop: +2 is a full target, -1 a full stop. "
          "The paper account follows the frozen v1 bookkeeping ($0.50 micro fee, intraday dips not counted), so it reads a little high."]
    return "\n".join(s) + "\n"


def checkpoint_lines(public_status: str | None) -> list[str]:
    if not public_status or not os.path.exists(public_status):
        return []
    text = open(public_status).read()
    if "## Checkpoints (protocol v1)" not in text:
        return []
    part = text.split("## Checkpoints (protocol v1)", 1)[1]
    return [x[2:].strip() for x in part.splitlines() if x.startswith("- ") and "none reached yet" not in x]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", help="research/private/forward_v1_state.json (absent until the first scored run)")
    ap.add_argument("--public-status", help="research/forward_v1_status.md, for the checkpoint lines")
    ap.add_argument("--headline", required=True, help="OK | WAITING: ... | REFUSED: ... | FLAG: ...")
    ap.add_argument("--readings", default="", help="the day's Databento condition readings, one line")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    state = None
    if a.state and os.path.exists(a.state):
        with open(a.state) as fh:
            state = json.load(fh)
    text = page(state, a.headline, a.readings, checkpoint_lines(a.public_status), datetime.now(timezone.utc).isoformat())
    with open(a.out, "w") as fh:
        fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
