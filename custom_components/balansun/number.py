"""Numbers (max routed, triac target, config) via REST."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_config_value, read_snapshot_key
from .platform_setup import get_coordinator, get_effective_mode


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="number")
    async_add_entities([BalansunNumber(coordinator, entry, spec) for spec in specs])


class BalansunNumber(BalansunEntity, NumberEntity):
    def __init__(self, coordinator, entry, spec):
        super().__init__(coordinator, entry, spec)
        self._attr_native_unit_of_measurement = spec.native_unit
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step or 1
        self._attr_mode = (
            NumberMode.SLIDER if spec.number_mode == "slider" else NumberMode.BOX
        )

    @property
    def native_value(self) -> float | None:
        if self.spec.config_key or self.spec.daily_cap_index is not None:
            val = read_config_value(self.coordinator.data, self.spec)
            return float(val) if val is not None else None
        if self.spec.key == "max_routed_w":
            cfg = self.coordinator.data.get("config") or {}
            val = cfg.get("max_routed_w")
            return float(val) if val is not None else None
        val = read_snapshot_key(self.coordinator.data, self.spec.key)
        if val is None and self.spec.key == "triac_target":
            val = read_snapshot_key(self.coordinator.data, "triac_open_percent")
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        if not self.spec.writable:
            return
        if self.spec.daily_cap_index is not None:
            cfg = dict(self.coordinator.data.get("config") or {})
            caps = list(cfg.get("action_daily_cap_wh") or [])
            while len(caps) <= self.spec.daily_cap_index:
                caps.append(0)
            caps[self.spec.daily_cap_index] = int(value)
            await self.coordinator.async_patch_config({"action_daily_cap_wh": caps})
        elif self.spec.config_key:
            key = self.spec.config_key
            await self.coordinator.async_patch_config({key: int(value)})
        elif self.spec.key == "max_routed_w":
            await self.coordinator.async_patch_config({"max_routed_w": int(value)})
        elif self.spec.key == "triac_target":
            await self.coordinator.async_post_triac_override(str(int(value)))
        await self.coordinator.async_request_refresh_after_write()
