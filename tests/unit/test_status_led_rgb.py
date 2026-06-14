"""RGB hex helpers."""

from tests.unit.balansun_import import load_status_led_rgb

rgb = load_status_led_rgb()


def test_hex_round_trip():
    assert rgb.rgb_list("#ffb400") == [255, 180, 0]
    assert rgb.rgb_to_hex([0, 255, 0], "#000000") == "#00ff00"


def test_source_wire_options():
    from tests.unit.balansun_import import load_config_registry

    config_registry = load_config_registry()
    data = {
        "sources": {"supported": ["Linky", "JsyMk194", "NotDef"]},
        "config": {"source": "Linky"},
    }
    opts = config_registry.source_wire_options(data)
    assert opts == ["Linky", "JsyMk194"]
    assert "NotDef" not in opts
