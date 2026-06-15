"""Buttons (discovery, triac/action auto, status LED test)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .config_registry import default_hex_for_color_key
from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_config_value
from .platform_setup import get_coordinator, get_effective_mode
from .status_led_rgb import rgb_list, rgb_to_hex


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="button")
    async_add_entities([BalansunButton(coordinator, entry, spec) for spec in specs])


class BalansunButton(BalansunEntity, ButtonEntity):
    async def async_press(self) -> None:
        if self.spec.key == "republish_discovery":
            await self.coordinator.async_post_mqtt_discover()
        elif self.spec.button_action == "triac_auto":
            await self.coordinator.async_post_triac_override("AUTO")
        elif self.spec.button_action == "action_auto" and self.spec.action_index is not None:
            await self.coordinator.async_post_action_override(self.spec.action_index, "auto")
        elif self.spec.button_action == "status_led_test" and self.spec.status_led_role:
            await self.coordinator.async_post_status_led_test(self._status_led_test_body())
        elif self.spec.button_action == "self_test_run":
            await self.coordinator.async_post_self_test_run()
        elif self.spec.button_action == "device_reboot":
            await self.coordinator.async_post_system_reboot()
            return
        await self.coordinator.async_request_refresh_after_write()

    def _status_led_test_body(self) -> dict[str, Any]:
        cfg = self.coordinator.data.get("config") or {}
        if not isinstance(cfg, dict):
            cfg = {}
        body: dict[str, Any] = {
            "role": self.spec.status_led_role,
            "duration_ms": 5000,
        }
        for key in (
            "status_led_mode",
            "status_led_gpio_activity",
            "status_led_gpio_regulation",
            "status_led_rgb_gpio",
            "status_led_active_low",
        ):
            if key in cfg:
                body[key] = cfg[key]
        for color_key in (
            "status_led_color_activity",
            "status_led_color_regulation",
            "status_led_color_reboot",
            "status_led_color_ap",
        ):
            raw = cfg.get(color_key)
            if isinstance(raw, list):
                body[color_key] = raw
            else:
                body[color_key] = rgb_list(
                    rgb_to_hex(None, default_hex_for_color_key(color_key))
                )
        return body
