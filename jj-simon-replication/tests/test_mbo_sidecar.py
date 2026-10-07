import datetime as dt
import json
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest

databento_dbn = pytest.importorskip("databento_dbn")

from research import mbo_sidecar  # noqa: E402
from research.mbo_sidecar import annotate, load_features, read_dbn, reference_cuts  # noqa: E402

NQ, ES = 261401, 10252
F_LAST = 0x80
S = 1_000_000_000


def _ns(day: str, hhmmss: str) -> int:
    return pd.Timestamp(f"{day} {hhmmss}", tz="UTC").value


def _msg(ts, iid, action, side, price, size, oid, last=True):
    return databento_dbn.MBOMsg(publisher_id=1, instrument_id=iid, ts_event=ts, order_id=oid, price=int(round(price * S)), size=size,
                                action=getattr(databento_dbn.Action, action), side=getattr(databento_dbn.Side, side), ts_recv=ts + 1000,
                                ts_in_delta=0, sequence=0, flags=F_LAST if last else 0, channel_id=0)


def write_day(path, day: str, crossed: bool = False):
    """A small New York session (EDT: 09:30 ET = 13:30 UTC). Book at the 09:31 boundary: bids 20000.00 x5 and
    19999.75 x3, offers 20000.25 x2 (4 less a 2-lot fill) and 20000.50 x6. NQ buys 2 at 20000.25 in the 09:30 minute
    and sells 1 at 19999.75 in the 09:31 minute; ES sells 3 in the 09:30 minute."""
    t0 = pd.Timestamp(day, tz="UTC").value
    recs = [_msg(t0, NQ, "CLEAR", "NONE", 0, 0, 0)]
    for oid, (side, px, q) in enumerate([("BID", 20000.00, 5), ("BID", 19999.75, 3), ("ASK", 20000.25, 4), ("ASK", 20000.50, 6)], start=1):
        recs.append(_msg(t0 + oid, NQ, "ADD", side, px, q, oid, last=(oid == 4)))
    recs += [_msg(_ns(day, "13:30:10"), NQ, "TRADE", "BID", 20000.25, 2, 0, last=False),
             _msg(_ns(day, "13:30:10") + 1, NQ, "FILL", "ASK", 20000.25, 2, 3, last=False),
             _msg(_ns(day, "13:30:10") + 2, NQ, "CANCEL", "ASK", 20000.25, 2, 3),
             _msg(_ns(day, "13:30:20"), ES, "TRADE", "ASK", 6000.00, 3, 0),
             _msg(_ns(day, "13:31:05"), NQ, "ADD", "BID", 20000.00, 2, 5),
             _msg(_ns(day, "13:31:30"), NQ, "TRADE", "ASK", 19999.75, 1, 0)]
    if crossed:
        recs.append(_msg(_ns(day, "13:40:00"), NQ, "ADD", "BID", 20001.00, 1, 9))
    maps = [NS(raw_symbol="NQZ6", intervals=[NS(start_date=pd.Timestamp(day).date(), end_date=pd.Timestamp(day).date() + dt.timedelta(days=1), symbol=str(NQ))]),
            NS(raw_symbol="ESZ6", intervals=[NS(start_date=pd.Timestamp(day).date(), end_date=pd.Timestamp(day).date() + dt.timedelta(days=1), symbol=str(ES))])]
    md = databento_dbn.Metadata(dataset="GLBX.MDP3", start=t0, end=t0 + 21 * 3600 * S, stype_in=databento_dbn.SType.RAW_SYMBOL,
                                stype_out=databento_dbn.SType.INSTRUMENT_ID, schema=databento_dbn.Schema.MBO, symbols=["ESZ6", "NQZ6"], partial=[],
                                not_found=[], mappings=maps)
    path.write_bytes(md.encode() + b"".join(bytes(r) for r in recs))
    return recs


def write_bars(path, days):
    rows = []
    for day in days:
        rows += [(f"{day}T13:30:00Z", 20000.25, 20000.25, 20000.25, 20000.25, 2, NQ), (f"{day}T13:31:00Z", 19999.75, 19999.75, 19999.75, 19999.75, 1, NQ)]
    pd.DataFrame(rows, columns=["ts_event", "open", "high", "low", "close", "volume", "symbol"]).to_csv(path, index=False)


def test_the_parse_matches_the_official_decoder(tmp_path):
    recs = write_day(tmp_path / "d.dbn", "2026-10-06")
    info, rec = read_dbn(str(tmp_path / "d.dbn"))
    assert info["ids"] == {"NQZ6": NQ, "ESZ6": ES} and len(rec) == len(recs)
    dec = databento_dbn.DBNDecoder()
    dec.write((tmp_path / "d.dbn").read_bytes())
    official = dec.decode()[1:]
    assert [r.order_id for r in official] == rec["order_id"].tolist() and [r.price for r in official] == rec["price"].tolist()
    assert [str(r.action.value) for r in official] == [a.decode() for a in rec["action"]] and [r.ts_recv for r in official] == rec["ts_recv"].tolist()
    zst = pytest.importorskip("zstandard")
    (tmp_path / "d.dbn.zst").write_bytes(zst.ZstdCompressor().compress((tmp_path / "d.dbn").read_bytes()))
    assert (read_dbn(str(tmp_path / "d.dbn.zst"))[1] == rec).all()
    (tmp_path / "bad.dbn").write_bytes((tmp_path / "d.dbn").read_bytes()[:-3])
    with pytest.raises(SystemExit, match="whole MBO records"):
        read_dbn(str(tmp_path / "bad.dbn"))


def _day(tmp_path, monkeypatch, day, crossed=False):
    write_day(tmp_path / f"{day}.dbn", day, crossed)
    monkeypatch.setattr("sys.argv", ["mbo_sidecar.py", "day", "--mbo", str(tmp_path / f"{day}.dbn"), "--bars", str(tmp_path / "bars.csv"),
                                     "--out", str(tmp_path / "feat")])
    assert mbo_sidecar.main() == 0
    return json.loads((tmp_path / "feat" / f"{day}.check.json").read_text())


def test_features_and_annotations(tmp_path, monkeypatch):
    write_bars(tmp_path / "bars.csv", ["2026-10-02", "2026-10-06", "2026-10-07"])
    ref = _day(tmp_path, monkeypatch, "2026-10-02")  # before the forward test: a reference session
    fwd = _day(tmp_path, monkeypatch, "2026-10-06")
    assert ref["admitted"] and fwd["admitted"] and fwd["bar_match"] == {"minutes": 2, "matched": 2, "share": 1.0}
    assert fwd["crossed_or_locked_boundaries"] == 0 and fwd["unknown_order_events"] == 0
    bad = _day(tmp_path, monkeypatch, "2026-10-07", crossed=True)
    assert not bad["admitted"] and bad["crossed_or_locked_boundaries"] > 0
    feats, checks = load_features(str(tmp_path / "feat"))
    assert sorted(feats) == ["2026-10-02", "2026-10-06"] and len(checks) == 3
    f = feats["2026-10-06"]
    b931 = f.loc[pd.Timestamp("2026-10-06 13:31", tz="UTC")]
    assert (b931["bid"], b931["ask"], b931["bid_depth"], b931["ask_depth"]) == (20000.0, 20000.25, 8.0, 8.0)
    assert b931["nq_flow"] == 1.0 and b931["es_flow"] == -1.0 and b931["next_lo"] == 19999.75 and b931["spread_ticks"] == 1.0
    b930 = f.loc[pd.Timestamp("2026-10-06 13:30", tz="UTC")]
    assert (b930["ask"], b930["ask_depth"]) == (20000.25, 10.0) and np.isnan(b930["nq_flow"])
    cuts = reference_cuts({"2026-10-02": feats["2026-10-02"]})
    # ES flow is -1 at one boundary: of {-1, +1} the 20th percentile is -0.6; NQ flow is +1 then -1: of {+1, -1, -1, +1} it is -1
    assert cuts["es_flow"] == pytest.approx(-0.6) and cuts["nq_flow"] == pytest.approx(-1.0)
    trades = pd.DataFrame([{"candidate": "S3", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "long", "entry": 20000.50,
                            "stop": 19990.50, "r": -1.0, "exit_reason": "stop"},
                           {"candidate": "S4", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "short", "entry": 19999.75,
                            "stop": 20009.75, "r": 2.0, "exit_reason": "target"},
                           {"candidate": "S3", "date": "2026-10-07", "entry_time": "2026-10-07 09:31:00-04:00", "direction": "long", "entry": 1.0,
                            "stop": 0.0, "r": 0.0, "exit_reason": "flat"}])
    ann = annotate(trades, feats, cuts)
    assert len(ann) == 2  # the day that failed its check is not annotated
    lng, sht = ann.iloc[0], ann.iloc[1]
    # long: the far touch 20000.25 is a tick better than the engine's 20000.50; the bid 20000.00 traded through: two ticks better
    assert lng["e1_ticks"] == 1.0 and lng["e2_filled"] and lng["e2_ticks"] == 2.0
    assert lng["signed_nq_flow"] == 1.0 and not lng["flag_nq_flow"] and lng["flag_es_flow"] and not lng["skip_flag"]
    # short: the far touch 20000.00 is a tick better than 19999.75; the offer 20000.25 never traded through in the minute, so it
    # sells at the bid a minute later (20000.00 with the 13:31:05 order)
    assert sht["e1_ticks"] == 1.0 and not sht["e2_filled"] and sht["e2_ticks"] == 1.0
    assert sht["signed_nq_flow"] == -1.0 and not sht["flag_nq_flow"] and sht["signed_imbalance"] == 0.0  # flagged only strictly below the cut


def test_the_report(tmp_path, monkeypatch):
    write_bars(tmp_path / "bars.csv", ["2026-10-02", "2026-10-06"])
    _day(tmp_path, monkeypatch, "2026-10-02")
    _day(tmp_path, monkeypatch, "2026-10-06")
    state = {"trades": [{"candidate": "S3", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "long", "entry": 20000.50,
                         "stop": 19990.50, "r": -1.0, "exit_reason": "stop"}]}
    (tmp_path / "state.json").write_text(json.dumps(state))
    monkeypatch.setattr("sys.argv", ["mbo_sidecar.py", "report", "--features", str(tmp_path / "feat"), "--state", str(tmp_path / "state.json"),
                                     "--out", str(tmp_path / "rep.md")])
    assert mbo_sidecar.main() == 0
    rep = (tmp_path / "rep.md").read_text()
    assert "| forward | S3 | 1 | +1.00 | +2.00 | 100% | 0 |" in rep and "| 2026-10-06 | True | 2/2 | 0 | 0 |" in rep
    assert len(pd.read_csv(tmp_path / "rep.csv")) == 1
