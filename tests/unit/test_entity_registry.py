"""Unit tests for entity_registry read helpers."""

from tests.unit.balansun_import import load_const, load_entity_registry

const = load_const()
entity_registry = load_entity_registry()

MODE_REST_ONLY = const.MODE_REST_ONLY
MODE_COMPANION = const.MODE_COMPANION
entities_for_mode = entity_registry.entities_for_mode
iter_action_specs = entity_registry.iter_action_specs
iter_temperature_specs = entity_registry.iter_temperature_specs
read_binary_value = entity_registry.read_binary_value
read_snapshot_key = entity_registry.read_snapshot_key
entity_display_name = entity_registry.entity_display_name
capability_enabled = entity_registry.capability_enabled


def test_read_snapshot_key_prefers_snapshot():
    data = {
        "snapshot": {"house_net_power_w": 42},
        "measurements": {
            "house": {"active_import_w": 100, "active_export_w": 58},
            "raw_meter": {"house_net_power_w": 99},
        },
    }
    assert read_snapshot_key(data, "house_net_power_w") == 42


def test_read_snapshot_key_net_from_import_export():
    data = {
        "snapshot": {},
        "measurements": {"house": {"active_import_w": 500, "active_export_w": 100}},
    }
    assert read_snapshot_key(data, "house_net_power_w") == 400


def test_entity_display_name_uses_probe_labels():
    data = {
        "measurements": {
            "probe_house_name": "Réseau",
            "probe_second_name": "Cumulus",
            "house": {},
        },
        "snapshot": {},
    }
    assert entity_display_name(data, "house_active_import_w", "House active import") == (
        "Réseau active import"
    )
    assert entity_display_name(data, "second_active_export_w", "Second active export") == (
        "Cumulus active export"
    )


def test_entity_display_name_temperature_primary_live_label():
    data = {
        "measurements": {
            "temperature_c": 48.2,
            "temperature_sensors": {
                "sensors": [
                    {
                        "slot": 0,
                        "enabled": True,
                        "label": "temperature_triac",
                        "valid": True,
                        "temperature_c": 48.2,
                        "primary": True,
                    },
                ],
            },
        },
        "snapshot": {},
        "config": {},
    }
    assert entity_display_name(data, "temperature_c", "temperature_c") == "temperature_triac"


def test_entity_display_name_temperature_primary_from_device_label():
    data = {
        "measurements": {"temperature_c": 48.2, "temperature_sensors": {"sensors": []}},
        "device": {"temperature_label": "temperature_triac"},
        "snapshot": {},
        "config": {},
    }
    assert entity_display_name(data, "temperature_c", "temperature_c") == "temperature_triac"


def test_entity_display_name_temperature_primary_config_uses_primary_slot():
    data = {
        "measurements": {
            "temperature_c": 48.2,
            "temperature_sensors": {"sensors": []},
        },
        "config": {
            "temperature_slots": [
                {"enabled": False, "label": "Unused"},
                {"enabled": True, "label": "temperature_triac"},
            ],
        },
        "snapshot": {},
    }
    assert entity_display_name(data, "temperature_c", "temperature_c") == "temperature_triac"


def test_entity_display_name_temperature_slot_live_label():
    data = {
        "measurements": {
            "temperature_c": 48.2,
            "temperature_sensors": {
                "sensors": [
                    {
                        "slot": 0,
                        "enabled": True,
                        "label": "Ballon",
                        "valid": True,
                        "temperature_c": 48.2,
                        "primary": True,
                    },
                    {
                        "slot": 1,
                        "enabled": True,
                        "label": "Ambiante",
                        "valid": True,
                        "temperature_c": 19.1,
                        "primary": False,
                    },
                ],
            },
        },
        "snapshot": {},
        "config": {},
    }
    assert entity_display_name(data, "temperature_slot_1_c", "Temperature slot 2") == "Ambiante"


def _actions_data(*titles: str) -> dict:
    return {
        "actions_config": {
            "actions": [{"title": title} for title in titles],
        },
        "snapshot": {},
    }


def test_entity_display_name_action_switch_live_title():
    data = _actions_data("Triac", "Chauffe-eau")
    assert entity_display_name(data, "action_1", "Heater 1") == "Chauffe-eau"


def test_entity_display_name_action_auto_and_daily_cap():
    data = _actions_data("Triac", "Chauffe-eau")
    assert entity_display_name(data, "action_1_auto", "Chauffe-eau auto") == "Chauffe-eau auto"
    assert entity_display_name(data, "action_1_daily_cap_wh", "Action 1 daily cap") == (
        "Chauffe-eau daily cap"
    )


def test_entity_display_name_triac_entities_use_action_zero_title():
    data = _actions_data("Ballon ECS")
    assert entity_display_name(data, "triac_open_percent", "Triac open") == "Ballon ECS open"
    assert entity_display_name(data, "triac_target", "Target triac opening") == (
        "Ballon ECS target opening"
    )
    assert entity_display_name(data, "triac_auto", "Triac regulation auto") == (
        "Ballon ECS regulation auto"
    )


def test_read_second_channel_from_nested_measurements():
    data = {
        "snapshot": {},
        "measurements": {
            "second": {
                "active_import_w": 879,
                "active_export_w": 0,
                "energy_total_import_wh": 42599,
                "energy_day_import_wh": 407,
            },
            "raw_meter": {
                "voltage_second_v": 235.2,
                "current_second_a": 6.33,
                "pf_second": 0.59,
            },
        },
    }
    assert read_snapshot_key(data, "second_active_import_w") == 879
    assert read_snapshot_key(data, "second_voltage_v") == 235.2
    assert read_snapshot_key(data, "second_current_a") == 6.33
    assert read_snapshot_key(data, "second_energy_import_wh") == 42599
    assert read_snapshot_key(data, "second_day_energy_import_wh") == 407


def test_read_second_channel_prefers_snapshot():
    data = {
        "snapshot": {"second_active_import_w": 100},
        "measurements": {"second": {"active_import_w": 879}},
    }
    assert read_snapshot_key(data, "second_active_import_w") == 100


def test_triac_capability_from_raw_meter_voltage():
    data = {"measurements": {"raw_meter": {"voltage_second_v": 230.0}}, "snapshot": {}}
    assert capability_enabled(data, "triac_channel") is True


def test_read_binary_vacation_from_config():
    data = {"config": {"vacation_enabled": True}, "snapshot": {}}
    assert read_binary_value(data, "vacation") is True


def test_read_binary_on_off_from_snapshot():
    data = {"snapshot": {"source_stale": "ON"}}
    assert read_binary_value(data, "source_stale") is True


def test_linky_capability_gated():
    data = {"measurements": {}, "snapshot": {}}
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "linky_ltarf" not in keys
    data_linky = {"measurements": {"linky_tariff": "HC"}, "snapshot": {}}
    keys2 = {s.key for s in entities_for_mode(data_linky, MODE_REST_ONLY)}
    assert "linky_ltarf" in keys2
    linky_spec = next(s for s in entities_for_mode(data_linky, MODE_REST_ONLY) if s.key == "linky_ltarf")
    assert linky_spec.platform == "sensor"
    assert linky_spec.writable is False


def test_balansun_peer_source_data_gated():
    data = {"config": {"source": "BalansunPeer"}, "sources": {"current_data": "Linky"}, "snapshot": {}}
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "source_data" in keys
    data2 = {"config": {"source": "Linky"}, "snapshot": {}}
    keys2 = {s.key for s in entities_for_mode(data2, MODE_REST_ONLY)}
    assert "source_data" not in keys2


def test_temperature_specs_primary_and_slot_one():
    data = {
        "measurements": {
            "temperature_c": 48.2,
            "temperature_sensors": {
                "gpio": 13,
                "max_count": 2,
                "discovered_count": 2,
                "bus_active": True,
                "sensors": [
                    {
                        "slot": 0,
                        "enabled": True,
                        "label": "Ballon",
                        "valid": True,
                        "temperature_c": 48.2,
                        "primary": True,
                    },
                    {
                        "slot": 1,
                        "enabled": True,
                        "label": "Ambiante",
                        "valid": True,
                        "temperature_c": 19.1,
                        "primary": False,
                    },
                ],
            },
        },
        "snapshot": {},
        "config": {},
    }
    specs = entity_registry.iter_temperature_specs(data)
    keys = {s.key for s in specs}
    assert "temperature_c" in keys
    assert "temperature_slot_1_c" in keys
    assert "temperature_slot_0_c" not in keys
    primary = next(s for s in specs if s.key == "temperature_c")
    assert primary.name == "Ballon"
    assert read_snapshot_key(data, "temperature_slot_1_c") == 19.1


def test_temperature_capability_disabled_slots():
    data = {
        "measurements": {
            "temperature_c": -127,
            "temperature_sensors": {
                "sensors": [
                    {"slot": 0, "enabled": False, "valid": False},
                    {"slot": 1, "enabled": False, "valid": False},
                ],
            },
        },
        "snapshot": {},
    }
    assert capability_enabled(data, "temperature") is False
    assert entity_registry.iter_temperature_specs(data) == []


def test_read_snapshot_key_temperature_c_ignores_invalid_state():
    data = {
        "measurements": {},
        "state": {"temperature_c": -127},
        "snapshot": {},
    }
    assert read_snapshot_key(data, "temperature_c") is None


def test_read_snapshot_key_temperature_slot_ignores_invalid_reading():
    data = {
        "measurements": {
            "temperature_sensors": {
                "sensors": [
                    {
                        "slot": 1,
                        "enabled": True,
                        "valid": True,
                        "temperature_c": -127,
                    },
                ],
            },
        },
        "snapshot": {},
    }
    assert read_snapshot_key(data, "temperature_slot_1_c") is None


def test_state_machine_entities_from_health_and_status():
    data = {
        "health": {
            "device_lifecycle": "regulating",
            "product_profile": "full_router",
            "output_suspend": {"active": True, "reason": "vacation"},
        },
        "state": {
            "status": {
                "regulation_motion": "increasing",
                "device_lifecycle": "regulating",
            }
        },
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": True},
            }
        },
        "snapshot": {},
        "measurements": {},
    }
    assert read_snapshot_key(data, "device_lifecycle") == "regulating"
    assert read_snapshot_key(data, "regulation_motion") == "increasing"
    assert read_snapshot_key(data, "product_profile") == "full_router"
    assert read_binary_value(data, "output_suspended") is True
    assert capability_enabled(data, "surplus_regulation") is True


def test_entities_for_mode_hides_surplus_sensors_on_meter_only():
    data = {
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": False},
            }
        },
        "snapshot": {},
        "measurements": {},
        "actions_config": {"actions": []},
    }
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "device_lifecycle" in keys
    assert "regulation_motion" not in keys
    assert "output_suspended" not in keys
    assert "output_suspend_reason" not in keys


def test_output_suspend_reason_reads_nested_health():
    data = {
        "health": {
            "output_suspend": {"active": True, "reason": "source_stale"},
        },
        "snapshot": {},
        "measurements": {},
    }
    assert read_snapshot_key(data, "output_suspend_reason") == "source_stale"


def test_surplus_regulation_capability_hides_motion_on_meter_only():
    data = {
        "device": {
            "capabilities": {
                "firmware_capabilities": {"surplus_regulation": False},
            }
        },
        "snapshot": {},
        "measurements": {},
    }
    assert capability_enabled(data, "surplus_regulation") is False


JSY_MK194_METER_DEVICE = {
    "device": {
        "capabilities": {
            "product_profile": "jsy_mk194_meter",
            "firmware_capabilities": {
                "surplus_regulation": False,
                "triac": False,
                "multi_action": False,
                "source_test_inject": False,
                "meter_pack": "jsy_mk194",
                "meters": ["JsyMk194"],
            },
        }
    },
    "snapshot": {},
    "measurements": {},
    "actions_config": {"actions": []},
}


def test_jsy_mk194_meter_hides_router_entities():
    keys = {s.key for s in entities_for_mode(JSY_MK194_METER_DEVICE, MODE_REST_ONLY)}
    assert "triac_open_percent" not in keys
    assert "triac_auto" not in keys
    assert "max_routed_w" not in keys
    assert "regulation_active" not in keys
    assert "product_profile" in keys
    assert "meter_pack" in keys
    assert read_snapshot_key(JSY_MK194_METER_DEVICE, "meter_pack") == "jsy_mk194"


JSY_MK194_ROUTER_DEVICE = {
    "device": {
        "capabilities": {
            "product_profile": "jsy_mk194_router",
            "firmware_capabilities": {
                "surplus_regulation": True,
                "triac": True,
                "multi_action": False,
                "source_test_inject": False,
                "meter_pack": "jsy_mk194",
                "meters": ["JsyMk194"],
            },
        }
    },
    "snapshot": {},
    "measurements": {},
    "actions_config": {"actions": [{"title": "Triac"}]},
}


def test_jsy_mk194_router_shows_triac_entities():
    keys = {s.key for s in entities_for_mode(JSY_MK194_ROUTER_DEVICE, MODE_REST_ONLY)}
    assert "triac_open_percent" in keys
    assert "triac_auto" in keys
    assert "max_routed_w" in keys
    assert "regulation_active" in keys


def test_self_test_run_button_gated_by_capability():
    router_with_self_test = {
        **JSY_MK194_ROUTER_DEVICE,
        "device": {
            "capabilities": {
                **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"],
                "firmware_capabilities": {
                    **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"]["firmware_capabilities"],
                    "self_test_triac": True,
                },
            }
        },
    }
    button_keys = {
        s.key for s in entities_for_mode(router_with_self_test, MODE_REST_ONLY, platform="button")
    }
    assert "self_test_run" in button_keys
    meter_keys = {
        s.key for s in entities_for_mode(JSY_MK194_METER_DEVICE, MODE_REST_ONLY, platform="button")
    }
    assert "self_test_run" not in meter_keys


def test_companion_mode_includes_action_buttons():
    minimal = {"measurements": {}, "snapshot": {}}
    button_keys = {
        s.key for s in entities_for_mode(minimal, MODE_COMPANION, platform="button")
    }
    assert button_keys == {"republish_discovery", "device_reboot"}

    router_with_self_test = {
        **JSY_MK194_ROUTER_DEVICE,
        "device": {
            "capabilities": {
                **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"],
                "firmware_capabilities": {
                    **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"]["firmware_capabilities"],
                    "self_test_triac": True,
                },
            }
        },
    }
    button_keys_router = {
        s.key
        for s in entities_for_mode(router_with_self_test, MODE_COMPANION, platform="button")
    }
    assert button_keys_router == {"republish_discovery", "device_reboot", "self_test_run"}
    assert "device_reboot" in {
        s.key for s in entities_for_mode(router_with_self_test, MODE_REST_ONLY, platform="button")
    }


def test_self_test_last_run_sensor_gated_and_reads_epoch():
    from tests.unit.balansun_import import load_entity_registry

    entity_registry = load_entity_registry()
    read_snapshot_key = entity_registry.read_snapshot_key

    router_with_self_test = {
        **JSY_MK194_ROUTER_DEVICE,
        "device": {
            "capabilities": {
                **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"],
                "firmware_capabilities": {
                    **JSY_MK194_ROUTER_DEVICE["device"]["capabilities"]["firmware_capabilities"],
                    "self_test_triac": True,
                },
            }
        },
        "health": {"self_test": {"last_run_epoch": 1_700_000_000}},
    }
    sensor_keys = {
        s.key for s in entities_for_mode(router_with_self_test, MODE_REST_ONLY, platform="sensor")
    }
    assert "self_test_last_run" in sensor_keys
    assert read_snapshot_key(router_with_self_test, "self_test_last_run") == 1_700_000_000
    assert (
        read_snapshot_key(
            {
                **router_with_self_test,
                "health": {"self_test": {"last_run_epoch": 529}},
            },
            "self_test_last_run",
        )
        is None
    )
    meter_sensor_keys = {
        s.key for s in entities_for_mode(JSY_MK194_METER_DEVICE, MODE_REST_ONLY, platform="sensor")
    }
    assert "self_test_last_run" not in meter_sensor_keys


def test_surplus_regulation_true_implies_triac_entities_without_triac_key():
    data = {
        "device": {
            "capabilities": {
                "product_profile": "jsy_mk194_router",
                "firmware_capabilities": {
                    "surplus_regulation": True,
                    "meters": ["JsyMk194"],
                },
            }
        },
        "snapshot": {},
        "measurements": {},
        "actions_config": {"actions": [{"title": "Triac"}]},
    }
    keys = {s.key for s in entities_for_mode(data, MODE_REST_ONLY)}
    assert "triac_open_percent" in keys
    assert capability_enabled(data, "triac") is True


def test_iter_action_specs_skips_index_zero():
    data = {
        "actions_config": {
            "actions": [
                {"title": "Triac"},
                {"title": "Heater 1"},
                {"title": "Heater 2"},
            ]
        }
    }
    specs = iter_action_specs(data)
    assert len(specs) == 2
    assert specs[0].key == "action_1"
    assert specs[0].action_index == 1
