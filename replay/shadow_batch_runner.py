"""
Shadow Batch Runner V1

Run Shadow Replay records through historical future klines
and Shadow Outcome Engine.

No live orders.
No modification of Strategy A.
"""

from __future__ import annotations

import json
from pathlib import Path

from replay.shadow_adapter import iter_replay_records
from replay.shadow_historical_data import load_shadow_future_klines
from replay.shadow_outcome_engine import simulate_shadow_outcome


OUTPUT_PATH = Path("runtime/shadow/shadow_outcomes.jsonl")
NOTIONAL = 100.0


def run_shadow_batch() -> list[dict]:
    records = list(iter_replay_records())
    outcomes: list[dict] = []

    print("=" * 60)
    print("Shadow Batch Replay V1")
    print("=" * 60)
    print("Records:", len(records))

    for index, record in enumerate(records, start=1):
        symbol = record.get("symbol")
        side = record.get("side")
        timestamp = record.get("timestamp")

        print(
            f"[{index}/{len(records)}] "
            f"{symbol} {side} {timestamp}"
        )

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

                outcome["timestamp"] = timestamp
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

            print("  ERROR:", exc)

        outcomes.append(outcome)

        print(
            "  ->",
            outcome.get("status"),
            outcome.get("result"),
            "PnL=",
            outcome.get("realized_pnl"),
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for outcome in outcomes:
            file.write(
                json.dumps(
                    outcome,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

    print()
    print("=" * 60)
    print("Shadow Batch Finished")
    print("Total:", len(outcomes))
    print("Output:", OUTPUT_PATH)
    print("=" * 60)

    return outcomes


if __name__ == "__main__":
    run_shadow_batch()
