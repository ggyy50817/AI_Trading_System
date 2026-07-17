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

from datetime import datetime, timezone
from typing import Any

from core.trading_decision import TradingDecision


def from_scanner(scanner_result: dict[str, Any]) -> TradingDecision:
    """Map a Scanner result dict into a TradingDecision. No business logic."""
    timestamp = scanner_result.get("timestamp")
    if not timestamp:
        timestamp = datetime.now(timezone.utc).isoformat()

    return TradingDecision(
        timestamp=str(timestamp),
        symbol=str(scanner_result.get("symbol") or ""),
        side=str(scanner_result.get("side") or ""),
        source="scanner",
        price=scanner_result.get("price"),
        long_score=scanner_result.get("long_score"),
        short_score=scanner_result.get("short_score"),
        ai_score=scanner_result.get("ai_score"),
        market_regime=scanner_result.get("market_regime"),
        signal_ok=scanner_result.get("signal_ok", False),
        blocked=scanner_result.get("blocked", False),
        block_reason=scanner_result.get("block_reason"),
        order_submitted=scanner_result.get("order_submitted", False),
        order_success=scanner_result.get("order_success"),
        order_result=scanner_result.get("order_result"),
        reason=scanner_result.get("reason"),
        skip_reason=scanner_result.get("skip_reason"),
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
