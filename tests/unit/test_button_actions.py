"""Unit tests for BalansunButton async_press (reboot / self-test)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from tests.unit.balansun_import import load_button, load_entity_registry

entity_registry = load_entity_registry()
STATIC_ENTITIES = entity_registry.STATIC_ENTITIES


def _spec_by_key(key: str):
    for spec in STATIC_ENTITIES:
        if spec.key == key:
            return spec
    raise KeyError(key)


def _make_button(button_mod, spec_key: str):
    coordinator = MagicMock()
    coordinator.data = {"device": {}, "config": {}}
    coordinator.async_post_system_reboot = AsyncMock()
    coordinator.async_post_self_test_run = AsyncMock()
    coordinator.async_post_mqtt_discover = AsyncMock()
    coordinator.async_request_refresh_after_write = AsyncMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    btn = button_mod.BalansunButton(coordinator, entry, _spec_by_key(spec_key))
    return btn, coordinator


def test_device_reboot_press_skips_refresh() -> None:
    button_mod = load_button()
    btn, coord = _make_button(button_mod, "device_reboot")

    asyncio.run(btn.async_press())

    coord.async_post_system_reboot.assert_awaited_once()
    coord.async_request_refresh_after_write.assert_not_awaited()


def test_self_test_run_press_refreshes() -> None:
    button_mod = load_button()
    btn, coord = _make_button(button_mod, "self_test_run")

    asyncio.run(btn.async_press())

    coord.async_post_self_test_run.assert_awaited_once()
    coord.async_request_refresh_after_write.assert_awaited_once()


def test_republish_discovery_press_refreshes() -> None:
    button_mod = load_button()
    btn, coord = _make_button(button_mod, "republish_discovery")

    asyncio.run(btn.async_press())

    coord.async_post_mqtt_discover.assert_awaited_once()
    coord.async_request_refresh_after_write.assert_awaited_once()
