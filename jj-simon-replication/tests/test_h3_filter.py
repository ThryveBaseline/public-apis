import os

import numpy as np
import pandas as pd
import pytest

from research.h3_filter import STREAMS, h3_frames


def test_h3_frames_filter_continuation_only():
    idx = range(6)
    frame = pd.DataFrame({"setup": ["continuation"] * 4 + ["reversion"] * 2, "r": np.arange(6.0)}, index=idx)
    pre = {name: frame for _, name in STREAMS}
    h3 = pd.Series([1.0, 0.0, np.nan, 1.0, np.nan, np.nan], index=idx)
    got = dict(h3_frames(pre, h3))
    assert list(got["S1 where H3 is defined"].index) == [0, 1, 3, 4, 5]  # the undefined continuation entry 2 is out
    assert list(got["S1 on H3's favoured side"].index) == [0, 3, 4, 5]  # reversion entries kept in both
    assert len(got) == 2 * len(STREAMS)


def test_cli_runs_and_pins_its_registration_and_cut(sealed_4y, tmp_path, monkeypatch):
    from research import h3_filter
    reg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "research", "preregistration_conditional_edge.md")
    args = [*sealed_4y["b3"], "--registration", reg, "--out", str(tmp_path / "h3.md")]
    monkeypatch.setattr("sys.argv", ["h3_filter.py", *args])
    with pytest.raises(SystemExit, match="H3 is registered at --oos-start 2025-10-06"):
        h3_filter.main()
    monkeypatch.setattr("sys.argv", ["h3_filter.py", *args, "--allow-other-cut"])
    assert h3_filter.main() == 0
    text = (tmp_path / "h3.md").read_text()
    assert "NOT THE REGISTERED RUN" in text and "| S4 on H3's favoured side | development |" in text and "| S1 where H3 is defined | benchmark |" in text
    fake = tmp_path / "reg.md"
    fake.write_text("edited")
    monkeypatch.setattr("sys.argv", ["h3_filter.py", *[str(fake) if x == reg else x for x in args], "--allow-other-cut"])
    with pytest.raises(SystemExit, match="is not the pinned one"):
        h3_filter.main()
