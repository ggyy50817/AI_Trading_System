"""Decision Pipeline MVP — dispatch TradingDecision to consumers.

Architecture::

    Scanner / Replay / Research / Shadow
        → TradingDecision Adapter
        → TradingDecision
        → Decision Pipeline  (this module)
        → Consumers

Responsibility
    Accept a completed ``TradingDecision`` and fan-out to registered
    consumers. This module only dispatches. It must not score, decide
    side, detect regime, size positions, apply risk, call APIs, place
    orders, retry, or mutate the decision.

MVP
    Consumers are registered in ``consumer_registry.py``.
    Each consumer is invoked inside its own try/except so one failure
    does not stop the others.
"""

from __future__ import annotations

from core.trading_decision import TradingDecision
from decision_pipeline.consumer_registry import CONSUMERS
from viewlogs.logger import log_message


def process_decision(decision: TradingDecision) -> None:
    """Dispatch one TradingDecision to all consumers. Dispatch only."""
    for consumer in CONSUMERS:
        try:
            consumer(decision)
        except Exception as e:
            log_message(f"❌ Decision Pipeline Consumer Error: {e}")