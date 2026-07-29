from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

DATASET_DIR = Path("decision_dataset")
DATASET_FILE = DATASET_DIR / "decisions.jsonl"


def iter_records() -> Iterator[dict]:
    """Yield every decision record from the dataset."""

    if not DATASET_FILE.exists():
        return

    with DATASET_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_all() -> list[dict]:
    """Load every decision into memory."""

    return list(iter_records())


def load_last(n: int) -> list[dict]:
    """Return the latest n records."""

    records = load_all()
    return records[-n:]


def count() -> int:
    """Return total number of records."""

    return sum(1 for _ in iter_records())