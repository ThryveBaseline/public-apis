# Forward data log

Dated data-quality decisions for the forward paper test. Each is written before any trade result for the dates it concerns has been computed.

## 2026-10-07: 2026-10-06 rejected as a vendor-quality day

**The evidence.**

- **Databento's condition report.** `metadata.get_dataset_condition` for GLBX.MDP3 was queried at 2026-10-07T17:21:20Z and again at 17:24:28Z.
  - 2026-10-06 read "degraded", last modified 2026-10-06.
  - It was the only date from 2026-09-15 on that was not "available".
  - Every other date's last-modified date was the day after its session. 2026-10-06's was the day itself, and it had not been revised.
- **The MBO file.** `glbx-mdp3-20261006.mbo.dbn.zst`, sha256 `bbe8acbdf6f9ea72c5310254235b2ff5e4bba3df1b49ca7083be069167caca0c`, bought 2026-10-07T16:04Z for $2.303361.
  - It carries Databento's possibly-bad-book flag on every non-snapshot record, from the first record of the day to the last: NQZ6 15,218,093 of 15,220,671 records, and ESZ6 9,307,544 of 9,315,197.
  - Its request parameters are identical to round 1's batch files, which carry the flag on no record.
  - The sidecar's admission rule rejects it.
  - It is kept read-only on the GB10 as a quarantined artifact.
- **No trade result exists for 2026-10-06.** No forward bar for 2026-10-06 has been bought, and the forward runner has not run on any forward data. The rejection rests only on the vendor's condition report and the record flags.

**Chris's decisions.**

1. The rejection is a valid data-quality exclusion. It is not a win, a loss or a missing trade.
2. The runner stays unchanged. The fix belongs in the data layer: `forward_data_spec.md`, "Data condition, before any date is fetched".
3. Forward scoring begins on the first session that satisfies the admission rule: Databento reports the date "available" and revised after its session. 2026-10-06 must not hold the test hostage.
4. Oct 6 MBO is not re-bought unless, after a revision, a specific research need arises for that exact date. The pilot collects the next 10 sessions that pass the gate.

**What the runner allows.** The frozen runner needs bars that continue the sealed file from 2026-10-06 00:00 UTC. The next sessions' indicators also need those bars as history, starting with the previous session's range for 2026-10-07. That leaves two cases:

- **If Databento revises 2026-10-06 to "available":** it passes the same rule as any other day and is scored like any other day. The rule looks only at the vendor's state, never at the day's result.
- **If it is still degraded at the morning check on 2026-10-09:** the test cannot start without a change to the runner. Chris then decides between two things, before any session is scored:
  - wait longer; or
  - a version-1 amendment: a list of excluded dates, 2026-10-06's bars used as unscored history only, and the baseline rerun and re-pinned, because the runner's hash is frozen in it.
