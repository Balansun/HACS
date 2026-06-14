"""Companion vs rest_only integration mode."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import COMPANION_ENTITY_KEYS, MODE_COMPANION, MODE_REST_ONLY


def configured_mode(entry: ConfigEntry) -> str:
    mode = entry.options.get("integration_mode") or entry.data.get("integration_mode")
    if mode in (MODE_COMPANION, MODE_REST_ONLY):
        return mode
    return MODE_REST_ONLY


def _device_matches_router_uid(device: er.DeviceEntry, device_uid: str) -> bool:
    """True when an MQTT discovery device belongs to this router uid."""
    if device.serial_number == device_uid:
        return True
    for ident in device.identifiers:
        if not ident:
            continue
        if device_uid in ident:
            return True
        if len(ident) == 1 and ident[0] == device_uid:
            return True
    return False


def mqtt_entities_for_device(hass: HomeAssistant, device_uid: str) -> list[er.RegistryEntry]:
    """Return entity registry entries on the MQTT integration for this router uid."""
    reg = er.async_get(hass)
    out: list[er.RegistryEntry] = []
    matched_device_ids: set[str] = set()
    for dev_id, device in reg.devices.items():
        if _device_matches_router_uid(device, device_uid):
            matched_device_ids.add(dev_id)

    for ent in reg.entities.values():
        if ent.platform != "mqtt":
            continue
        if ent.device_id and ent.device_id in matched_device_ids:
            out.append(ent)
    return out


def detect_mqtt_present(hass: HomeAssistant, device_uid: str) -> bool:
    return len(mqtt_entities_for_device(hass, device_uid)) > 0


def effective_mode(hass: HomeAssistant, entry: ConfigEntry, device_uid: str | None) -> str:
    mode = configured_mode(entry)
    if mode == MODE_REST_ONLY:
        return MODE_REST_ONLY
    if device_uid and detect_mqtt_present(hass, device_uid):
        return MODE_COMPANION
    return MODE_REST_ONLY


def entity_enabled_for_mode(key: str, mode: str) -> bool:
    if mode == MODE_REST_ONLY:
        return True
    return key in COMPANION_ENTITY_KEYS
