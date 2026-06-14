"""Balansun HACS integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PRODUCT_PROFILE, DOMAIN, PRODUCT_ACTION_NODE, PRODUCT_WARM_ACTUATOR
from .coordinator import BalansunCoordinator
from .action_node_coordinator import BalansunActionNodeCoordinator
from .warm_coordinator import BalansunWarmCoordinator

ROUTER_PLATFORMS = [
    "sensor",
    "binary_sensor",
    "switch",
    "number",
    "select",
    "light",
    "datetime",
    "button",
]

WARM_PLATFORMS = ["climate"]


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    coordinator = getattr(entry, "runtime_data", None)
    if coordinator is None:
        coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is None:
        return
    if isinstance(coordinator, BalansunCoordinator) and coordinator.update_from_entry(entry):
        await hass.config_entries.async_reload(entry.entry_id)
        return
    await coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    profile = entry.data.get(CONF_PRODUCT_PROFILE)
    if profile == PRODUCT_WARM_ACTUATOR:
        coordinator = BalansunWarmCoordinator(hass, entry)
        platforms = WARM_PLATFORMS
    elif profile == PRODUCT_ACTION_NODE:
        coordinator = BalansunActionNodeCoordinator(hass, entry)
        platforms = WARM_PLATFORMS
    else:
        coordinator = BalansunCoordinator(hass, entry)
        platforms = ROUTER_PLATFORMS
    await coordinator.async_config_entry_first_refresh()
    if hasattr(entry, "runtime_data"):
        entry.runtime_data = coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    profile = entry.data.get(CONF_PRODUCT_PROFILE)
    platforms = (
        WARM_PLATFORMS
        if profile in (PRODUCT_WARM_ACTUATOR, PRODUCT_ACTION_NODE)
        else ROUTER_PLATFORMS
    )
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
