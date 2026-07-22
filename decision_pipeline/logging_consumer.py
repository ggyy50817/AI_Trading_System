"""Logging consumer — print concise TradingDecision summaries."""

from __future__ import annotations

from core.trading_decision import TradingDecision
from viewlogs.logger import log_message


def consume(decision: TradingDecision) -> None:
    """Log a concise one-block summary of a TradingDecision."""
    lines = [
        "📝 Decision",
        decision.get("symbol", ""),
        decision.get("side", ""),
        f"AI={decision.get('ai_score')}",
        f"Regime={decision.get('market_regime')}",
        f"Submitted={decision.get('order_submitted', False)}",
    ]

    if decision.get("order_submitted", False):
        lines.append(f"Success={decision.get('order_success')}")

    log_message("\n".join(lines))
