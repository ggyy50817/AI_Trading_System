"""Decision Dataset logger — persist TradingDecision records for downstream use.

Decision Dataset will store every ``TradingDecision`` produced by the system
so that Validation, Replay Learning, and AI Dataset pipelines can consume a
consistent historical record.

This module defines the write entry point only. Persistence is not
implemented yet. No trading business logic belongs here.
"""

from __future__ import annotations

from core.trading_decision import TradingDecision


def append_decision(decision: TradingDecision) -> None:
    """Append one TradingDecision to the decision dataset."""
    raise NotImplementedError
