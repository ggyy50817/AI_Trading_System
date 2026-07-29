"""
Opportunity Engine V2

Single entry point for Opportunity observation.

Input

    TradingDecision

Responsibilities

- Receive TradingDecision
- Log Opportunity

Future

- Shadow Trading
- AI Memory
- Knowledge Analyzer
- AI Advisor

Opportunity Engine never modifies trading logic.
"""

from __future__ import annotations

from core.trading_decision import TradingDecision
from opportunity.logger import log_opportunity


class OpportunityEngine:
    """
    Opportunity subsystem entry point.
    """

    def process(self, decision: TradingDecision) -> None:
        """
        Process one TradingDecision.
        """

        log_opportunity(decision)


opportunity_engine = OpportunityEngine()