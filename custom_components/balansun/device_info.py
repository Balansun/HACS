"""Shared device registry and entity unique_id helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import BalansunCoordinator


def entity_unique_id(entry: ConfigEntry, key: str) -> str:
    """Per-config-entry unique_id so multiple routers do not collide."""
    return f"{entry.entry_id}_{key}"


def _device_payload(coordinator: BalansunCoordinator) -> dict:
    device = coordinator.data.get("device")
    return device if isinstance(device, dict) else {}


_METER_PACK_MODELS: dict[str, str] = {
    "jsy_mk194": "Balansun JSY-MK-194",
    "jsy_mk333": "Balansun JSY-MK-333",
    "linky": "Balansun Linky",
    "analog": "Balansun Analog",
    "full": "PV excess router",
}


def _model_from_device(device: dict) -> str:
    caps = device.get("capabilities") if isinstance(device.get("capabilities"), dict) else {}
    fc = caps.get("firmware_capabilities") if isinstance(caps.get("firmware_capabilities"), dict) else {}
    pack = str(fc.get("meter_pack") or "").strip()
    if pack:
        return _METER_PACK_MODELS.get(pack, f"Balansun {pack}")
    profile = str(caps.get("product_profile") or "").strip()
    if profile.endswith("_meter"):
        return "Balansun meter gateway"
    if profile.endswith("_router"):
        return "Balansun meter router"
    return "PV excess router"


def build_device_info(
    entry: ConfigEntry, coordinator: "BalansunCoordinator"
) -> DeviceInfo:
    """Device registry entry using live router metadata from the coordinator."""
    device = _device_payload(coordinator)
    name = (device.get("router_name") or "").strip() or "Balansun"
    info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Balansun",
        model=_model_from_device(device),
        configuration_url=coordinator.host,
    )
    fw = device.get("firmware_version")
    if fw:
        info["sw_version"] = str(fw)
    uid = device.get("device_uid")
    if uid:
        info["serial_number"] = str(uid)
    return info


def build_warm_device_info(entry: ConfigEntry, coordinator: object) -> DeviceInfo:
    """Device registry entry for a Balansun Warm node."""
    host = getattr(coordinator, "host", entry.data.get("host", ""))
    data = getattr(coordinator, "data", {}) or {}
    device = data.get("device")
    payload = device if isinstance(device, dict) else {}
    name = (payload.get("router_name") or "").strip() or "Balansun Warm"
    warm = data.get("warm")
    warm_body = warm if isinstance(warm, dict) else {}
    sku = str(warm_body.get("sku") or warm_body.get("hardware_profile") or "warm")
    info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Balansun",
        model=f"Warm {sku.upper()}",
        configuration_url=host,
    )
    fw = payload.get("firmware_version")
    if fw:
        info["sw_version"] = str(fw)
    return info


def title_from_public(body: dict, host: str) -> str:
    """Config entry title from /api/v1/public (setup before first coordinator poll)."""
    product = (body.get("product") or "").strip()
    if product:
        return product
    device = body.get("device")
    if isinstance(device, dict):
        name = (device.get("router_name") or "").strip()
        if name:
            return name
    hostname = (body.get("hostname") or "").strip()
    if hostname:
        return hostname
    return f"Balansun ({host})"
