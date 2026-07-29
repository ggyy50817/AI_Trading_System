"""
Opportunity Logger V3

Write OpportunityRecord objects into JSONL.

One OpportunityRecord
        ↓
One JSON line

Responsibilities

- Write OpportunityRecord
- Never interrupt Scanner
- No business logic
- No trading
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.opportunity_record import OpportunityRecord

LOG_DIR = Path("runtime") / "opportunity"
LOG_FILE = LOG_DIR / "opportunity_log.jsonl"


def _json_default(obj):
    """
    JSON serializer for unsupported types.
    """

    if isinstance(obj, datetime):
        return obj.isoformat()

    return str(obj)


def log_opportunity(record: OpportunityRecord) -> None:
    """
    Append one OpportunityRecord into JSONL.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:

        with LOG_FILE.open("a", encoding="utf-8") as f:

            json.dump(
                asdict(record),
                f,
                ensure_ascii=False,
                default=_json_default,
            )

            f.write("\n")

    except Exception as e:
        print(f"[Opportunity Logger] {e}")