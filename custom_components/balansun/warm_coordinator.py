"""Poll Balansun Warm fil pilote REST API."""

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


def _normalise_warm_channels(warm: dict[str, Any]) -> list[dict[str, Any]]:
    """Return per-channel state dicts (legacy flat state → channel 0)."""
    channels = warm.get("channels")
    if isinstance(channels, list) and channels:
        out: list[dict[str, Any]] = []
        for row in channels:
            if isinstance(row, dict):
                out.append(row)
        return out
    if warm.get("pilot_wire_order") is not None:
        legacy = dict(warm)
        legacy.setdefault("channel_id", 0)
        legacy.setdefault("enabled", True)
        return [legacy]
    return []


class BalansunWarmCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Warm actuator state for a dedicated config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = scan_interval_seconds(entry.options)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_warm",
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
            warm = await self._get_json("/api/v1/warm/state")
            device = await self._get_json("/api/v1/device")
            channels = _normalise_warm_channels(warm)
            if not channels:
                try:
                    summary = await self._get_json("/api/v1/warm/channels")
                    raw = summary.get("channels")
                    if isinstance(raw, list):
                        channels = [c for c in raw if isinstance(c, dict)]
                except UpdateFailed:
                    pass
            return {"warm": warm, "device": device, "channels": channels}
        except aiohttp.ClientError as err:
            raise UpdateFailed(str(err)) from err

    def warm_channels(self) -> list[dict[str, Any]]:
        data = self.data or {}
        channels = data.get("channels")
        if isinstance(channels, list):
            return [c for c in channels if isinstance(c, dict)]
        return _normalise_warm_channels(data.get("warm") or {})

    async def async_set_pilot_order(self, order: str, channel_id: int = 0) -> None:
        warm = self.data.get("warm") if self.data else {}
        triac = 0
        if isinstance(warm, dict) and channel_id == 0 and "triac_open_percent" in warm:
            triac = int(warm.get("triac_open_percent") or 0)
        else:
            for ch in self.warm_channels():
                if int(ch.get("channel_id", 0)) == channel_id:
                    triac = int(ch.get("triac_open_percent") or 0)
                    break
        path = (
            f"/api/v1/warm/channels/{channel_id}/command"
            if len(self.warm_channels()) > 1 or channel_id > 0
            else "/api/v1/warm/command"
        )
        await self._request(
            "PUT",
            path,
            json={"pilot_wire_order": order, "triac_open_percent": triac},
        )
        await self.async_request_refresh()
