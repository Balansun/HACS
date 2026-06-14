"""Poll Balansun ESP8266 fil pilote action node REST API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .connection import scan_interval_seconds
from .const import CONF_API_TOKEN, CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)
_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class BalansunActionNodeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch action node fil pilote state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = scan_interval_seconds(entry.options)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_action_node",
            update_interval=__import__("datetime").timedelta(seconds=interval),
        )
        self.entry = entry
        self.host = entry.data[CONF_HOST].rstrip("/")
        self._token = (entry.data.get(CONF_API_TOKEN) or "").strip() or None
        self._session = async_get_clientsession(hass)

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    async def _get_json(self, path: str) -> dict[str, Any]:
        async with self._session.get(
            f"{self.host}{path}",
            headers=self._headers(),
            timeout=_REQUEST_TIMEOUT,
        ) as resp:
            if resp.status == 401:
                raise UpdateFailed("invalid_auth")
            if resp.status != 200:
                raise UpdateFailed(f"http_{resp.status}")
            body = await resp.json()
            return body if isinstance(body, dict) else {}

    async def _request(self, method: str, path: str, **kwargs: Any) -> None:
        headers = {**self._headers(), **kwargs.pop("headers", {})}
        async with self._session.request(
            method,
            f"{self.host}{path}",
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
            **kwargs,
        ) as resp:
            if resp.status == 401:
                raise HomeAssistantError("invalid_auth")
            if resp.status not in (200, 204):
                raise HomeAssistantError(f"http_{resp.status}")

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            state = await self._get_json("/api/v1/action/state")
            health = await self._get_json("/api/v1/health")
            return {"action": state, "health": health}
        except aiohttp.ClientError as err:
            raise UpdateFailed(str(err)) from err

    @property
    def action_state(self) -> dict[str, Any]:
        data = self.data or {}
        body = data.get("action")
        return body if isinstance(body, dict) else {}

    async def async_set_pilot_order(self, order: str) -> None:
        await self._request(
            "PUT",
            "/api/v1/action/command",
            json={"pilot_wire_order": order},
        )
        await self.async_request_refresh()
