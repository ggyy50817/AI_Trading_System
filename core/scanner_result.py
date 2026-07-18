"""ScannerResult — Scanner domain output contract.

``ScannerResult`` is the data contract produced by the Scanner domain.
It is a plain data container only and contains no business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ScannerResult:
    symbol: str
    side: str
    timestamp: datetime

    ai_score: int
    threshold: int
    market_regime: str

    context: dict[str, Any]

    order_result: Any
