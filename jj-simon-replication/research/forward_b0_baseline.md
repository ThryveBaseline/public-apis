# Forward paper test v1: the baseline

Sealed bars (sha256 d2e4ebf90949244441d898fd9d34236eb768100ff64c298812604522b6be316b, the manifest's), 66 roll dates excluded (the manifest's). Protocol: docs/research/forward_protocol_v1.md (sha256 4bdd5c737c9c4647240ece64bb159a72c7dcc92de65d27ba80e51ae4f3006aa5). Both candidates rerun through research/engine.py exactly as frozen; development through 2025-10-05, benchmark to 2026-10-05. A session is a trading day: a New York date with a 09:30 bar. R is per contract (one_contract); whole micros at a full stop-out within $1,000 (evaluation) and $500 (funded) beside it. Tail check: rerunning from 120 calendar days before the day after the sealed bars, as the day mode does, reproduces the full run's trades after the first 60 days of that tail for both candidates (165 trades compared). The code that produces the trades, this runner included, is frozen from here (its sha256 and both configurations are in the JSON block below).

The day mode's gap rule applied to the benchmark year's bars: 258 scheduled halts, of which 9 early ends (2025-11-27 12:59 holiday halt, 2025-11-28 13:14 early close, 2025-12-24 13:14 early close, 2026-01-19 12:59 holiday halt, 2026-02-16 12:59 holiday halt, 2026-05-25 12:59 holiday halt, 2026-06-19 12:59 holiday halt, 2026-07-03 12:59 holiday halt, 2026-09-07 12:59 holiday halt); 1 gaps inside a 09:30-16:00 session and 0 across 00:00 UTC (each would stop a daily run): 2026-04-03 09:14:00-04:00 to 2026-04-05 18:00:00-04:00; 1 overnight (reported only).

| candidate | period | trades | sessions | trades per session | R per trade (se, by day) | target | stop | flat 16:00 | long | micros: evaluation / funded |
|---|---|---|---|---|---|---|---|---|---|---|
| B0 | development | 7431 | 3877 | 1.92 | -0.037 (0.013) | 33.1% | 54.8% | 0.0% | 51.2% | 18.7 / 8.9 |
| B0 | benchmark | 1258 | 254 | 4.95 | -0.071 (0.037) | 37.5% | 62.5% | 0.0% | 49.8% | 18.0 / 8.5 |

## Checkpoint thresholds, from development trades (fixed before any forward day is scored)

S3's 20- and 30-setup checks decide; S4's are computed at S4's own 20th and 30th setups and reported beside.

```json
{
 "candidates": {
  "B0": {
   "allow_grade_a": true,
   "allow_grade_a_continuation": null,
   "allow_grade_a_reversion": null,
   "anchor": "open_0930",
   "atr_period": 14,
   "atr_tiers": [
    [
     20.0,
     50.0,
     1
    ],
    [
     7.0,
     25.0,
     2
    ],
    [
     0.0,
     16.5,
     3
    ]
   ],
   "band_points": 38.0,
   "big_open_candle_points": 25.0,
   "big_open_measure": "body",
   "big_open_scope": "continuation",
   "commission_per_contract_side": 2.5,
   "consolidation_atr_mult": 1.5,
   "consolidation_bars": 8,
   "continuation_atr_k": null,
   "continuation_direction": "open_candle",
   "continuation_end": "09:35",
   "continuation_rr": null,
   "continuation_stall_candles": 2,
   "daily_loss_stop_r": null,
   "daily_profit_stop_r": null,
   "displacement_mode": "jj",
   "extra_sessions": [],
   "flat_at_window_end": false,
   "flat_time": null,
   "max_consecutive_losses": 3,
   "max_contracts": 3,
   "max_target_overshoot_pct": 0.2,
   "max_trades_per_day": 100,
   "min_body_atr": 0.5,
   "min_distance_from_fv": 0.0,
   "one_contract": false,
   "pm_continuation_end": "14:05",
   "pm_end": "15:00",
   "pm_session": false,
   "pm_start": "14:00",
   "point_value": 20.0,
   "require_band_touch": false,
   "reversion_end": null,
   "risk_dollars": 500.0,
   "rolling_fair_value": true,
   "rr": 1.5,
   "session_start": "09:30",
   "size_mode": "risk",
   "skip_first_minutes": 0,
   "slippage_points": 0.25,
   "stop_mode": "fixed",
   "stop_points": 25.0,
   "stop_scope": "session",
   "structure_lookback": 60,
   "swing_left": 1,
   "swing_right": 1,
   "target_points": 38.0,
   "wick_pct": 0.2,
   "window_end": "11:00"
  }
 },
 "code": {
  "fpt/data.py": "1d341ec53caf504ddeaa95a0fd655e9f46d0fb0604413f05fef8297be3eb8442",
  "fpt/evaluate.py": "9113ac8da08fac925dad82f6631db929a2f2897a0aaadc0254fdcacafd25794f",
  "fpt/fair_value.py": "a65b9b7692a367cda43df59c2c6bd2b035ea6d496255476b79e14d6635e1cf62",
  "fpt/indicators.py": "d6d1cc10fdd9e1aa285b0afaccfac7629b900bf43529d9b61e265e7f984e3831",
  "fpt/risk.py": "b2a4f0cb371ba438e0fbccfdf08b8d7158b7620138ada0047928cc1c1e345190",
  "fpt/strategy.py": "87b73c20d59456a851026b1b7462385d69bf3841b7800cca698edaba939f59ba",
  "fpt/structure.py": "050188f70bd51d105699fa39dd5b95e325d948681d3400e4230c1a0b5fbb7263",
  "research/anatomy.py": "7abd491dc0ab086c043c49af2e394c62a65d3083745d76d4fa67d0cdd1794318",
  "research/bracket_replay.py": "a12402b92de212619a9d4ebe86181c21610615f1583b5b134a6eac9003e3ebbf",
  "research/candidates.py": "45567aa748819fcc33e6acb2641a0742597c8307f03a9d462eba05545fc8c366",
  "research/engine.py": "4909d5339ecf1b2e4e05a1292af41f2331b90c4064bf3152ea0200ec54ad6a1a",
  "research/forward.py": "642cba5161e3cd01fcad9263425cc7b32dde173d15118236be40d445f2d8f50c",
  "research/forward_b0.py": "a369c755145493484a1b4fc06e4c30ae6e5febc419142dcdb35d8650fd4a1b7e"
 },
 "thresholds": {
  "B0": {
   "count_p01": 5.0,
   "count_p99": 60.0,
   "drawdown_20_p99": 14.319999999999997,
   "drawdown_30_p99": 17.41494999999999,
   "flat_share_p01": 0.0,
   "flat_share_p99": 0.0,
   "long_share_p01": 0.14285714285714285,
   "long_share_p99": 0.8571428571428571,
   "mean_r_20_p025": -0.51529375,
   "mean_r_30_p025": -0.43433333333333324,
   "sessions_window": 10,
   "stop_share_p01": 0.0,
   "stop_share_p99": 0.8333333333333334,
   "target_share_20_p01": 0.0,
   "target_share_30_p01": 0.0,
   "target_share_p01": 0.0,
   "target_share_p99": 0.6019999999999995
  }
 }
}
```
