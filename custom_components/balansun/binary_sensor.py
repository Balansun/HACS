"""Binary sensors from REST telemetry."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_binary_value
from .platform_setup import get_coordinator, get_effective_mode


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="binary_sensor")
    async_add_entities([BalansunBinarySensor(coordinator, entry, spec) for spec in specs])


class BalansunBinarySensor(BalansunEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, spec) -> None:
        super().__init__(coordinator, entry, spec)
        if spec.binary_device_class:
            self._attr_device_class = spec.binary_device_class

    @property
    def is_on(self) -> bool | None:
        return read_binary_value(self.coordinator.data, self.spec.key)
