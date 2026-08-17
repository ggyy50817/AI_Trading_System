"""
Shadow Context Batch Runner V1

Replay only Shadow records containing Context V1 data.

Safety:
- Simulation only
- No live orders
- No Strategy A modification
- Does not overwrite legacy shadow_outcomes.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

from replay.shadow_adapter import iter_replay_records
from replay.shadow_historical_data import load_shadow_future_klines
from replay.shadow_outcome_engine import simulate_shadow_outcome


OUTPUT_PATH = Path(
    "runtime/shadow/shadow_context_outcomes.jsonl"
)

NOTIONAL = 100.0


def run_context_batch() -> list[dict]:
    records = [
        r for r in iter_replay_records()
        if r.get("context")
    ]

    outcomes = []

    print("=" * 70)
    print("Shadow Context Replay V1")
    print("=" * 70)
    print("Context Records:", len(records))

    for i, record in enumerate(records, 1):
        try:
            df = load_shadow_future_klines(
                record,
                interval="15m",
                limit=500,
            )

            if df.empty:
                outcome = {
                    **record,
                    "status": "NO_FUTURE_DATA",
                    "result": None,
                    "realized_pnl": 0.0,
                    "realized_return_pct": 0.0,
                    "events": [],
                }
            else:
                outcome = simulate_shadow_outcome(
                    record,
                    df,
                    NOTIONAL,
                )

                outcome["future_klines"] = len(df)

        except Exception as exc:
            outcome = {
                **record,
                "status": "ERROR",
                "result": None,
                "realized_pnl": 0.0,
                "realized_return_pct": 0.0,
                "events": [],
                "error": str(exc),
            }

        outcomes.append(outcome)

        if i % 25 == 0 or i == len(records):
            print(
                f"Progress {i}/{len(records)}"
            )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        for outcome in outcomes:
            f.write(
                json.dumps(
                    outcome,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

    print()
    print("Finished:", len(outcomes))
    print("Output:", OUTPUT_PATH)

    return outcomes


if __name__ == "__main__":
    run_context_batch()
