"""Shared coordinator entity helpers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import BalansunCoordinator
from .device_info import build_device_info, entity_unique_id
from .entity_registry import HelioEntitySpec, entity_display_name
from .safety_lockout import routing_writes_blocked


def apply_spec_attributes(entity: object, spec: HelioEntitySpec) -> None:
    """Apply registry metadata to a platform entity."""
    entity._attr_has_entity_name = True  # type: ignore[attr-defined]
    entity._attr_translation_key = spec.translation_key or spec.key  # type: ignore[attr-defined]
    if spec.icon:
        entity._attr_icon = spec.icon  # type: ignore[attr-defined]
    if not spec.enabled_by_default:
        entity._attr_entity_registry_enabled_default = False  # type: ignore[attr-defined]


class BalansunEntity(CoordinatorEntity):
    """Base entity bound to registry spec."""

    def __init__(
        self,
        coordinator: BalansunCoordinator,
        entry: ConfigEntry,
        spec: HelioEntitySpec,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.spec = spec
        self._attr_unique_id = entity_unique_id(entry, spec.key)
        if spec.entity_category == "config":
            self._attr_entity_category = EntityCategory.CONFIG
        elif spec.entity_category == "diagnostic":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        apply_spec_attributes(self, spec)

    @property
    def name(self) -> str:
        return entity_display_name(self.coordinator.data, self.spec.key, self.spec.name)

    @property
    def device_info(self):
        return build_device_info(self._entry, self.coordinator)

    def _routing_write_entity(self) -> bool:
        if self.spec.action_index is not None:
            return True
        if self.spec.button_action in ("triac_auto", "action_auto"):
            return True
        if self.spec.capability == "surplus_regulation" and self.spec.writable:
            return True
        return False

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        if self._routing_write_entity() and routing_writes_blocked(self.coordinator.data):
            return False
        return True
