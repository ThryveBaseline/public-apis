"""The paper test's status page (STATUS.md on the private repo's forward-v1-status branch), written by the daily job.

Plain and short: what state the test is in, whether a person is needed, the numbers so far, the next milestones,
and the latest trades. It reads only the forward record; it computes nothing new about the strategy.

usage (by the daily job, after research/forward.py day or after the gate decides to wait):
  python research/status_page.py --state research/private/forward_v1_state.json --public-status research/forward_v1_status.md \\
      --headline "OK" --readings "2026-10-07 available 2026-10-08; 2026-10-08 available 2026-10-08" --out STATUS.md --html site/index.html

--html also writes a single self-contained web page (and robots.txt beside it, keeping it out of search engines), for a
Netlify site that publishes the branch's site/ folder on every push.
"""
from __future__ import annotations

import argparse
import html as esc
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


COLOURS = {"OK": "#1a7f37", "WAITING": "#6e7781", "REFUSED": "#cf222e", "FLAG": "#bf8700"}


def _spark(r: list[float]) -> str:
    """S3's cumulative R as a small line, zero marked."""
    if len(r) < 2:
        return ""
    c = [0.0]
    for x in r:
        c.append(c[-1] + x)
    lo, hi = min(c), max(c)
    span = (hi - lo) or 1.0
    w, h = 600, 120
    pts = " ".join(f"{i * w / (len(c) - 1):.1f},{h - (v - lo) / span * h:.1f}" for i, v in enumerate(c))
    zero = h - (0 - lo) / span * h
    return (f'<svg viewBox="-4 -4 {w + 8} {h + 8}" class="spark" role="img" aria-label="S3 cumulative R">'
            f'<line x1="0" y1="{zero:.1f}" x2="{w}" y2="{zero:.1f}" class="zero"/><polyline points="{pts}" class="line"/></svg>')


def html_page(state: dict | None, headline: str, readings: str, flags: list[str], now: str) -> str:
    kind = headline.split(":", 1)[0].strip().upper()
    dates = state["dates"] if state else []
    led = pd.DataFrame(state["trades"]) if state and state["trades"] else pd.DataFrame(columns=["candidate", "r", "exit_reason", "entry_time"])
    rows = list(zip(*[_summary(led[led["candidate"] == c]) for c in ("S3", "S4")]))
    table = "".join(f"<tr><th>{label}</th><td>{esc.escape(a)}</td><td>{esc.escape(b)}</td></tr>"
                    for label, (a, b) in zip(("Trades", "Up / down", "Target / stop / 4 pm exit", "Total R", "R per trade"), rows))
    table += f"<tr><th>Paper account from $2,000</th><td>{esc.escape(_account(led, dates, 'S3'))}</td><td>{esc.escape(_account(led, dates, 'S4'))}</td></tr>"
    s3 = led[led["candidate"] == "S3"].sort_values("entry_time") if len(led) else led
    n3 = len(s3)
    bars = [(f"First {SESSION_WINDOW}-session check", len(dates), SESSION_WINDOW)] + [(f"{n} S3 trades", n3, n) for n in SETUP_CHECKS]
    miles = "".join(f'<div class="mile"><span>{label}</span><span>{min(v, n)} / {n}</span><div class="bar"><div style="width:{min(v, n) / n * 100:.0f}%"></div></div></div>'
                    for label, v, n in bars)
    latest = "".join(f"<tr><td>{esc.escape(str(t['date']))}</td><td>{esc.escape(str(t['direction']))}</td><td>{esc.escape(str(t['exit_reason']))}</td>"
                     f"<td class=\"num\">{float(t['r']):+.2f}</td></tr>" for _, t in s3.tail(10).iloc[::-1].iterrows())
    checks = "".join(f"<li>{esc.escape(f)}</li>" for f in flags) or "<li>none reached yet</li>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>S3 paper test</title>
<style>
:root {{ --fg:#1f2328; --muted:#656d76; --bg:#ffffff; --line:#d0d7de; --card:#f6f8fa; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --line:#30363d; --card:#161b22; }} }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.45 -apple-system, system-ui, "Segoe UI", sans-serif; }}
main {{ max-width:640px; margin:0 auto; padding:20px 16px 40px; }}
h1 {{ font-size:20px; margin:0 0 12px; }} h2 {{ font-size:15px; margin:28px 0 8px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
.status {{ border-left:6px solid {COLOURS.get(kind, "#6e7781")}; background:var(--card); padding:12px 14px; border-radius:6px; }}
.status b {{ display:block; font-size:18px; }} .muted {{ color:var(--muted); font-size:14px; }}
table {{ width:100%; border-collapse:collapse; font-size:15px; }} th, td {{ text-align:left; padding:6px 4px; border-bottom:1px solid var(--line); }}
td, .num {{ font-variant-numeric:tabular-nums; }} .num {{ text-align:right; }}
.mile {{ display:grid; grid-template-columns:1fr auto; gap:2px 8px; margin:8px 0; font-size:15px; }}
.bar {{ grid-column:1 / -1; height:6px; background:var(--line); border-radius:3px; overflow:hidden; }} .bar div {{ height:100%; background:{COLOURS["OK"]}; }}
.spark {{ width:100%; height:auto; }} .spark .line {{ fill:none; stroke:var(--fg); stroke-width:2; }} .spark .zero {{ stroke:var(--line); stroke-dasharray:4 4; }}
ul {{ padding-left:18px; }}
</style></head><body><main>
<h1>S3 paper test</h1>
<div class="status"><b>{esc.escape(headline)}</b>{esc.escape(MEANING.get(kind, ""))}<div class="muted">Last run {esc.escape(_when(now))}</div></div>
<h2>So far</h2>
<p class="muted">{len(dates)} session(s) scored{esc.escape(f" ({dates[0]} to {dates[-1]})" if dates else "")}</p>
<table><tr><th></th><th>S3 (decides)</th><th>S4 (watched only)</th></tr>{table}</table>
{"<h2>S3 cumulative R</h2>" + _spark(s3["r"].astype(float).tolist()) if n3 >= 2 else ""}
<h2>Milestones</h2>{miles}<p class="muted">After about 20 to 30 S3 trades with no flag, Chris decides on one $49 evaluation.</p>
<h2>Checkpoints</h2><ul>{checks}</ul>
{"<h2>Latest S3 trades</h2><table><tr><th>date</th><th>side</th><th>exit</th><th class='num'>R</th></tr>" + latest + "</table>" if latest else ""}
{"<h2>Market data</h2><p class='muted'>" + esc.escape(readings) + "</p>" if readings else ""}
<p class="muted">R is the result per contract in units of the trade's stop: +2 is a full target, -1 a full stop. The paper account follows the frozen v1
bookkeeping ($0.50 micro fee, intraday dips not counted), so it reads a little high.</p>
</main></body></html>
"""


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
    ap.add_argument("--html", help="also write the web page here (robots.txt beside it)")
    a = ap.parse_args()
    state = None
    if a.state and os.path.exists(a.state):
        with open(a.state) as fh:
            state = json.load(fh)
    now = datetime.now(timezone.utc).isoformat()
    flags = checkpoint_lines(a.public_status)
    text = page(state, a.headline, a.readings, flags, now)
    with open(a.out, "w") as fh:
        fh.write(text)
    if a.html:
        os.makedirs(os.path.dirname(os.path.abspath(a.html)), exist_ok=True)
        with open(a.html, "w") as fh:
            fh.write(html_page(state, a.headline, a.readings, flags, now))
        with open(os.path.join(os.path.dirname(os.path.abspath(a.html)), "robots.txt"), "w") as fh:
            fh.write("User-agent: *\nDisallow: /\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
