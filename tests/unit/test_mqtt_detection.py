"""Unit tests for MQTT companion detection."""

from __future__ import annotations

from unittest.mock import MagicMock

from tests.unit.balansun_import import load_integration_mode

integration_mode = load_integration_mode()

_device_matches_router_uid = integration_mode._device_matches_router_uid
detect_mqtt_present = integration_mode.detect_mqtt_present
mqtt_entities_for_device = integration_mode.mqtt_entities_for_device


def _make_device(*, identifiers, serial_number=None):
    device = MagicMock()
    device.identifiers = identifiers
    device.serial_number = serial_number
    return device


def test_device_matches_router_uid_by_serial():
    dev = _make_device(identifiers=set(), serial_number="HZ-ABC")
    assert _device_matches_router_uid(dev, "HZ-ABC")


def test_device_matches_router_uid_by_mqtt_ids_tuple():
    dev = _make_device(identifiers={("HZ-ABC",)}, serial_number=None)
    assert _device_matches_router_uid(dev, "HZ-ABC")


def test_device_matches_router_uid_by_pair_identifier():
    dev = _make_device(identifiers={("mqtt", "HZ-ABC")}, serial_number=None)
    assert _device_matches_router_uid(dev, "HZ-ABC")


def test_detect_mqtt_present_finds_entities():
    hass = MagicMock()
    device_id = "mqtt-device-1"
    device = _make_device(identifiers={("HZ-ABC",)}, serial_number="HZ-ABC")
    ent = MagicMock()
    ent.platform = "mqtt"
    ent.device_id = device_id

    reg = MagicMock()
    reg.devices = {device_id: device}
    reg.entities = {"sensor.foo": ent}

    integration_mode.er = MagicMock()
    integration_mode.er.async_get.return_value = reg
    assert detect_mqtt_present(hass, "HZ-ABC") is True
    found = mqtt_entities_for_device(hass, "HZ-ABC")
    assert len(found) == 1


def test_detect_mqtt_present_no_balansun_domain_false_positive():
    hass = MagicMock()
    other_id = "other-device"
    device = _make_device(identifiers={("balansun", "entry-uuid")}, serial_number=None)
    ent = MagicMock()
    ent.platform = "mqtt"
    ent.device_id = other_id
    reg = MagicMock()
    reg.devices = {other_id: device}
    reg.entities = {"sensor.x": ent}
    integration_mode.er = MagicMock()
    integration_mode.er.async_get.return_value = reg
    assert detect_mqtt_present(hass, "HZ-REAL-UID") is False
