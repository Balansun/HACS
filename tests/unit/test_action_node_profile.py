"""Unit tests for async_fetch_product_profile action node detection."""

from __future__ import annotations

import asyncio
from typing import Any

from tests.unit.balansun_import import load_connection

connection = load_connection()
async_fetch_product_profile = connection.async_fetch_product_profile


class _FakeResponse:
    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self._body = body

    async def __aenter__(self) -> _FakeResponse:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def json(self) -> Any:
        return self._body


class _FakeSession:
    def __init__(self, routes: dict[str, tuple[int, Any]]) -> None:
        self._routes = routes

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        for path, payload in self._routes.items():
            if url.endswith(path):
                status, body = payload
                return _FakeResponse(status, body)
        return _FakeResponse(404, {})


def test_fetch_product_profile_action_node_from_health() -> None:
    session = _FakeSession(
        {"/api/v1/health": (200, {"ok": True, "role": "action_node"})}
    )

    async def run() -> str | None:
        return await async_fetch_product_profile(session, "http://192.168.4.1", None)

    assert asyncio.run(run()) == "action_node"


def test_fetch_product_profile_falls_back_to_device() -> None:
    session = _FakeSession(
        {
            "/api/v1/health": (200, {"ok": True, "role": "router"}),
            "/api/v1/device": (
                200,
                {"capabilities": {"product_profile": "warm_actuator"}},
            ),
        }
    )

    async def run() -> str | None:
        return await async_fetch_product_profile(session, "http://192.168.1.42", None)

    assert asyncio.run(run()) == "warm_actuator"


def test_fetch_product_profile_malformed_returns_none() -> None:
    session = _FakeSession(
        {
            "/api/v1/health": (500, {}),
            "/api/v1/device": (200, "not-json-object"),
        }
    )

    async def run() -> str | None:
        return await async_fetch_product_profile(session, "http://192.168.1.42", None)

    assert asyncio.run(run()) is None
