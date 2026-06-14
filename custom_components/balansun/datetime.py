"""Config datetime entities (vacation end)."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .entity import BalansunEntity
from .entity_registry import entities_for_mode, read_config_value
from .platform_setup import get_coordinator, get_effective_mode


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = get_coordinator(hass, entry)
    mode = get_effective_mode(hass, entry, coordinator)
    specs = entities_for_mode(coordinator.data, mode, platform="datetime")
    async_add_entities([BalansunDateTime(coordinator, entry, spec) for spec in specs])


class BalansunDateTime(BalansunEntity, DateTimeEntity):
    @property
    def native_value(self) -> datetime | None:
        epoch = read_config_value(self.coordinator.data, self.spec)
        if epoch is None:
            return None
        try:
            ts = int(epoch)
        except (TypeError, ValueError):
            return None
        if ts <= 0:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    async def async_set_value(self, value: datetime) -> None:
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_util.get_time_zone(self.hass.config.time_zone))
        epoch = int(value.timestamp())
        key = self.spec.config_key or self.spec.key
        await self.coordinator.async_patch_config({key: epoch})
        await self.coordinator.async_request_refresh_after_write()
