"""REST poll failure handling (options-driven availability)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    CONF_SKIP_UNAVAILABLE_ON_FAILURE,
    DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE,
    MAX_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    MIN_FAILURE_COUNT_UNTIL_UNAVAILABLE,
)


def skip_unavailable_on_failure(options: dict[str, Any]) -> bool:
    raw = options.get(
        CONF_SKIP_UNAVAILABLE_ON_FAILURE, DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE
    )
    return bool(raw)


def failure_count_until_unavailable(options: dict[str, Any]) -> int:
    raw = options.get(
        CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
        DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    )
    try:
        count = int(raw)
    except (TypeError, ValueError):
        count = DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE
    return max(
        MIN_FAILURE_COUNT_UNTIL_UNAVAILABLE,
        min(MAX_FAILURE_COUNT_UNTIL_UNAVAILABLE, count),
    )


def should_raise_update_failed(
    *,
    skip_unavailable: bool,
    consecutive_failures: int,
    failure_threshold: int,
    has_stored_data: bool,
) -> bool:
    """True when the coordinator should raise UpdateFailed (entities unavailable)."""
    if not has_stored_data:
        return True
    if not skip_unavailable:
        return True
    if failure_threshold == 0:
        return False
    return consecutive_failures >= failure_threshold


@dataclass
class PollFailureTracker:
    """Counts consecutive failed polls for availability options."""

    consecutive_failures: int = 0

    def record_success(self) -> None:
        self.consecutive_failures = 0

    def record_failure(self) -> int:
        self.consecutive_failures += 1
        return self.consecutive_failures

    def should_raise(self, options: dict[str, Any], *, has_stored_data: bool) -> bool:
        return should_raise_update_failed(
            skip_unavailable=skip_unavailable_on_failure(options),
            consecutive_failures=self.consecutive_failures,
            failure_threshold=failure_count_until_unavailable(options),
            has_stored_data=has_stored_data,
        )
