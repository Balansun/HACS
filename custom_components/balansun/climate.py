"""Climate entity for Balansun Warm fil pilote preset modes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .device_info import build_warm_device_info, entity_unique_id
from .warm_coordinator import BalansunWarmCoordinator
from .action_node_coordinator import BalansunActionNodeCoordinator
from .const import DOMAIN, PRODUCT_ACTION_NODE, CONF_PRODUCT_PROFILE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    if entry.data.get(CONF_PRODUCT_PROFILE) == PRODUCT_ACTION_NODE:
        async_add_entities([BalansunActionNodeClimate(entry, coordinator)])
        return

    channels = coordinator.warm_channels()
    enabled = [c for c in channels if c.get("enabled", True)]
    if not enabled:
        async_add_entities([BalansunWarmClimate(entry, coordinator, 0)])
        return
    async_add_entities(
        [
            BalansunWarmClimate(
                entry,
                coordinator,
                int(ch.get("channel_id", idx)),
            )
            for idx, ch in enumerate(enabled)
        ]
    )


class BalansunWarmClimate(CoordinatorEntity[BalansunWarmCoordinator], ClimateEntity):
    """Fil pilote radiator as HA climate presets."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = ["heat", "off"]
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: BalansunWarmCoordinator,
        channel_id: int,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._channel_id = channel_id
        suffix = f"_{channel_id}" if channel_id > 0 else ""
        self._attr_unique_id = entity_unique_id(entry, f"warm_climate{suffix}")
        self._attr_device_info = build_warm_device_info(entry, coordinator)

    @property
    def name(self) -> str:
        label = str(self._warm.get("label") or "").strip()
        if label:
            return label
        if self._channel_id == 0:
            return "Radiator"
        return f"Radiator {self._channel_id + 1}"

    @property
    def _warm(self) -> dict[str, Any]:
        for ch in self.coordinator.warm_channels():
            if int(ch.get("channel_id", 0)) == self._channel_id:
                return ch
        body = self.coordinator.data.get("warm") if self.coordinator.data else None
        return body if isinstance(body, dict) else {}

    @property
    def preset_modes(self) -> list[str] | None:
        orders = self._warm.get("supported_orders")
        if isinstance(orders, list) and orders:
            return [str(o) for o in orders]
        return ["confort", "eco", "hors_gel", "arret"]

    @property
    def preset_mode(self) -> str | None:
        order = self._warm.get("pilot_wire_order")
        return str(order) if order else None

    @property
    def hvac_mode(self) -> str:
        if self.preset_mode == "arret":
            return "off"
        return "heat"

    @property
    def current_temperature(self) -> float | None:
        return None

    @property
    def target_temperature(self) -> float | None:
        return None

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == "off":
            await self.coordinator.async_set_pilot_order("arret", self._channel_id)
        else:
            await self.coordinator.async_set_pilot_order("confort", self._channel_id)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.async_set_pilot_order(preset_mode, self._channel_id)


class BalansunActionNodeClimate(CoordinatorEntity[BalansunActionNodeCoordinator], ClimateEntity):
    """ESP8266 fil pilote action node as HA climate presets."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = ["heat", "off"]
    _attr_supported_features = ClimateEntityFeature.PRESET_MODE

    def __init__(self, entry: ConfigEntry, coordinator: BalansunActionNodeCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entity_unique_id(entry, "action_node_climate")
        self._attr_name = "Fil pilote"
        health = (coordinator.data or {}).get("health") if coordinator.data else {}
        wiring = ""
        if isinstance(health, dict):
            wiring = str(health.get("wiring_profile") or "")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Balansun action node",
            manufacturer="Balansun",
            model=wiring or "ESP8266 fil pilote R2",
            configuration_url=coordinator.host,
        )

    @property
    def _action(self) -> dict[str, Any]:
        return self.coordinator.action_state

    @property
    def preset_modes(self) -> list[str] | None:
        orders = self._action.get("supported_orders")
        if isinstance(orders, list) and orders:
            return [str(o) for o in orders]
        return ["confort", "eco", "hors_gel", "arret"]

    @property
    def preset_mode(self) -> str | None:
        order = self._action.get("pilot_wire_order")
        return str(order) if order else None

    @property
    def hvac_mode(self) -> str:
        if self.preset_mode == "arret":
            return "off"
        return "heat"

    @property
    def current_temperature(self) -> float | None:
        temp = self._action.get("temperature_c")
        if isinstance(temp, (int, float)):
            return float(temp)
        return None

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        if hvac_mode == "off":
            await self.coordinator.async_set_pilot_order("arret")
        else:
            await self.coordinator.async_set_pilot_order("confort")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self.coordinator.async_set_pilot_order(preset_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if ATTR_TEMPERATURE in kwargs:
            return
