"""
ShadowTrade V1

A virtual trade created from an OpportunityRecord.

Shadow trades never submit real orders.

Lifecycle

OpportunityRecord
    ->
ShadowTrade
    ->
Shadow Validator
    ->
Statistics
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ShadowTrade:
    """
    Virtual trade used only for observation and validation.
    """

    created_at: datetime

    symbol: str
    side: str

    entry_price: float

    ai_score: int
    threshold: int
    market_regime: str

    context: dict[str, Any] | None = None

    tp1: float | None = None
    tp2: float | None = None
    tp3: float | None = None

    stop_loss: float | None = None

    status: str = "OPEN"

    result: str | None = None