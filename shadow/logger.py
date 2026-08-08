"""
Shadow Logger V1

Persist ShadowTrade records for research and replay.

Responsibilities

- Receive ShadowTrade.
- Append one JSON record per shadow trade.
- Create runtime/shadow automatically.
- No trading.
- No API calls.
- No validation logic.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from core.shadow_trade import ShadowTrade


SHADOW_LOG_PATH = Path("runtime/shadow/shadow_trades.jsonl")


def log_shadow_trade(trade: ShadowTrade) -> None:
    """
    Append one ShadowTrade to the shadow dataset.
    """

    SHADOW_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = asdict(trade)

    record["created_at"] = trade.created_at.isoformat()

    with SHADOW_LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )