"""TradingDecision adapters — convert module outputs into the shared contract.

This module is responsible for adapting outputs from individual system
modules into the ``TradingDecision`` V1 contract defined in
``core.trading_decision``.

Adapters:

    - from_scanner  — Scanner / live scan path
    - from_replay   — Replay engine path (stub)
    - from_research — Research / decision-engine path (stub)
    - from_shadow   — Shadow Trading path (stub)

Adapters must only perform structural mapping into ``TradingDecision``.
They must not contain trading business logic (scoring, risk, entry rules,
or order execution).
"""

from __future__ import annotations

from typing import Any

from core.scanner_result import ScannerResult
from core.trading_decision import TradingDecision


def from_scanner(scanner_result: ScannerResult) -> TradingDecision:
    """Map a ScannerResult into a TradingDecision. No business logic."""
    context = scanner_result.context

    return TradingDecision(
        timestamp=scanner_result.timestamp.isoformat(),
        symbol=str(scanner_result.symbol or ""),
        side=str(scanner_result.side or ""),
        source="scanner",
        price=context.get("price"),
        long_score=context.get("long_score"),
        short_score=context.get("short_score"),
        ai_score=scanner_result.ai_score,
        market_regime=scanner_result.market_regime,
        signal_ok=context.get("signal_ok", False),
        blocked=context.get("blocked", False),
        block_reason=context.get("block_reason"),
        order_submitted=context.get("order_submitted", False),
        order_success=context.get("order_success"),
        order_result=scanner_result.order_result,
        reason=context.get("reason"),
        skip_reason=context.get("skip_reason"),
    )


def from_replay(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Replay outputs into a TradingDecision."""
    raise NotImplementedError("from_replay is not implemented yet")


def from_research(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Research outputs into a TradingDecision."""
    raise NotImplementedError("from_research is not implemented yet")


def from_shadow(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Shadow Trading outputs into a TradingDecision."""
    raise NotImplementedError
