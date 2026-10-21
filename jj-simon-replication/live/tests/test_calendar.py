import json
import pytest

from live.feed import calendar_for_day, check_calendar_receipt
from live.models import Blocked


def test_calendar_uses_only_snapshot_before_exchange_day(tmp_path):
    raw = [{"date":"2026-10-22T08:30:00-04:00","country":"USD","impact":"High","title":"CPI"}]
    before = tmp_path / "ff_thisweek_20261021T190000Z.json"
    before.write_text(json.dumps(raw))
    (tmp_path / "ff_thisweek_20261022T120000Z.json").write_text(json.dumps([{**raw[0],"title":"Future revision"}]))
    events, receipt = calendar_for_day(tmp_path, "2026-10-22")
    assert events == [(510,"High","CPI")]
    assert receipt["file"] == before.name
    check_calendar_receipt(tmp_path, receipt)
    before.write_text("[]")
    with pytest.raises(Blocked, match="REVISION"):
        check_calendar_receipt(tmp_path, receipt)


def test_missing_calendar_is_not_no_news(tmp_path):
    with pytest.raises(Blocked, match="CALENDAR"):
        calendar_for_day(tmp_path, "2026-10-22")
