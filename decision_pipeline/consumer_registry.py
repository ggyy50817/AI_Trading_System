"""Decision Pipeline Consumer Registry.

Single place to register all consumers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.trading_decision import TradingDecision
from decision_pipeline.logging_consumer import consume as logging_consumer
from decision_pipeline.dataset_consumer import consume as dataset_consumer

Consumer = Callable[[TradingDecision], Any]

CONSUMERS: list[Consumer] = [
    logging_consumer,
    dataset_consumer,
]