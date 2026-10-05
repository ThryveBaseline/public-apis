# Assumptions made where the public record is silent

Every rule in `fpt/` traces either to a public statement by JJ Simon or to a
third-party codification of his method (fxreplay, TradingView indicators,
backtesters). The items below are places where those sources do not pin a
value down, so the code exposes a parameter and documents the default it
ships with. Each one is a dial you should test against real NQ data.

| # | Parameter | Default | Why this default | Where to change it |
|---|---|---|---|---|
| 1 | Fair value anchor | `open_0930` (open of the 09:30 ET 1-minute bar) | JJ describes "the price of a single candle right before the NASDAQ opens"; fxreplay's codification uses "the 9:30 AM market open price". The 09:30 open and the 09:29 close are the same print to within a tick. `close_0929` and `vwap_0929_0930` are provided for comparison. | `StrategyConfig.anchor` |
| 2 | Continuation window length | 5 minutes (09:30-09:35) | JJ's own $1.6M video: continuation only in the first ~5 minutes, then reversion for the remaining ~85. fxreplay and AndrewFXTD codify "the first 10-15 minutes" and fxreplay's optimisation also skips the first 3 minutes. Test 09:35, 09:40 and 09:45. | `StrategyConfig.continuation_end` |
| 3 | Window end | 11:00 ET | "a 90-minute window" from the open. | `StrategyConfig.window_end` |
| 4 | Afternoon session | off (14:00-15:00 when enabled) | JJ's earlier videos describe a 14:00-15:00 NY session anchored to the 14:00 price; his Sept 2026 videos add 6PM and 8PM sessions that are not codified anywhere public yet. Enable with `pm_session=True`. | `StrategyConfig.pm_session`, `pm_start`, `pm_end` |
| 5 | Premium/discount band | 38 points, not required | The 38-point band is joetroyer's TradingView codification, not a number JJ has published. Off by default; `require_band_touch=True` reproduces the indicator's reversion gate. | `StrategyConfig.band_points`, `require_band_touch` |
| 6 | Displacement size | body >= 1.0 x 1-minute ATR(14) | Sources say a "strong" displacement candle and give only the wick rule (counter-wick < 20% of open-to-extreme). A size filter is needed to avoid tagging 2-point candles; 1 ATR is a conservative reading of "strong". Set to 0 to use the wick rule alone. | `StrategyConfig.min_body_atr` |
| 7 | ATR definition | Wilder RMA, period 14, on 1-minute bars | The tiers (above 20 / 7-20 / below 7) are published; the ATR period is not. 14 is TradingView's default and the most likely number he reads off the chart. | `StrategyConfig.atr_period`, `indicators.atr(method=)` |
| 8 | Swing definition for BOS/MSB | pivot high/low with 3 bars left and right, only used once confirmed | JJ's structure reading is discretionary. Pivot(3,3) is the smallest symmetric pivot that is robust on 1-minute NQ. | `swing_left`, `swing_right` |
| 9 | Structure lookback | 60 bars | A swing from 90 minutes ago is not "recent structure". | `structure_lookback` |
| 10 | Grade A entries | taken | JJ names A+ (break of structure), A (displacement) and B (avoid). Whether he takes grade A alone is not stated explicitly; the aggressive ~10 trades/day cadence suggests yes. `allow_grade_a=False` restricts to A+. | `allow_grade_a` |
| 11 | Entry fill | market at the open of the next bar, plus 0.25 points slippage | He enters on the displacement close; the first fill after a 1-minute close is the next bar's open. | `slippage_points` |
| 12 | Stop fill | stop price minus 0.25 points slippage; if a bar touches both stop and target, the stop is assumed to fill first | Conservative convention. | `strategy.py` exit logic |
| 13 | Commission | $2.50 per contract per side | Typical retail futures all-in rate on NQ; prop firms charge similar. | `commission_per_contract_side` |
| 14 | One position at a time | yes | Not stated; keeps the daily trade count comparable to his "about 10 trades". | not configurable (edit `strategy.py`) |
| 15 | Flat at window end | yes | Whether he holds past 11:00 is not published. Off = hold to stop/target or session close. | `flat_at_window_end` |
| 16 | Max trades per day | 10 | "around 10 trades per day". | `max_trades_per_day` |
| 17 | Daily loss stop | none in the backtester; `fpt.risk.daily_stop_from_stats` computes one | JJ's own stop rule is reported qualitatively; the statistical stop (5th-percentile day) is the mechanism the dossier reconstructs. | `daily_loss_stop_r`, `max_consecutive_losses` |
| 18 | Risk per trade | ~$1,000 via 1/2/3 NQ contracts | Published tiers. On a 50k account use MNQ or `size_mode="risk"` with a smaller `risk_dollars`. | `size_mode`, `risk_dollars` |
| 19 | Prop firm rule presets | templates flagged `verified=False` unless confirmed | Firm rules change monthly. Confirm every number on the firm's site before trusting a simulation. | `fpt/propfirm.py` |
| 20 | Copy trading | every account gets identical signals and R outcomes | This is what a trade copier does; slippage differences across accounts are ignored. | `PortfolioConfig.copy_trading` |
