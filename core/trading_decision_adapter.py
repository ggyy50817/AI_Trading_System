"""TradingDecision adapters — convert module outputs into the shared contract.

This module is responsible for adapting outputs from individual system
modules into the ``TradingDecision`` V1 contract defined in
``core.trading_decision``.

Planned adapters:

    - from_scanner  — Scanner / live scan path
    - from_replay   — Replay engine path
    - from_research — Research / decision-engine path
    - from_shadow   — Shadow Trading path

Adapters must only perform structural mapping into ``TradingDecision``.
They must not contain trading business logic (scoring, risk, entry rules,
or order execution).

All adapter implementations are stubs in V1 and raise
``NotImplementedError`` until wired by a later change.
"""

from __future__ import annotations

from typing import Any

from core.trading_decision import TradingDecision


def from_scanner(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Scanner outputs into a TradingDecision."""
    raise NotImplementedError("from_scanner is not implemented yet")


def from_replay(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Replay outputs into a TradingDecision."""
    raise NotImplementedError("from_replay is not implemented yet")


def from_research(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Research outputs into a TradingDecision."""
    raise NotImplementedError("from_research is not implemented yet")


def from_shadow(*args: Any, **kwargs: Any) -> TradingDecision:
    """Adapt Shadow Trading outputs into a TradingDecision."""
    raise NotImplementedError
