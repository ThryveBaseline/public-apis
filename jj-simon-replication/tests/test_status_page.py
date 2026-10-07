from research.status_page import checkpoint_lines, html_page, page


def _trade(c, d, r, why, side="long"):
    return {"candidate": c, "date": d, "entry_time": f"{d} 09:41:00-04:00", "exit_time": f"{d} 10:20:00-04:00", "direction": side, "entry": 25000.0,
            "stop": 24900.0, "r": r, "exit_reason": why, "setup": "continuation"}


def test_a_waiting_page_before_any_score():
    text = page(None, "WAITING: 2026-10-06 degraded", "2026-10-06 degraded 2026-10-06", [], "2026-10-08T07:05:00+00:00")
    assert "**Status: WAITING: 2026-10-06 degraded**" in text and "Nothing for you to do." in text
    assert "Sessions scored: 0" in text and "| Trades | 0 | 0 |" in text and "Last run: Thu 08 Oct 2026, 03:05 ET" in text


def test_a_page_with_trades(tmp_path):
    state = {"dates": ["2026-10-06", "2026-10-07"],
             "trades": [_trade("S3", "2026-10-06", 2.0, "target"), _trade("S3", "2026-10-07", -1.02, "stop", "short"), _trade("S4", "2026-10-07", 0.3, "flat")]}
    text = page(state, "OK", "", ["S3, first 10 sessions: within the development 1st-99th percentiles"], "2026-10-08T07:05:00Z")
    assert "| Trades | 2 | 1 |" in text and "| Up / down | 1 / 1 | 1 / 0 |" in text and "| Total R | +0.98 | +0.30 |" in text
    assert "- 20 S3 trades: 18 to go" in text and "First 10-session check: 8 session(s) to go" in text
    assert text.index("| 2026-10-07 | short | stop | -1.02 |") < text.index("| 2026-10-06 | long | target | +2.00 |")  # newest first
    assert "Paper account from $2,000 | $" in text and "within the development" in text
    pub = tmp_path / "status.md"
    pub.write_text("x\n\n## Checkpoints (protocol v1)\n\n- S3, first 10 sessions: **FLAG: count**\n")
    assert checkpoint_lines(str(pub)) == ["S3, first 10 sessions: **FLAG: count**"]


def test_the_web_page():
    state = {"dates": ["2026-10-06", "2026-10-07"],
             "trades": [_trade("S3", "2026-10-06", 2.0, "target"), _trade("S3", "2026-10-07", -1.02, "stop", "short")]}
    h = html_page(state, "OK", "2026-10-07 available", [], "2026-10-08T07:05:00Z")
    assert h.startswith("<!doctype html>") and 'content="noindex, nofollow"' in h and "<b>OK</b>" in h and "<svg" in h
    assert "<td>2</td>" in h and "+0.98" in h and "2 / 10" in h
    w = html_page(None, "REFUSED: <bad>", "", [], "2026-10-08T07:05:00Z")
    assert "&lt;bad&gt;" in w and "<svg" not in w and "#cf222e" in w
