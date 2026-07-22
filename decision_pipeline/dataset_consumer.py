"""Decision Dataset Consumer.

Append every TradingDecision to a JSON Lines dataset.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.trading_decision import TradingDecision

DATASET_DIR = Path("decision_dataset")
DATASET_FILE = DATASET_DIR / "decisions.jsonl"


def consume(decision: TradingDecision) -> None:
    """Append one TradingDecision to the dataset."""

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "schema_version": 1,
        **decision,
    }

    with DATASET_FILE.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")