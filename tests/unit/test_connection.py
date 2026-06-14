"""Unit tests for connection helpers."""

from __future__ import annotations

import pytest

from tests.unit.balansun_import import load_connection, load_const, load_device_info

connection = load_connection()
device_info = load_device_info()
const = load_const()
normalize_host = connection.normalize_host
scan_interval_seconds = connection.scan_interval_seconds
resolve_api_token = connection.resolve_api_token
title_from_public = device_info.title_from_public
CONF_SCAN_INTERVAL = const.CONF_SCAN_INTERVAL
DEFAULT_SCAN_INTERVAL = const.DEFAULT_SCAN_INTERVAL
MIN_SCAN_INTERVAL = const.MIN_SCAN_INTERVAL
MAX_SCAN_INTERVAL = const.MAX_SCAN_INTERVAL


def test_normalize_host_strips_slash() -> None:
    assert normalize_host("http://192.168.1.42/") == "http://192.168.1.42"


def test_normalize_host_requires_scheme() -> None:
    with pytest.raises(ValueError):
        normalize_host("192.168.1.42")


def test_normalize_host_empty() -> None:
    with pytest.raises(ValueError):
        normalize_host("   ")


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ({}, DEFAULT_SCAN_INTERVAL),
        ({CONF_SCAN_INTERVAL: 60}, 60),
        ({CONF_SCAN_INTERVAL: 10}, 10),
        ({CONF_SCAN_INTERVAL: 1}, 1),
        ({CONF_SCAN_INTERVAL: 0}, MIN_SCAN_INTERVAL),
        ({CONF_SCAN_INTERVAL: 300}, 300),
        ({CONF_SCAN_INTERVAL: 400}, MAX_SCAN_INTERVAL),
        ({CONF_SCAN_INTERVAL: 200}, 200),
        ({CONF_SCAN_INTERVAL: "bad"}, DEFAULT_SCAN_INTERVAL),
    ],
)
def test_scan_interval_seconds(options: dict, expected: int) -> None:
    assert scan_interval_seconds(options) == expected


def test_normalize_host_https() -> None:
    assert normalize_host("https://helio.local/") == "https://helio.local"


@pytest.mark.parametrize(
    ("token_raw", "existing", "reconfigure", "expected"),
    [
        (None, "keep-me", True, "keep-me"),
        ("", "keep-me", True, "keep-me"),
        ("   ", "keep-me", True, "keep-me"),
        ("new-token", "keep-me", True, "new-token"),
        ("", None, True, None),
        ("fresh", None, False, "fresh"),
        (None, None, False, None),
    ],
)
def test_resolve_api_token(
    token_raw, existing: str | None, reconfigure: bool, expected: str | None
) -> None:
    assert (
        resolve_api_token(
            token_raw, existing_token=existing, reconfigure=reconfigure
        )
        == expected
    )


def test_title_from_public_router_name() -> None:
    body = {"device": {"router_name": "Lab Router"}}
    assert title_from_public(body, "http://192.168.2.159") == "Lab Router"


def test_title_from_public_fallback_host() -> None:
    assert title_from_public({}, "http://192.168.2.159") == "Balansun (http://192.168.2.159)"
