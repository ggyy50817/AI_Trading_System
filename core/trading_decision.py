"""TradingDecision V1 — shared output contract for the AI Trading System.

TradingDecision is the common output contract (Contract) for the entire
AI Trading System. Future producers will include:

    - Scanner
    - Replay
    - Research
    - Shadow Trading

Consumers such as Opportunity Logger, Validation, and Decision Dataset
must consume TradingDecision records as-is. They must not assemble or
invent decision fields on their own.

This module defines the V1 schema only. It contains no business logic
and no helper functions.
"""

from __future__ import annotations

from typing import Any, TypedDict


class TradingDecision(TypedDict):
    """V1 contract for a single trading decision record."""

    timestamp: str
    symbol: str
    side: str | None
    source: str

    price: float | None

    long_score: float | None
    short_score: float | None
    ai_score: float | None

    market_regime: str | None

    signal_ok: bool

    blocked: bool
    block_reason: str | None

    order_submitted: bool
    order_success: bool | None
    order_result: Any | None

    reason: str | None

    skip_reason: str | None
