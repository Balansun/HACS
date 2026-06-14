"""Diagnostics panel."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE,
    CONF_SKIP_UNAVAILABLE_ON_FAILURE,
    DOMAIN,
)
from .entity_registry import firmware_capabilities, read_snapshot_key
from .integration_mode import effective_mode
from .safety_lockout import safety_lockout_active, safety_lockout_reasons


def _redact(entry: ConfigEntry) -> dict:
    return {
        "host": entry.data.get("host"),
        "has_token": bool(entry.data.get("api_token")),
        "integration_mode": entry.options.get("integration_mode"),
        "scan_interval": entry.options.get("scan_interval"),
        "skip_unavailable_on_failure": entry.options.get(CONF_SKIP_UNAVAILABLE_ON_FAILURE),
        "failure_count_until_unavailable": entry.options.get(
            CONF_FAILURE_COUNT_UNTIL_UNAVAILABLE
        ),
    }


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    coordinator = getattr(entry, "runtime_data", None) or hass.data[DOMAIN][entry.entry_id]
    device = coordinator.data.get("device") or {}
    if not isinstance(device, dict):
        device = {}
    uid = device.get("device_uid")
    mode = effective_mode(hass, entry, uid)
    diag = coordinator.data.get("measurements", {}).get("diagnostics", {})
    data = coordinator.data if isinstance(coordinator.data, dict) else {}
    health = data.get("health") if isinstance(data.get("health"), dict) else {}
    return {
        **_redact(entry),
        "effective_mode": mode,
        "router_name": device.get("router_name"),
        "device_uid": uid,
        "firmware_version": device.get("firmware_version"),
        "product_profile": read_snapshot_key(data, "product_profile"),
        "meter_pack": read_snapshot_key(data, "meter_pack"),
        "firmware_capabilities": firmware_capabilities(data),
        "device_lifecycle": read_snapshot_key(data, "device_lifecycle"),
        "safety_lockout_active": safety_lockout_active(data),
        "safety_lockout_reasons": safety_lockout_reasons(data),
        "telemetry_ready": health.get("telemetry_ready"),
        "self_test": health.get("self_test") if isinstance(health.get("self_test"), dict) else {},
        "last_update_success": coordinator.last_update_success,
        "measurements_diagnostics": diag if isinstance(diag, dict) else {},
        "snapshot_keys": list((coordinator.data.get("snapshot") or {}).keys()),
    }
