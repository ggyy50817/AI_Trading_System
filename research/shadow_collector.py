"""
Shadow Universe Collector V1

Long-running research-only collector.

Runs Shadow Universe independently from the Strategy A trading loop.

IMPORTANT:
- No exchange orders.
- No VST orders.
- Does not modify Strategy A.
- Research / observation only.
"""

from __future__ import annotations

import time
import traceback
from datetime import datetime

from research.shadow_universe_runner import run_shadow_universe


TOP_N = 100
INTERVAL_SECONDS = 900


def run_collector():
    print("=" * 90)
    print("Shadow Universe Collector V1")
    print("=" * 90)
    print(f"Top N    : {TOP_N}")
    print(f"Interval : {INTERVAL_SECONDS} seconds")
    print()

    while True:
        started_at = datetime.now()

        print()
        print("=" * 90)
        print(
            "Shadow cycle started:",
            started_at.isoformat(
                timespec="seconds"
            ),
        )
        print("=" * 90)

        try:
            result = run_shadow_universe(
                top_n=TOP_N,
            )

            print()
            print(
                "Shadow cycle completed:",
                result,
            )

        except KeyboardInterrupt:
            print()
            print("Shadow Collector stopped.")
            break

        except Exception as exc:
            print()
            print(
                "Shadow Collector error:",
                f"{type(exc).__name__}: {exc}",
            )
            traceback.print_exc()

        print()
        print(
            f"Sleeping {INTERVAL_SECONDS} "
            "seconds before next cycle..."
        )

        time.sleep(
            INTERVAL_SECONDS
        )


if __name__ == "__main__":
    run_collector()
