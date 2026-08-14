"""
Risk Integration Engine V1

Pipeline:
Risk Score
    -> Position Size
    -> Total Risk
    -> Final ALLOW / REDUCE / REJECT

Responsibilities:
- Combine existing validated risk engines.
- Preserve MAX_LEVERAGE.
- Preserve MAX_SINGLE_RISK.
- Preserve MAX_TOTAL_RISK.
- Never place exchange orders.
- Never modify Shadow Trading.
"""

from config.settings import (
    MAX_LEVERAGE,
    MAX_SINGLE_RISK,
    MAX_TOTAL_RISK,
)

from risk_manager.risk_score_engine import calculate_risk_score
from position_size_engine import calculate_risk_based_position
from risk_manager.total_risk_engine import evaluate_total_risk


def evaluate_trade_risk(
    equity,
    entry_price,
    stop_loss_price,
    position_risks=None,
    market_regime="UNKNOWN",
    atr_ratio=0.0,
    volume_ratio=1.0,
    funding_rate=0.0,
    ai_score=0.0,
    leverage=MAX_LEVERAGE,
):
    """
    Run one trade candidate through the complete risk pipeline.

    Returns:
        risk_score_result
        position_size_result
        total_risk_result
        final_action
        final_allowed_risk
        final_notional_value
        final_quantity
        final_margin_required
    """

    if position_risks is None:
        position_risks = []

    # Step 1: Risk Score
    risk_result = calculate_risk_score(
        market_regime=market_regime,
        atr_ratio=atr_ratio,
        volume_ratio=volume_ratio,
        funding_rate=funding_rate,
        ai_score=ai_score,
    )

    risk_score = float(risk_result["risk_score"])

    # Step 2: Position Size
    position_result = calculate_risk_based_position(
        equity=equity,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        risk_score=risk_score,
        leverage=leverage,
        max_single_risk=MAX_SINGLE_RISK,
    )

    requested_risk = float(
        position_result["estimated_loss_at_stop"]
    )

    # Step 3: Total Account Risk
    total_risk_result = evaluate_total_risk(
        equity=equity,
        position_risks=position_risks,
        requested_new_risk=requested_risk,
        max_total_risk=MAX_TOTAL_RISK,
        max_single_risk=MAX_SINGLE_RISK,
    )

    final_action = total_risk_result["action"]

    final_allowed_risk = float(
        total_risk_result["allowed_new_risk"]
    )

    # REJECT means no position may be opened.
    if final_action == "REJECT" or final_allowed_risk <= 0:
        final_notional_value = 0.0
        final_quantity = 0.0
        final_margin_required = 0.0

    # ALLOW means Position Size Engine output can be used unchanged.
    elif final_action == "ALLOW":
        final_notional_value = float(
            position_result["notional_value"]
        )
        final_quantity = float(
            position_result["quantity"]
        )
        final_margin_required = float(
            position_result["margin_required"]
        )

    # REDUCE means Total Risk Engine has less risk capacity remaining.
    # Scale the already validated Position Size result proportionally.
    else:
        original_risk = float(
            position_result["estimated_loss_at_stop"]
        )

        if original_risk <= 0:
            raise ValueError(
                "position estimated loss must be greater than 0"
            )

        scale = final_allowed_risk / original_risk

        final_notional_value = (
            float(position_result["notional_value"]) * scale
        )

        final_quantity = (
            float(position_result["quantity"]) * scale
        )

        final_margin_required = (
            float(position_result["margin_required"]) * scale
        )

    return {
        "risk_score_result": risk_result,
        "position_size_result": position_result,
        "total_risk_result": total_risk_result,
        "final_action": final_action,
        "final_allowed_risk": round(
            final_allowed_risk,
            8,
        ),
        "final_notional_value": round(
            final_notional_value,
            8,
        ),
        "final_quantity": round(
            final_quantity,
            8,
        ),
        "final_margin_required": round(
            final_margin_required,
            8,
        ),
    }