"""Stub Home Assistant so unit tests run without installing homeassistant."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock


def _ensure_stub(name: str) -> MagicMock:
    if name not in sys.modules:
        sys.modules[name] = MagicMock()
    return sys.modules[name]


_ensure_stub("homeassistant")
_const = _ensure_stub("homeassistant.const")
for _name, _val in (
    ("UnitOfPower", type("U", (), {"WATT": "W"})),
    ("UnitOfElectricPotential", type("U", (), {"VOLT": "V"})),
    ("UnitOfElectricCurrent", type("U", (), {"AMPERE": "A"})),
    ("UnitOfEnergy", type("U", (), {"WATT_HOUR": "Wh"})),
    ("UnitOfFrequency", type("U", (), {"HERTZ": "Hz"})),
    ("UnitOfTemperature", type("U", (), {"CELSIUS": "°C"})),
):
    setattr(_const, _name, _val())

for _mod in (
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_registry",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.entity",
    "homeassistant.components.sensor",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.switch",
    "homeassistant.components.number",
    "homeassistant.components.select",
    "homeassistant.components.button",
    "homeassistant.components.text",
    "homeassistant.data_entry_flow",
):
    _ensure_stub(_mod)

_exc = _ensure_stub("homeassistant.exceptions")


class _HomeAssistantError(Exception):
    pass


class _UpdateFailed(Exception):
    pass


_exc.HomeAssistantError = _HomeAssistantError
_exc.UpdateFailed = _UpdateFailed
