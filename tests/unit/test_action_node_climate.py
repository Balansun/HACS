"""Unit tests for BalansunActionNodeClimate read-only properties."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.unit.balansun_import import load_action_node_climate, load_const

climate_mod = load_action_node_climate()
const = load_const()
BalansunActionNodeClimate = climate_mod.BalansunActionNodeClimate
CONF_HOST = const.CONF_HOST


def _climate_from_state(action_body: dict, health_body: dict | None = None) -> BalansunActionNodeClimate:
    entry = MagicMock()
    entry.data = {CONF_HOST: "http://192.168.4.1"}
    entry.entry_id = "test-entry"
    coordinator = MagicMock()
    coordinator.host = "http://192.168.4.1"
    coordinator.data = {
        "action": action_body,
        "health": health_body or {"wiring_profile": "r2_full_3relay"},
    }
    coordinator.action_state = action_body
    return BalansunActionNodeClimate(entry, coordinator)


def test_preset_modes_from_supported_orders() -> None:
    entity = _climate_from_state(
        {"supported_orders": ["confort", "eco", "hors_gel", "arret"], "pilot_wire_order": "eco"}
    )
    assert entity.preset_modes == ["confort", "eco", "hors_gel", "arret"]
    assert entity.preset_mode == "eco"


def test_hvac_mode_off_for_arret() -> None:
    entity = _climate_from_state({"pilot_wire_order": "arret", "supported_orders": ["arret"]})
    assert entity.hvac_mode == "off"


def test_hvac_mode_heat_for_confort() -> None:
    entity = _climate_from_state({"pilot_wire_order": "confort", "supported_orders": ["confort"]})
    assert entity.hvac_mode == "heat"


def test_current_temperature_from_action_state() -> None:
    entity = _climate_from_state({"temperature_c": 21.5, "temperature_ok": True, "pilot_wire_order": "confort"})
    assert entity.current_temperature == 21.5


def test_current_temperature_none_when_missing() -> None:
    entity = _climate_from_state({"pilot_wire_order": "confort", "temperature_ok": False})
    assert entity.current_temperature is None
