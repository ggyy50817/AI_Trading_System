from __future__ import annotations

from collections.abc import Iterator

from decision_dataset.reader import iter_records


def replay() -> Iterator[dict]:
    """Replay every decision from the dataset."""

    for record in iter_records():
        yield record