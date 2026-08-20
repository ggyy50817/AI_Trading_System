"""
Historical BEAR Episode Audit V1

Group consecutive historical BTC BEAR regime buckets
into independent BEAR episodes.

Research only:
- No live trading
- No Strategy A modification
- No automatic parameter changes
- Historical analysis only
"""

from __future__ import annotations

from typing import Any


INTERVAL_MS = 15 * 60 * 1000


def group_bear_episodes(
    bear_events: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """
    Group consecutive 15-minute BEAR buckets into episodes.

    Two BEAR events belong to the same episode when their
    BTC bucket timestamps are exactly one 15m interval apart.
    """

    if not bear_events:
        return []

    ordered = sorted(
        bear_events,
        key=lambda item: int(
            item["bucket_ms"]
        ),
    )

    episodes: list[
        list[dict[str, Any]]
    ] = []

    current_episode = [
        ordered[0]
    ]

    for event in ordered[1:]:

        previous = current_episode[-1]

        previous_bucket = int(
            previous["bucket_ms"]
        )

        current_bucket = int(
            event["bucket_ms"]
        )

        if (
            current_bucket
            - previous_bucket
            == INTERVAL_MS
        ):
            current_episode.append(
                event
            )
        else:
            episodes.append(
                current_episode
            )

            current_episode = [
                event
            ]

    episodes.append(
        current_episode
    )

    return episodes


def episode_summary(
    episode: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Return structural information for one BEAR episode.
    """

    if not episode:
        raise ValueError(
            "Episode cannot be empty"
        )

    ordered = sorted(
        episode,
        key=lambda item: int(
            item["bucket_ms"]
        ),
    )

    start_bucket_ms = int(
        ordered[0]["bucket_ms"]
    )

    end_bucket_ms = int(
        ordered[-1]["bucket_ms"]
    )

    bucket_count = len(
        ordered
    )

    return {
        "start_bucket_ms": (
            start_bucket_ms
        ),
        "end_bucket_ms": (
            end_bucket_ms
        ),
        "bucket_count": (
            bucket_count
        ),
        "duration_minutes": (
            bucket_count * 15
        ),
    }
