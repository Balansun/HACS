"""Status LED RGB config lights (native color picker)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from .config_registry import default_hex_for_color_key
from .entity import BalansunEntity, apply_spec_attributes
from .entity_registry import entities_for_mode, read_config_value
from .platform_setup import get_coordinator, get_effective_mode
from .status_led_rgb import hex_to_rgb


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="light")
    async_add_entities([BalansunStatusLedColorLight(coordinator, entry, spec) for spec in specs])


class BalansunStatusLedColorLight(BalansunEntity, LightEntity):
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, spec) -> None:
        super().__init__(coordinator, entry, spec)
        apply_spec_attributes(self, spec)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        raw = read_config_value(self.coordinator.data, self.spec)
        if isinstance(raw, (list, tuple)) and len(raw) >= 3:
            try:
                return (int(raw[0]), int(raw[1]), int(raw[2]))
            except (TypeError, ValueError):
                pass
        fallback = default_hex_for_color_key(self.spec.key)
        return hex_to_rgb(fallback)

    @property
    def is_on(self) -> bool:
        return True

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.spec.writable:
            return
        rgb = kwargs.get("rgb_color")
        if rgb is None:
            return
        key = self.spec.config_key or self.spec.key
        await self.coordinator.async_patch_config({key: list(rgb)})
        await self.coordinator.async_request_refresh_after_write()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Color config only; no off state."""
