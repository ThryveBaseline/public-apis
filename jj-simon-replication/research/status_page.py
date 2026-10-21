"""The paper test's status page (STATUS.md on the private repo's forward-v1-status branch), written by the daily job.

Plain and short: what state the test is in, whether a person is needed, the numbers so far, the next milestones,
and the latest trades. It reads only the forward record; it computes nothing new about the strategy.

usage (by the daily job, after research/forward.py day or after the gate decides to wait):
  python research/status_page.py --state research/private/forward_v1_state.json --public-status research/forward_v1_status.md \\
      --state-jj research/private/jj_system_v1_state.json --state-b0 research/private/forward_b0_state.json \\
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
from research import forward_jj, personal_account  # noqa: E402
from research.forward import SESSION_WINDOW, SETUP_CHECKS, paper_account  # noqa: E402

NY = "America/New_York"
MEANING = {
    "OK": "Ran normally. Nothing for you to do.",
    "WAITING": "Waiting for market data to be final. Nothing for you to do.",
    "REFUSED": "The runner stopped itself and scored nothing this run; the record so far is unchanged. The next run (03:00 or 15:00 ET) "
               "starts over on its own. If it refuses twice in a row, open the bridge window.",
    "FLAG": "A checkpoint is outside its historical range. Stop and look before anything else.",
}


def _when(ts: str) -> str:
    t = pd.Timestamp(ts)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return t.tz_convert(NY).strftime("%a %d %b %Y, %H:%M ET")


STREAMS = (("S3", "S3 continuation"), ("S4", "S4 + A+ reversion"), ("JJ", "JJ system"))
JJ_SESSIONS = (("18:00", "18:00"), ("20:00", "20:00 Asia"), ("book", "overnight orders"), ("news", "08:30 news"), ("09:30", "09:30"),
               ("14:00", "14:00"), ("fri", "Friday last hour"))


def _summary(t: pd.DataFrame) -> list[str]:
    r = t["r"].astype(float)
    reason = t["exit_reason"].astype(str)
    n = len(t)
    if not n:
        return ["0", "-", "-", "-", "-"]
    other = n - int((reason == "target").sum()) - int((reason == "stop").sum())
    return [str(n), f"{(r > 0).sum()} / {(r <= 0).sum()}", f"{(reason == 'target').sum()} / {(reason == 'stop').sum()} / {other}",
            f"{r.sum():+.2f}", f"{r.mean():+.3f}"]


REASON_KIND = dict(personal_account.REASONS)


def _account(led: pd.DataFrame, dates: list, name: str) -> str:
    if not len(led[led["candidate"] == name]):
        return "no trade yet"
    if name == "JJ":  # his evaluation playbook: +$1,500 a day, the next trade after a loss (research/forward_jj.paper_account)
        p = forward_jj.paper_account(led[led["candidate"] == name], dates, "wait")
    else:
        p = paper_account(led, [pd.Timestamp(d) for d in dates], name, "wait")
    state = "ruined" if p["ruined"] else f"{p['evals']:.0f} eval(s), {p['passes']:.0f} passed, {p['payouts']:.0f} payout(s)"
    return f"${p['final_cash']:,.0f} ({state})"


def _streams(states: dict) -> tuple[pd.DataFrame, dict]:
    """All trades in one table (each keeps its stream's name) and each stream's scored sessions."""
    frames, dates = [], {}
    for code, _ in STREAMS:
        st = states.get("JJ" if code == "JJ" else "v1")
        dates[code] = st["dates"] if st else []
        if st and st["trades"]:
            t = pd.DataFrame(st["trades"])
            frames.append(t[t["candidate"] == code])
    led = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["candidate", "date", "entry_time", "direction", "r", "exit_reason"])
    return led, dates


def _rows(led: pd.DataFrame, dates: dict) -> list[tuple[str, list[str]]]:
    cols = [_summary(led[led["candidate"] == c]) for c, _ in STREAMS]
    rows = [("Sessions scored", [str(len(dates[c])) for c, _ in STREAMS])]
    rows += [(label, [col[i] for col in cols]) for i, label in enumerate(("Trades", "Up / down", "Target / stop / other exit", "Total R", "R per trade"))]
    rows.append(("Prop-firm paper account from $2,000", [_account(led, dates[c], c) for c, _ in STREAMS]))
    return rows


def jj_sessions(led: pd.DataFrame) -> list[tuple[str, int, float]]:
    """The JJ system's trades and total R by session of his day."""
    t = led[led["candidate"] == "JJ"] if len(led) else led
    return [(label, int((t["session"] == code).sum()), float(t.loc[t["session"] == code, "r"].astype(float).sum())) if len(t) else (label, 0, 0.0)
            for code, label in JJ_SESSIONS]


def retired_line(states: dict) -> str:
    """Baseline 0's record, kept: JJ's 09:30 rules only, the JJ stream until the JJ system replaced it."""
    st = states.get("B0")
    if not st:
        return ""
    t = pd.DataFrame(st["trades"]) if st["trades"] else pd.DataFrame(columns=["r"])
    return (f"JJ's 09:30 rules only (B0), retired 13 Oct 2026 when the JJ system replaced it: {len(st['dates'])} sessions, {len(t)} trades, "
            f"{t['r'].astype(float).sum():+.2f} R.")


def _label(t) -> str:
    return f"JJ {t['session']}" if t["candidate"] == "JJ" and isinstance(t.get("session"), str) else str(t["candidate"])


def page(states: dict, headline: str, readings: str, flags: list[str], now: str) -> str:
    kind = headline.split(":", 1)[0].strip().upper()
    led, dates = _streams(states)
    s = ["# Forward paper test", "", f"**Status: {headline}**", "", MEANING.get(kind, ""), "", f"Last run: {_when(now)}", "",
         "| | " + " | ".join(label for _, label in STREAMS) + " |", "|---|" + "---|" * len(STREAMS)]
    s += [f"| {label} | " + " | ".join(vals) + " |" for label, vals in _rows(led, dates)]
    s += ["", "## Milestones", ""]
    for code, label in STREAMS:
        n = int((led["candidate"] == code).sum()) if len(led) else 0
        s.append(f"- {label}: {len(dates[code])} of the first {SESSION_WINDOW} sessions; " + ", ".join(
            f"{min(n, k)} of {k} trades" for k in SETUP_CHECKS))
    s += ["- After about 20 to 30 trades in a stream with no flag, Chris decides on one $49 evaluation", "",
          "## JJ system by session", "", "| session | trades | total R |", "|---|---|---|"]
    s += [f"| {label} | {k} | {r:+.2f} |" for label, k, r in jj_sessions(led)]
    s += ["", "A few of his clauses cannot run yet (he gives no number, or they need 1-second data): docs/research/jj_system_v1.md lists them.",
          "", "## Checkpoints", ""]
    s += [f"- {f}" for f in flags] or ["- none reached yet"]
    if len(led):
        latest = led.sort_values("entry_time").tail(12).iloc[::-1]
        s += ["", "## Latest trades", "", "| stream | date | side | exit | R |", "|---|---|---|---|---|"]
        s += [f"| {_label(t)} | {t['date']} | {t['direction']} | {t['exit_reason']} | {float(t['r']):+.2f} |" for _, t in latest.iterrows()]
    s += accounts_md(states)
    s += learn_md(states.get("learn"))
    s += lab_md(states.get("lab"))
    s += tournament_md(states.get("tournament"))
    if readings:
        s += ["", "## Market data status (Databento)", ""] + [f"- {x}" for x in readings_lines(readings)]
    if retired_line(states):
        s += ["", "## Earlier versions", "", retired_line(states)]
    s += ["", "R is the result in units of the trade's stop: +2 is a full target on S3, about +1.5 on the JJ system, -1 a full stop. The PROP-FIRM "
          "paper accounts follow the frozen bookkeeping ($0.50 micro fee, intraday dips not counted), so they read a little high; the personal cash "
          "account above is costed separately at retail rates and does not share that convention."]
    return "\n".join(s) + "\n"


COLOURS = {"OK": "#1a7f37", "WAITING": "#6e7781", "REFUSED": "#cf222e", "FLAG": "#bf8700"}


def _spark(r: list[float]) -> str:
    """A stream's cumulative R as a small line, zero marked."""
    if len(r) < 2:
        return '<p class="muted">not enough trades yet</p>'
    c = [0.0]
    for x in r:
        c.append(c[-1] + x)
    lo, hi = min(c + [0.0]), max(c + [0.0])
    span = (hi - lo) or 1.0
    w, h = 600, 90
    pts = " ".join(f"{i * w / (len(c) - 1):.1f},{h - (v - lo) / span * h:.1f}" for i, v in enumerate(c))
    zero = h - (0 - lo) / span * h
    return (f'<svg viewBox="-4 -4 {w + 8} {h + 8}" class="spark" role="img" aria-label="cumulative R">'
            f'<line x1="0" y1="{zero:.1f}" x2="{w}" y2="{zero:.1f}" class="zero"/><polyline points="{pts}" class="line"/></svg>')


def html_page(states: dict, headline: str, readings: str, flags: list[str], now: str) -> str:
    kind = headline.split(":", 1)[0].strip().upper()
    led, dates = _streams(states)
    head = "<tr><th></th>" + "".join(f"<th>{esc.escape(label)}</th>" for _, label in STREAMS) + "</tr>"
    table = head + "".join("<tr><th>" + esc.escape(label) + "</th>" + "".join(f"<td>{esc.escape(v)}</td>" for v in vals) + "</tr>"
                           for label, vals in _rows(led, dates))
    miles, sparks = "", ""
    for code, label in STREAMS:
        t = led[led["candidate"] == code].sort_values("entry_time") if len(led) else led
        n = len(t)
        for title, v, k in [(f"{label}: first {SESSION_WINDOW} sessions", len(dates[code]), SESSION_WINDOW), (f"{label}: {SETUP_CHECKS[-1]} trades", n, SETUP_CHECKS[-1])]:
            miles += (f'<div class="mile"><span>{esc.escape(title)}</span><span>{min(v, k)} / {k}</span>'
                      f'<div class="bar"><div style="width:{min(v, k) / k * 100:.0f}%"></div></div></div>')
        sparks += f"<h3>{esc.escape(label)}</h3>" + _spark(t["r"].astype(float).tolist() if n else [])
    bysess = "".join(f"<tr><td>{esc.escape(label)}</td><td class='num'>{k}</td><td class='num'>{r:+.2f}</td></tr>" for label, k, r in jj_sessions(led))
    latest = "".join(f"<tr><td>{esc.escape(_label(t))}</td><td>{esc.escape(str(t['date']))}</td><td>{esc.escape(str(t['direction']))}</td>"
                     f"<td>{esc.escape(str(t['exit_reason']))}</td><td class=\"num\">{float(t['r']):+.2f}</td></tr>"
                     for _, t in (led.sort_values("entry_time").tail(12).iloc[::-1].iterrows() if len(led) else []))
    checks = "".join(f"<li>{esc.escape(f)}</li>" for f in flags) or "<li>none reached yet</li>"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>Forward paper test</title>
<style>
:root {{ --fg:#1f2328; --muted:#656d76; --bg:#ffffff; --line:#d0d7de; --card:#f6f8fa; }}
@media (prefers-color-scheme: dark) {{ :root {{ --fg:#e6edf3; --muted:#9198a1; --bg:#0d1117; --line:#30363d; --card:#161b22; }} }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.45 -apple-system, system-ui, "Segoe UI", sans-serif; }}
main {{ max-width:760px; margin:0 auto; padding:20px 16px 40px; }}
h1 {{ font-size:20px; margin:0 0 12px; }} h2 {{ font-size:15px; margin:28px 0 8px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
h3 {{ font-size:14px; margin:14px 0 4px; font-weight:600; }}
.status {{ border-left:6px solid {COLOURS.get(kind, "#6e7781")}; background:var(--card); padding:12px 14px; border-radius:6px; }}
.status b {{ display:block; font-size:18px; }} .muted {{ color:var(--muted); font-size:14px; }}
.scroll {{ overflow-x:auto; }} table {{ width:100%; border-collapse:collapse; font-size:15px; }}
th, td {{ text-align:left; padding:6px 4px; border-bottom:1px solid var(--line); vertical-align:top; }}
td, .num {{ font-variant-numeric:tabular-nums; }} .num {{ text-align:right; }}
.mile {{ display:grid; grid-template-columns:1fr auto; gap:2px 8px; margin:8px 0; font-size:15px; }}
.bar {{ grid-column:1 / -1; height:6px; background:var(--line); border-radius:3px; overflow:hidden; }} .bar div {{ height:100%; background:{COLOURS["OK"]}; }}
.spark {{ width:100%; height:auto; }} .spark .line {{ fill:none; stroke:var(--fg); stroke-width:2; }} .spark .zero {{ stroke:var(--line); stroke-dasharray:4 4; }}
ul {{ padding-left:18px; }} tr.promo td {{ font-weight:600; }}
.acct {{ max-width:720px; }} .acct th {{ width:46%; font-weight:500; color:var(--muted); }}
.acct td {{ font-variant-numeric:tabular-nums; }}
.flag {{ color:#bf8700; font-weight:600; }}
h3 {{ font-size:16px; margin:18px 0 6px; }}
</style></head><body><main>
<h1>Forward paper test</h1>
<div class="status"><b>{esc.escape(headline)}</b>{esc.escape(MEANING.get(kind, ""))}<div class="muted">Last run {esc.escape(_when(now))}</div></div>
<h2>So far</h2><div class="scroll"><table>{table}</table></div>
<h2>Cumulative R</h2>{sparks}
<h2>Milestones</h2>{miles}<p class="muted">After about 20 to 30 trades in a stream with no flag, Chris decides on one $49 evaluation.</p>
<h2>JJ system by session</h2><div class="scroll"><table><tr><th>session</th><th class="num">trades</th><th class="num">total R</th></tr>{bysess}</table></div>
<p class="muted">A few of his clauses cannot run yet (he gives no number, or they need 1-second data); the spec, docs/research/jj_system_v1.md, lists them.</p>
<h2>Checkpoints</h2><ul>{checks}</ul>
{accounts_html(states)}
{learn_html(states.get("learn"))}
{lab_html(states.get("lab"))}
{tournament_html(states.get("tournament"))}
{"<h2>Latest trades</h2><div class='scroll'><table><tr><th>stream</th><th>date</th><th>side</th><th>exit</th><th class='num'>R</th></tr>" + latest + "</table></div>" if latest else ""}
{"<h2>Market data</h2><p class='muted'>" + "<br>".join(esc.escape(x) for x in readings_lines(readings)) + "</p>" if readings else ""}
{"<h2>Earlier versions</h2><p class='muted'>" + esc.escape(retired_line(states)) + "</p>" if retired_line(states) else ""}
<p class="muted">R is the result in units of the trade's stop: -1 is a full stop, about +1.5 a full JJ target. The PROP-FIRM paper accounts follow
the frozen bookkeeping ($0.50 micro fee, intraday dips not counted), so they read a little high; the personal cash account is costed separately at
retail rates and does not share that convention.</p>
</main></body></html>
"""


BOUND_MIN_SESSIONS, BOUND_MIN_TRADES = 5, 10  # below these a day-clustered error is not meaningful: no bound is shown


def _bound(t: dict, v: dict) -> float:
    return v["lower_bound"] if t["sessions"] >= BOUND_MIN_SESSIONS and v["trades"] >= BOUND_MIN_TRADES else float("nan")


def _tournament_rows(t: dict | None) -> list[tuple]:
    """The tournament's variants: by forward lower bound once bounds mean something, by version name until then."""
    if not t:
        return []
    rows = sorted(t["variants"].items())
    if t["sessions"] < BOUND_MIN_SESSIONS:
        return rows
    return sorted(rows, key=lambda kv: (_bound(t, kv[1]) != _bound(t, kv[1]), -(_bound(t, kv[1]) if _bound(t, kv[1]) == _bound(t, kv[1]) else 0), kv[0]))


def readings_lines(readings: str) -> list[str]:
    """The day's condition readings, one line per date; a pasted table ('| date | condition | last modified |') is unpacked."""
    cells = [c.strip() for c in readings.split("|") if c.strip()]
    if "|" in readings and cells and len(cells) % 3 == 0:
        return [f"{cells[i]}: {cells[i + 1]} (last revised {cells[i + 2]})" for i in range(0, len(cells), 3)]
    return [x.strip() for x in readings.split(";") if x.strip()]


def _f(x: float, fmt: str) -> str:
    return "-" if x != x else format(x, fmt)


def tournament_md(t: dict | None) -> list[str]:
    if not t:
        return []
    rows = _tournament_rows(t)
    promo = [k for k, v in rows if v["promotable"]]
    s = ["", f"## Tournament: {len(rows)} versions of JJ's rules, forward only", "",
         f"{t['sessions']} session(s). A version is promotable at {t['min_trades']}+ trades with its lower bound above zero (allowing for {len(rows)} tries). "
         + ("Promotable now: " + ", ".join(promo) if promo else "None promotable yet."), "",
         "| version | what changes | trades | R per trade | lower bound | total R |", "|---|---|---|---|---|---|"]
    s += [f"| {k} | {v['description']} | {v['trades']} | {_f(v['r_per_trade'], '+.3f')} | {_f(_bound(t, v), '+.3f')} | {v['total_r']:+.1f} |" for k, v in rows]
    return s


def tournament_html(t: dict | None) -> str:
    if not t:
        return ""
    rows = _tournament_rows(t)
    promo = [k for k, v in rows if v["promotable"]]
    body = "".join(f"<tr{' class=promo' if v['promotable'] else ''}><td>{esc.escape(k)}</td><td>{esc.escape(v['description'])}</td><td class='num'>{v['trades']}</td>"
                   f"<td class='num'>{_f(v['r_per_trade'], '+.3f')}</td><td class='num'>{_f(_bound(t, v), '+.3f')}</td><td class='num'>{v['total_r']:+.1f}</td></tr>"
                   for k, v in rows)
    note = (f"{t['sessions']} session(s). Lower bounds appear from {BOUND_MIN_SESSIONS} sessions and {BOUND_MIN_TRADES} trades. A version is promotable at {t['min_trades']}+ trades with its lower bound above zero, allowing for {len(rows)} tries. "
            + ("Promotable now: " + ", ".join(promo) + "." if promo else "None promotable yet."))
    return (f"<h2>Tournament: {len(rows)} versions of JJ's rules</h2><p class='muted'>{esc.escape(note)}</p><div class='scroll'><table>"
            "<tr><th>version</th><th>what changes</th><th class='num'>trades</th><th class='num'>R/trade</th><th class='num'>lower bound</th>"
            f"<th class='num'>total R</th></tr>{body}</table></div>")


def _lab_rows(lab: dict | None) -> list[dict]:
    """The lab's versions, best first against the JJ system once a few days are in, by name before that."""
    if not lab:
        return []
    rows = [dict(v, batch=b["batch"]) for b in lab["batches"] for v in b["versions"]]
    for r in rows:
        if r.get("kind") == "challenger":
            r["description"] = "CHALLENGER: " + r["description"]
    if max([r["days"] for r in rows] + [0]) < lab.get("show_days", 5):
        return sorted(rows, key=lambda r: r["version"])
    return sorted(rows, key=lambda r: (r["per_day_vs_jj"] != r["per_day_vs_jj"], -(r["per_day_vs_jj"] if r["per_day_vs_jj"] == r["per_day_vs_jj"] else 0), r["version"]))


def _lab_note(lab: dict) -> str:
    rows = _lab_rows(lab)
    beats = [r["version"] for r in rows if r["verdict"] == "beats JJ"]
    days = max([r["days"] for r in rows] + [0])
    return (f"{len(rows)} versions of the JJ system (whole-system challengers, their ablations and single-setting components) run beside it on "
            f"paper and are compared with it day by day ({days} day(s) so far). The verdict is taken every {lab['min_days']} days, with the bar "
            f"raised for each of the {lab['tries']} tries and each look. Nothing here changes the JJ system; a version that beats it is a proposal for you. "
            + ("Beating JJ now: " + ", ".join(beats) + "." if beats else "None beats it yet."))


def learn_lines(rep: dict | None, k: int = 6) -> list[str]:
    """The nightly learning report's largest findings (research/jj_learn.py)."""
    if not rep:
        return []
    if rep.get("in_step") is False:
        return ["The learning engine is out of step with the live ledger; the report is paused until that is fixed."]
    return list(rep.get("findings", []))[:k]


def learn_md(rep: dict | None) -> list[str]:
    lines = learn_lines(rep)
    if not lines:
        return []
    return ["", "## What the JJ system is learning", "", f"From {rep.get('n_days', 0)} trading day(s) of its own trades; every signal its rules saw, "
            "taken or passed, is replayed with other exits. Largest first:", ""] + [f"- {x}" for x in lines]


def learn_html(rep: dict | None) -> str:
    lines = learn_lines(rep)
    if not lines:
        return ""
    return (f"<h2>What the JJ system is learning</h2><p class='muted'>From {rep.get('n_days', 0)} trading day(s) of its own trades; every signal its "
            "rules saw, taken or passed, is replayed with other exits. Largest first:</p><ul>" + "".join(f"<li>{esc.escape(x)}</li>" for x in lines) + "</ul>")


def lab_md(lab: dict | None) -> list[str]:
    if not lab:
        return []
    s = ["", "## Background lab", "", _lab_note(lab), "", "| version | what changes | days | trades | total R | vs JJ per day | verdict |",
         "|---|---|---|---|---|---|---|"]
    s += [f"| {r['version']} | {r['description']} | {r['days']} | {r['trades']} | {r['total_r']:+.1f} | {_f(r['per_day_vs_jj'], '+.2f')} | {r['verdict']} |"
          for r in _lab_rows(lab)]
    return s


def lab_html(lab: dict | None) -> str:
    if not lab:
        return ""
    body = "".join(f"<tr{' class=promo' if r['verdict'] == 'beats JJ' else ''}><td>{esc.escape(r['version'])}</td><td>{esc.escape(r['description'])}</td>"
                   f"<td class='num'>{r['days']}</td><td class='num'>{r['trades']}</td><td class='num'>{r['total_r']:+.1f}</td>"
                   f"<td class='num'>{_f(r['per_day_vs_jj'], '+.2f')}</td><td>{esc.escape(r['verdict'])}</td></tr>" for r in _lab_rows(lab))
    return (f"<h2>Background lab</h2><p class='muted'>{esc.escape(_lab_note(lab))}</p><div class='scroll'><table><tr><th>version</th><th>what changes</th>"
            f"<th class='num'>days</th><th class='num'>trades</th><th class='num'>total R</th><th class='num'>vs JJ per day</th><th>verdict</th></tr>{body}</table></div>")


ACCOUNTS_NOTE = ("Two accounts, kept apart on purpose. They answer different questions and their dollars are not "
                 "comparable one for one: the personal account is cash, the prop-firm figures are evaluation fees, "
                 "activations and payouts with trade P&L modelled at the firm's risk budget per R.")


def _stale(pers: dict | None, states: dict) -> str:
    """Is the personal account's reconstruction behind the JJ record it is drawn from? The step is
    best effort, so it can fail while the rest of the run succeeds, and a stale balance must say
    so rather than look current."""
    jj = states.get("JJ")
    if not pers or not jj:
        return ""
    have, want = pers.get("days") or [], jj.get("dates") or []
    if len(have) < len(want):
        return (f"STALE: reconstructed through {have[-1] if have else 'no day'}, but the record now has "
                f"{len(want)} day(s) through {want[-1] if want else '-'}. The figures below are behind.")
    return ""


def _personal_rows(pers: dict | None) -> list[tuple[str, str]]:
    if not pers or not pers.get("result"):
        return []
    r, m = pers["result"], pers.get("marked_to_market") or {}
    days = len(pers.get("days") or [])
    rows = [("Starting balance", f"${r['start_cash']:,.2f}"),
            ("Current balance", f"${r['end_cash']:,.2f}"),
            ("Net profit / loss", f"{'+' if r['net_usd'] >= 0 else '-'}${abs(r['net_usd']):,.2f}"),
            ("Return", f"{r['return_pct']:+.2f}% over {days} scored day(s)"),
            ("Trades", f"{r['trades_taken']} taken of {r['trades_available']} signals, {r['wins']} up / {r['losses']} down"),
            ("Largest drawdown (closed balance)", f"${r['max_drawdown_closed_usd']:,.2f} ({r['max_drawdown_closed_pct']:.2f}%)")]
    if m:
        rows.append(("Largest drawdown (marked to market)",
                     f"${m['mtm_max_drawdown_usd']:,.2f} ({m['mtm_max_drawdown_pct']:.2f}%), worst equity ${m['worst_equity_usd']:,.2f}"))
        rows.append(("Minutes below required day margin", str(m["margin_breach_minutes"])))
    rows.append(("Trading costs", f"${r['costs_usd']:,.2f} (commission ${r['commission_usd']:,.2f} + entry slippage ${r['entry_slip_usd']:,.2f})"))
    rows.append(("Declined by its own limits", f"{r['trades_skipped']} signals, together {r['r_skipped']:+.2f} R"))
    return rows


def _prop_rows(states: dict) -> list[tuple[str, str]]:
    led, dates = _streams(states)
    jj = states.get("JJ")
    if not jj or not len(led[led["candidate"] == "JJ"]):
        return []
    p = forward_jj.paper_account(led[led["candidate"] == "JJ"], jj.get("dates") or [], "wait")
    if not p:
        return []
    return [("Cash left of the $2,000 stake", f"${p['final_cash']:,.0f}"),
            ("Evaluations bought", f"{p['evals']:.0f}, {p['passes']:.0f} passed"),
            ("Activations", f"{p['activations']:.0f}"),
            ("Fees paid to the firm", f"${p['fees']:,.0f}"),
            ("Payouts requested / received", f"{p['payouts']:.0f} / ${p['paid']:,.0f}"),
            ("State", "ruined" if p["ruined"] else "running")]


LEDGER_N = 15  # the dashboard shows the most recent few; the full ledger is in the .md report


def _ledger_rows(pers: dict | None) -> list[list[str]]:
    """The most recent trades as real dollars, newest first, with the balance after each close."""
    led = (pers or {}).get("ledger") or []
    out = []
    for x in led[-LEDGER_N:][::-1]:
        fees = x["commission_usd"] + x["entry_slip_usd"]
        bal = x.get("cash_after_close")
        out.append([x["date"], x["session"], str(x["direction"]), str(x["exit_reason"]),
                    str(x["micros"]),
                    f"{'+' if x['gross_usd'] >= 0 else '-'}${abs(x['gross_usd']):,.2f}",
                    f"-${fees:,.2f}",
                    f"{'+' if x['net_usd'] >= 0 else '-'}${abs(x['net_usd']):,.2f}",
                    f"${bal:,.2f}" if bal is not None else "-"])
    return out


def _skipped_rows(pers: dict | None) -> list[list[str]]:
    """Every signal the account declined, with the limit that declined it."""
    return [[x["date"], x["session"], str(x.get("direction", "-")), f"{x['stop_points']:.1f}",
             f"{x['r']:+.2f}", str(x["would_size"]), x["reason"], x["kind"]]
            for x in ((pers or {}).get("skipped") or [])]


LEDGER_HEAD = ["date", "session", "side", "exit", "micros", "gross", "fees", "net", "balance after"]
SKIP_HEAD = ["date", "session", "side", "stop pts", "recorded R", "would_size", "reason", "kind"]


def accounts_md(states: dict) -> list[str]:
    pers = states.get("personal")
    s = ["", "## Money: two separate accounts", "", ACCOUNTS_NOTE, "",
         "### 1. Personal cash account - what would my own $2,000 be worth?", ""]
    stale = _stale(pers, states)
    if stale:
        s += [f"**{stale}**", ""]
    rows = _personal_rows(pers)
    if not rows:
        s += ["Not reconstructed yet.", ""]
    else:
        s += ["A HYPOTHETICAL accounting view over days already collected and scored, not a claim that this account "
              "was operating from the first of them. MNQ micros, retail commissions, its own sizing, margin and risk "
              "limits: docs/research/personal_account_assumptions.md states every assumption and what is not modelled.",
              "", "| | |", "|---|---|"]
        s += [f"| {k} | {v} |" for k, v in rows]
        s += [""]
        r = pers["result"]
        if r.get("latched_off"):
            s += ["**The account hit its trading floor and stopped for good.**", ""]
        if r.get("open_at_flatten"):
            s += [f"**FLAG: {r['open_at_flatten']} taken position(s) would still have been open at the daily "
                  "flatten time; the record holds no liquidation price for them.**", ""]
        by = r.get("skipped_by_reason") or {}
        if by:
            s += ["Why signals were declined (none counts as profit or loss):", ""]
            s += [f"- {why}: {k} ({REASON_KIND.get(why, '?')})" for why, k in by.items()]
            s += [""]
        rows_l = _ledger_rows(pers)
        if rows_l:
            n = len(pers.get("ledger") or [])
            s += [f"The last {len(rows_l)} of {n} simulated trades in real dollars, newest first. Fees are this "
                  "trade's commission plus entry slippage, both charged at the entry. The full trade-by-trade "
                  "ledger is research/private/personal_account_jj.md.", "",
                  "| " + " | ".join(LEDGER_HEAD) + " |", "|" + "---|" * len(LEDGER_HEAD)]
            s += ["| " + " | ".join(r) + " |" for r in rows_l]
            s += [""]
        rows_s = _skipped_rows(pers)
        if rows_s:
            s += ["Every signal the account declined, and the limit that declined it. None of these contributes a "
                  "cent to the balance above.", "",
                  "| " + " | ".join(SKIP_HEAD) + " |", "|" + "---|" * len(SKIP_HEAD)]
            s += ["| " + " | ".join(r) + " |" for r in rows_s]
            s += [""]
        sens = pers.get("sensitivity") or []
        if sens:
            s += ["The per-trade risk cap is the knob that moves this most, and it is a policy choice, not a "
                  "figure the data forced. Each row reruns the whole account:", "",
                  "| max risk per trade | trades | net P&L | return |", "|---|---|---|---|"]
            s += [f"| {100 * x['cap_frac']:.3f}% | {x['trades_taken']} | "
                  f"{'+' if x['net_usd'] >= 0 else '-'}${abs(x['net_usd']):,.2f} | {x['return_pct']:+.2f}% |"
                  for x in sens]
            s += [""]
    s += ["### 2. Prop-firm account (Topstep) - what have the evaluations cost and paid?", ""]
    prop = _prop_rows(states)
    if not prop:
        s += ["No trade yet.", ""]
    else:
        s += ["The same $2,000, spent on Topstep 50K evaluations instead. Trade P&L here is modelled at the firm's "
              "risk budget per R on the frozen bookkeeping ($0.50 micro fee, intraday dips not counted), so it reads "
              "a little high and is NOT own cash.", "", "| | |", "|---|---|"]
        s += [f"| {k} | {v} |" for k, v in prop]
        s += [""]
    return s


def accounts_html(states: dict) -> str:
    pers = states.get("personal")
    out = [f"<h2>Money: two separate accounts</h2><p class='muted'>{esc.escape(ACCOUNTS_NOTE)}</p>"]
    stale = _stale(pers, states)
    out.append("<h3>1. Personal cash account &mdash; what would my own $2,000 be worth?</h3>")
    if stale:
        out.append(f"<p class='flag'>{esc.escape(stale)}</p>")
    rows = _personal_rows(pers)
    if not rows:
        out.append("<p class='muted'>Not reconstructed yet.</p>")
    else:
        out.append("<p class='muted'>A HYPOTHETICAL accounting view over days already collected and scored, not a "
                   "claim that this account was operating from the first of them. MNQ micros, retail commissions, its "
                   "own sizing, margin and risk limits.</p>")
        body = "".join(f"<tr><th>{esc.escape(k)}</th><td>{esc.escape(v)}</td></tr>" for k, v in rows)
        out.append(f"<table class='acct'>{body}</table>")
        r = pers["result"]
        if r.get("latched_off"):
            out.append("<p class='flag'>The account hit its trading floor and stopped for good.</p>")
        if r.get("open_at_flatten"):
            out.append(f"<p class='flag'>FLAG: {r['open_at_flatten']} taken position(s) would still have been open at "
                       "the daily flatten time; the record holds no liquidation price for them.</p>")
        by = r.get("skipped_by_reason") or {}
        if by:
            lis = "".join(f"<li>{esc.escape(why)}: {k} ({esc.escape(REASON_KIND.get(why, '?'))})</li>"
                          for why, k in by.items())
            out.append(f"<p class='muted'>Why signals were declined (none counts as profit or loss):</p><ul>{lis}</ul>")
        rows_l = _ledger_rows(pers)
        if rows_l:
            n = len(pers.get("ledger") or [])
            head = "".join(f"<th{' class=num' if h not in ('date', 'session', 'side', 'exit') else ''}>"
                           f"{esc.escape(h)}</th>" for h in LEDGER_HEAD)
            body = "".join("<tr>" + "".join(f"<td{' class=num' if i >= 4 else ''}>{esc.escape(v)}</td>"
                                            for i, v in enumerate(r)) + "</tr>" for r in rows_l)
            out.append(f"<p class='muted'>The last {len(rows_l)} of {n} simulated trades in real dollars, newest "
                       "first. Fees are this trade's commission plus entry slippage, both charged at the entry.</p>"
                       f"<div class='scroll'><table><tr>{head}</tr>{body}</table></div>")
        rows_s = _skipped_rows(pers)
        if rows_s:
            head = "".join(f"<th{' class=num' if h in ('stop pts', 'recorded R', 'would_size') else ''}>"
                           f"{esc.escape(h)}</th>" for h in SKIP_HEAD)
            body = "".join("<tr>" + "".join(f"<td{' class=num' if i in (3, 4, 5) else ''}>{esc.escape(v)}</td>"
                                            for i, v in enumerate(r)) + "</tr>" for r in rows_s)
            out.append("<p class='muted'>Every signal the account declined, and the limit that declined it. None of "
                       "these contributes a cent to the balance above.</p>"
                       f"<div class='scroll'><table><tr>{head}</tr>{body}</table></div>")
        sens = pers.get("sensitivity") or []
        if sens:
            srows = "".join(f"<tr><td class='num'>{100 * x['cap_frac']:.3f}%</td><td class='num'>{x['trades_taken']}</td>"
                            f"<td class='num'>{'+' if x['net_usd'] >= 0 else '-'}${abs(x['net_usd']):,.2f}</td>"
                            f"<td class='num'>{x['return_pct']:+.2f}%</td></tr>" for x in sens)
            out.append("<p class='muted'>The per-trade risk cap moves this most, and it is a policy choice, not a "
                       "figure the data forced. Each row reruns the whole account:</p>"
                       "<div class='scroll'><table><tr><th class='num'>max risk per trade</th><th class='num'>trades</th>"
                       f"<th class='num'>net P&amp;L</th><th class='num'>return</th></tr>{srows}</table></div>")
    out.append("<h3>2. Prop-firm account (Topstep) &mdash; what have the evaluations cost and paid?</h3>")
    prop = _prop_rows(states)
    if not prop:
        out.append("<p class='muted'>No trade yet.</p>")
    else:
        out.append("<p class='muted'>The same $2,000, spent on Topstep 50K evaluations instead. Trade P&amp;L here is "
                   "modelled at the firm's risk budget per R on the frozen bookkeeping ($0.50 micro fee, intraday dips "
                   "not counted), so it reads a little high and is NOT own cash.</p>")
        body = "".join(f"<tr><th>{esc.escape(k)}</th><td>{esc.escape(v)}</td></tr>" for k, v in prop)
        out.append(f"<table class='acct'>{body}</table>")
    return "".join(out)


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
    ap.add_argument("--state", help="research/private/forward_v1_state.json, S3 and S4 (absent until the first scored run)")
    ap.add_argument("--state-jj", help="research/private/jj_system_v1_state.json, the JJ system")
    ap.add_argument("--state-b0", help="research/private/forward_b0_state.json, Baseline 0's kept record (retired)")
    ap.add_argument("--public-status", help="research/forward_v1_status.md, for the checkpoint lines")
    ap.add_argument("--public-status-b0", help="ignored: Baseline 0 is retired (accepted so an older job still runs)")
    ap.add_argument("--tournament", help="research/private/tournament_v1_summary.json")
    ap.add_argument("--lab", help="research/private/jj_lab_summary.json, the background lab")
    ap.add_argument("--learn", help="research/private/jj_learn_report.json, the nightly learning report")
    ap.add_argument("--personal", help="research/private/personal_account_jj.json, the personal cash account")
    ap.add_argument("--headline", required=True, help="OK | WAITING: ... | REFUSED: ... | FLAG: ...")
    ap.add_argument("--readings", default="", help="the day's Databento condition readings, one line")
    ap.add_argument("--out", required=True)
    ap.add_argument("--html", help="also write the web page here (robots.txt beside it)")
    a = ap.parse_args()
    states = {}
    for key, path in (("v1", a.state), ("JJ", a.state_jj), ("B0", a.state_b0), ("tournament", a.tournament), ("lab", a.lab), ("learn", a.learn),
                      ("personal", a.personal)):
        if path and os.path.exists(path):
            with open(path) as fh:
                states[key] = json.load(fh)
    now = datetime.now(timezone.utc).isoformat()
    flags = checkpoint_lines(a.public_status)  # Baseline 0 is retired: its checkpoints no longer apply
    text = page(states, a.headline, a.readings, flags, now)
    with open(a.out, "w") as fh:
        fh.write(text)
    if a.html:
        os.makedirs(os.path.dirname(os.path.abspath(a.html)), exist_ok=True)
        with open(a.html, "w") as fh:
            fh.write(html_page(states, a.headline, a.readings, flags, now))
        with open(os.path.join(os.path.dirname(os.path.abspath(a.html)), "robots.txt"), "w") as fh:
            fh.write("User-agent: *\nDisallow: /\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
