# run1 data-preparation provenance

Written 2026-10-06T22:15:26Z on GB10 (gx10-e9c7). This file sits NEXT TO `sealed/run1`; nothing inside
`sealed/run1` was touched after its SEALED marker was written.

Why a preparation step exists at all: the frozen evaluator derives contract-roll days from
changes in the CSV's `symbol` column. Databento's `map_symbols=True` on a *continuous* symbol
writes the **requested** symbol (`NQ.n.0`) into every row, so the transcoded file carries one
distinct symbol value and the evaluator would have found zero roll days and excluded nothing.
`fpt/` could not change before the sealed run, so the documented step below writes each row's
`instrument_id` into the `symbol` field. Nothing else was altered; the proof is mechanical, in
section 4. The substitution was decided and written down before the sealed run, not after
seeing any outcome.

## 1. Raw DBN as delivered by Databento (preserved, mode 0400)

| file | bytes | sha256 |
|---|---|---|
| `/home/buddy2/databento-nq-raw/nq_1min.ohlcv-1m.dbn.zst` | 92,092,728 | `d1e3585f3d7e68fb75d60f949c680247240a054880c0489c36da85710aa66753` |
| `/home/buddy2/databento-nq-raw/nq_1d_rolls.ohlcv-1d.dbn.zst` | 189,832 | `27f3597e62a5d204e6e9ced7dbf4783eb27d664de50854011c209a3489ae8c48` |

Byte-identical copies remain on the Surface at `C:\Users\Chris\databento-nq\`.

Purchase parameters: dataset `GLBX.MDP3`, symbols `["NQ.n.0"]`, `stype_in=continuous`,
schemas `ohlcv-1m` and `ohlcv-1d`, `start=2010-06-06`, `end=2026-10-06` (end exclusive, so
coverage runs to 2026-10-05T23:59Z), `encoding=dbn`, `compression=zstd`. Billable 308,509,488 B
and 283,752 B; quoted cost $20.112530 and $0.050210.

## 2. Transcoded CSV (official tooling; these originals are untouched)

Kept at `/home/buddy2/jj-simon-sources/repo/jj-simon-replication/data/`.

| file | bytes | data rows | sha256 |
|---|---|---|---|
| `nq_1min_databento.csv` | 628,263,175 | 5,509,098 | `7f39447961bfb2e7c193974e0266c11e1e8d0e4f60cefc038c0f0bb9dc31f441` |
| `nq_1d_databento_rolls.csv` | 593,813 | 5,067 | `4ac568a616cab8005d45efd6c3de26b292afd979b3629858df8ace345304a31a` |

Produced with `databento-dbn` 0.71.0 (Apache-2.0, hash-pinned wheel
`f2d9cbcca7cd1db47768c8c1d9c1dfce998ab3f53b07b0e8643411032d913d62`), raw file piped through
`zstd -dc`. Exact invocation:

```python
import sys
import databento_dbn as d
out_path = sys.argv[1]
with open(out_path, 'wb') as out:
    tr = d.Transcoder(out, d.Encoding.CSV, d.Compression.NONE,
                      pretty_px=True, pretty_ts=True, map_symbols=True)
    src = sys.stdin.buffer
    while True:
        chunk = src.read(1 << 20)
        if not chunk:
            break
        tr.write(chunk)
    tr.flush()
```

Header produced: `ts_event,rtype,publisher_id,instrument_id,open,high,low,close,volume,symbol`

## 3. Prepared evaluator input

Written to `/home/buddy2/public-apis/jj-simon-replication/data/`, gitignored by `jj-simon-replication/.gitignore:4: data/*.csv`.

| file | bytes | data rows | sha256 |
|---|---|---|---|
| `nq_1min_databento.csv` | 622,801,595 | 5,509,098 | `d2e4ebf90949244441d898fd9d34236eb768100ff64c298812604522b6be316b` |
| `nq_1d_databento_rolls.csv` | 588,754 | 5,067 | `b7fd2ae4c38614c518ab8394fc14c5c90ed25482e0ca0d5575f4864b7ac30567` |

Exact preparation script, verbatim:

```python
import sys
src, dst = sys.argv[1], sys.argv[2]
# byte-faithful: split on commas, put field[3] (instrument_id) into the last field (symbol).
# No field in this file contains a comma or a quote, so split/join is lossless.
n = 0
with open(src, 'rb') as fi, open(dst, 'wb') as fo:
    header = fi.readline()
    cols = header.rstrip(b'\r\n').split(b',')
    assert cols[3] == b'instrument_id' and cols[-1] == b'symbol', cols
    fo.write(header)
    for line in fi:
        nl = b''
        while line[-1:] in (b'\n', b'\r'):
            nl = line[-1:] + nl
            line = line[:-1]
        f = line.split(b',')
        f[-1] = f[3]
        fo.write(b','.join(f) + nl)
        n += 1
print("data rows written:", n)
```

The header line is copied unchanged, so the column name `symbol` is retained while its value
becomes the instrument_id as text. No reordering, no dedup, no rounding, no row added or
removed.

## 4. Mechanical proof that only the symbol field changed

sha256 over the first nine columns only (`cut -d, -f1-9 <file> | sha256sum` equivalent):

| file | cols 1-9, transcoded | cols 1-9, prepared | identical | rows equal |
|---|---|---|---|---|
| `nq_1min_databento.csv` | `35353809a24f2ddc653b6af2d0620c5e825f726a80046b448aa5b8958ce47311` | `35353809a24f2ddc653b6af2d0620c5e825f726a80046b448aa5b8958ce47311` | yes | yes |
| `nq_1d_databento_rolls.csv` | `9bf0be5a7b9dee646421c62519e6b7508c3a62055e26e26b5bbb4eb3d8aa9d27` | `9bf0be5a7b9dee646421c62519e6b7508c3a62055e26e26b5bbb4eb3d8aa9d27` | yes | yes |

In the prepared files, column 10 equals column 4 on every data row, checked row by row with
zero mismatches; they hold 67 distinct symbol values against 1 in the transcoded files.

## 5. Frozen-loader check, output exactly as printed

```
bars: 5509098
roll_days: 66
  2010-06-17
  2010-09-15
  2010-12-16
  2011-03-17
  2011-06-15
  2011-09-15
  2011-12-14
  2012-03-13
  2012-06-13
  2012-09-18
  2012-12-19
  2013-03-12
  2013-06-18
  2013-09-15
  2013-12-17
  2014-03-19
  2014-06-17
  2014-09-16
  2014-12-16
  2015-03-17
  2015-06-16
  2015-09-20
  2015-12-15
  2016-03-15
  2016-06-14
  2016-09-13
  2016-12-14
  2017-03-14
  2017-06-13
  2017-09-12
  2017-12-13
  2018-03-14
  2018-06-12
  2018-09-19
  2018-12-19
  2019-03-13
  2019-06-18
  2019-09-18
  2019-12-17
  2020-03-18
  2020-06-16
  2020-09-15
  2020-12-16
  2021-03-16
  2021-06-16
  2021-09-14
  2021-12-15
  2022-03-16
  2022-06-15
  2022-09-14
  2022-12-14
  2023-03-15
  2023-06-14
  2023-09-13
  2023-12-12
  2024-03-13
  2024-06-18
  2024-09-18
  2024-12-18
  2025-03-19
  2025-06-17
  2025-09-17
  2025-12-17
  2026-03-18
  2026-06-16
  2026-09-16
```

These are New York trading dates. A roll stamped 00:00 UTC falls on the previous New York date,
so the UTC instrument_id changes of 2026-03-19 / 2026-06-17 / 2026-09-17 appear above as
2026-03-18 / 2026-06-16 / 2026-09-16. Printed unadjusted.

## 6. Environment and code state

- test suite: `65 passed in 5.37s`
- interpreter: Python 3.12.3 / numpy 2.5.3 / pandas 3.0.6 / tabulate 0.10.0
- venv `/home/buddy2/jj-venv`. `tabulate>=0.9` is a declared dependency in both
  `requirements.txt` and `pyproject.toml` and is used by `fpt/backtest.py:166` via
  `to_markdown`; the environment spec handed to me omitted it, one test failed on the missing
  import, and it was installed before the suite passed and before the sealed run. No frozen
  code was modified.
- repository `ThryveBaseline/public-apis`, branch `claude/replicate-researcher-work-lhd1rm`
- commit the sealed run executed on: `bd2be643d8dc5f1fb4cb221023a640620c4b1772`
- `git diff --stat f585bfb HEAD -- jj-simon-replication/fpt jj-simon-replication/pine`: empty (no output)
- `git status --porcelain` at seal time: 

```
?? jj-simon-replication/sealed/
```
- `manifest.json` records `working_tree_dirty: false`

## 7. What this file does not claim

It records the provenance of the input, not the quality of the result, and it does not
interpret `sealed/run1`.
