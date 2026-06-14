"""Unit tests for BalansunActionNodeCoordinator."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from tests.unit.balansun_import import load_action_node_coordinator, load_const

coordinator_mod = load_action_node_coordinator()
const = load_const()
BalansunActionNodeCoordinator = coordinator_mod.BalansunActionNodeCoordinator
from homeassistant.exceptions import HomeAssistantError, UpdateFailed
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


class _RecordingSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append(("GET", url, kwargs.get("json")))
        if url.endswith("/api/v1/action/state"):
            return _FakeResponse(
                200,
                {"pilot_wire_order": "confort", "control_mode": "auto", "supported_orders": ["confort", "eco"]},
            )
        if url.endswith("/api/v1/health"):
            return _FakeResponse(200, {"role": "action_node", "wiring_profile": "r2_full_3relay"})
        return _FakeResponse(404, {"error": "not_found"})

    def request(self, method: str, url: str, **kwargs: Any) -> _FakeResponse:
        self.calls.append((method, url, kwargs.get("json")))
        if kwargs.get("json") == {"pilot_wire_order": "eco"}:
            return _FakeResponse(200, {"pilot_wire_order": "eco", "control_mode": "manual"})
        return _FakeResponse(200, {})


def _make_coordinator(session: _RecordingSession) -> BalansunActionNodeCoordinator:
    hass = MagicMock()
    entry = MagicMock()
    entry.data = {CONF_HOST: "http://192.168.4.1", CONF_API_TOKEN: "tok"}
    entry.options = {}
    coord = BalansunActionNodeCoordinator(hass, entry)
    coord._session = session  # noqa: SLF001
    return coord


def test_async_update_data_polls_action_and_health() -> None:
    session = _RecordingSession()
    coord = _make_coordinator(session)

    async def run() -> dict[str, Any]:
        return await coord._async_update_data()

    data = asyncio.run(run())
    assert "action" in data
    assert data["action"]["pilot_wire_order"] == "confort"
    assert data["health"]["role"] == "action_node"
    get_urls = [url for method, url, _ in session.calls if method == "GET"]
    assert any(u.endswith("/api/v1/action/state") for u in get_urls)
    assert any(u.endswith("/api/v1/health") for u in get_urls)


def test_async_set_pilot_order_puts_command() -> None:
    session = _RecordingSession()
    coord = _make_coordinator(session)
    coord.async_request_refresh = MagicMock(return_value=asyncio.sleep(0))  # type: ignore[method-assign]

    async def run() -> None:
        await coord.async_set_pilot_order("eco")

    asyncio.run(run())
    puts = [(m, u, body) for m, u, body in session.calls if m == "PUT"]
    assert len(puts) == 1
    assert puts[0][1].endswith("/api/v1/action/command")
    assert puts[0][2] == {"pilot_wire_order": "eco"}


def test_get_json_401_raises_update_failed() -> None:
    session = MagicMock()

    def get(url: str, **kwargs: Any) -> _FakeResponse:
        return _FakeResponse(401, {"error": "invalid_auth"})

    session.get = get
    coord = _make_coordinator(session)

    async def run() -> None:
        await coord._get_json("/api/v1/action/state")

    with pytest.raises(UpdateFailed, match="invalid_auth"):
        asyncio.run(run())


def test_request_401_raises_home_assistant_error() -> None:
    session = MagicMock()
    session.request = MagicMock(return_value=_FakeResponse(401, {}))
    coord = _make_coordinator(session)

    async def run() -> None:
        await coord._request("PUT", "/api/v1/action/command", json={"pilot_wire_order": "eco"})

    with pytest.raises(HomeAssistantError, match="invalid_auth"):
        asyncio.run(run())


def test_action_state_empty_when_no_data() -> None:
    coord = _make_coordinator(_RecordingSession())
    coord.data = None
    assert coord.action_state == {}
