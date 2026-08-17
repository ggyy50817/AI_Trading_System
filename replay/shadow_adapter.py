"""
Shadow Replay Adapter V1

Bridge between Shadow Trading dataset and Replay subsystem.

Responsibilities

- Read runtime/shadow/shadow_trades.jsonl.
- Convert ShadowTrade records into replay-compatible records.
- Validate basic record structure.
- Never modify live trading logic.
- Never submit exchange orders.
- Never modify the original shadow dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


SHADOW_DATASET_PATH = Path("runtime/shadow/shadow_trades.jsonl")


def iter_shadow_records(
    path: Path = SHADOW_DATASET_PATH,
) -> Iterator[dict]:
    """
    Yield valid JSON records from the Shadow dataset.

    Empty lines are ignored.
    Invalid JSON lines are skipped.
    """

    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(
                    f"[SHADOW REPLAY] "
                    f"Invalid JSON at line {line_number}, skipped"
                )
                continue

            yield record


def to_replay_record(shadow_record: dict) -> dict:
    """
    Convert one Shadow record into a replay-compatible observation record.
    """

    return {
        "schema_version": "shadow_replay_v1",
        "timestamp": shadow_record.get("created_at"),
        "symbol": shadow_record.get("symbol"),
        "side": shadow_record.get("side"),
        "ai_score": shadow_record.get("ai_score"),
        "threshold": shadow_record.get("threshold"),
        "market_regime": shadow_record.get("market_regime"),
        "context": shadow_record.get("context"),
        "entry_price": shadow_record.get("entry_price"),
        "tp1": shadow_record.get("tp1"),
        "tp2": shadow_record.get("tp2"),
        "tp3": shadow_record.get("tp3"),
        "stop_loss": shadow_record.get("stop_loss"),
        "status": shadow_record.get("status"),
        "result": shadow_record.get("result"),
        "source": "shadow",
    }


def iter_replay_records(
    path: Path = SHADOW_DATASET_PATH,
) -> Iterator[dict]:
    """
    Yield replay-compatible records converted from Shadow records.
    """

    for shadow_record in iter_shadow_records(path):
        yield to_replay_record(shadow_record)