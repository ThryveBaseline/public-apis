from research.status_page import checkpoint_lines, html_page, page


def _trade(c, d, r, why, side="long"):
    return {"candidate": c, "date": d, "entry_time": f"{d} 09:41:00-04:00", "exit_time": f"{d} 10:20:00-04:00", "direction": side, "entry": 25000.0,
            "stop": 24900.0, "r": r, "exit_reason": why, "setup": "continuation"}


STATES = {"v1": {"dates": ["2026-10-06", "2026-10-07"],
                 "trades": [_trade("S3", "2026-10-06", 2.0, "target"), _trade("S3", "2026-10-07", -1.02, "stop", "short"), _trade("S4", "2026-10-07", 0.3, "flat")]},
          "B0": {"dates": ["2026-10-06", "2026-10-07"],
                 "trades": [_trade("B0", "2026-10-06", 1.5, "target"), _trade("B0", "2026-10-06", -1.02, "stop"), _trade("B0", "2026-10-07", 0.1, "session_end")]}}


def test_a_waiting_page_before_any_score():
    text = page({}, "WAITING: 2026-10-06 degraded", "2026-10-06 degraded 2026-10-06", [], "2026-10-08T07:05:00+00:00")
    assert "**Status: WAITING: 2026-10-06 degraded**" in text and "Nothing for you to do." in text and "Last run: Thu 08 Oct 2026, 03:05 ET" in text
    assert "| Trades | 0 | 0 | 0 |" in text and "| Sessions scored | 0 | 0 | 0 |" in text


def test_three_streams_side_by_side(tmp_path):
    text = page(STATES, "OK", "", ["S3, first 10 sessions: within the development 1st-99th percentiles"], "2026-10-08T07:05:00Z")
    assert "| | S3 continuation | S4 + A+ reversion | JJ full rules |" in text
    assert "| Trades | 2 | 1 | 3 |" in text and "| Total R | +0.98 | +0.30 | +0.58 |" in text and "| Target / stop / other exit | 1 / 1 / 0 | 0 / 0 / 1 | 1 / 1 / 1 |" in text
    assert "- JJ full rules: 2 of the first 10 sessions; 3 of 20 trades, 3 of 30 trades" in text
    assert "| B0 | 2026-10-07 | long | session_end | +0.10 |" in text and "within the development" in text
    pub = tmp_path / "status.md"
    pub.write_text("x\n\n## Checkpoints (protocol v1)\n\n- S3, first 10 sessions: **FLAG: count**\n")
    assert checkpoint_lines(str(pub)) == ["S3, first 10 sessions: **FLAG: count**"]


def test_the_web_page():
    h = html_page(STATES, "OK", "2026-10-07 available", [], "2026-10-08T07:05:00Z")
    assert h.startswith("<!doctype html>") and 'content="noindex, nofollow"' in h and "<b>OK</b>" in h and h.count("<svg") == 2 and "not enough trades yet" in h  # S4 has one trade
    assert "<th>JJ full rules</th>" in h and "+0.58" in h and "2 / 10" in h
    w = html_page({}, "REFUSED: <bad>", "", [], "2026-10-08T07:05:00Z")
    assert "&lt;bad&gt;" in w and "<svg" not in w and "#cf222e" in w
