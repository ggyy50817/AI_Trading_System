"""Opportunity Logger V1 — append opportunities as JSON Lines."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_DIR: Path = Path("runtime") / "opportunity"
LOG_FILE: Path = LOG_DIR / "opportunity_log.jsonl"


def log_opportunity(data: dict[str, Any]) -> None:
    """Append one opportunity record (with ISO timestamp) to the JSONL log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data,
    }

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Opportunity Logger Error: {e}")
