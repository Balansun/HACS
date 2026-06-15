"""Unit tests for companion vs rest_only filtering."""

from tests.unit.balansun_import import load_const, load_entity_registry, load_integration_mode

const = load_const()
integration_mode = load_integration_mode()
entity_registry = load_entity_registry()

MODE_COMPANION = const.MODE_COMPANION
MODE_REST_ONLY = const.MODE_REST_ONLY
COMPANION_ENTITY_KEYS = const.COMPANION_ENTITY_KEYS
entities_for_mode = entity_registry.entities_for_mode
entity_enabled_for_mode = integration_mode.entity_enabled_for_mode

ROUTER_WITH_SELF_TEST = {
    "measurements": {},
    "snapshot": {},
    "device": {
        "capabilities": {
            "firmware_capabilities": {
                "self_test_triac": True,
            }
        }
    },
}


def test_companion_entity_keys_allow_action_buttons():
    assert COMPANION_ENTITY_KEYS == frozenset(
        {"republish_discovery", "self_test_run", "device_reboot"}
    )
    for key in COMPANION_ENTITY_KEYS:
        assert entity_enabled_for_mode(key, MODE_COMPANION)
    assert not entity_enabled_for_mode("vacation", MODE_COMPANION)
    assert entity_enabled_for_mode("vacation", MODE_REST_ONLY)


def test_rest_only_includes_sensors():
    data = {
        "measurements": {
            "probe_house_name": "House",
            "house": {"active_import_w": 100, "active_export_w": 0},
            "raw_meter": {"house_net_power_w": 100},
        },
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": True},
            }
        },
        "snapshot": {},
    }
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY, platform="sensor")}
    assert "house_net_power_w" in keys
    assert "triac_open_percent" in keys


def test_companion_entity_list_minimal():
    data = {"measurements": {}, "snapshot": {}}
    keys = {s.key for s in entities_for_mode(data, MODE_COMPANION)}
    assert keys == {"republish_discovery", "device_reboot"}


def test_companion_entity_list_includes_self_test_when_capable():
    keys = {s.key for s in entities_for_mode(ROUTER_WITH_SELF_TEST, MODE_COMPANION)}
    assert keys == {"republish_discovery", "device_reboot", "self_test_run"}


def test_companion_button_platform_excludes_triac_auto():
    data = {
        "measurements": {},
        "snapshot": {},
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": True},
            }
        },
    }
    keys = {s.key for s in entities_for_mode(data, MODE_COMPANION, platform="button")}
    assert keys == {"republish_discovery", "device_reboot"}
    assert "triac_auto" not in keys


def test_configured_mode_defaults_to_rest_only():
    from unittest.mock import MagicMock

    configured_mode = integration_mode.configured_mode
    entry = MagicMock()
    entry.options = {}
    entry.data = {}
    assert configured_mode(entry) == MODE_REST_ONLY
