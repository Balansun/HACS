"""Unit tests for REST poll availability options."""

from __future__ import annotations

import pytest

from tests.unit.balansun_import import load_const, load_poll_availability

poll_availability = load_poll_availability()
const = load_const()

CONF_SKIP_UNAVAILABLE_ON_FAILURE = const.CONF_SKIP_UNAVAILABLE_ON_FAILURE
CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE = const.CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE
DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE = const.DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE
DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE = const.DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE

skip_unavailable_on_failure = poll_availability.skip_unavailable_on_failure
failure_count_until_unavailable = poll_availability.failure_count_until_unavailable
should_raise_update_failed = poll_availability.should_raise_update_failed
PollFailureTracker = poll_availability.PollFailureTracker


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, DEFAULT_SKIP_UNAVAILABLE_ON_FAILURE),
        ({CONF_SKIP_UNAVAILABLE_ON_FAILURE: False}, False),
        ({CONF_SKIP_UNAVAILABLE_ON_FAILURE: True}, True),
    ],
)
def test_skip_unavailable_on_failure(options: dict, expected: bool) -> None:
    assert skip_unavailable_on_failure(options) is expected


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE),
        ({CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE: 0}, 0),
        ({CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE: 3}, 3),
        ({CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE: 9999}, 1000),
        ({CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE: "bad"}, DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE),
    ],
)
def test_failure_count_until_unavailable(options: dict, expected: int) -> None:
    assert failure_count_until_unavailable(options) == expected


@pytest.mark.parametrize(
    ("skip", "failures", "threshold", "has_data", "expected_raise"),
    [
        (False, 1, 10, True, True),
        (True, 1, 10, False, True),
        (True, 5, 10, True, False),
        (True, 10, 10, True, True),
        (True, 99, 0, True, False),
        (True, 1, 0, True, False),
    ],
)
def test_should_raise_update_failed(
    skip: bool, failures: int, threshold: int, has_data: bool, expected_raise: bool
) -> None:
    assert (
        should_raise_update_failed(
            skip_unavailable=skip,
            consecutive_failures=failures,
            failure_threshold=threshold,
            has_stored_data=has_data,
        )
        is expected_raise
    )


def test_poll_failure_tracker_resets_on_success() -> None:
    tracker = PollFailureTracker()
    tracker.record_failure()
    tracker.record_failure()
    assert tracker.consecutive_failures == 2
    tracker.record_success()
    assert tracker.consecutive_failures == 0


def test_poll_failure_tracker_default_options_tolerates_burst() -> None:
    tracker = PollFailureTracker()
    options = {}
    for _ in range(DEFAULT_FAILURE_COUNT_UNTIL_UNAVAILABLE - 1):
        tracker.record_failure()
    assert tracker.should_raise(options, has_stored_data=True) is False
    tracker.record_failure()
    assert tracker.should_raise(options, has_stored_data=True) is True


def test_poll_failure_tracker_threshold_zero_never_raises() -> None:
    tracker = PollFailureTracker()
    options = {CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE: 0}
    for _ in range(50):
        tracker.record_failure()
    assert tracker.should_raise(options, has_stored_data=True) is False
