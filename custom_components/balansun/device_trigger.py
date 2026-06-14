"""Device automation triggers for rest_only mode (MQTT event parity)."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components import event as event_trigger
from homeassistant.components.device_automation import (
    CONF_SUBTYPE,
    DEVICE_TRIGGER_BASE_SCHEMA,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_PLATFORM, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

TRIGGER_SUBTYPES = (
    "surplus_started",
    "surplus_ended",
    "source_lost",
    "triac_cap_hit",
    "regulation_hunting",
    "vacation_ended",
    "action_cap_hit",
    "linky_tariff_changed",
    "safety_lockout_started",
    "safety_lockout_cleared",
)

TRIGGER_SCHEMA = vol.All(
    DEVICE_TRIGGER_BASE_SCHEMA,
    {
        vol.Required(CONF_TYPE): DOMAIN,
        vol.Required(CONF_SUBTYPE): vol.In(TRIGGER_SUBTYPES),
    },
)


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    """List device triggers for automations UI."""
    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(device_id)
    if device is None or DOMAIN not in device.identifiers:
        return []
    return [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: DOMAIN,
            CONF_SUBTYPE: subtype,
        }
        for subtype in TRIGGER_SUBTYPES
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach listener for balansun device events."""
    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: f"{DOMAIN}_device_event",
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_ID: config[CONF_DEVICE_ID],
                CONF_SUBTYPE: config[CONF_SUBTYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )


async def async_get_trigger_capabilities(hass: HomeAssistant, config: ConfigType) -> dict:
    return {}


async def async_validate_trigger_config(hass: HomeAssistant, config: ConfigType) -> ConfigType:
    return TRIGGER_SCHEMA(config)
