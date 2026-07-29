"""
OpportunityRecord V1

OpportunityRecord is the earliest observation contract in the AI Trading
System.

Lifecycle

    Market
        ↓
    Scanner
        ↓
    OpportunityRecord
        ↓
    TradingDecision (optional)
        ↓
    Execution
        ↓
    Validation

Every completed scanner analysis MUST generate exactly one
OpportunityRecord, regardless of whether a trade is opened.

Purpose

- Record every opportunity.
- Record rejected opportunities.
- Feed AI Memory.
- Feed Shadow Trading.
- Feed Knowledge Analyzer.

This module contains DATA ONLY.
No business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class OpportunityRecord:
    """
    Scanner observation contract.

    This record is created immediately after a scanner finishes
    evaluating one symbol.

    It exists regardless of whether a trade is opened.
    """

    # Metadata
    timestamp: datetime
    source: str

    # Symbol
    symbol: str

    # Market
    market_regime: str

    # AI Scores
    long_score: int
    short_score: int

    # Thresholds
    long_threshold: int
    short_threshold: int

    # Scanner Result
    can_long: bool
    can_short: bool

    # Why this opportunity was accepted/rejected.
    # None means "no specific reason".
    reason: str | None = None

    # Full scanner context (optional)
    context: dict[str, Any] | None = None