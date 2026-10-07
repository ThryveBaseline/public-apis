import numpy as np
import pandas as pd
import pytest

from fpt.data import NY, synthetic_minute_bars
from fpt.evaluate import trading_days_of, walk_forward_pass_probability
from fpt.strategy import StrategyConfig, generate_trades
from research.anatomy import load_trades
from research.candidates import MAX_EVAL_DAYS, PRESETS, ny_day, score
from research.ledger_filters import sequential_pass
from research.lifetime import HORIZONS, POLICIES, RUNS
from research.stream_report import on_span, scoring_sections


@pytest.fixture(scope="module")
def stream(tmp_path_factory):
    bars = synthetic_minute_bars(days=200, seed=9)
    p = tmp_path_factory.mktemp("sr") / "trades.csv"
    generate_trades(bars, StrategyConfig()).to_csv(p, index=False)
    pre = load_trades(str(p))
    cal = trading_days_of(bars)
    day = pre["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    cut = (day.max() - pd.DateOffset(months=2)).normalize()
    start = cal[60]
    return pre, cal, cut, start


def test_on_span_cuts_the_entries_and_the_calendar(stream):
    pre, cal, cut, start = stream
    p, c = on_span(pre, cal, start)
    day = p["entry_time"].dt.tz_convert(NY).dt.normalize().dt.tz_localize(None)
    assert len(p) < len(pre) and (day >= start).all() and c[0] == start and len(c) == len(cal) - 60
    q, d = on_span(pre, cal, None)
    assert q is pre and d is cal


def _row(text, name, per):
    line = next(x for x in text.split("\n") if x.startswith(f"| {name} | {per} |"))
    return [x.strip() for x in line.strip("|").split("|")]


def test_a_stream_is_scored_on_its_span_only(stream):
    """A stream with no entry before its span. On the whole calendar the evaluations started more than a horizon before
    its first entry see no trade and stay open (failures to the rate), and the later early starts replay its first days
    on a shortened window; on its span every start can trade from its first day. The table is the span's."""
    pre, cal, cut, start = stream
    late, _ = on_span(pre, cal, start)
    st = sequential_pass(late)
    dev = cal[cal <= cut]
    wide = walk_forward_pass_probability(st[(ny_day(st) <= cut).to_numpy()], PRESETS["topstep_50k"], 500.0, MAX_EVAL_DAYS, trading_days=dev)
    i0 = list(dev).index(ny_day(st).min())
    assert i0 > MAX_EVAL_DAYS and (wide["outcome"].iloc[:i0 - MAX_EVAL_DAYS + 1] == "open").all()  # idle starts
    text = "\n".join(scoring_sections([("late", late, start), ("late, whole calendar", late, None)], cal, cut))
    spanned = score(st, cal[cal >= start], cut)["development"]["firms"].set_index("firm").loc["topstep_50k"]
    whole = score(st, cal, cut)["development"]["firms"].set_index("firm").loc["topstep_50k"]
    assert spanned["pass_rate"] != whole["pass_rate"]
    row = _row(text, "late", "development")  # stream, period, span from, trades, R/trade, total R, P(pass), ...
    assert row[2] == str(start.date()) and row[3] == str(int((ny_day(st) <= cut).sum())) and row[6] == f"{spanned['pass_rate']:.1%}"
    assert _row(text, "late, whole calendar", "development")[2:7:4] == ["all", f"{whole['pass_rate']:.1%}"]


def test_stream_names_must_be_distinct(stream):
    pre, cal, cut, start = stream
    with pytest.raises(ValueError, match="distinct"):
        scoring_sections([("a", pre, start), ("a", pre, None)], cal, cut)


def test_every_section_has_a_row_per_stream_and_period(stream):
    pre, cal, cut, start = stream
    text = "\n".join(scoring_sections([("a", pre, start), ("b", pre[pre["setup"].astype(str) == "continuation"], start)], cal, cut))
    heads = ["### B3 summary", "### Size sensitivity", "### Whole micro contracts", "### Lifetime (B4)"]
    at = [text.index(h) for h in heads]
    assert at == sorted(at)
    sections = [text[i:j] for i, j in zip(at, at[1:] + [len(text)])]
    for sec in sections[:3]:
        for name in ("a", "b"):
            for per in ("development", "benchmark"):
                assert f"| {name} | {per} |" in sec
    life = sections[3]
    for firm, size in RUNS:
        assert f"{firm} at {size:.2f} of the budget:" in life
    for name in ("a", "b"):
        for policy in POLICIES:
            assert life.count(f"| {name} | development | {policy} |") == len(RUNS)
    row = _row(life, "a", "development")
    assert len(row) == 6 + len(HORIZONS) + 2 and row[2] == "ask"
    assert not any(c.strip() in ("nan", "+nan") for c in text.replace("|", "\n").split("\n"))  # missing values print as n/a
    assert np.isfinite(float(row[3].rstrip("%")))


def test_a_period_whose_trades_fit_no_micro_still_has_its_row(stream):
    """Entries whose stops are too wide for one micro within the budget: the period keeps a row that says so."""
    pre, cal, cut, start = stream
    wide = pre.copy()
    wide["stop_points"] = 600.0
    text = "\n".join(scoring_sections([("wide", wide, start)], cal, cut))
    micro = text[text.index("### Whole micro contracts"):text.index("### Lifetime (B4)")]
    for per in ("development", "benchmark"):
        assert f"| wide | {per} | 0, n/a |" in micro and "n/a (no trade fits the evaluation budget)" in micro
