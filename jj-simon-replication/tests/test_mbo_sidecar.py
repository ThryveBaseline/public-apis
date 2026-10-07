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
F_LAST, F_SNAPSHOT, F_MAYBE_BAD_BOOK = 0x80, 0x20, 0x04
S = 1_000_000_000


def _ns(day: str, hhmmss: str) -> int:
    return pd.Timestamp(f"{day} {hhmmss}", tz="UTC").value


def _msg(ts, iid, action, side, price, size, oid, last=True, extra=0):
    return databento_dbn.MBOMsg(publisher_id=1, instrument_id=iid, ts_event=ts, order_id=oid, price=int(round(price * S)), size=size,
                                action=getattr(databento_dbn.Action, action), side=getattr(databento_dbn.Side, side), ts_recv=ts + 1000,
                                ts_in_delta=0, sequence=0, flags=(F_LAST if last else 0) | extra, channel_id=0)


def write_day(path, day: str, crossed: bool = False, damage: str | None = None):
    """A small New York session (EDT: 09:30 ET = 13:30 UTC). Book at the 09:31 boundary: bids 20000.00 x5 and
    19999.75 x3, offers 20000.25 x2 (4 less a 2-lot fill) and 20000.50 x6. NQ buys 2 at 20000.25 in the 09:30 minute
    and sells 1 at 19999.75 in the 09:31 minute; ES sells 3 in the 09:30 minute."""
    t0 = pd.Timestamp(day, tz="UTC").value
    recs = [] if damage == "no clear" else [_msg(t0, NQ, "CLEAR", "NONE", 0, 0, 0)]
    for oid, (side, px, q) in enumerate([("BID", 20000.00, 5), ("BID", 19999.75, 3), ("ASK", 20000.25, 4), ("ASK", 20000.50, 6)], start=1):
        recs.append(_msg(t0 + oid, NQ, "ADD", side, px, q, oid, last=(oid == 4), extra=0 if damage == "no snapshot" else F_SNAPSHOT))
    recs += [_msg(_ns(day, "13:30:10"), NQ, "TRADE", "BID", 20000.25, 2, 0, last=False),
             _msg(_ns(day, "13:30:10") + 1, NQ, "FILL", "ASK", 20000.25, 2, 3, last=False),
             _msg(_ns(day, "13:30:10") + 2, NQ, "CANCEL", "ASK", 20000.25, 2, 3),
             _msg(_ns(day, "13:30:20"), ES, "TRADE", "ASK", 6000.00, 3, 0),
             _msg(_ns(day, "13:31:05"), NQ, "ADD", "BID", 20000.00, 2, 5),
             _msg(_ns(day, "13:31:30"), NQ, "TRADE", "ASK", 19999.75, 1, 0)]
    if crossed:
        recs.append(_msg(_ns(day, "13:40:00"), NQ, "ADD", "BID", 20001.00, 1, 9))
    if damage == "unknown cancel":
        recs.append(_msg(_ns(day, "13:45:00"), NQ, "CANCEL", "BID", 19000.00, 1, 777))
    if damage == "bad book":
        recs.append(_msg(_ns(day, "13:45:00"), NQ, "ADD", "BID", 19000.00, 1, 778, extra=F_MAYBE_BAD_BOOK))
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


def _day(tmp_path, monkeypatch, day, crossed=False, damage=None):
    write_day(tmp_path / f"{day}.dbn", day, crossed, damage)
    monkeypatch.setattr("sys.argv", ["mbo_sidecar.py", "day", "--mbo", str(tmp_path / f"{day}.dbn"), "--bars", str(tmp_path / "bars.csv"),
                                     "--out", str(tmp_path / "feat")])
    assert mbo_sidecar.main() == 0
    return json.loads((tmp_path / "feat" / f"{day}.check.json").read_text())


def test_features_and_annotations(tmp_path, monkeypatch):
    write_bars(tmp_path / "bars.csv", ["2026-10-02", "2026-10-06", "2026-10-07"])
    ref = _day(tmp_path, monkeypatch, "2026-10-02")  # before the forward test: a reference session
    fwd = _day(tmp_path, monkeypatch, "2026-10-06")
    assert ref["admitted"] and fwd["admitted"] and fwd["bar_match"]["ts_event"] == {"minutes": 2, "matched": 2, "share": 1.0}
    assert fwd["crossed_or_locked_boundaries"] == 0 and fwd["unknown_cancels"] == 0 and fwd["starts_with_clear"] and fwd["snapshot_records"] == 4
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
    # the bar file holds 09:30 and 09:31 only, so a trade entered at 09:31 is flat at that bar's close (19999.75), a tick through
    trades = pd.DataFrame([{"candidate": "S3", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "long", "entry": 20000.50,
                            "stop": 19990.50, "target": 20020.50, "r": -0.125, "exit_reason": "flat"},
                           {"candidate": "S4", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "short", "entry": 19999.75,
                            "stop": 20009.75, "target": 19979.75, "r": -0.05, "exit_reason": "flat"},
                           {"candidate": "S4", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "short", "entry": 19999.75,
                            "stop": 20009.75, "target": 19979.75, "r": 0.5, "exit_reason": "target"},
                           {"candidate": "S3", "date": "2026-10-07", "entry_time": "2026-10-07 09:31:00-04:00", "direction": "long", "entry": 1.0,
                            "stop": 0.0, "target": 2.0, "r": 0.0, "exit_reason": "flat"}])
    bars = mbo_sidecar.load_minute_bars(str(tmp_path / "bars.csv"), source_tz="UTC")
    ann, aside = annotate(trades, feats, cuts, bars)
    assert len(ann) == 2 and sorted(x[2] for x in aside) == ["no admitted book for the day", "replay mismatch"]
    lng, sht = ann.iloc[0], ann.iloc[1]
    # long: the far touch 20000.25 is a tick better than the engine's 20000.50 (R -0.125 to -0.100); the bid 20000.00 traded through
    # within the minute: two ticks better (R -0.075)
    assert lng["e1_ticks"] == 1.0 and lng["e2_filled"] and lng["e2_ticks"] == 2.0
    assert lng["r_e1"] == pytest.approx(-0.1) and lng["dr_e1"] == pytest.approx(0.025) and lng["r_e2"] == pytest.approx(-0.075) and lng["dr_e2"] == pytest.approx(0.05)
    assert lng["signed_nq_flow"] == 1.0 and not lng["flag_nq_flow"] and lng["flag_es_flow"] and not lng["skip_flag"]
    # short: the far touch 20000.00 is a tick better than 19999.75; the offer 20000.25 never traded through, and there is no later bar
    # before 16:00 in this file, so the passive order never trades (R 0)
    assert sht["e1_ticks"] == 1.0 and sht["r_e1"] == pytest.approx(-0.025) and not sht["e2_filled"] and sht["r_e2"] == 0.0 and sht["dr_e2"] == pytest.approx(0.05)
    assert sht["signed_nq_flow"] == -1.0 and not sht["flag_nq_flow"] and sht["signed_imbalance"] == 0.0  # flagged only strictly below the cut
    with pytest.raises(SystemExit, match="unknown trade direction"):
        annotate(trades.assign(direction="1.0"), feats, cuts, bars)


def test_the_book_must_be_whole(tmp_path, monkeypatch):
    write_bars(tmp_path / "bars.csv", ["2026-10-06"])
    for damage in ("no clear", "no snapshot", "unknown cancel", "bad book"):
        c = _day(tmp_path, monkeypatch, "2026-10-06", damage=damage)
        assert not c["admitted"], damage
    write_day(tmp_path / "x.dbn", "2026-10-06")
    info, rec = read_dbn(str(tmp_path / "x.dbn"))
    rec = rec.copy()
    rec["ts_recv"][5], rec["ts_recv"][6] = rec["ts_recv"][6], rec["ts_recv"][5]
    with pytest.raises(SystemExit, match="receive-time order"):
        mbo_sidecar.day_features(rec, info["ids"], pd.Timestamp("2026-10-06"))


def test_the_report(tmp_path, monkeypatch):
    write_bars(tmp_path / "bars.csv", ["2026-10-02", "2026-10-06"])
    _day(tmp_path, monkeypatch, "2026-10-06")
    state = {"trades": [{"candidate": "S3", "date": "2026-10-06", "entry_time": "2026-10-06 09:31:00-04:00", "direction": "long", "entry": 20000.50,
                         "stop": 19990.50, "target": 20020.50, "r": -0.125, "exit_reason": "flat"}]}
    (tmp_path / "state.json").write_text(json.dumps(state))
    args = ["mbo_sidecar.py", "report", "--features", str(tmp_path / "feat"), "--state", str(tmp_path / "state.json"), "--bars", str(tmp_path / "bars.csv"),
            "--reference-bars", str(tmp_path / "bars.csv"), "--out", str(tmp_path / "rep.md")]
    monkeypatch.setattr("sys.argv", args)
    with pytest.raises(SystemExit, match="no admitted reference session"):
        mbo_sidecar.main()
    _day(tmp_path, monkeypatch, "2026-10-02")
    monkeypatch.setattr("sys.argv", args)
    assert mbo_sidecar.main() == 0
    rep = (tmp_path / "rep.md").read_text()
    assert "| forward | S3 | 1 | +1.00 | +2.00 | 100% | +0.025 | +0.050 | 1 of 1 | +0.025 (1) |" in rep and "| 2026-10-06 | True | 2/2 / 2/2 | True + 4 | 0 / 0 | 0 | 0 |" in rep
    assert len(pd.read_csv(tmp_path / "rep.csv")) == 1
