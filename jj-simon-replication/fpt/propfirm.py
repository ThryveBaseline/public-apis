"""Prop firm account rules and a vectorised account simulator.

The presets below are PARAMETER TEMPLATES. Firm rules change monthly; every
number carries a `verified` flag and `source` so you can see what was
checked against a primary source (see docs/DOSSIER.md section 9) and what
is a placeholder you must confirm on the firm's site before trusting a
simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

EVAL, FUNDED, FAILED = 0, 1, 2


@dataclass(frozen=True)
class FirmRules:
    firm: str
    plan: str
    account_size: float
    eval_cost: float  # per month if eval_cost_is_monthly else one-time
    eval_cost_is_monthly: bool
    reset_cost: float
    activation_fee: float  # paid when the evaluation is passed
    profit_target: float
    max_drawdown: float
    drawdown_type: str  # "trailing_intraday" | "trailing_eod" | "static"
    drawdown_lock_profit: float | None  # trailing threshold stops rising once it reaches start + this (None = never locks)
    daily_loss_limit: float | None
    daily_loss_fails_account: bool
    consistency_pct: float | None  # best day must be <= this fraction of profit at pass / payout
    min_trading_days: int
    max_contracts: int
    payout_min_days: int  # trading days required before each payout
    payout_min_amount: float
    payout_max: float | None
    payout_split: float
    payout_buffer: float  # balance must stay above start + buffer after withdrawal
    verified: bool = False
    source: str = ""
    notes: str = ""

    def with_(self, **kw) -> "FirmRules":
        return replace(self, **kw)


# ---------------------------------------------------------------------------
# Presets. Values marked verified=False are placeholders from general
# knowledge of 2025-26 futures prop firm plans; confirm before use.
# ---------------------------------------------------------------------------
FIRM_PRESETS: dict[str, FirmRules] = {
    "topstep_50k": FirmRules("Topstep", "50K Trading Combine", 50_000, 49.0, True, 49.0, 149.0, 3_000, 2_000, "trailing_eod", 2_100, None, False, 0.50, 2, 5, 5, 125.0, 5_000, 0.90, 0.0, False, "https://www.topstep.com", "EOD trailing drawdown; 50% consistency and five $200+ winning days gate payouts on the Express Funded Account; split 90% then 100% after first 10k"),
    "topstep_100k": FirmRules("Topstep", "100K Trading Combine", 100_000, 99.0, True, 99.0, 149.0, 6_000, 3_000, "trailing_eod", 3_100, None, False, 0.50, 2, 10, 5, 125.0, 5_000, 0.90, 0.0, False, "https://www.topstep.com", ""),
    "topstep_150k": FirmRules("Topstep", "150K Trading Combine", 150_000, 149.0, True, 149.0, 149.0, 9_000, 4_500, "trailing_eod", 4_600, None, False, 0.50, 2, 15, 5, 125.0, 5_000, 0.90, 0.0, False, "https://www.topstep.com", ""),
    "tradeify_100k_select": FirmRules("Tradeify", "Select 100K", 100_000, 299.0, False, 99.0, 0.0, 6_000, 3_500, "trailing_eod", 3_600, None, False, 0.35, 3, 10, 5, 250.0, None, 0.90, 100.0, False, "https://tradeify.co", "Select plan: EOD drawdown, 35% consistency, payouts every 5 trading days"),
    "e8_100k": FirmRules("E8 Futures", "100K", 100_000, 239.0, False, 99.0, 0.0, 6_000, 3_000, "trailing_intraday", 3_100, None, False, 0.40, 1, 10, 5, 250.0, None, 0.90, 100.0, False, "https://e8markets.com", "placeholder values"),
    "mffu_100k_starter": FirmRules("MyFundedFutures", "Starter 100K", 100_000, 165.0, True, 100.0, 0.0, 6_000, 3_500, "trailing_eod", 3_600, None, False, 0.40, 1, 10, 5, 250.0, None, 0.90, 100.0, False, "https://myfundedfutures.com", "placeholder values"),
    "funded_engineer_100k": FirmRules("Funded Engineer", "100K", 100_000, 199.0, True, 100.0, 0.0, 6_000, 3_500, "trailing_eod", 3_600, None, False, 0.40, 1, 10, 5, 250.0, None, 0.90, 100.0, False, "https://fundedengineer.com", "placeholder values"),
}


class PropAccount:
    """Vectorised simulation of `sims` independent copies of one account.

    Trades are applied with `apply_day(r_matrix, mask)` where r_matrix holds
    per-trade R outcomes (shape sims x max_trades) and mask says which trade
    slots are real. Dollar P&L = R * risk_per_trade.
    """

    def __init__(self, rules: FirmRules, sims: int, risk_per_trade: float, start_phase: int = EVAL, restart_failed: bool = True, eval_risk: float | None = None):
        self.rules = rules
        self.sims = sims
        self.risk = float(risk_per_trade)  # funded-phase risk per trade
        self.eval_risk = float(eval_risk) if eval_risk is not None else float(risk_per_trade)
        self.restart_failed = restart_failed
        self.phase = np.full(sims, start_phase, dtype=np.int8)
        self.balance = np.full(sims, rules.account_size, dtype=float)
        self.peak = self.balance.copy()
        self.threshold = self.balance - rules.max_drawdown
        self.trading_days = np.zeros(sims, dtype=int)
        self.days_since_payout = np.zeros(sims, dtype=int)
        self.best_day = np.zeros(sims)
        self.profit_since_reset = np.zeros(sims)  # for consistency
        self.payouts_total = np.zeros(sims)
        self.costs_total = np.full(sims, rules.eval_cost if start_phase == EVAL else rules.activation_fee, dtype=float)
        self.breaches = np.zeros(sims, dtype=int)
        self.passes = np.zeros(sims, dtype=int)
        self.payout_count = np.zeros(sims, dtype=int)

    # -- helpers ---------------------------------------------------------
    def _lock(self):
        r = self.rules
        if r.drawdown_lock_profit is not None:
            cap = r.account_size + r.drawdown_lock_profit - r.max_drawdown
            self.threshold = np.minimum(self.threshold, cap)

    def _trail(self):
        r = self.rules
        if r.drawdown_type == "static":
            return
        self.peak = np.maximum(self.peak, self.balance)
        self.threshold = np.maximum(self.threshold, self.peak - r.max_drawdown)
        self._lock()

    def _fail(self, mask: np.ndarray):
        if not mask.any():
            return
        self.breaches[mask] += 1
        self.phase[mask] = FAILED

    def _reset_account(self, mask: np.ndarray, phase: int):
        r = self.rules
        self.phase[mask] = phase
        self.balance[mask] = r.account_size
        self.peak[mask] = r.account_size
        self.threshold[mask] = r.account_size - r.max_drawdown
        self.trading_days[mask] = 0
        self.days_since_payout[mask] = 0
        self.best_day[mask] = 0.0
        self.profit_since_reset[mask] = 0.0

    # -- one trading day ------------------------------------------------------
    def apply_day(self, r_matrix: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply a day's trades. Returns the day's realised P&L per sim."""
        rules = self.rules
        alive = (self.phase == EVAL) | (self.phase == FUNDED)
        day_pnl = np.zeros(self.sims)
        stopped = np.zeros(self.sims, dtype=bool)
        traded = np.zeros(self.sims, dtype=bool)
        for k in range(r_matrix.shape[1]):
            m = mask[:, k] & alive & ~stopped
            if not m.any():
                continue
            risk = np.where(self.phase == EVAL, self.eval_risk, self.risk)
            pnl = np.where(m, r_matrix[:, k] * risk, 0.0)
            self.balance += pnl
            day_pnl += pnl
            traded |= m
            if rules.drawdown_type == "trailing_intraday":
                self._trail()
            if rules.drawdown_type in ("trailing_intraday", "static"):
                breach = m & (self.balance <= self.threshold)
            else:  # trailing_eod still fails intraday on the current threshold
                breach = m & (self.balance <= self.threshold)
            if rules.daily_loss_limit is not None:
                dll = m & (day_pnl <= -rules.daily_loss_limit)
                if rules.daily_loss_fails_account:
                    breach |= dll
                else:
                    stopped |= dll
            self._fail(breach)
            alive = alive & ~breach
        # end of day
        self.trading_days += (traded & alive).astype(int)
        self.days_since_payout += (traded & alive).astype(int)
        self.best_day = np.where(alive, np.maximum(self.best_day, day_pnl), self.best_day)
        self.profit_since_reset = np.where(alive, self.profit_since_reset + day_pnl, self.profit_since_reset)
        if rules.drawdown_type == "trailing_eod":
            self._trail()
            self._fail(alive & (self.balance <= self.threshold))
            alive = (self.phase == EVAL) | (self.phase == FUNDED)
        # evaluation pass check
        ev = alive & (self.phase == EVAL)
        profit = self.balance - rules.account_size
        ok = ev & (profit >= rules.profit_target) & (self.trading_days >= rules.min_trading_days)
        if rules.consistency_pct is not None:
            ok &= self.best_day <= rules.consistency_pct * np.maximum(profit, 1e-9)
        if ok.any():
            self.passes[ok] += 1
            self.costs_total[ok] += rules.activation_fee
            self._reset_account(ok, FUNDED)
        return day_pnl

    # -- month boundary ---------------------------------------------------
    def month_end(self) -> np.ndarray:
        """Charge subscriptions, restart failed accounts, request payouts.
        Returns cash received by the trader per sim (payouts, net of split)."""
        rules = self.rules
        cash = np.zeros(self.sims)
        if rules.eval_cost_is_monthly:
            ev = self.phase == EVAL
            self.costs_total[ev] += rules.eval_cost
        failed = self.phase == FAILED
        if self.restart_failed and failed.any():
            self.costs_total[failed] += rules.reset_cost if rules.reset_cost > 0 else rules.eval_cost
            self._reset_account(failed, EVAL)
        funded = self.phase == FUNDED
        profit = self.balance - rules.account_size - rules.payout_buffer
        eligible = funded & (self.days_since_payout >= rules.payout_min_days) & (profit >= rules.payout_min_amount)
        if rules.consistency_pct is not None:
            eligible &= self.best_day <= rules.consistency_pct * np.maximum(self.profit_since_reset, 1e-9)
        amount = np.where(eligible, profit, 0.0)
        if rules.payout_max is not None:
            amount = np.minimum(amount, rules.payout_max)
        self.balance -= amount
        self.peak = np.where(eligible, np.maximum(self.balance, self.threshold + rules.max_drawdown), self.peak)
        paid = amount * rules.payout_split
        self.payouts_total += paid
        self.payout_count += eligible.astype(int)
        self.days_since_payout[eligible] = 0
        self.best_day[eligible] = 0.0
        self.profit_since_reset[eligible] = 0.0
        cash += paid
        return cash
