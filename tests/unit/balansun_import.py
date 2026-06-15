"""Load balansun modules without importing package __init__ (no homeassistant required)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

_PKG = Path(__file__).resolve().parents[2] / "custom_components" / "balansun"
_PKG_NAME = "custom_components.balansun"


def _ensure_balansun_package() -> None:
    for name, path in (
        ("custom_components", _PKG.parent),
        (_PKG_NAME, _PKG),
    ):
        if name in sys.modules:
            continue
        pkg = ModuleType(name)
        pkg.__path__ = [str(path)]
        sys.modules[name] = pkg


def _stub_ha() -> None:
    for name in (
        "homeassistant",
        "homeassistant.config_entries",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.entity_registry",
    ):
        if name not in sys.modules:
            sys.modules[name] = MagicMock()

    const = sys.modules.setdefault("homeassistant.const", MagicMock())
    for cls_name, attrs in (
        ("UnitOfPower", {"WATT": "W"}),
        ("UnitOfElectricPotential", {"VOLT": "V"}),
        ("UnitOfElectricCurrent", {"AMPERE": "A"}),
        ("UnitOfEnergy", {"WATT_HOUR": "Wh"}),
        ("UnitOfFrequency", {"HERTZ": "Hz"}),
        ("UnitOfTemperature", {"CELSIUS": "°C"}),
        ("UnitOfApparentPower", {"VOLT_AMPERE": "VA"}),
    ):
        setattr(const, cls_name, type(cls_name, (), attrs))


def load_module(rel_path: str) -> ModuleType:
    _stub_ha()
    _ensure_balansun_package()
    full_name = f"{_PKG_NAME}.{rel_path.replace('/', '.').replace('.py', '')}"
    if full_name in sys.modules:
        return sys.modules[full_name]
    path = _PKG / rel_path
    spec = importlib.util.spec_from_file_location(full_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_const():
    return load_module("const.py")


def load_integration_mode():
    load_const()
    return load_module("integration_mode.py")


def load_entity_registry():
    load_integration_mode()
    load_module("status_led_rgb.py")
    return load_module("entity_registry.py")


def load_events_logic():
    return load_module("events_logic.py")


def load_config_registry():
    load_entity_registry()
    load_module("regulation_labels.py")
    return load_module("config_registry.py")


def load_status_led_rgb():
    return load_module("status_led_rgb.py")


def load_connection():
    load_const()
    if "aiohttp" not in sys.modules:
        sys.modules["aiohttp"] = MagicMock()
    return load_module("connection.py")


def load_poll_availability():
    load_const()
    return load_module("poll_availability.py")


def load_source_wires():
    load_const()
    return load_module("source_wires.py")


def load_safety_lockout():
    load_entity_registry()
    return load_module("safety_lockout.py")


def load_device_info():
    load_const()
    if "aiohttp" not in sys.modules:
        sys.modules["aiohttp"] = MagicMock()
    coord_name = f"{_PKG_NAME}.coordinator"
    if coord_name not in sys.modules:
        coord_mod = ModuleType(coord_name)
        coord_mod.BalansunCoordinator = MagicMock()  # type: ignore[attr-defined]
        sys.modules[coord_name] = coord_mod
    return load_module("device_info.py")


def _ensure_ha_exceptions() -> None:
    exc_name = "homeassistant.exceptions"
    if exc_name not in sys.modules:
        exc_mod = ModuleType(exc_name)

        class HomeAssistantError(Exception):
            pass

        class UpdateFailed(Exception):
            pass

        exc_mod.HomeAssistantError = HomeAssistantError  # type: ignore[attr-defined]
        exc_mod.UpdateFailed = UpdateFailed  # type: ignore[attr-defined]
        sys.modules[exc_name] = exc_mod


def _stub_update_coordinator() -> None:
    from typing import Generic, TypeVar

    _ensure_ha_exceptions()
    t_coordinator = TypeVar("t_coordinator")
    t_data = TypeVar("t_data")

    class CoordinatorEntity(Generic[t_coordinator]):
        def __init__(self, coordinator=None) -> None:
            self.coordinator = coordinator

    class DataUpdateCoordinator(Generic[t_data]):
        def __init__(self, hass, logger, name, update_interval=None) -> None:
            self.hass = hass
            self.data = None

        async def async_config_entry_first_refresh(self) -> None:
            return None

        async def async_request_refresh(self) -> None:
            return None

    uc_mod = ModuleType("homeassistant.helpers.update_coordinator")
    uc_mod.CoordinatorEntity = CoordinatorEntity  # type: ignore[attr-defined]
    uc_mod.DataUpdateCoordinator = DataUpdateCoordinator  # type: ignore[attr-defined]
    uc_mod.UpdateFailed = sys.modules["homeassistant.exceptions"].UpdateFailed  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.update_coordinator"] = uc_mod


def load_coordinator():
    load_const()
    _stub_ha()
    _stub_update_coordinator()
    if "aiohttp" not in sys.modules:
        import aiohttp  # noqa: F401
    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    load_safety_lockout()
    load_module("poll_availability.py")
    load_module("events_logic.py")
    sys.modules.pop(f"{_PKG_NAME}.coordinator", None)
    return load_module("coordinator.py")


def load_action_node_coordinator():
    load_const()
    _stub_ha()
    _stub_update_coordinator()
    if "aiohttp" not in sys.modules:
        import aiohttp  # noqa: F401
    aiohttp_client = ModuleType("homeassistant.helpers.aiohttp_client")
    aiohttp_client.async_get_clientsession = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    load_module("connection.py")
    return load_module("action_node_coordinator.py")


def load_action_node_climate():
    load_const()
    _stub_ha()
    _stub_update_coordinator()

    climate_ha = ModuleType("homeassistant.components.climate")

    class ClimateEntity:
        pass

    climate_ha.ClimateEntity = ClimateEntity  # type: ignore[attr-defined]
    climate_ha.ClimateEntityFeature = type("ClimateEntityFeature", (), {"PRESET_MODE": 1})  # type: ignore[attr-defined]
    sys.modules["homeassistant.components.climate"] = climate_ha

    entity_mod = ModuleType("homeassistant.helpers.entity")
    entity_mod.DeviceInfo = dict  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.entity"] = entity_mod

    helpers_pkg = sys.modules.setdefault("homeassistant.helpers", ModuleType("helpers"))
    platform_mod = ModuleType("homeassistant.helpers.entity_platform")
    platform_mod.AddEntitiesCallback = MagicMock  # type: ignore[attr-defined]
    sys.modules["homeassistant.helpers.entity_platform"] = platform_mod
    helpers_pkg.entity_platform = platform_mod  # type: ignore[attr-defined]

    coord_mod = load_action_node_coordinator()
    load_module("device_info.py")

    class BalansunWarmCoordinator:
        pass

    warm_name = f"{_PKG_NAME}.warm_coordinator"
    warm_mod = ModuleType(warm_name)
    warm_mod.BalansunWarmCoordinator = BalansunWarmCoordinator  # type: ignore[attr-defined]
    sys.modules[warm_name] = warm_mod
    sys.modules[f"{_PKG_NAME}.action_node_coordinator"] = coord_mod

    return load_module("climate.py")


def load_button():
    load_coordinator()
    load_config_registry()
    _stub_ha()
    _stub_update_coordinator()
    entity_ha = sys.modules.setdefault("homeassistant.helpers.entity", ModuleType("entity"))
    entity_ha.EntityCategory = type(
        "EntityCategory", (), {"CONFIG": "config", "DIAGNOSTIC": "diagnostic"}
    )
    button_ha = sys.modules.setdefault("homeassistant.components.button", ModuleType("button"))

    class ButtonEntity:
        pass

    button_ha.ButtonEntity = ButtonEntity  # type: ignore[attr-defined]
    for mod_name in (f"{_PKG_NAME}.entity", f"{_PKG_NAME}.button"):
        sys.modules.pop(mod_name, None)
    load_module("device_info.py")
    return load_module("button.py")
