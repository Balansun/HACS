"""Unit tests for BalansunCoordinator self-test run."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

from tests.unit.balansun_import import load_const, load_coordinator

coordinator_mod = load_coordinator()
const = load_const()
BalansunCoordinator = coordinator_mod.BalansunCoordinator
CONF_HOST = const.CONF_HOST
CONF_API_TOKEN = const.CONF_API_TOKEN


class _FakeResponse:
    def __init__(self, status: int, body: Any = None) -> None:
        self.status = status
        self._body = body if body is not None else {}

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def json(self) -> Any:
        return self._body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


class _RecordingSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append((method, url, kwargs.get("json")))
        if method == "POST" and url.endswith("/api/v1/health/self-test/run"):
            return _FakeResponse(200, {"ok": True, "running": True})
        return _FakeResponse(404, {"error": "not_found"})


def _make_coordinator(session: _RecordingSession) -> BalansunCoordinator:
    hass = MagicMock()
    entry = MagicMock()
    entry.data = {CONF_HOST: "http://192.168.2.159", CONF_API_TOKEN: "tok"}
    entry.options = {}
    coord = BalansunCoordinator(hass, entry)
    coord._session = session  # noqa: SLF001
    return coord


def test_async_post_self_test_run_posts_health_endpoint() -> None:
    session = _RecordingSession()
    coord = _make_coordinator(session)

    async def run() -> None:
        await coord.async_post_self_test_run()

    asyncio.run(run())
    posts = [(m, u, body) for m, u, body in session.calls if m == "POST"]
    assert len(posts) == 1
    assert posts[0][1].endswith("/api/v1/health/self-test/run")
    assert posts[0][2] is None
