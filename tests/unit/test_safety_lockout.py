"""Unit tests for safety lockout helpers and entity gating."""

from __future__ import annotations

import json
from pathlib import Path

from tests.unit.balansun_import import load_const, load_entity_registry, load_events_logic, load_safety_lockout

const = load_const()
entity_registry = load_entity_registry()
events_logic = load_events_logic()
safety_lockout = load_safety_lockout()

MODE_REST_ONLY = const.MODE_REST_ONLY
entities_for_mode = entity_registry.entities_for_mode
read_binary_value = entity_registry.read_binary_value
MqttHaEventInput = events_logic.MqttHaEventInput
mqtt_ha_events_logic_detect = events_logic.mqtt_ha_events_logic_detect
fired_subtypes = events_logic.fired_subtypes

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "health_golden.json"


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _router_data(**overrides) -> dict:
    base = {
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": True},
            }
        },
        "health": _load_fixture(),
        "measurements": {},
        "snapshot": {},
    }
    base.update(overrides)
    return base


def test_safety_lockout_inactive_on_golden_health():
    data = _router_data()
    assert safety_lockout.safety_lockout_active(data) is False
    assert safety_lockout.safety_lockout_reasons(data) == []
    assert safety_lockout.routing_writes_blocked(data) is False


def test_safety_lockout_active_from_health_block():
    health = _load_fixture()
    health["safety_lockout"] = {"active": True, "reasons": ["zc_failed"]}
    data = _router_data(health=health)
    assert safety_lockout.safety_lockout_active(data) is True
    assert safety_lockout.safety_lockout_reasons(data) == ["zc_failed"]
    assert safety_lockout.routing_writes_blocked(data) is True


def test_safety_lockout_active_from_output_suspend_reason():
    data = _router_data(
        health={
            "safety_lockout": {"active": False, "reasons": []},
            "output_suspend": {"active": True, "reason": "safety_lockout"},
        }
    )
    assert safety_lockout.safety_lockout_active(data) is True


def test_lockout_hides_writable_triac_entities():
    health = _load_fixture()
    health["safety_lockout"] = {"active": True, "reasons": ["triac_failed"]}
    data = _router_data(health=health)
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "triac_open_percent" in keys
    assert "max_routed_w" in keys
    assert read_binary_value(data, "safety_lockout_active") is True


def test_meter_profile_blocks_routing_without_lockout():
    data = {
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": False},
            }
        },
        "health": _load_fixture(),
        "measurements": {},
        "snapshot": {},
    }
    assert safety_lockout.routing_writes_blocked(data) is True
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "triac_open_percent" not in keys


def test_safety_lockout_device_trigger_edges():
    inp = MqttHaEventInput(
        safety_lockout_active=True,
        prev_safety_lockout_active=False,
    )
    out = mqtt_ha_events_logic_detect(inp)
    assert "safety_lockout_started" in fired_subtypes(out)

    cleared = MqttHaEventInput(
        safety_lockout_active=False,
        prev_safety_lockout_active=True,
    )
    out_cleared = mqtt_ha_events_logic_detect(cleared)
    assert "safety_lockout_cleared" in fired_subtypes(out_cleared)
