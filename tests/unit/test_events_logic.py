"""Unit tests for mqtt_ha_events_logic port."""

from tests.unit.balansun_import import load_events_logic

events_logic = load_events_logic()
MqttHaEventInput = events_logic.MqttHaEventInput
mqtt_ha_events_logic_detect = events_logic.mqtt_ha_events_logic_detect
fired_subtypes = events_logic.fired_subtypes


def test_surplus_started_edge():
    inp = MqttHaEventInput(surplus_active=True, prev_surplus_active=False)
    out = mqtt_ha_events_logic_detect(inp)
    assert out.surplus_started
    assert "surplus_started" in fired_subtypes(out)


def test_source_lost_edge():
    inp = MqttHaEventInput(source_stale=True, prev_source_stale=False)
    out = mqtt_ha_events_logic_detect(inp)
    assert out.source_lost


def test_linky_tariff_changed():
    inp = MqttHaEventInput(linky_tariff="HC", prev_linky_tariff="HP")
    out = mqtt_ha_events_logic_detect(inp)
    assert out.linky_tariff_changed
