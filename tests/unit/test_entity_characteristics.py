"""Regression checks for entity platform and HA metadata."""

from tests.unit.balansun_import import load_config_registry, load_const, load_entity_registry

const = load_const()
entity_registry = load_entity_registry()
config_registry = load_config_registry()

MODE_REST_ONLY = const.MODE_REST_ONLY
STATIC_ENTITIES = entity_registry.STATIC_ENTITIES
CONFIG_ENTITIES = config_registry.CONFIG_ENTITIES
entities_for_mode = entity_registry.entities_for_mode


def _spec_by_key(key: str):
    for spec in list(STATIC_ENTITIES) + list(CONFIG_ENTITIES):
        if spec.key == key:
            return spec
    raise KeyError(key)


def test_no_text_platform_in_registry():
    all_specs = list(STATIC_ENTITIES) + list(CONFIG_ENTITIES)
    for spec in config_registry.status_led_entities():
        all_specs.append(spec)
    assert all(spec.platform != "text" for spec in all_specs)


def test_tempo_linky_are_read_only_sensors():
    data = {
        "measurements": {"linky_tariff": "HC"},
        "snapshot": {"rte_today": "Bleu"},
    }
    keys = {s.key: s for s in entities_for_mode(data, MODE_REST_ONLY)}
    for key in ("linky_ltarf", "rte_today", "tariff_code"):
        assert keys[key].platform == "sensor"
        assert keys[key].writable is False
        assert keys[key].entity_category == "diagnostic"


def test_expert_regulation_select_labels():
    spec = _spec_by_key("expert_regulation_mode")
    assert spec.platform == "select"
    assert "Integral only" in spec.select_options
    assert "PID" in spec.select_options[1]
    assert "2" not in spec.select_options


def test_regulation_gain_bounds():
    spec = _spec_by_key("regulation_gain")
    assert spec.min_value == 1
    assert spec.max_value == 99


def test_hunting_bounds():
    rev = _spec_by_key("hunting_reversal_threshold")
    win = _spec_by_key("hunting_window_min")
    assert rev.min_value == 3 and rev.max_value == 30
    assert win.min_value == 2 and win.max_value == 30


def test_binary_sensors_have_device_class():
    for key, dc in (
        ("mqtt_connected", "connectivity"),
        ("source_stale", "problem"),
        ("regulation_active", "running"),
    ):
        spec = _spec_by_key(key)
        assert spec.binary_device_class == dc


def test_device_reboot_button_metadata():
    spec = _spec_by_key("device_reboot")
    assert spec.platform == "button"
    assert spec.button_action == "device_reboot"
    assert spec.companion_allowed is True
    assert spec.entity_category == "diagnostic"
    assert spec.icon == "mdi:restart"
    assert spec.capability is None


def test_self_test_run_companion_allowed():
    spec = _spec_by_key("self_test_run")
    assert spec.companion_allowed is True
    assert spec.button_action == "self_test_run"
    assert spec.capability == "self_test_triac"


def test_status_led_colors_are_light_platform():
    for spec in config_registry.status_led_entities():
        if spec.key.startswith("status_led_color_"):
            assert spec.platform == "light"
