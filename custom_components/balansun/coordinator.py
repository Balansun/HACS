"""Poll Balansun REST API."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .connection import scan_interval_seconds
from .const import (
    CONF_API_TOKEN,
    CONF_HOST,
    DOMAIN,
    MODE_REST_ONLY,
    POST_WRITE_REFRESH_DELAY_SEC,
)
from .entity_registry import capability_enabled, read_binary_value, read_snapshot_key
from .events_logic import MqttHaEventInput, fired_subtypes, mqtt_ha_events_logic_detect
from .integration_mode import configured_mode
from .poll_availability import PollFailureTracker
from .safety_lockout import safety_lockout_active, safety_lockout_reasons

_LOGGER = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)

_POLL_PATHS: tuple[tuple[str, bool], ...] = (
    ("/api/v1/measurements", True),
    ("/api/v1/device", True),
    ("/api/v1/state", False),
    ("/api/v1/health", False),
    ("/api/v1/config", False),
    ("/api/v1/telemetry/snapshot", False),
    ("/api/v1/sources", False),
    ("/api/v1/sources/diagnostics", False),
    ("/api/v1/actions/config", False),
)


@dataclass
class _EventPrev:
    surplus_active: bool = False
    source_stale: bool = False
    site_cap_active: bool = False
    regulation_hunting: bool = False
    vacation_active: bool = False
    action_cap_hit: bool = False
    linky_tariff: str = ""
    safety_lockout_active: bool = False


class BalansunCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch measurements, telemetry snapshot, and device info."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval = scan_interval_seconds(entry.options)
        coordinator_kwargs: dict[str, Any] = {
            "update_interval": timedelta(seconds=interval),
        }
        try:
            super().__init__(
                hass,
                _LOGGER,
                name=DOMAIN,
                config_entry=entry,
                **coordinator_kwargs,
            )
        except TypeError:
            super().__init__(
                hass,
                _LOGGER,
                name=DOMAIN,
                **coordinator_kwargs,
            )
        self._entry = entry
        self._session = async_get_clientsession(hass)
        self._configured_mode = configured_mode(entry)
        self._event_prev = _EventPrev()
        self._poll_failures = PollFailureTracker()
        self._write_refresh_task: asyncio.Task[None] | None = None
        self._apply_entry_data(entry)

    def _apply_entry_data(self, entry: ConfigEntry) -> None:
        self._host = entry.data[CONF_HOST].rstrip("/")
        token = entry.data.get(CONF_API_TOKEN) or ""
        self._token = token if token else None

    def update_from_entry(self, entry: ConfigEntry) -> bool:
        """Apply connection and poll-interval changes. Return True if platforms need reload."""
        new_mode = configured_mode(entry)
        needs_reload = new_mode != self._configured_mode
        self._entry = entry
        self._apply_entry_data(entry)
        self.update_interval = timedelta(seconds=scan_interval_seconds(entry.options))
        self._configured_mode = new_mode
        self._poll_failures = PollFailureTracker()
        return needs_reload

    @property
    def host(self) -> str:
        return self._host

    @property
    def entry(self) -> ConfigEntry:
        return self._entry

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> aiohttp.ClientResponse:
        return await self._session.request(
            method,
            f"{self._host}{path}",
            headers=self._auth_headers(),
            json=json,
            timeout=_REQUEST_TIMEOUT,
        )

    @staticmethod
    def _non_empty_dict(payload: Any) -> dict[str, Any] | None:
        if isinstance(payload, dict) and payload:
            return payload
        return None

    async def _async_get_json(self, path: str, *, required: bool) -> dict[str, Any] | None:
        async with await self._request("GET", path) as resp:
            if resp.status == 503:
                try:
                    payload = await resp.json()
                except (aiohttp.ContentTypeError, ValueError):
                    payload = {}
                if isinstance(payload, dict) and payload.get("error") == "not_ready":
                    prior = self.data if isinstance(self.data, dict) else {}
                    if path == "/api/v1/measurements":
                        health = prior.get("health")
                        if not isinstance(health, dict):
                            health = {}
                        if health.get("telemetry_ready") is False or prior.get("measurements"):
                            _LOGGER.debug(
                                "Keeping stale measurements after 503 not_ready on %s",
                                path,
                            )
                            return None
                    elif not required:
                        return None
            if required:
                resp.raise_for_status()
                payload = await resp.json()
                parsed = self._non_empty_dict(payload)
                if parsed is None:
                    raise UpdateFailed(f"Empty or invalid JSON from {path}")
                return parsed
            if resp.status != 200:
                return None
            payload = await resp.json()
            return self._non_empty_dict(payload)

    @staticmethod
    async def _raise_for_write_response(resp: aiohttp.ClientResponse) -> None:
        if resp.status == 403:
            try:
                payload = await resp.json()
            except (aiohttp.ContentTypeError, ValueError):
                payload = {}
            if isinstance(payload, dict):
                error = str(payload.get("error") or "")
                message = str(
                    payload.get("message") or payload.get("detail") or error
                ).strip()
                if error == "safety_lockout":
                    raise HomeAssistantError(
                        f"Routing disabled: safety lockout. {message}".strip()
                    )
                if error == "capability_disabled":
                    raise HomeAssistantError(
                        f"Capability disabled. {message}".strip()
                    )
        resp.raise_for_status()

    def _ensure_routing_write_allowed(self) -> None:
        if safety_lockout_active(self.data):
            reasons = ", ".join(safety_lockout_reasons(self.data)) or "safety_lockout"
            raise HomeAssistantError(f"Routing disabled: safety lockout ({reasons})")

    @staticmethod
    def _routing_config_keys(body: dict[str, Any]) -> bool:
        from .config_registry import CONFIG_ENTITIES

        routing_keys = {
            spec.config_key or spec.key
            for spec in CONFIG_ENTITIES
            if spec.capability == "surplus_regulation"
        }
        return any(key in routing_keys for key in body)

    def _firmware_capabilities_from_poll(
        self, results: list[dict[str, Any] | None]
    ) -> dict[str, Any]:
        device: dict[str, Any] = {}
        if len(results) > 1 and isinstance(results[1], dict):
            device = results[1]
        elif isinstance(self.data, dict):
            prior = self.data.get("device")
            device = prior if isinstance(prior, dict) else {}
        caps = device.get("capabilities") if isinstance(device.get("capabilities"), dict) else {}
        fc = caps.get("firmware_capabilities")
        return fc if isinstance(fc, dict) else {}

    async def _async_fetch_poll_bundle(self) -> tuple[dict[str, Any], ...]:
        """Sequential GETs — avoids overloading the router HTTP stack after writes."""
        results: list[dict[str, Any] | None] = []
        for path, required in _POLL_PATHS:
            if path == "/api/v1/actions/config":
                fc = self._firmware_capabilities_from_poll(results)
                if fc.get("multi_action") is not True:
                    results.append(None)
                    continue
            payload = await self._async_get_json(path, required=required)
            results.append(payload)
        return tuple(results)

    @staticmethod
    def _section_or_prior(
        new: dict[str, Any] | None, prior: dict[str, Any], key: str
    ) -> dict[str, Any]:
        if isinstance(new, dict) and new:
            return new
        old = prior.get(key)
        return old if isinstance(old, dict) else {}

    def _build_coordinator_data(
        self,
        measurements: dict[str, Any],
        device: dict[str, Any],
        state: dict[str, Any] | None,
        health: dict[str, Any] | None,
        cfg_body: dict[str, Any] | None,
        snapshot: dict[str, Any] | None,
        sources: dict[str, Any] | None,
        sources_diag: dict[str, Any] | None,
        actions_cfg: dict[str, Any] | None,
    ) -> dict[str, Any]:
        prior = self.data if isinstance(self.data, dict) else {}
        state = self._section_or_prior(state, prior, "state")
        health = self._section_or_prior(health, prior, "health")
        snapshot = self._section_or_prior(snapshot, prior, "snapshot")
        sources = self._section_or_prior(sources, prior, "sources")
        sources_diag = self._section_or_prior(sources_diag, prior, "sources_diagnostics")
        actions_cfg_merged = self._section_or_prior(actions_cfg, prior, "actions_config")
        if isinstance(cfg_body, dict) and cfg_body:
            config = cfg_body.get("config", cfg_body)
            if not isinstance(config, dict):
                config = {}
        else:
            config = prior.get("config") if isinstance(prior.get("config"), dict) else {}
        actions_config = actions_cfg_merged if isinstance(actions_cfg_merged, dict) else {}
        return {
            "measurements": measurements,
            "device": device,
            "state": state,
            "health": health,
            "config": config,
            "snapshot": snapshot,
            "sources": sources,
            "sources_diagnostics": sources_diag,
            "actions_config": actions_config,
        }

    async def async_request_refresh_after_write(
        self, *, delay_sec: float | None = None
    ) -> None:
        """Debounced refresh after REST write (delay + sequential poll)."""
        if self._write_refresh_task is not None and not self._write_refresh_task.done():
            self._write_refresh_task.cancel()
        wait = (
            POST_WRITE_REFRESH_DELAY_SEC
            if delay_sec is None
            else max(0.0, float(delay_sec))
        )
        self._write_refresh_task = self.hass.async_create_task(
            self._async_refresh_after_write(wait)
        )

    async def _async_refresh_after_write(self, delay_sec: float) -> None:
        try:
            await asyncio.sleep(delay_sec)
            await self.async_request_refresh()
        except asyncio.CancelledError:
            pass

    async def async_patch_config(self, body: dict[str, Any]) -> None:
        if self._routing_config_keys(body):
            self._ensure_routing_write_allowed()
        async with await self._request("PATCH", "/api/v1/config", json=body) as resp:
            await self._raise_for_write_response(resp)

    async def async_post_mqtt_discover(self) -> None:
        async with await self._request("POST", "/api/v1/mqtt/discover") as resp:
            await self._raise_for_write_response(resp)

    async def async_post_triac_override(self, command: str) -> None:
        self._ensure_routing_write_allowed()
        if not capability_enabled(self.data, "surplus_regulation"):
            _LOGGER.debug("skip triac override: surplus_regulation cap disabled")
            return
        async with await self._request(
            "POST", "/api/v1/triac/override", json={"command": command}
        ) as resp:
            await self._raise_for_write_response(resp)

    async def async_post_action_override(
        self, idx: int, state: str, *, triac_open_percent: int = 0
    ) -> None:
        self._ensure_routing_write_allowed()
        if not capability_enabled(self.data, "surplus_regulation"):
            _LOGGER.debug("skip action override: surplus_regulation cap disabled")
            return
        if idx >= 1 and not capability_enabled(self.data, "multi_action"):
            _LOGGER.debug("skip action override: multi_action cap disabled")
            return
        body: dict[str, Any] = {"state": state}
        if triac_open_percent:
            body["triac_open_percent"] = triac_open_percent
        async with await self._request(
            "POST", f"/api/v1/actions/{idx}/override", json=body
        ) as resp:
            await self._raise_for_write_response(resp)

    async def async_post_status_led_test(self, body: dict[str, Any]) -> None:
        async with await self._request(
            "POST", "/api/v1/hardware/status-led/test", json=body
        ) as resp:
            await self._raise_for_write_response(resp)

    async def async_post_self_test_run(self) -> None:
        async with await self._request("POST", "/api/v1/health/self-test/run") as resp:
            await self._raise_for_write_response(resp)

    async def async_post_system_reboot(self) -> None:
        async with await self._request("POST", "/api/v1/system/reboot") as resp:
            await self._raise_for_write_response(resp)

    def _bool_on(self, data: dict[str, Any], key: str) -> bool:
        val = read_binary_value(data, key)
        return bool(val) if val is not None else False

    def _build_event_input(self, data: dict[str, Any]) -> MqttHaEventInput:
        triac = read_snapshot_key(data, "triac_open_percent")
        try:
            triac_n = float(triac) if triac is not None else 0.0
        except (TypeError, ValueError):
            triac_n = 0.0
        cfg = data.get("config") or {}
        m = data.get("measurements") or {}
        linky = str(m.get("linky_tariff") or read_snapshot_key(data, "linky_ltarf") or "")
        return MqttHaEventInput(
            surplus_active=triac_n > 5,
            prev_surplus_active=self._event_prev.surplus_active,
            source_stale=self._bool_on(data, "source_stale"),
            prev_source_stale=self._event_prev.source_stale,
            site_cap_active=self._bool_on(data, "site_cap_active"),
            prev_site_cap_active=self._event_prev.site_cap_active,
            regulation_hunting=self._bool_on(data, "regulation_hunting"),
            prev_regulation_hunting=self._event_prev.regulation_hunting,
            vacation_active=self._bool_on(data, "vacation"),
            prev_vacation_active=self._event_prev.vacation_active,
            action_cap_hit=False,
            prev_action_cap_hit=self._event_prev.action_cap_hit,
            linky_tariff=linky,
            prev_linky_tariff=self._event_prev.linky_tariff,
            safety_lockout_active=safety_lockout_active(data),
            prev_safety_lockout_active=self._event_prev.safety_lockout_active,
        )

    def _store_event_prev(self, inp: MqttHaEventInput) -> None:
        self._event_prev.surplus_active = inp.surplus_active
        self._event_prev.source_stale = inp.source_stale
        self._event_prev.site_cap_active = inp.site_cap_active
        self._event_prev.regulation_hunting = inp.regulation_hunting
        self._event_prev.vacation_active = inp.vacation_active
        self._event_prev.action_cap_hit = inp.action_cap_hit
        self._event_prev.linky_tariff = inp.linky_tariff
        self._event_prev.safety_lockout_active = inp.safety_lockout_active

    @callback
    def _fire_device_events(self, data: dict[str, Any]) -> None:
        if self._configured_mode != MODE_REST_ONLY:
            return
        dev_reg = dr.async_get(self.hass)
        device = dev_reg.async_get_device({(DOMAIN, self._entry.entry_id)})
        if device is None:
            return
        inp = self._build_event_input(data)
        out = mqtt_ha_events_logic_detect(inp)
        self._store_event_prev(inp)
        for subtype in fired_subtypes(out):
            self.hass.bus.async_fire(
                f"{DOMAIN}_device_event",
                {"device_id": device.id, "subtype": subtype},
            )

    def _handle_poll_failure(self, err: Exception) -> dict[str, Any]:
        failures = self._poll_failures.record_failure()
        has_data = bool(self.data)
        if self._poll_failures.should_raise(self._entry.options, has_stored_data=has_data):
            raise UpdateFailed(str(err)) from err
        _LOGGER.debug(
            "Keeping last successful Balansun data after poll failure (%s/%s): %s",
            failures,
            self._entry.options.get("failure_count_until_unavailable"),
            err,
        )
        return self.data

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            bundle = await self._async_fetch_poll_bundle()
        except Exception as err:
            return self._handle_poll_failure(err)
        self._poll_failures.record_success()
        data = self._build_coordinator_data(*bundle)
        self._fire_device_events(data)
        return data
