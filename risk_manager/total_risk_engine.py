"""
Total Risk Engine V1

Responsibilities:
- Enforce MAX_TOTAL_RISK across all open positions.
- Calculate used and remaining account risk.
- Determine whether a new trade fits inside the total risk budget.
- Reduce the allowed risk of a new trade when necessary.
- Never increase MAX_TOTAL_RISK.
- Never increase MAX_SINGLE_RISK.
- Never place orders.
"""

from config.settings import MAX_TOTAL_RISK, MAX_SINGLE_RISK


def calculate_total_risk_budget(
    equity,
    max_total_risk=MAX_TOTAL_RISK,
):
    """
    Calculate the maximum USDT risk allowed across all open positions.
    """

    equity = float(equity)
    max_total_risk = float(max_total_risk)

    if equity <= 0:
        raise ValueError("equity must be greater than 0")

    if max_total_risk <= 0:
        raise ValueError("max_total_risk must be greater than 0")

    if max_total_risk > MAX_TOTAL_RISK:
        raise ValueError(
            "max_total_risk cannot exceed configured MAX_TOTAL_RISK"
        )

    return equity * max_total_risk


def calculate_used_risk(position_risks):
    """
    Sum estimated Stop Loss risk from existing open positions.

    position_risks example:
        [5.0, 3.75, 2.5]
    """

    if position_risks is None:
        position_risks = []

    used_risk = 0.0

    for risk in position_risks:
        risk = float(risk)

        if risk < 0:
            raise ValueError(
                "position risk cannot be negative"
            )

        used_risk += risk

    return used_risk


def evaluate_total_risk(
    equity,
    position_risks,
    requested_new_risk,
    max_total_risk=MAX_TOTAL_RISK,
    max_single_risk=MAX_SINGLE_RISK,
):
    """
    Evaluate whether a new position fits inside total account risk.

    The engine may reduce the allowed risk for the new position,
    but it can never increase configured risk limits.
    """

    equity = float(equity)
    requested_new_risk = float(requested_new_risk)
    max_single_risk = float(max_single_risk)

    if equity <= 0:
        raise ValueError("equity must be greater than 0")

    if requested_new_risk < 0:
        raise ValueError(
            "requested_new_risk cannot be negative"
        )

    if max_single_risk <= 0:
        raise ValueError(
            "max_single_risk must be greater than 0"
        )

    if max_single_risk > MAX_SINGLE_RISK:
        raise ValueError(
            "max_single_risk cannot exceed configured MAX_SINGLE_RISK"
        )

    total_risk_budget = calculate_total_risk_budget(
        equity,
        max_total_risk,
    )

    single_risk_budget = (
        equity * max_single_risk
    )

    used_risk = calculate_used_risk(
        position_risks
    )

    remaining_total_risk = max(
        0.0,
        total_risk_budget - used_risk,
    )

    requested_new_risk = min(
        requested_new_risk,
        single_risk_budget,
    )

    allowed_new_risk = min(
        requested_new_risk,
        remaining_total_risk,
    )

    projected_total_risk = (
        used_risk + allowed_new_risk
    )

    if remaining_total_risk <= 0:
        action = "REJECT"
        reason = "TOTAL_RISK_LIMIT_REACHED"

    elif allowed_new_risk < requested_new_risk:
        action = "REDUCE"
        reason = "REDUCED_TO_REMAINING_TOTAL_RISK"

    else:
        action = "ALLOW"
        reason = "WITHIN_TOTAL_RISK_LIMIT"

    return {
        "equity": round(equity, 8),
        "total_risk_budget": round(
            total_risk_budget,
            8,
        ),
        "single_risk_budget": round(
            single_risk_budget,
            8,
        ),
        "used_risk": round(
            used_risk,
            8,
        ),
        "remaining_total_risk": round(
            remaining_total_risk,
            8,
        ),
        "requested_new_risk": round(
            requested_new_risk,
            8,
        ),
        "allowed_new_risk": round(
            allowed_new_risk,
            8,
        ),
        "projected_total_risk": round(
            projected_total_risk,
            8,
        ),
        "action": action,
        "reason": reason,
    }