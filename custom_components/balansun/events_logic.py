"""Edge detection for Balansun device automation triggers (MQTT parity)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MqttHaEventInput:
    surplus_active: bool = False
    prev_surplus_active: bool = False
    source_stale: bool = False
    prev_source_stale: bool = False
    site_cap_active: bool = False
    prev_site_cap_active: bool = False
    regulation_hunting: bool = False
    prev_regulation_hunting: bool = False
    vacation_active: bool = False
    prev_vacation_active: bool = False
    action_cap_hit: bool = False
    prev_action_cap_hit: bool = False
    linky_tariff: str = ""
    prev_linky_tariff: str = ""
    safety_lockout_active: bool = False
    prev_safety_lockout_active: bool = False


@dataclass
class MqttHaEventOutput:
    surplus_started: bool = False
    surplus_ended: bool = False
    source_lost: bool = False
    triac_cap_hit: bool = False
    linky_tariff_changed: bool = False
    regulation_hunting_started: bool = False
    vacation_ended: bool = False
    action_cap_hit: bool = False
    safety_lockout_started: bool = False
    safety_lockout_cleared: bool = False


def mqtt_ha_events_logic_detect(inp: MqttHaEventInput) -> MqttHaEventOutput:
    """Port of firmware mqtt_ha_events_logic_detect."""
    out = MqttHaEventOutput()
    if inp.surplus_active and not inp.prev_surplus_active:
        out.surplus_started = True
    if not inp.surplus_active and inp.prev_surplus_active:
        out.surplus_ended = True
    if inp.source_stale and not inp.prev_source_stale:
        out.source_lost = True
    if inp.site_cap_active and not inp.prev_site_cap_active:
        out.triac_cap_hit = True
    if inp.regulation_hunting and not inp.prev_regulation_hunting:
        out.regulation_hunting_started = True
    if not inp.vacation_active and inp.prev_vacation_active:
        out.vacation_ended = True
    if inp.action_cap_hit and not inp.prev_action_cap_hit:
        out.action_cap_hit = True
    if inp.linky_tariff != inp.prev_linky_tariff and (
        inp.linky_tariff or inp.prev_linky_tariff
    ):
        out.linky_tariff_changed = True
    if inp.safety_lockout_active and not inp.prev_safety_lockout_active:
        out.safety_lockout_started = True
    if not inp.safety_lockout_active and inp.prev_safety_lockout_active:
        out.safety_lockout_cleared = True
    return out


def fired_subtypes(out: MqttHaEventOutput) -> list[str]:
    """Map output flags to HA device trigger subtypes (matches MQTT discovery)."""
    subtypes: list[str] = []
    if out.surplus_started:
        subtypes.append("surplus_started")
    if out.surplus_ended:
        subtypes.append("surplus_ended")
    if out.source_lost:
        subtypes.append("source_lost")
    if out.triac_cap_hit:
        subtypes.append("triac_cap_hit")
    if out.linky_tariff_changed:
        subtypes.append("linky_tariff_changed")
    if out.regulation_hunting_started:
        subtypes.append("regulation_hunting")
    if out.vacation_ended:
        subtypes.append("vacation_ended")
    if out.action_cap_hit:
        subtypes.append("action_cap_hit")
    if out.safety_lockout_started:
        subtypes.append("safety_lockout_started")
    if out.safety_lockout_cleared:
        subtypes.append("safety_lockout_cleared")
    return subtypes
