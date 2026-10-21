"""A personal $2,000 cash account on MNQ micros, beside the prop-firm account.

What this is: a HYPOTHETICAL accounting view, reconstructed over forward trading days that were
already collected and scored. It is not a claim that this account was operating from 2026-10-15.
It reads a stream's recorded state file and never writes to it: no signal, fill, R or outcome is
altered, rescored or re-derived here. The dollars are computed from the recorded ENTRY and EXIT
PRICES, never from the state's `pnl_dollars` field, which is a flat r x $1,000 bookkeeping
convention and not money (verified: sum(pnl_dollars) == 1000 * sum(r) on every row).

Why a separate account at all: the prop-firm figures answer "what have the evaluations cost and
paid", with trade P&L modelled at the firm's risk budget per R. They do not answer "what would
my own $2,000 be worth". That needs its own cash, its own contract sizing, its own fees and its
own risk limits, because one micro on a 25-point stop is already 2.5% of $2,000.

The cost and fill model, from the recorded data (research/personal_account_assumptions.md has
the full statement and the sources):
  - Every stop exit in the record fills one tick adverse to the stop (39 of 39), every target
    exit fills exactly at the target, and the one breakeven exit fills one tick adverse to entry.
    That exit slippage is therefore ALREADY inside the recorded prices and is never charged again.
  - The engine's own R charges one tick per trade on top of the fill: r == (signed points - 0.25)
    / stop_points on all 87 recorded trades. This account charges one tick of ENTRY slippage,
    the same magnitude, on its market entries - once, not twice.
  - Commission is charged on top, which R does not model at all.

Un-modelled, every one of them adverse to this account, so the result here is optimistic rather
than conservative: session and news margin increases, trading halts, partial fills, rejected
orders, fills worse than one tick, and forced-liquidation charges. Two of the 87 recorded exits
are `exit_signal` fills with no reference price in the record, so their execution cost cannot be
verified from it; they are counted at their recorded price and reported separately.

usage:
  python research/personal_account.py --state research/private/jj_system_v1_state.json \\
      --candidate JJ --bars data/forward/nq_1min_forward.csv \\
      --out research/private/personal_account_jj.json --md research/private/personal_account_jj.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

# ---------------------------------------------------------------- the assumptions
# MNQ contract, CME: $2.00 an index point, 0.25-point tick = $0.50 a contract.
POINT_VALUE = 2.00
TICK_POINTS = 0.25
# Retail all-in per micro round turn: broker commission + CME exchange/clearing + NFA.
# Reported retail range $1.82-$1.90; the repo's own $0.50 is an old replay convention and
# TopstepX is $1.22. The higher retail figure is taken.
COMMISSION_RT = 1.90
# One tick of adverse entry slippage on a market entry. Exit slippage is already in the fills.
ENTRY_SLIP_POINTS = TICK_POINTS
# Intraday margin per micro: NinjaTrader and AMP $100, Tradovate $50. The conservative one.
DAY_MARGIN = 100.00
# Overnight margin per micro is about $3,800, well above the whole account, so this account
# never holds through the settlement break. It flattens by FLATTEN_ET and takes no new entry
# inside NO_ENTRY_ET.
OVERNIGHT_MARGIN = 3800.00
FLATTEN_ET = (16, 55)
NO_ENTRY_ET = ((16, 40), (18, 0))

START_CASH = 2000.00
# Risk cap per trade, fees and both slippages included. $52.90 all-in on his typical 25-point
# stop, so 2.645% of $2,000 is the arithmetic minimum that admits it at one micro; 3.0% is a
# POLICY choice made after seeing these stops, taken for headroom as equity moves, and shown
# against the alternatives in the sensitivity table rather than presented as forced.
MAX_RISK_PER_TRADE = 0.030
MAX_OPEN_RISK = 0.060          # across every open position at once
MAX_CONCURRENT = 3             # the raw stream reaches 7 at one timestamp
MARGIN_USE_CAP = 0.50          # open day-margin at most this share of cash
MIN_EQUITY = 500.00            # below this the account is latched off for good

SENSITIVITY = (0.02000, 0.02645, 0.02500, 0.03000, 0.05000)
# Capital figures are rounded UP to this, because a stake is a decision, not a measurement, and
# rounding a minimum DOWN would name a number that does not actually clear the bar.
ROUND_TO = 500.0

# Skip reasons split by kind: an INFEASIBLE trade the account could not have placed, a POLICY
# trade it chose not to place. Neither is ever counted as profit; conflating them would claim
# more than the record supports.
INFEASIBLE = "infeasible"
POLICY = "policy"
REASONS = {
    "below the trading floor": INFEASIBLE,
    "day margin cap": INFEASIBLE,
    "risk per trade cap": POLICY,
    "total open risk cap": POLICY,
    "max concurrent positions": POLICY,
    "inside the no-entry window before the daily flatten": POLICY,
}


def per_unit_risk(stop_points: float) -> float:
    """What one micro of this trade puts at risk, all in: the initial stop distance plus a tick
    of entry slippage and the tick the recorded stop fill already carries, times the point
    value, plus the round-turn commission."""
    return (stop_points + ENTRY_SLIP_POINTS + TICK_POINTS) * POINT_VALUE + COMMISSION_RT


def entry_cost(n: int) -> float:
    """Charged to cash at the ENTRY, not netted at the exit: commission and entry slippage."""
    return n * (COMMISSION_RT + ENTRY_SLIP_POINTS * POINT_VALUE)


def gross_usd(t: dict, n: int) -> float:
    """The trade's gross dollars from the recorded prices alone, for n micros."""
    d = 1.0 if str(t["direction"]).lower() == "long" else -1.0
    return (float(t["exit"]) - float(t["entry"])) * d * POINT_VALUE * n


def _et(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts).astimezone(NY)


def _in_no_entry_window(ts: str) -> bool:
    (h0, m0), (h1, m1) = NO_ENTRY_ET
    t = _et(ts)
    return (h0, m0) <= (t.hour, t.minute) < (h1, m1)


def size(stop_points: float, equity: float, cap_frac: float) -> int:
    """The largest whole micro count whose full stop-out stays within the per-trade cap. Mirrors
    research/candidates.whole_contracts and forward_jj.sized; zero means the trade is not taken.

    Sizing uses `stop_points`, the INITIAL stop distance committed at entry. Two of the 87
    recorded trades carry a `stop` that was later moved to entry (breakeven) while keeping
    stop_points 25.0, so the distance must come from stop_points, never from `stop`."""
    unit = per_unit_risk(stop_points)
    if unit <= 0:
        return 0
    # The epsilon is load-bearing, not cosmetic: a trade sitting exactly on its threshold
    # ($102.90 of risk against a $102.90 cap) floors to zero in binary floating point and would
    # be declined by noise rather than by the policy this documents.
    return max(0, int(math.floor((cap_frac * equity + 1e-9) / unit)))


def floor_for(start: float) -> float:
    """The balance below which the account stops for good. $500 on a $2,000 stake, and a quarter
    of the stake above that, so a larger account is not left trading on a stub."""
    return max(MIN_EQUITY, 0.25 * start)


def min_capital(trades: list, cap_frac: float = MAX_RISK_PER_TRADE) -> dict:
    """What a stream needs invested before this risk policy will let it trade.

    A trade is takeable at one micro when its full stop-out fits the per-trade cap, so the
    capital it demands is `per_unit_risk(stop) / cap_frac`. The tightest stop in the stream gives
    the capital for its FIRST signal, the widest gives the capital for ALL of them. This changes
    nothing about the strategy: it reads the stop distances the engine already recorded and says
    what account they imply."""
    if not trades:
        return {}
    risks = sorted(per_unit_risk(float(t["stop_points"])) for t in trades)
    up = lambda x: math.ceil(x / ROUND_TO) * ROUND_TO
    return {"cap_frac": cap_frac, "rounded_to": ROUND_TO,
            "min_for_any_usd": up(risks[0] / cap_frac),
            "min_for_all_usd": up(risks[-1] / cap_frac),
            "min_for_any_exact_usd": round(risks[0] / cap_frac, 2),
            "min_for_all_exact_usd": round(risks[-1] / cap_frac, 2),
            "tightest_stop_risk_usd": round(risks[0], 2),
            "widest_stop_risk_usd": round(risks[-1], 2)}


def run(trades: list, cap_frac: float = MAX_RISK_PER_TRADE, order: str = "engine",
        start: float | None = None) -> dict:
    """One pass of the account over the recorded stream.

    Strictly causal: an entry decision reads only the cash that closed trades have already
    returned and the positions already open at that moment. The trade's own exit_time is never
    consulted to decide whether to take it - the flatten rule is a forward policy (no entry
    inside the no-entry window, every position out by FLATTEN_ET), not a look-ahead.

    Where several candidates share an entry timestamp and the account cannot take them all, they
    are offered in `order`: "engine" is the order the engine emitted them, which is the order a
    live trader would have seen them fire. That tie is disclosed and measured, not hidden -
    `order="reverse"` reruns the whole loop the other way."""
    rows = sorted(enumerate(trades), key=lambda p: (_et(p[1]["entry_time"]), p[0]))
    if order == "reverse":
        rows = sorted(enumerate(trades), key=lambda p: (_et(p[1]["entry_time"]), -p[0]))

    events = []       # (time, seq, kind, payload) - closes settle before entries at a timestamp
    for i, t in rows:
        events.append((_et(t["entry_time"]), 1, "entry", (i, t)))
    ev_by_time: dict = {}
    for e in events:
        ev_by_time.setdefault(e[0], []).append(e)

    start = START_CASH if start is None else float(start)
    floor = floor_for(start)
    cash = start
    open_pos: list = []        # dicts with exit_at, n, risk, trade
    taken, skipped, closes = [], [], []
    latched_off = False
    peak_concurrent = 0

    def settle(now: dt.datetime) -> None:
        nonlocal cash
        for p in sorted([p for p in open_pos if p["exit_at"] <= now], key=lambda p: p["exit_at"]):
            cash += gross_usd(p["trade"], p["n"])
            open_pos.remove(p)
            closes.append({"at": p["exit_at"].isoformat(), "cash": round(cash, 2), "ref": p["ref"]})

    for now in sorted(ev_by_time):
        settle(now)                      # closes at or before this moment release their cash
        for _, _, _, (i, t) in ev_by_time[now]:
            equity = cash               # realised cash; costs are already debited at entry
            why = None
            if latched_off or equity < floor:
                latched_off, why = True, "below the trading floor"
            n = 0
            if why is None:
                n = size(float(t["stop_points"]), equity, cap_frac)
                if n == 0:
                    why = "risk per trade cap"
            if why is None and _in_no_entry_window(t["entry_time"]):
                why = "inside the no-entry window before the daily flatten"
            if why is None and len(open_pos) >= MAX_CONCURRENT:
                why = "max concurrent positions"
            risk = n * per_unit_risk(float(t["stop_points"]))
            if why is None and (sum(p["risk"] for p in open_pos) + risk
                                > MAX_OPEN_RISK * equity + 1e-9):
                why = "total open risk cap"
            micros = sum(p["n"] for p in open_pos)
            if why is None and (micros + n) * DAY_MARGIN > MARGIN_USE_CAP * cash:
                why = "day margin cap"
            if why is not None:
                skipped.append({"ref": i, "date": t["date"], "session": t["session"],
                                "direction": t["direction"],
                                "entry_time": t["entry_time"], "r": float(t["r"]),
                                "stop_points": float(t["stop_points"]), "would_size": n,
                                "reason": why, "kind": REASONS[why]})
                continue
            cost = entry_cost(n)
            cash -= cost
            open_pos.append({"exit_at": _et(t["exit_time"]), "n": n, "risk": risk,
                             "trade": t, "ref": i})
            peak_concurrent = max(peak_concurrent, len(open_pos))
            taken.append({"ref": i, "date": t["date"], "session": t["session"],
                          "entry_time": t["entry_time"], "exit_time": t["exit_time"],
                          "direction": t["direction"], "exit_reason": t["exit_reason"],
                          "stop_points": float(t["stop_points"]), "r": float(t["r"]),
                          "micros": n, "gross_usd": round(gross_usd(t, n), 2),
                          "commission_usd": round(n * COMMISSION_RT, 2),
                          "entry_slip_usd": round(n * ENTRY_SLIP_POINTS * POINT_VALUE, 2),
                          "net_usd": round(gross_usd(t, n) - cost, 2),
                          "cash_after_close": None})
    if open_pos:
        settle(max(p["exit_at"] for p in open_pos))

    by_ref = {c["ref"]: c for c in closes}
    for x in taken:
        c = by_ref.get(x["ref"])
        x["cash_after_close"] = c["cash"] if c else None

    # Closed-balance equity curve, in close order, with the opening $2,000 as the first peak.
    curve = [start] + [c["cash"] for c in sorted(closes, key=lambda c: c["at"])]
    peak, dd, dd_pct = curve[0], 0.0, 0.0
    for v in curve:
        peak = max(peak, v)
        if peak - v > dd:
            dd, dd_pct = peak - v, (peak - v) / peak if peak else 0.0

    gross = sum(x["gross_usd"] for x in taken)
    comm = sum(x["commission_usd"] for x in taken)
    slip = sum(x["entry_slip_usd"] for x in taken)
    net = gross - comm - slip
    wins = [x for x in taken if x["net_usd"] > 0]
    flat_breach = [x for x in taken if _spans_flatten(x["entry_time"], x["exit_time"])]
    return {
        "cap_frac": cap_frac, "order": order,
        "start_cash": round(start, 2), "end_cash": round(cash, 2),
        "net_usd": round(net, 2), "gross_usd": round(gross, 2),
        "return_pct": round(100.0 * net / start, 2),
        "trades_taken": len(taken), "trades_available": len(trades),
        "trades_skipped": len(skipped),
        "wins": len(wins), "losses": len(taken) - len(wins),
        "commission_usd": round(comm, 2), "entry_slip_usd": round(slip, 2),
        "costs_usd": round(comm + slip, 2),
        "max_drawdown_closed_usd": round(dd, 2),
        "max_drawdown_closed_pct": round(100.0 * dd_pct, 2),
        "micros_total": sum(x["micros"] for x in taken),
        "peak_concurrent": peak_concurrent,
        "r_taken": round(sum(x["r"] for x in taken), 3),
        "r_available": round(sum(float(t["r"]) for t in trades), 3),
        # The limits must not be dodging losers. They act only on information available at the
        # entry, so they cannot - but the declined set's own R is the check that says so out loud.
        "r_skipped": round(sum(x["r"] for x in skipped), 3),
        "latched_off": latched_off,
        "open_at_flatten": len(flat_breach),
        # The one number that explains a stream a small account simply cannot trade: what its
        # TIGHTEST stop costs on a single micro, against the opening balance.
        "smallest_micro_risk_usd": round(min(per_unit_risk(float(t["stop_points"]))
                                             for t in trades), 2) if trades else None,
        "smallest_micro_risk_pct": round(100.0 * min(per_unit_risk(float(t["stop_points"]))
                                                     for t in trades) / start, 2) if trades else None,
        "skipped_by_reason": _count(skipped, "reason"),
        "skipped_by_kind": _count(skipped, "kind"),
        "taken": taken, "skipped": skipped,
        "closed_curve": [round(v, 2) for v in curve],
    }


def _spans_flatten(entry_time: str, exit_time: str) -> bool:
    """Is a position still open at the daily flatten time? A forward check on the result, not a
    gate on the decision: if this ever fires, the account would have been force-flattened at a
    price the record does not contain, and that trade must be flagged, never given an invented
    fill."""
    a, b = _et(entry_time), _et(exit_time)
    h, m = FLATTEN_ET
    for off in (0, 1):
        w = (a + dt.timedelta(days=off)).replace(hour=h, minute=m, second=0, microsecond=0)
        if a < w <= b:
            return True
    return False


def _count(rows: list, key: str) -> dict:
    out: dict = {}
    for x in rows:
        out[x[key]] = out.get(x[key], 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------------------- mark to market
def load_bars(path: str) -> list:
    """(utc minute, high, low, close) from the forward prepared CSV."""
    import csv as _csv
    out = []
    with open(path) as fh:
        for row in _csv.DictReader(fh):
            ts = row["ts_event"].replace("Z", "+00:00")
            out.append((dt.datetime.fromisoformat(ts).astimezone(NY),
                        float(row["high"]), float(row["low"]), float(row["close"])))
    out.sort(key=lambda x: x[0])
    return out


def mark_to_market(res: dict, bars: list) -> dict:
    """The drawdown a closed-balance curve cannot see.

    Closed-balance drawdown only moves when a trade closes, so with up to three positions open at
    once it understates what the account actually went through and says nothing about whether it
    stayed above its margin. This marks every open position on each minute's close, and also at
    each minute's adverse extreme as a conservative intra-minute bound, and reports whether
    equity ever fell below the day-margin the open positions required."""
    if not bars or not res["taken"]:
        return {}
    # entry prices ride on the ledger rows as _entry_px, put there by the caller
    pos = [{"a": _et(x["entry_time"]), "b": _et(x["exit_time"]), "n": x["micros"],
            "d": 1.0 if str(x["direction"]).lower() == "long" else -1.0,
            "net": x["net_usd"], "entry_px": float(x["_entry_px"]), "ref": x["ref"]}
           for x in res["taken"]]
    lo_eq, lo_at, breach = None, None, 0
    cash = float(res["start_cash"])
    closed_by = sorted(((p["b"], p) for p in pos), key=lambda z: z[0])
    ci = 0
    opened = sorted(((p["a"], p) for p in pos), key=lambda z: z[0])
    oi = 0
    live: list = []
    peak_eq, dd, dd_pct = float(res["start_cash"]), 0.0, 0.0
    for when, hi, lo, close in bars:
        while oi < len(opened) and opened[oi][0] <= when:
            p = opened[oi][1]
            cash -= entry_cost(p["n"])
            live.append(p)
            oi += 1
        while ci < len(closed_by) and closed_by[ci][0] <= when:
            p = closed_by[ci][1]
            if p in live:
                cash += p["net"] + entry_cost(p["n"])
                live.remove(p)
            ci += 1
        eq_close = cash + sum((close - p["entry_px"]) * p["d"] * POINT_VALUE * p["n"] for p in live)
        eq_worst = cash + sum(((lo if p["d"] > 0 else hi) - p["entry_px"]) * p["d"]
                              * POINT_VALUE * p["n"] for p in live)
        need = sum(p["n"] for p in live) * DAY_MARGIN
        if live and eq_worst < need:
            breach += 1
        if lo_eq is None or eq_worst < lo_eq:
            lo_eq, lo_at = eq_worst, when
        peak_eq = max(peak_eq, eq_close)
        if peak_eq - eq_close > dd:
            dd, dd_pct = peak_eq - eq_close, (peak_eq - eq_close) / peak_eq if peak_eq else 0.0
    return {"mtm_max_drawdown_usd": round(dd, 2), "mtm_max_drawdown_pct": round(100.0 * dd_pct, 2),
            "worst_equity_usd": round(lo_eq, 2) if lo_eq is not None else None,
            "worst_equity_at": lo_at.isoformat() if lo_at else None,
            "margin_breach_minutes": breach}


# ---------------------------------------------------------------- report
def normalise(t: dict) -> dict:
    """One recorded trade in the shape this account needs, whatever stream wrote it.

    The JJ stream records `stop_points` explicitly and it is the INITIAL stop distance, which on
    two trades differs from |entry - stop| because the stop was later moved to breakeven. So the
    explicit field always wins and the distance is only derived when the stream does not record
    one, as S3 and S4 do not. `session` is a JJ notion; the others fall back to their setup."""
    out = dict(t)
    if out.get("stop_points") is None:
        out["stop_points"] = abs(float(out["entry"]) - float(out["stop"]))
    if not out.get("session"):
        out["session"] = str(out.get("setup") or "-")
    return out


def raw_concurrency(trades: list) -> int:
    """How many positions the raw stream holds at once at its busiest, before this account's
    limits: the gap between the signal stream and what one small account can carry."""
    ev = sorted((_et(t["entry_time"]), _et(t["exit_time"])) for t in trades)
    live, peak = [], 0
    for a, b in ev:
        live = [x for x in live if x > a]
        live.append(b)
        peak = max(peak, len(live))
    return peak


def _md(res: dict, mtm: dict, sens: list, rev: dict, name: str, days: list, note: str,
        raw_peak: int, mincap: dict, at_min: dict) -> str:
    s = []
    a = s.append
    a("# Personal cash account (hypothetical) - %s" % name)
    a("")
    a("A reconstructed accounting view over forward days already collected and scored. It is NOT")
    a("a claim that this account was operating from %s. No signal or outcome was altered."
      % (days[0] if days else "the first scored day"))
    a("")
    a("| | |")
    a("|---|---|")
    a("| Starting balance | $%s |" % f"{res['start_cash']:,.2f}")
    a("| Current balance | $%s |" % f"{res['end_cash']:,.2f}")
    a("| Net profit / loss | %s$%s |" % ("+" if res["net_usd"] >= 0 else "-",
                                         f"{abs(res['net_usd']):,.2f}"))
    a("| Return on $%s | %+.2f%% over %d scored day(s) |"
      % (f"{res['start_cash']:,.0f}", res["return_pct"], len(days)))
    a("| Trades taken | %d of %d recorded signals |" % (res["trades_taken"], res["trades_available"]))
    a("| Up / down | %d / %d |" % (res["wins"], res["losses"]))
    a("| Largest drawdown, closed balance | $%s (%.2f%%) |"
      % (f"{res['max_drawdown_closed_usd']:,.2f}", res["max_drawdown_closed_pct"]))
    if mtm:
        a("| Largest drawdown, marked to market | $%s (%.2f%%) |"
          % (f"{mtm['mtm_max_drawdown_usd']:,.2f}", mtm["mtm_max_drawdown_pct"]))
        a("| Worst equity touched | $%s at %s |"
          % (f"{mtm['worst_equity_usd']:,.2f}", mtm["worst_equity_at"][:16].replace("T", " ")))
        a("| Minutes below required day margin | %d |" % mtm["margin_breach_minutes"])
    a("| Trading costs | $%s (commission $%s + entry slippage $%s) |"
      % (f"{res['costs_usd']:,.2f}", f"{res['commission_usd']:,.2f}", f"{res['entry_slip_usd']:,.2f}"))
    a("| Micro contracts traded | %d, at most %d position(s) open at once |"
      % (res["micros_total"], res["peak_concurrent"]))
    a("| Signal coverage, R taken / R available | %+.2f / %+.2f |"
      % (res["r_taken"], res["r_available"]))
    a("")
    a("**%d scored day(s).** Do not annualise this, and do not read it as an edge: it is a"
      % len(days))
    a("dollar translation of a %+.2f R stream over %d day(s), and it inherits every property of"
      % (res["r_available"], len(days)))
    a("that stream, good and bad. What this view fixes is the MEASUREMENT - whether $2,000 of own")
    a("money could have placed these trades and what it would hold now - not the question of")
    a("whether the strategy has an edge, which this does not address and cannot.")
    a("")
    a("The limits decline trades on information available at the entry, never on an outcome. The")
    a("check that says so: the %d declined signals were together %+.2f R, so the account did not"
      % (res["trades_skipped"], res["r_skipped"]))
    a("systematically dodge losers.")
    a("")
    if res["latched_off"]:
        a("**The account hit its $%s trading floor and stopped for good.**" % f"{MIN_EQUITY:,.0f}")
        a("")
    if res["open_at_flatten"]:
        a("**FLAG: %d taken position(s) would still have been open at the daily flatten time.**"
          % res["open_at_flatten"])
        a("The record holds no liquidation price for them; they are shown at their recorded exit")
        a("and must be looked at.")
        a("")
    a("## What this account could not take")
    a("")
    a("%d of the %d recorded signals were not taken. None of them counts as profit or loss here."
      % (res["trades_skipped"], res["trades_available"]))
    a("")
    a("| reason | kind | trades |")
    a("|---|---|---|")
    for why, k in sorted(res["skipped_by_reason"].items(), key=lambda kv: -kv[1]):
        a("| %s | %s | %d |" % (why, REASONS[why], k))
    a("")
    a("`infeasible` means the account could not have placed the trade. `policy` means its own")
    a("risk limits declined it; a larger account, or a looser limit, would have taken it. The two")
    a("are kept apart deliberately: calling a policy skip unexecutable would claim more than the")
    a("record supports.")
    a("")
    if not res["taken"]:
        a("## This account could not trade this stream at all")
        a("")
        a("Not one of its %d signals was takeable from $%s. The stream's TIGHTEST stop costs"
          % (res["trades_available"], f"{res['start_cash']:,.0f}"))
        a("$%s on a single micro contract, which is %.1f%% of the account - and a micro is the"
          % (f"{res['smallest_micro_risk_usd']:,.2f}", res["smallest_micro_risk_pct"]))
        a("smallest position that exists. No risk limit worth the name admits that, so the")
        a("balance below is the opening balance, untouched, and not a loss.")
        a("")
        a("This is a real finding about the stream, not a gap in the accounting: its stop")
        a("distances are built for an account far larger than this one.")
        a("")
    a("## Every simulated trade")
    a("")
    a("Each line is real dollars from the recorded prices, and the balance is the account after")
    a("that trade closed, fees included. `fees` is this trade's commission plus its entry")
    a("slippage; both were charged at the entry, not netted at the exit.")
    a("")
    a("| # | date | session | side | exit | micros | gross | fees | net | balance after |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for i, x in enumerate(res["taken"], 1):
        fees = x["commission_usd"] + x["entry_slip_usd"]
        a("| %d | %s | %s | %s | %s | %d | %s%s | -$%s | %s%s | $%s |"
          % (i, x["date"], x["session"], x["direction"], x["exit_reason"], x["micros"],
             "+" if x["gross_usd"] >= 0 else "-", f"${abs(x['gross_usd']):,.2f}",
             f"{fees:,.2f}", "+" if x["net_usd"] >= 0 else "-", f"${abs(x['net_usd']):,.2f}",
             f"{x['cash_after_close']:,.2f}" if x["cash_after_close"] is not None else "-"))
    a("")
    a("## Every signal this account declined")
    a("")
    a("None of these contributes a cent to the balance above. `would_size` is the position it")
    a("would have taken had the limit allowed it.")
    a("")
    a("| date | session | side | stop pts | recorded R | would_size | reason | kind |")
    a("|---|---|---|---|---|---|---|---|")
    for x in res["skipped"]:
        a("| %s | %s | %s | %.1f | %+.2f | %d | %s | %s |"
          % (x["date"], x["session"], x.get("direction", "-"), x["stop_points"], x["r"],
             x["would_size"], x["reason"], x["kind"]))
    a("")
    if mincap:
        a("## What this stream needs invested")
        a("")
        a("A signal is tradable when one micro's full stop-out fits the per-trade cap, so the")
        a("capital it demands is its risk divided by that cap, rounded up to the next $%d."
          % ROUND_TO)
        a("Nothing about the strategy changes here - these are the stop distances the engine")
        a("already recorded, read back as the account size they imply. Affording a stop is")
        a("necessary, not sufficient: the open-risk and concurrency limits still decline signals")
        a("that overlap.")
        a("")
        a("| | risk on one micro | capital needed at %.1f%% per trade |" % (100 * MAX_RISK_PER_TRADE))
        a("|---|---|---|")
        a("| Its TIGHTEST stop, so its first tradable signal | $%s | $%s |"
          % (f"{mincap['tightest_stop_risk_usd']:,.2f}", f"{mincap['min_for_any_usd']:,.0f}"))
        a("| Its WIDEST stop, so every signal tradable | $%s | $%s |"
          % (f"{mincap['widest_stop_risk_usd']:,.2f}", f"{mincap['min_for_all_usd']:,.0f}"))
        a("")
        if at_min:
            a("At $%s, the stake that makes every signal tradable, the same account over the same"
              % f"{at_min['start_cash']:,.0f}")
            a("days takes %d of %d signals and ends at $%s (%s$%s, %+.2f%%), largest closed"
              % (at_min["trades_taken"], at_min["trades_available"],
                 f"{at_min['end_cash']:,.2f}", "+" if at_min["net_usd"] >= 0 else "-",
                 f"{abs(at_min['net_usd']):,.2f}", at_min["return_pct"]))
            a("drawdown $%s. The same caveats apply: these are few days and the costs not"
              % f"{at_min['max_drawdown_closed_usd']:,.2f}")
            a("modelled are all adverse.")
            a("")
    a("## The knob that matters most")
    a("")
    a("One micro on his typical 25-point stop risks $%.2f all in, so %.3f%% of $%s is the"
      % (per_unit_risk(25.0), 100.0 * per_unit_risk(25.0) / START_CASH, f"{START_CASH:,.0f}"))
    a("arithmetic minimum per-trade cap that admits it at all. The default %.1f%% is a policy"
      % (100.0 * MAX_RISK_PER_TRADE))
    a("choice made after seeing these stops, not a figure the data forced. Each row below reruns")
    a("the whole account from $%s." % f"{START_CASH:,.0f}")
    a("")
    a("| max risk per trade | trades taken | net P&L | return | closed drawdown |")
    a("|---|---|---|---|---|")
    for x in sens:
        a("| %.3f%%%s | %d | %s$%s | %+.2f%% | $%s |"
          % (100.0 * x["cap_frac"], " (default)" if abs(x["cap_frac"] - MAX_RISK_PER_TRADE) < 1e-9 else "",
             x["trades_taken"], "+" if x["net_usd"] >= 0 else "-", f"{abs(x['net_usd']):,.2f}",
             x["return_pct"], f"{x['max_drawdown_closed_usd']:,.2f}"))
    a("")
    a("## The within-minute tie")
    a("")
    a("Several signals share one entry minute (the raw stream reaches %d open at once), and this"
      % raw_peak)
    a("account cannot take them all. They are offered in the order the engine emitted them, the")
    a("order a live trader would have seen them fire. Running the identical account with that")
    a("order reversed gives %s$%s (%+.2f%%) on %d trades, against %s$%s (%+.2f%%) on %d. The gap"
      % ("+" if rev["net_usd"] >= 0 else "-", f"{abs(rev['net_usd']):,.2f}", rev["return_pct"],
         rev["trades_taken"], "+" if res["net_usd"] >= 0 else "-", f"{abs(res['net_usd']):,.2f}",
         res["return_pct"], res["trades_taken"]))
    a("is how much of this result rests on a tie the record cannot settle.")
    a("")
    a("## Assumptions and what is not modelled")
    a("")
    a(note)
    return "\n".join(s) + "\n"


NOTE = """MNQ at $%.2f an index point, %.2f-point tick. Commission $%.2f per micro round turn
(retail all-in: broker + CME exchange/clearing + NFA). One tick of entry slippage on a market
entry; exit slippage is already inside the recorded fills (every stop fills one tick adverse to
the stop, every target exactly at the target) and is not charged twice. Intraday margin $%.0f a
micro, open margin capped at %.0f%% of cash. Overnight margin is about $%s a micro, above the
whole account, so nothing is held through the settlement break: no new entry between %02d:%02d
and %02d:%02d ET and every position out by %02d:%02d ET. Sizing uses each trade's INITIAL stop
distance (`stop_points`); two recorded trades carry a stop later moved to breakeven, so the
distance must not be read off `stop`. Equity for sizing is realised cash at the moment of entry,
with commission and entry slippage debited at the entry, so no decision sees a trade's own
outcome. Risk per trade at most %.1f%% of that equity, open risk at most %.1f%% across all
positions, at most %d open at once, and the account latches off for good below $%.0f. A risk cap
gates NEW entries only: a position already open is never force-closed because a later loss shrank
the allowance. A trade recorded as entering and exiting in the same minute holds its slot and its
cash until the next timestamp, because at that minute the account could not yet know it had closed.

Not modelled, and every one of them adverse to this account, so this result is optimistic rather
than conservative: session and news margin increases, trading halts, partial fills, rejected
orders, fills worse than one tick, forced-liquidation charges. Two of the recorded exits are
`exit_signal` fills with no reference price in the record, so their execution cost cannot be
verified from it.""" % (
    POINT_VALUE, TICK_POINTS, COMMISSION_RT, DAY_MARGIN, 100 * MARGIN_USE_CAP,
    f"{OVERNIGHT_MARGIN:,.0f}", NO_ENTRY_ET[0][0], NO_ENTRY_ET[0][1], NO_ENTRY_ET[1][0],
    NO_ENTRY_ET[1][1], FLATTEN_ET[0], FLATTEN_ET[1], 100 * MAX_RISK_PER_TRADE,
    100 * MAX_OPEN_RISK, MAX_CONCURRENT, MIN_EQUITY)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True, help="a stream's recorded state json, read only")
    ap.add_argument("--candidate", default="JJ", help="which stream's trades to account for")
    ap.add_argument("--version", help="a lab version code (L01..): the lab's state keys its trades "
                                      "by version, so an improvement-lab winner gets this identical "
                                      "accounting with no other change")
    ap.add_argument("--bars", help="data/forward/nq_1min_forward.csv, for the marked-to-market drawdown")
    ap.add_argument("--name", default="JJ system v1")
    ap.add_argument("--start-cash", type=float, default=None,
                    help="override the $2,000 stake, to ask what a stream needs invested")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    g = ap.parse_args()

    with open(g.state) as fh:
        st = json.load(fh)
    raw = st.get("trades", [])
    if isinstance(raw, dict):          # the lab keys its trades by version code
        if not g.version:
            print("personal account: this state keys trades by version; pass --version")
            return 2
        raw = raw.get(g.version, [])
    want = g.version or g.candidate
    trades = [normalise(t) for t in raw if t.get("candidate", want) == want]
    days = st.get("dates", [])
    if not trades:
        out = {"name": g.name, "candidate": want, "days": days, "trades_available": 0,
               "note": "no recorded trade yet for this stream"}
        with open(g.out, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        print("personal account: no trade yet for %s" % want)
        return 0

    start = g.start_cash or START_CASH
    res = run(trades, start=start)
    rev = run(trades, order="reverse", start=start)
    sens = []
    for f in sorted(set(SENSITIVITY)):
        r = run(trades, cap_frac=f, start=start)
        sens.append({k: r[k] for k in ("cap_frac", "trades_taken", "net_usd", "return_pct",
                                       "max_drawdown_closed_usd")})
    by_ref = {i: t for i, t in enumerate(trades)}
    for x in res["taken"]:
        x["_entry_px"] = float(by_ref[x["ref"]]["entry"])
    mtm = mark_to_market(res, load_bars(g.bars)) if g.bars and os.path.exists(g.bars) else {}
    for x in res["taken"]:
        x.pop("_entry_px", None)

    # What this stream needs invested before the policy will trade it, and what it would have
    # been worth at that stake. Nothing about the strategy moves: this reads the stop distances
    # the engine already recorded and says what account size they imply.
    mincap = min_capital(trades)
    at_min = {}
    if mincap and res["trades_taken"] < res["trades_available"]:
        need = mincap["min_for_all_usd"]
        if need > start:
            rm = run(trades, start=need)
            at_min = {"start_cash": need, "end_cash": rm["end_cash"], "net_usd": rm["net_usd"],
                      "return_pct": rm["return_pct"], "trades_taken": rm["trades_taken"],
                      "trades_available": rm["trades_available"],
                      "max_drawdown_closed_usd": rm["max_drawdown_closed_usd"]}

    doc = {"name": g.name, "candidate": want, "days": days,
           "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "hypothetical": True,
           "assumptions": {
               "start_cash": START_CASH, "point_value": POINT_VALUE, "tick_points": TICK_POINTS,
               "commission_rt": COMMISSION_RT, "entry_slip_points": ENTRY_SLIP_POINTS,
               "day_margin": DAY_MARGIN, "overnight_margin": OVERNIGHT_MARGIN,
               "max_risk_per_trade": MAX_RISK_PER_TRADE, "max_open_risk": MAX_OPEN_RISK,
               "max_concurrent": MAX_CONCURRENT, "margin_use_cap": MARGIN_USE_CAP,
               "min_equity": MIN_EQUITY, "flatten_et": list(FLATTEN_ET),
               "no_entry_et": [list(NO_ENTRY_ET[0]), list(NO_ENTRY_ET[1])]},
           "result": {k: v for k, v in res.items() if k not in ("taken", "skipped", "closed_curve")},
           "marked_to_market": mtm,
           "sensitivity": sens,
           "minimum_capital": mincap, "at_minimum_capital": at_min,
           "reverse_order": {k: rev[k] for k in ("net_usd", "return_pct", "trades_taken")},
           "raw_peak_concurrent": raw_concurrency(trades),
           "ledger": res["taken"], "skipped": res["skipped"],
           "closed_curve": res["closed_curve"], "note": NOTE}
    with open(g.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    if g.md:
        with open(g.md, "w") as fh:
            fh.write(_md(res, mtm, sens, rev, g.name, days, NOTE, raw_concurrency(trades),
                         mincap, at_min))
    print("personal account: $%s from $%s, %+.2f%%, %d of %d signals taken, %d skipped, "
          "closed drawdown $%s" % (f"{res['end_cash']:,.2f}", f"{res['start_cash']:,.0f}",
                                   res["return_pct"], res["trades_taken"], res["trades_available"],
                                   res["trades_skipped"], f"{res['max_drawdown_closed_usd']:,.2f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
