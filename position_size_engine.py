"""
Position Size Engine V2

Responsibilities:
- Preserve the legacy fixed-margin position sizing interface.
- Calculate risk-based position sizing for future VST / LIVE integration.
- Respect MAX_SINGLE_RISK as a hard upper limit.
- Allow Risk Score to reduce position risk.
- Never increase leverage.
- Never increase configured risk limits.
- Never place exchange orders.

Important:
Risk means the estimated loss at Stop Loss,
NOT margin size and NOT notional position value.
"""

from config.settings import MAX_LEVERAGE, MAX_SINGLE_RISK


DEFAULT_MARGIN_USDT = 10.0


# ============================================================
# Legacy Position Size
# ============================================================

def calculate_position_quantity(
    symbol,
    price,
    margin_usdt=DEFAULT_MARGIN_USDT,
    leverage=MAX_LEVERAGE,
):
    """
    Legacy position sizing used by the current VST execution path.

    This function intentionally preserves the existing behavior:
        notional = margin * leverage
        quantity = notional / price

    Position Size V2 does NOT change current bot execution yet.
    """

    if leverage <= 0:
        raise ValueError("leverage must be greater than 0")

    if leverage > MAX_LEVERAGE:
        raise ValueError("leverage cannot exceed MAX_LEVERAGE")

    if price <= 0:
        raise ValueError("price must be greater than 0")

    if margin_usdt <= 0:
        raise ValueError("margin_usdt must be greater than 0")

    notional_value = margin_usdt * leverage
    quantity = notional_value / price

    return quantity


def estimate_notional_value(
    margin_usdt=DEFAULT_MARGIN_USDT,
    leverage=MAX_LEVERAGE,
):
    """
    Preserve legacy notional-value calculation.
    """

    if leverage <= 0:
        raise ValueError("leverage must be greater than 0")

    if leverage > MAX_LEVERAGE:
        raise ValueError("leverage cannot exceed MAX_LEVERAGE")

    if margin_usdt <= 0:
        raise ValueError("margin_usdt must be greater than 0")

    return margin_usdt * leverage


# ============================================================
# Risk Score Adjustment
# ============================================================

def get_risk_multiplier(risk_score):
    """
    Convert Risk Score into a position-risk multiplier.

    Lower Risk Score = more of the configured risk budget may be used.
    Higher Risk Score = position risk is reduced.

    Risk Score never increases MAX_SINGLE_RISK.
    """

    risk_score = float(risk_score)

    if risk_score < 0:
        risk_score = 0.0

    if risk_score > 100:
        risk_score = 100.0

    if risk_score < 30:
        return 1.00

    if risk_score < 60:
        return 0.75

    if risk_score < 80:
        return 0.50

    return 0.25


# ============================================================
# Position Size Engine V2
# ============================================================

def calculate_risk_based_position(
    equity,
    entry_price,
    stop_loss_price,
    risk_score,
    leverage=MAX_LEVERAGE,
    max_single_risk=MAX_SINGLE_RISK,
):
    """
    Calculate position size from account equity and Stop Loss distance.

    Formula:

        hard_risk_budget
            = equity * MAX_SINGLE_RISK

        adjusted_risk_budget
            = hard_risk_budget * risk_multiplier

        stop_distance_pct
            = abs(entry - stop) / entry

        notional
            = adjusted_risk_budget / stop_distance_pct

        quantity
            = notional / entry

    A leverage cap is then applied so calculated notional cannot require
    more than the account equity multiplied by allowed leverage.
    """

    equity = float(equity)
    entry_price = float(entry_price)
    stop_loss_price = float(stop_loss_price)
    leverage = float(leverage)
    max_single_risk = float(max_single_risk)

    if equity <= 0:
        raise ValueError("equity must be greater than 0")

    if entry_price <= 0:
        raise ValueError("entry_price must be greater than 0")

    if stop_loss_price <= 0:
        raise ValueError("stop_loss_price must be greater than 0")

    if stop_loss_price == entry_price:
        raise ValueError("stop_loss_price cannot equal entry_price")

    if leverage <= 0:
        raise ValueError("leverage must be greater than 0")

    if leverage > MAX_LEVERAGE:
        raise ValueError("leverage cannot exceed MAX_LEVERAGE")

    if max_single_risk <= 0:
        raise ValueError("max_single_risk must be greater than 0")

    if max_single_risk > MAX_SINGLE_RISK:
        raise ValueError(
            "max_single_risk cannot exceed configured MAX_SINGLE_RISK"
        )

    risk_multiplier = get_risk_multiplier(risk_score)

    hard_risk_budget = equity * max_single_risk

    adjusted_risk_budget = (
        hard_risk_budget * risk_multiplier
    )

    stop_distance = abs(
        entry_price - stop_loss_price
    )

    stop_distance_pct = (
        stop_distance / entry_price
    )

    raw_notional_value = (
        adjusted_risk_budget / stop_distance_pct
    )

    max_notional_by_leverage = (
        equity * leverage
    )

    notional_value = min(
        raw_notional_value,
        max_notional_by_leverage,
    )

    quantity = (
        notional_value / entry_price
    )

    estimated_loss_at_stop = (
        notional_value * stop_distance_pct
    )

    margin_required = (
        notional_value / leverage
    )

    return {
        "equity": round(equity, 8),
        "entry_price": round(entry_price, 8),
        "stop_loss_price": round(stop_loss_price, 8),
        "stop_distance_pct": round(
            stop_distance_pct * 100,
            4,
        ),
        "risk_score": round(float(risk_score), 2),
        "risk_multiplier": risk_multiplier,
        "hard_risk_budget": round(
            hard_risk_budget,
            8,
        ),
        "adjusted_risk_budget": round(
            adjusted_risk_budget,
            8,
        ),
        "notional_value": round(
            notional_value,
            8,
        ),
        "quantity": round(
            quantity,
            12,
        ),
        "margin_required": round(
            margin_required,
            8,
        ),
        "estimated_loss_at_stop": round(
            estimated_loss_at_stop,
            8,
        ),
        "leverage": leverage,
        "leverage_cap_applied": (
            raw_notional_value
            > max_notional_by_leverage
        ),
    }