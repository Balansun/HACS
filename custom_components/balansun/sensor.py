"""Sensors from REST telemetry snapshot."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_config_value, read_snapshot_key
from .platform_setup import get_coordinator, get_effective_mode

_STRING_SNAPSHOT_KEYS = frozenset(
    {"linky_ltarf", "rte_today", "rte_tomorrow", "tariff_code", "source_data"}
)
_TIMESTAMP_SNAPSHOT_KEYS = frozenset({"self_test_last_run"})


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="sensor")
    async_add_entities([BalansunSensor(coordinator, entry, spec) for spec in specs])


class BalansunSensor(BalansunEntity, SensorEntity):
    def __init__(self, coordinator, entry, spec):
        super().__init__(coordinator, entry, spec)
        self._attr_device_class = spec.device_class
        self._attr_state_class = spec.state_class
        self._attr_native_unit_of_measurement = spec.native_unit

    @property
    def native_value(self):
        if self.spec.key == "source_data":
            return read_config_value(self.coordinator.data, self.spec)
        val = read_snapshot_key(self.coordinator.data, self.spec.key)
        if self.spec.key in _TIMESTAMP_SNAPSHOT_KEYS:
            if val is None:
                return None
            return datetime.fromtimestamp(int(val), tz=timezone.utc)
        if self.spec.key in _STRING_SNAPSHOT_KEYS:
            return str(val) if val is not None else None
        return val
