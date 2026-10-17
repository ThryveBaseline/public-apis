from research.status_page import checkpoint_lines, html_page, page


def _trade(c, d, r, why, side="long", session=None, grade="A", setup="continuation"):
    t = {"candidate": c, "date": d, "entry_time": f"{d} 09:41:00-04:00", "exit_time": f"{d} 10:20:00-04:00", "direction": side, "entry": 25000.0,
         "stop": 24900.0, "r": r, "exit_reason": why, "setup": setup, "grade": grade, "stop_points": 25.0}
    if session:
        t["session"] = session
    return t


STATES = {"v1": {"dates": ["2026-10-06", "2026-10-07"],
                 "trades": [_trade("S3", "2026-10-06", 2.0, "target"), _trade("S3", "2026-10-07", -1.02, "stop", "short"), _trade("S4", "2026-10-07", 0.3, "flat")]},
          "JJ": {"dates": ["2026-10-06", "2026-10-07"],
                 "trades": [_trade("JJ", "2026-10-06", 1.5, "target", session="09:30"), _trade("JJ", "2026-10-06", -1.02, "stop", session="news", setup="reversion"),
                            _trade("JJ", "2026-10-07", 0.1, "firm_close", session="book", grade="A+", setup="overnight")]},
          "B0": {"dates": ["2026-10-06"], "trades": [_trade("B0", "2026-10-06", -1.02, "stop")]}}


def test_a_waiting_page_before_any_score():
    text = page({}, "WAITING: 2026-10-06 degraded", "2026-10-06 degraded 2026-10-06", [], "2026-10-08T07:05:00+00:00")
    assert "**Status: WAITING: 2026-10-06 degraded**" in text and "Nothing for you to do." in text and "Last run: Thu 08 Oct 2026, 03:05 ET" in text
    assert "| Trades | 0 | 0 | 0 |" in text and "| Sessions scored | 0 | 0 | 0 |" in text


def test_three_streams_side_by_side(tmp_path):
    text = page(STATES, "OK", "", ["S3, first 10 sessions: within the development 1st-99th percentiles"], "2026-10-08T07:05:00Z")
    assert "| | S3 continuation | S4 + A+ reversion | JJ system |" in text
    assert "| Trades | 2 | 1 | 3 |" in text and "| Total R | +0.98 | +0.30 | +0.58 |" in text and "| Target / stop / other exit | 1 / 1 / 0 | 0 / 0 / 1 | 1 / 1 / 1 |" in text
    assert "- JJ system: 2 of the first 10 sessions; 3 of 20 trades, 3 of 30 trades" in text
    assert "| JJ book | 2026-10-07 | long | firm_close | +0.10 |" in text and "within the development" in text
    assert "| 08:30 news | 1 | -1.02 |" in text and "| 18:00 | 0 | +0.00 |" in text and "| overnight orders | 1 | +0.10 |" in text
    assert "retired 13 Oct 2026" in text and "1 trades, -1.02 R" in text
    pub = tmp_path / "status.md"
    pub.write_text("x\n\n## Checkpoints (protocol v1)\n\n- S3, first 10 sessions: **FLAG: count**\n")
    assert checkpoint_lines(str(pub)) == ["S3, first 10 sessions: **FLAG: count**"]


def test_the_web_page():
    h = html_page(STATES, "OK", "2026-10-07 available", [], "2026-10-08T07:05:00Z")
    assert h.startswith("<!doctype html>") and 'content="noindex, nofollow"' in h and "<b>OK</b>" in h and h.count("<svg") == 2 and "not enough trades yet" in h  # S4 has one trade
    assert "<th>JJ system</th>" in h and "+0.58" in h and "2 / 10" in h and "JJ system by session" in h and "Earlier versions" in h
    w = html_page({}, "REFUSED: <bad>", "", [], "2026-10-08T07:05:00Z")
    assert "&lt;bad&gt;" in w and "<svg" not in w and "#cf222e" in w


def test_the_tournament_table():
    t = {"sessions": 3, "min_trades": 50, "z": 2.92, "variants": {
        "T00": {"description": "JJ's rules", "trades": 12, "r_per_trade": 0.1, "se": 0.3, "lower_bound": -0.776, "total_r": 1.2, "wins": 6, "promotable": False},
        "T05": {"description": "reversions only until 10:00", "trades": 60, "r_per_trade": 0.9, "se": 0.2, "lower_bound": 0.316, "total_r": 54.0, "wins": 40, "promotable": True},
        "T21": {"description": "50-point stop", "trades": 0, "r_per_trade": float("nan"), "se": float("nan"), "lower_bound": float("nan"), "total_r": 0.0, "wins": 0,
                "promotable": False}}}
    text = page({"tournament": t}, "OK", "", [], "2026-10-08T07:05:00Z")
    assert "Promotable now: T05" in text and text.index("| T00 |") < text.index("| T05 |") < text.index("| T21 |")  # 3 sessions: by name, no bounds
    assert "| T05 | reversions only until 10:00 | 60 | +0.900 | - |" in text
    later = page({"tournament": {**t, "sessions": 8}}, "OK", "", [], "2026-10-08T07:05:00Z")
    assert later.index("| T05 |") < later.index("| T00 |") < later.index("| T21 |") and "| T05 | reversions only until 10:00 | 60 | +0.900 | +0.316 |" in later
    h = html_page({"tournament": t}, "OK", "", [], "2026-10-08T07:05:00Z")
    assert "<tr class=promo><td>T05</td>" in h and "None promotable" not in h


def test_readings_from_a_pasted_table():
    from research.status_page import readings_lines
    assert readings_lines("| 2026-10-06 | available | 2026-10-08 | | 2026-10-07 | available | 2026-10-07 |") == [
        "2026-10-06: available (last revised 2026-10-08)", "2026-10-07: available (last revised 2026-10-07)"]
    assert readings_lines("2026-10-06 degraded; 2026-10-07 available") == ["2026-10-06 degraded", "2026-10-07 available"]


def test_the_background_lab_section():
    lab = {"tries": 15, "min_days": 20, "show_days": 5, "batches": [{"batch": 1, "versions": [
        {"version": "L05", "description": "no overnight orders", "days": 6, "trades": 90, "total_r": 4.2, "per_day_vs_jj": 0.8, "verdict": "too early"},
        {"version": "L01", "description": "continuation window 15 minutes", "days": 6, "trades": 120, "total_r": -3.0, "per_day_vs_jj": -0.4, "verdict": "too early"}]}]}
    text = page({"lab": lab}, "OK", "", [], "2026-10-20T07:05:00Z")
    assert "## Background lab" in text and text.index("| L05 |") < text.index("| L01 |") and "None beats it yet." in text
    assert "| L05 | no overnight orders | 6 | 90 | +4.2 | +0.80 | too early |" in text
    h = html_page({"lab": lab}, "OK", "", [], "2026-10-20T07:05:00Z")
    assert "<h2>Background lab</h2>" in h and "no overnight orders" in h
