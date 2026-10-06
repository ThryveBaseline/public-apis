"""Prop firm account rules and a vectorised account simulator.

The presets below are PARAMETER TEMPLATES. Firm rules change monthly; every
number carries a `verified` flag and `source` so you can see what was
checked against a primary source (see docs/DOSSIER.md section 9) and what
is a placeholder you must confirm on the firm's site before trusting a
simulation.

Coverage: presets exist for 8 of the 17 firms JJ names (Topstep, E8,
MyFundedFutures, Tradeify, Lucid, Alpha Futures, Apex, FundedNext). No preset
or research row yet for Bulwark Prime ($55,000 of his payouts), TickTick
Trader, FFF, Bulenox, Futures Elite, Take Profit Trader, Funding Futures, BGF,
Phidias, FXIFY or TopOneFutures. "Funded Engineer" (~$180,000 in his July 2026
video) went bankrupt in 2024, so that name is a mishearing of one of these.

Approximation: "trailing_intraday" trails the balance after each closed trade,
not the unrealised intraday equity high, so it is slightly more lenient than a
real intraday-trailing limit.
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
    drawdown_lock_profit: float | None  # profit (balance - start) at which the trailing threshold stops rising; it then locks at start + this - max_drawdown (Topstep: the start balance). None = never locks
    daily_loss_limit: float | None
    daily_loss_fails_account: bool
    consistency_pct: float | None  # evaluation rule: best day must be <= this fraction of profit at the pass check (None = no eval rule)
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
    funded_consistency_pct: float | None = None  # funded rule: best day since the last payout must be <= this fraction of profit since then (None = no funded rule)

    def with_(self, **kw) -> "FirmRules":
        return replace(self, **kw)


# ---------------------------------------------------------------------------
# Presets. Values marked verified=False are placeholders from general
# knowledge of 2025-26 futures prop firm plans; confirm before use.
# ---------------------------------------------------------------------------
FIRM_PRESETS: dict[str, FirmRules] = {
    # Values researched 2026-10-05 (docs/research/prop-firm-rules.md). verified=True means the number comes from the
    # firm's own help center; otherwise a third-party review site. Rules change monthly: re-check before buying.
    "topstep_50k": FirmRules("Topstep", "50K Trading Combine -> Express Funded", 50_000, 49.0, True, 49.0, 149.0, 3_000, 2_000, "trailing_eod", 2_000, 1_000, False, 0.55, 1, 5, 5, 125.0, 2_000, 0.90, 0.0, True, "https://help.topstep.com/en/articles/8284197-trading-combine-parameters", "EOD-trailing loss limit locks at the starting balance; daily loss limit is a soft lockout; Combine consistency best day <= 55% of target; XFA payout after 5 winning days of $150+ (or 3 days with best day <= 40%); caps per request $2,000-$3,000; 90/10; max 5 XFAs, 20 purchases/month; copy trading across own accounts allowed"),
    "topstep_100k": FirmRules("Topstep", "100K Trading Combine -> Express Funded", 100_000, 99.0, True, 99.0, 149.0, 6_000, 3_000, "trailing_eod", 3_000, 2_000, False, 0.55, 1, 10, 5, 125.0, 3_000, 0.90, 0.0, True, "https://help.topstep.com/en/articles/8284215-express-funded-account-parameters", "caps per request $3,000-$4,000"),
    "topstep_150k": FirmRules("Topstep", "150K Trading Combine -> Express Funded", 150_000, 199.0, True, 199.0, 149.0, 9_000, 4_500, "trailing_eod", 4_500, 3_000, False, 0.55, 1, 15, 5, 125.0, 5_000, 0.90, 0.0, True, "https://help.topstep.com/en/articles/8284215-express-funded-account-parameters", "caps per request $5,000-$6,000"),
    "e8_100k_signature": FirmRules("E8 Futures", "Signature 100K", 100_000, 260.0, False, 260.0, 0.0, 6_000, 3_000, "trailing_eod", 3_000, None, False, None, 1, 8, 5, 0.0, 4_500, 0.80, 3_000.0, False, "https://help.e8markets.com/en/articles/13106558-all-product-overviews-e8-one-vs-e8-zero-vs-e8-pro-vs-e8-signature", "price official; 3% EOD-dynamic drawdown, no daily loss limit, funded 35% best-day rule, first payout after 14 days then every 5 profitable days, caps 2.5/2.5/4.5/5.5% of account size for payouts 1-4 then up to $25k (a single payout_max of $4,500 approximates the ladder), buffer equal to the drawdown (third-party restatements)", funded_consistency_pct=0.35),
    "mffu_50k_rapid": FirmRules("MyFundedFutures", "Rapid 50K", 50_000, 129.0, True, 0.0, 0.0, 3_000, 2_000, "trailing_intraday", 2_000, None, False, 0.50, 1, 5, 1, 500.0, None, 0.90, 2_100.0, True, "https://help.myfundedfutures.com/en/articles/13134709-rapid-plan-50k-a-comprehensive-look", "intraday trailing; daily payouts; 50% consistency; buffer $2,100; price $129/mo is third-party (tradecovex; others quote $109-$347); the phase of the 50% rule is not stated, applied to both", funded_consistency_pct=0.5),
    "mffu_100k_pro": FirmRules("MyFundedFutures", "Pro 100K", 100_000, 267.0, True, 0.0, 0.0, 6_000, 3_000, "trailing_eod", 3_000, None, False, 0.50, 1, 10, 10, 1_000.0, 100_000, 0.80, 3_100.0, False, "https://myfundedfutures.com/plans/pro", "payouts every 14 calendar days (about 10 trading days); 50% consistency per the official article (a third party says none); max 3 sim-funded accounts when any is 100K+; copy trading allowed; max contracts 10 assumed (research: 3-9 minis by size)", funded_consistency_pct=0.5),
    "tradeify_100k_growth": FirmRules("Tradeify", "Growth 100K", 100_000, 255.0, False, 169.0, 0.0, 6_000, 3_500, "trailing_eod", 3_500, 2_500, False, None, 1, 8, 5, 0.0, 4_000, 0.90, 4_500.0, True, "https://help.tradeify.co/en/articles/10495915-growth-evaluation-accounts", "soft daily loss limit; funded 35% consistency; payout after 5 winning days, balance must stay above $104,500, caps $2,000-$4,000; 90/10; 5 sim-funded accounts; price is the third-party-listed one-time fee", funded_consistency_pct=0.35),
    "tradeify_100k_select": FirmRules("Tradeify", "Select 100K (Flex payouts)", 100_000, 265.0, False, 169.0, 0.0, 6_000, 3_000, "trailing_eod", 3_000, None, False, 0.40, 3, 8, 5, 0.0, None, 0.90, 0.0, True, "https://help.tradeify.co/en/articles/12853921-select-evaluation-accounts", "eval 40% consistency, 3 minimum days, no daily loss limit; funded Select Daily (daily payouts, $1,250 DLL) or Select Flex (5-day cadence, no DLL); reset fee assumed equal to Growth's; Flex 100K payout cap and protected balance not captured, modelled as uncapped with no buffer"),
    "lucid_100k_flex": FirmRules("Lucid Trading", "LucidFlex 100K", 100_000, 307.0, False, 307.0, 0.0, 6_000, 3_000, "trailing_eod", 3_000, None, False, None, 1, 10, 5, 500.0, 2_500, 0.90, 0.0, False, "https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts", "payout rules official (5 profitable days, min $500, 50% of balance up to $2,500, 90/10, 5 payouts then live); price $307 is the third-party-quoted 100K LucidFlex fee (tradingtoolshub, 2026-09); max 5 funded per household; no sourced minimum trading days (1 used); max contracts 10 assumed"),
    "alpha_100k_standard": FirmRules("Alpha Futures", "Standard 100K", 100_000, 159.0, True, 159.0, 149.0, 6_000, 4_000, "trailing_eod", 4_000, None, False, None, 1, 10, 5, 200.0, 4_000, 0.80, 0.0, True, "https://alpha-futures.com/posts/alpha-futures-standard-plan-is-back-rules-fees-what-s-new", "6% target, 4% EOD trailing; qualified-account 40% consistency; payouts after 5 winning days of $200+, up to 4 per month, max $4,000 per request; split tiered 70% rising to 90% (0.80 used); max 5 accounts; copy trading only from an external master into Alpha", funded_consistency_pct=0.4),
    "apex_100k_intraday": FirmRules("Apex Trader Funding", "100K Intraday (4.0)", 100_000, 790.0, False, 790.0, 69.0, 6_000, 3_000, "trailing_intraday", 3_100, None, False, None, 1, 10, 5, 500.0, None, 0.90, 3_100.0, False, "https://support.apextraderfunding.com/hc/en-us/articles/4406804554779-How-Many-Paid-Funded-Accounts-Am-I-Allowed-to-Have", "account cap (20 per household) and copy-trading policy official; fees, 50% consistency, 5 qualifying days, $500 minimum and the safety net (drawdown + $100 for the first 3 payouts) from third parties; split is 100% of the first $25k then 90/10 (0.90 used); profit target assumed $6,000; price $790 one-time is third-party (damnpropfirms, March 2026); the $3,100 safety net is kept for every payout although Apex waives it from the 4th; no eval minimum days sourced; max contracts 10 assumed", funded_consistency_pct=0.5),
    "fundednext_50k_flex": FirmRules("FundedNext Futures", "Flex 50K", 50_000, 70.0, False, 70.0, 0.0, 3_000, 1_500, "trailing_eod", 1_500, None, False, 0.40, 1, 5, 5, 0.0, None, 0.95, 0.0, False, "https://damnpropfirms.com/futures-prop-firms/fundednext/", "third-party only; 40% consistency in the challenge, 95% split, five rewards then the account concludes; target and drawdown assumed; drawdown $1,500 = bottom of the third-party $1,500-$4,000 range"),
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
        self.failed_from = np.full(sims, -1, dtype=np.int8)  # phase the account was in when it breached

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
        self.failed_from[mask] = self.phase[mask]
        self.phase[mask] = FAILED

    def _restart_failed(self):
        """Re-buy failed accounts: a failed evaluation is reset (reset_cost), a
        failed funded account needs a new evaluation (eval_cost)."""
        r = self.rules
        failed = self.phase == FAILED
        if not failed.any():
            return
        reset = failed & (self.failed_from == EVAL) & (r.reset_cost > 0)
        self.costs_total += np.where(reset, r.reset_cost, np.where(failed, r.eval_cost, 0.0))
        self._reset_account(failed, EVAL)

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
        if self.restart_failed:
            self._restart_failed()  # an account that breached yesterday is re-bought and trades again today
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
            if rules.daily_loss_limit is not None and not rules.daily_loss_fails_account:
                over = day_pnl + pnl + rules.daily_loss_limit  # negative when this trade carries the day past the limit
                pnl = np.where(m & (over < 0), pnl - over, pnl)  # the firm liquidates at the limit
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
                dll = m & (day_pnl <= -rules.daily_loss_limit + 1e-9)
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
        if self.restart_failed:
            self._restart_failed()
        funded = self.phase == FUNDED
        profit = self.balance - rules.account_size - rules.payout_buffer
        eligible = funded & (self.days_since_payout >= rules.payout_min_days) & (profit >= rules.payout_min_amount)
        if rules.funded_consistency_pct is not None:
            eligible &= self.best_day <= rules.funded_consistency_pct * np.maximum(self.profit_since_reset, 1e-9)
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
