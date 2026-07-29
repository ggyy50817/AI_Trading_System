from __future__ import annotations

REQUIRED_FIELDS = [
    "schema_version",
    "timestamp",
    "symbol",
    "side",
    "ai_score",
]


def validate(record: dict) -> list[str]:
    """Return a list of validation errors."""

    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing field: {field}")

    return errors