# Data

The strategy needs 1-minute NQ (E-mini Nasdaq-100) bars in New York time.
Nothing here is bundled: `synthetic_demo.csv` is generated noise for
exercising the code, not market data.

Sources that export 1-minute continuous NQ history:

| Source | Notes |
|---|---|
| Databento (GLBX.MDP3, `NQ.c.0` or `NQ.v.0`, schema `ohlcv-1m`) | timestamps in UTC: load with `--source-tz UTC` |
| FirstRate Data, Kibot, PortaraCQG | bulk CSV, usually US/Eastern |
| Tradovate / NinjaTrader / TopstepX export | chart timezone; check the first row is 09:30 ET |
| TradingView "Export chart data" | limited history per export, chart timezone |

Expected columns (any order, any capitalisation): a timestamp column
(`timestamp`, `datetime`, `time`, `date`, or `date` + `time`), `open`,
`high`, `low`, `close`, optional `volume`. Include the full session if you
can (overnight bars are harmless and give the 09:29 pre-open candle for
`anchor="close_0929"`).
