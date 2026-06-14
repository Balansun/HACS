"""Meter source and config selects via REST."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .config_registry import current_meter_source, source_wire_options
from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_config_value
from .const import POST_WRITE_SOURCE_DELAY_SEC
from .platform_setup import get_coordinator, get_effective_mode
from .regulation_labels import (
    EXPERT_REGULATION_LABELS,
    STATUS_LED_MODE_LABELS,
    expert_regulation_label,
    expert_regulation_value,
    status_led_mode_api_value,
    status_led_mode_label,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="select")
    async_add_entities([BalansunSelect(coordinator, entry, spec) for spec in specs])


class BalansunSelect(BalansunEntity, SelectEntity):
    def __init__(self, coordinator, entry, spec) -> None:
        super().__init__(coordinator, entry, spec)
        if spec.key == "expert_regulation_mode":
            self._attr_options = list(EXPERT_REGULATION_LABELS)
        elif spec.key == "status_led_mode":
            self._attr_options = list(STATUS_LED_MODE_LABELS)
        elif spec.select_options:
            self._attr_options = list(spec.select_options)
        else:
            self._attr_options = []

    @property
    def options(self) -> list[str]:
        if self.spec.key == "source":
            return source_wire_options(self.coordinator.data) or []
        return list(self._attr_options or [])

    @property
    def current_option(self) -> str | None:
        if self.spec.key == "source":
            return current_meter_source(self.coordinator.data)
        val = read_config_value(self.coordinator.data, self.spec)
        if val is None:
            return None
        if self.spec.key == "expert_regulation_mode":
            return expert_regulation_label(val)
        if self.spec.key == "status_led_mode":
            return status_led_mode_label(val)
        return str(val)

    async def async_select_option(self, option: str) -> None:
        if not self.spec.writable:
            return
        key = self.spec.config_key or self.spec.key
        if key == "expert_regulation_mode":
            await self.coordinator.async_patch_config(
                {key: expert_regulation_value(option)}
            )
        elif key == "status_led_mode":
            await self.coordinator.async_patch_config(
                {key: status_led_mode_api_value(option)}
            )
        elif key == "source":
            await self.coordinator.async_patch_config({"source": option})
            await self.coordinator.async_request_refresh_after_write(
                delay_sec=POST_WRITE_SOURCE_DELAY_SEC
            )
            return
        else:
            await self.coordinator.async_patch_config({key: option})
        await self.coordinator.async_request_refresh_after_write()
