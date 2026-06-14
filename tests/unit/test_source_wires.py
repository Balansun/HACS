"""Meter source wire label helpers."""

from __future__ import annotations

from tests.unit.balansun_import import load_config_registry, load_source_wires

source_wires = load_source_wires()
config_registry = load_config_registry()

normalize_source_wire = source_wires.normalize_source_wire
current_meter_source = source_wires.current_meter_source
source_wire_options = source_wires.source_wire_options
balansun_peer_active = config_registry.balansun_peer_active


def test_normalize_canonical_wires() -> None:
    assert normalize_source_wire("JsyMk194") == "JsyMk194"
    assert normalize_source_wire("Analog") == "Analog"
    assert normalize_source_wire("BalansunPeer") == "BalansunPeer"
    assert normalize_source_wire("Pmqtt") == "Pmqtt"
    assert normalize_source_wire("NotDef") is None


def test_normalize_rejects_legacy_labels() -> None:
    assert normalize_source_wire("UxIx2") == "UxIx2"
    assert normalize_source_wire("Ext") == "Ext"


def test_source_wire_options_from_supported() -> None:
    data = {
        "sources": {"supported": ["Linky", "JsyMk194", "BalansunPeer", "NotDef"]},
        "config": {"source": "Linky"},
    }
    assert source_wire_options(data) == ["Linky", "JsyMk194", "BalansunPeer"]


def test_source_wire_options_includes_current_not_in_supported() -> None:
    data = {
        "sources": {"supported": ["Linky", "JsyMk194"], "current": "BalansunPeer"},
        "config": {},
    }
    opts = source_wire_options(data)
    assert opts[0] == "BalansunPeer"
    assert "Linky" in opts


def test_current_meter_source_prefers_sources_current() -> None:
    data = {
        "sources": {"current": "Pmqtt"},
        "config": {"source": "Linky"},
    }
    assert current_meter_source(data) == "Pmqtt"


def test_current_meter_source_from_config() -> None:
    data = {"sources": {}, "config": {"source": "JsyMk194"}}
    assert current_meter_source(data) == "JsyMk194"


def test_balansun_peer_active() -> None:
    data = {"config": {"source": "BalansunPeer"}, "sources": {}}
    assert balansun_peer_active(data) is True


def test_fallback_single_current_when_no_supported() -> None:
    data = {"sources": {}, "config": {"source": "Pmqtt"}}
    assert source_wire_options(data) == ["Pmqtt"]
