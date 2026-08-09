"""
Shadow Outcome Engine V1.1

Simulate the lifecycle and realized PnL of one Shadow trade.

Strategy A exit rules

LONG
- TP1: +1%
- TP2: +2%
- TP3: +3%
- SL:  -2%

SHORT
- TP1: -1%
- TP2: -2%
- TP3: -3%
- SL:  +2%

Position management
- TP1 closes 30% of original position.
- TP2 closes another 30% of original position.
- TP3 closes all remaining position.
- Stop loss closes all remaining position.
- TP1 activates breakeven protection.
- Trailing distance is 0.5%.
- A trailing stop calculated from candle N close becomes active
  from candle N+1.

PnL model
- Default virtual notional: 100 USDT.
- PnL is calculated from price return * closed fraction * notional.
- Fees and funding are NOT included in V1.1.

Safety
- Simulation only.
- No BingX API calls.
- No real orders.
- No VST orders.
- No modification of Strategy A.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


DEFAULT_NOTIONAL = 100.0


def calculate_levels(
    entry_price: float,
    side: str,
) -> dict[str, float]:
    """
    Calculate Strategy A TP/SL levels.
    """

    if side == "LONG":
        return {
            "tp1": entry_price * 1.01,
            "tp2": entry_price * 1.02,
            "tp3": entry_price * 1.03,
            "sl": entry_price * 0.98,
        }

    if side == "SHORT":
        return {
            "tp1": entry_price * 0.99,
            "tp2": entry_price * 0.98,
            "tp3": entry_price * 0.97,
            "sl": entry_price * 1.02,
        }

    raise ValueError(f"Unsupported side: {side}")


def calculate_trailing_stop(
    *,
    side: str,
    current_price: float,
    entry_price: float,
) -> float:
    """
    Reproduce Strategy A trailing-stop calculation.

    LONG:
        current_price * 0.995
        never below entry.

    SHORT:
        current_price * 1.005
        never above entry.
    """

    if side == "LONG":
        trailing_stop = current_price * 0.995

        if trailing_stop < entry_price:
            trailing_stop = entry_price

        return trailing_stop

    if side == "SHORT":
        trailing_stop = current_price * 1.005

        if trailing_stop > entry_price:
            trailing_stop = entry_price

        return trailing_stop

    raise ValueError(f"Unsupported side: {side}")


def calculate_return_ratio(
    *,
    side: str,
    entry_price: float,
    exit_price: float,
) -> float:
    """
    Calculate unleveraged price return.

    Example:
        LONG 100 -> 101 = +0.01
        SHORT 100 -> 99 = +0.01
    """

    if side == "LONG":
        return (exit_price - entry_price) / entry_price

    if side == "SHORT":
        return (entry_price - exit_price) / entry_price

    raise ValueError(f"Unsupported side: {side}")


def calculate_partial_pnl(
    *,
    side: str,
    entry_price: float,
    exit_price: float,
    fraction: float,
    notional: float,
) -> float:
    """
    Calculate realized PnL for one closed fraction.
    """

    return_ratio = calculate_return_ratio(
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
    )

    return notional * fraction * return_ratio


def build_result(
    *,
    shadow_record: dict[str, Any],
    status: str,
    result: str | None,
    exit_price: float | None,
    tp1_done: bool,
    tp2_done: bool,
    tp3_done: bool,
    breakeven_active: bool,
    trailing_active: bool,
    trailing_stop: float | None,
    remaining: float,
    realized_pnl: float,
    notional: float,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build standardized Shadow outcome.
    """

    closed_fraction = 1.0 - remaining

    realized_return_ratio = (
        realized_pnl / notional
        if notional > 0
        else 0.0
    )

    return {
        **shadow_record,
        "status": status,
        "result": result,
        "exit_price": exit_price,
        "tp1_done": tp1_done,
        "tp2_done": tp2_done,
        "tp3_done": tp3_done,
        "breakeven_active": breakeven_active,
        "trailing_active": trailing_active,
        "trailing_stop": trailing_stop,
        "closed_fraction": round(closed_fraction, 6),
        "remaining": round(remaining, 6),
        "notional": round(notional, 6),
        "realized_pnl": round(realized_pnl, 6),
        "realized_return_pct": round(
            realized_return_ratio * 100,
            6,
        ),
        "events": events,
    }


def simulate_shadow_outcome(
    shadow_record: dict[str, Any],
    future_klines: pd.DataFrame,
    notional: float = DEFAULT_NOTIONAL,
) -> dict[str, Any]:
    """
    Simulate one Shadow trade across future candles.

    Required candle columns:
    - High
    - Low
    - Close

    Timing model

    Candle N:
    1. Check protective stop already active before candle N.
    2. Check TP levels.
    3. At candle N close, calculate/update trailing stop.
    4. New trailing stop becomes active from candle N+1.
    """

    side = shadow_record["side"]
    entry_price = float(shadow_record["entry_price"])

    if entry_price <= 0:
        raise ValueError("entry_price must be greater than 0")

    if notional <= 0:
        raise ValueError("notional must be greater than 0")

    levels = calculate_levels(
        entry_price=entry_price,
        side=side,
    )

    tp1_done = False
    tp2_done = False
    tp3_done = False

    remaining = 1.0
    realized_pnl = 0.0

    breakeven_active = False
    trailing_active = False

    active_stop: float | None = levels["sl"]
    trailing_stop: float | None = None

    events: list[dict[str, Any]] = []

    for candle_index, candle in future_klines.iterrows():

        high = float(candle["High"])
        low = float(candle["Low"])
        close = float(candle["Close"])

        # -------------------------------------------------
        # STEP 1
        # Check stop that existed before this candle.
        # -------------------------------------------------

        if active_stop is not None:

            stop_hit = (
                side == "LONG" and low <= active_stop
            ) or (
                side == "SHORT" and high >= active_stop
            )

            if stop_hit:

                if breakeven_active:
                    if (
                        side == "LONG"
                        and active_stop > entry_price
                    ) or (
                        side == "SHORT"
                        and active_stop < entry_price
                    ):
                        reason = "TRAILING_STOP"
                    else:
                        reason = "BREAKEVEN"
                else:
                    reason = "STOP_LOSS"

                close_fraction = remaining

                pnl = calculate_partial_pnl(
                    side=side,
                    entry_price=entry_price,
                    exit_price=active_stop,
                    fraction=close_fraction,
                    notional=notional,
                )

                realized_pnl += pnl
                remaining = 0.0

                events.append({
                    "event": reason,
                    "price": active_stop,
                    "closed_fraction": close_fraction,
                    "pnl": round(pnl, 6),
                    "candle_index": candle_index,
                    "remaining": remaining,
                })

                return build_result(
                    shadow_record=shadow_record,
                    status="CLOSED",
                    result=reason,
                    exit_price=active_stop,
                    tp1_done=tp1_done,
                    tp2_done=tp2_done,
                    tp3_done=tp3_done,
                    breakeven_active=breakeven_active,
                    trailing_active=trailing_active,
                    trailing_stop=trailing_stop,
                    remaining=remaining,
                    realized_pnl=realized_pnl,
                    notional=notional,
                    events=events,
                )

        # -------------------------------------------------
        # STEP 2
        # Take-profit processing.
        # -------------------------------------------------

        if side == "LONG":

            tp1_hit = high >= levels["tp1"]
            tp2_hit = high >= levels["tp2"]
            tp3_hit = high >= levels["tp3"]

        elif side == "SHORT":

            tp1_hit = low <= levels["tp1"]
            tp2_hit = low <= levels["tp2"]
            tp3_hit = low <= levels["tp3"]

        else:

            raise ValueError(
                f"Unsupported side: {side}"
            )

        # TP1 = 30% of original position.
        if not tp1_done and tp1_hit:

            close_fraction = min(0.30, remaining)

            pnl = calculate_partial_pnl(
                side=side,
                entry_price=entry_price,
                exit_price=levels["tp1"],
                fraction=close_fraction,
                notional=notional,
            )

            realized_pnl += pnl
            remaining -= close_fraction

            tp1_done = True
            breakeven_active = True

            events.append({
                "event": "TP1",
                "price": levels["tp1"],
                "closed_fraction": close_fraction,
                "pnl": round(pnl, 6),
                "candle_index": candle_index,
                "remaining": round(remaining, 6),
            })

        # TP2 = another 30% of original position.
        if not tp2_done and tp2_hit:

            close_fraction = min(0.30, remaining)

            pnl = calculate_partial_pnl(
                side=side,
                entry_price=entry_price,
                exit_price=levels["tp2"],
                fraction=close_fraction,
                notional=notional,
            )

            realized_pnl += pnl
            remaining -= close_fraction

            tp2_done = True
            breakeven_active = True

            events.append({
                "event": "TP2",
                "price": levels["tp2"],
                "closed_fraction": close_fraction,
                "pnl": round(pnl, 6),
                "candle_index": candle_index,
                "remaining": round(remaining, 6),
            })

        # TP3 = close ALL remaining position.
        if not tp3_done and tp3_hit:

            close_fraction = remaining

            pnl = calculate_partial_pnl(
                side=side,
                entry_price=entry_price,
                exit_price=levels["tp3"],
                fraction=close_fraction,
                notional=notional,
            )

            realized_pnl += pnl
            remaining = 0.0
            tp3_done = True

            events.append({
                "event": "TP3",
                "price": levels["tp3"],
                "closed_fraction": close_fraction,
                "pnl": round(pnl, 6),
                "candle_index": candle_index,
                "remaining": remaining,
            })

            return build_result(
                shadow_record=shadow_record,
                status="CLOSED",
                result="TP3",
                exit_price=levels["tp3"],
                tp1_done=tp1_done,
                tp2_done=tp2_done,
                tp3_done=tp3_done,
                breakeven_active=breakeven_active,
                trailing_active=trailing_active,
                trailing_stop=trailing_stop,
                remaining=remaining,
                realized_pnl=realized_pnl,
                notional=notional,
                events=events,
            )

        # -------------------------------------------------
        # STEP 3
        # Update protection at candle close.
        #
        # New stop becomes active NEXT candle.
        # -------------------------------------------------

        if breakeven_active and remaining > 0:

            new_trailing_stop = calculate_trailing_stop(
                side=side,
                current_price=close,
                entry_price=entry_price,
            )

            if side == "LONG":

                if trailing_stop is None:
                    trailing_stop = new_trailing_stop
                else:
                    trailing_stop = max(
                        trailing_stop,
                        new_trailing_stop,
                    )

                active_stop = max(
                    entry_price,
                    trailing_stop,
                )

            else:

                if trailing_stop is None:
                    trailing_stop = new_trailing_stop
                else:
                    trailing_stop = min(
                        trailing_stop,
                        new_trailing_stop,
                    )

                active_stop = min(
                    entry_price,
                    trailing_stop,
                )

            trailing_active = True

    # -------------------------------------------------
    # No full exit yet.
    #
    # Partial TP PnL remains realized even while the
    # remaining position is still open.
    # -------------------------------------------------

    return build_result(
        shadow_record=shadow_record,
        status="OPEN",
        result=None,
        exit_price=None,
        tp1_done=tp1_done,
        tp2_done=tp2_done,
        tp3_done=tp3_done,
        breakeven_active=breakeven_active,
        trailing_active=trailing_active,
        trailing_stop=trailing_stop,
        remaining=remaining,
        realized_pnl=realized_pnl,
        notional=notional,
        events=events,
    )