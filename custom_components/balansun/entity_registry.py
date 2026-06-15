"""MQTT discovery parity registry for rest_only HACS entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from .integration_mode import entity_enabled_for_mode

_MIN_SELF_TEST_WALL_EPOCH = 1_000_000_000


@dataclass(frozen=True)
class HelioEntitySpec:
    key: str
    platform: str
    name: str
    companion_allowed: bool = False
    capability: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    native_unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    action_index: int | None = None
    config_key: str | None = None
    entity_category: str | None = None
    writable: bool = True
    select_options: tuple[str, ...] | None = None
    button_action: str | None = None
    status_led_role: str | None = None
    daily_cap_index: int | None = None
    binary_device_class: str | None = None
    translation_key: str | None = None
    icon: str | None = None
    enabled_by_default: bool = True
    number_mode: str | None = None


def _on_off(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).upper() == "ON"


def _snapshot(data: dict[str, Any]) -> dict[str, Any]:
    snap = data.get("snapshot")
    return snap if isinstance(snap, dict) else {}


def _measurements(data: dict[str, Any]) -> dict[str, Any]:
    m = data.get("measurements")
    return m if isinstance(m, dict) else {}


def _diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    m = _measurements(data)
    d = m.get("diagnostics")
    return d if isinstance(d, dict) else {}


def _state(data: dict[str, Any]) -> dict[str, Any]:
    s = data.get("state")
    return s if isinstance(s, dict) else {}


def _status(data: dict[str, Any]) -> dict[str, Any]:
    s = _state(data).get("status")
    return s if isinstance(s, dict) else {}


def _health(data: dict[str, Any]) -> dict[str, Any]:
    h = data.get("health")
    return h if isinstance(h, dict) else {}


def _self_test_last_run_epoch(data: dict[str, Any]) -> int | None:
    st = _health(data).get("self_test")
    if not isinstance(st, dict):
        return None
    raw = st.get("last_run_epoch")
    if raw is None:
        return None
    try:
        epoch = int(raw)
    except (TypeError, ValueError):
        return None
    if epoch < _MIN_SELF_TEST_WALL_EPOCH:
        return None
    return epoch


def _device_caps(data: dict[str, Any]) -> dict[str, Any]:
    device = data.get("device")
    if not isinstance(device, dict):
        return {}
    caps = device.get("capabilities")
    return caps if isinstance(caps, dict) else {}


def _firmware_capabilities(data: dict[str, Any]) -> dict[str, Any]:
    fc = _device_caps(data).get("firmware_capabilities")
    return fc if isinstance(fc, dict) else {}


# Entity key -> (measurements section, field) for CH2 REST parity with nested /measurements JSON.
_SECOND_CHANNEL_MEASUREMENT_KEYS: dict[str, tuple[str, str]] = {
    "second_active_import_w": ("second", "active_import_w"),
    "second_active_export_w": ("second", "active_export_w"),
    "second_voltage_v": ("raw_meter", "voltage_second_v"),
    "second_current_a": ("raw_meter", "current_second_a"),
    "second_power_factor": ("raw_meter", "pf_second"),
    "second_energy_import_wh": ("second", "energy_total_import_wh"),
    "second_energy_export_wh": ("second", "energy_total_export_wh"),
    "second_day_energy_import_wh": ("second", "energy_day_import_wh"),
    "second_day_energy_export_wh": ("second", "energy_day_export_wh"),
    "mains_frequency_hz": ("raw_meter", "freq_hz"),
}


def _temperature_sensors_block(data: dict[str, Any]) -> dict[str, Any]:
    ts = _measurements(data).get("temperature_sensors")
    return ts if isinstance(ts, dict) else {}


def _temperature_sensor_entry(data: dict[str, Any], slot: int) -> dict[str, Any] | None:
    sensors = _temperature_sensors_block(data).get("sensors")
    if not isinstance(sensors, list):
        return None
    for entry in sensors:
        if isinstance(entry, dict) and entry.get("slot") == slot:
            return entry
    return None


def _temperature_reading_valid(value: Any) -> bool:
    if value is None:
        return False
    try:
        return float(value) > -100
    except (TypeError, ValueError):
        return False


def _temperature_sensors_active(data: dict[str, Any]) -> bool:
    sensors = _temperature_sensors_block(data).get("sensors")
    if isinstance(sensors, list):
        for entry in sensors:
            if (
                isinstance(entry, dict)
                and entry.get("enabled")
                and entry.get("valid")
                and _temperature_reading_valid(entry.get("temperature_c"))
            ):
                return True
    for key in ("temperature_c",):
        val = _measurements(data).get(key)
        if val is None:
            val = _state(data).get(key) if isinstance(_state(data), dict) else None
        if val is None:
            val = _snapshot(data).get(key)
        if _temperature_reading_valid(val):
            return True
    return False


def _primary_temperature_slot(data: dict[str, Any]) -> int:
    sensors = _temperature_sensors_block(data).get("sensors")
    if isinstance(sensors, list):
        for entry in sensors:
            if isinstance(entry, dict) and entry.get("primary"):
                try:
                    return int(entry.get("slot", 0))
                except (TypeError, ValueError):
                    return 0
    cfg = data.get("config") or {}
    if isinstance(cfg, dict):
        slots = cfg.get("temperature_slots")
        if isinstance(slots, list):
            for idx, slot_cfg in enumerate(slots):
                if isinstance(slot_cfg, dict) and slot_cfg.get("enabled"):
                    return idx
    return 0


def _primary_temperature_label(data: dict[str, Any]) -> str:
    sensors = _temperature_sensors_block(data).get("sensors")
    if isinstance(sensors, list):
        for entry in sensors:
            if isinstance(entry, dict) and entry.get("primary"):
                label = entry.get("label")
                if label:
                    return str(label)
                slot = entry.get("slot")
                if slot is not None:
                    return f"Temperature slot {int(slot) + 1}"
    cfg = data.get("config") or {}
    if isinstance(cfg, dict):
        slots = cfg.get("temperature_slots")
        primary_slot = _primary_temperature_slot(data)
        if (
            isinstance(slots, list)
            and primary_slot < len(slots)
            and isinstance(slots[primary_slot], dict)
        ):
            label = slots[primary_slot].get("label")
            if label:
                return str(label)
        legacy = cfg.get("temperature_label")
        if legacy:
            return str(legacy)
    device = data.get("device") or {}
    if isinstance(device, dict):
        label = device.get("temperature_label")
        if label:
            return str(label)
    return "Temperature"


def _temperature_slot_display_label(data: dict[str, Any], slot: int, fallback: str) -> str:
    entry = _temperature_sensor_entry(data, slot)
    if entry:
        label = entry.get("label")
        if label:
            return str(label)
    cfg = data.get("config") or {}
    if isinstance(cfg, dict):
        slots = cfg.get("temperature_slots")
        if isinstance(slots, list) and slot < len(slots) and isinstance(slots[slot], dict):
            label = slots[slot].get("label")
            if label:
                return str(label)
    if fallback:
        return fallback
    return f"Temperature slot {slot + 1}"


def _actions_config_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = data.get("actions_config") or {}
    actions = cfg.get("actions") if isinstance(cfg, dict) else None
    if not isinstance(actions, list):
        return []
    return [entry for entry in actions if isinstance(entry, dict)]


def _action_channel_title(data: dict[str, Any], index: int, *, default: str) -> str:
    actions = _actions_config_list(data)
    if index < len(actions):
        title = actions[index].get("title") or actions[index].get("name")
        if title:
            return str(title)
    return default


def _parse_action_index_from_key(key: str) -> int | None:
    if not key.startswith("action_"):
        return None
    rest = key[len("action_") :]
    if rest.endswith("_auto"):
        rest = rest[: -len("_auto")]
    elif rest.endswith("_daily_cap_wh"):
        rest = rest[: -len("_daily_cap_wh")]
    if rest.isdigit():
        return int(rest)
    return None


def iter_temperature_specs(data: dict[str, Any]) -> list[HelioEntitySpec]:
    specs: list[HelioEntitySpec] = []
    sensors = _temperature_sensors_block(data).get("sensors")
    primary_slot = _primary_temperature_slot(data)
    if isinstance(sensors, list):
        for entry in sensors:
            if isinstance(entry, dict) and entry.get("primary"):
                try:
                    primary_slot = int(entry.get("slot", primary_slot))
                except (TypeError, ValueError):
                    primary_slot = 0
                break

    primary_c = _measurements(data).get("temperature_c")
    if primary_c is None:
        primary_c = _state(data).get("temperature_c")
    if primary_c is None:
        primary_c = _snapshot(data).get("temperature_c")
    if _temperature_reading_valid(primary_c) or _temperature_sensors_active(data):
        specs.append(
            HelioEntitySpec(
                key="temperature_c",
                platform="sensor",
                name=_primary_temperature_label(data),
                native_unit=UnitOfTemperature.CELSIUS,
                device_class="temperature",
                state_class="measurement",
                capability="temperature",
            )
        )

    if not isinstance(sensors, list):
        return specs

    for slot in (0, 1):
        if primary_slot is not None and slot == primary_slot:
            continue
        entry = _temperature_sensor_entry(data, slot)
        if not entry or not entry.get("enabled") or not entry.get("valid"):
            continue
        if not _temperature_reading_valid(entry.get("temperature_c")):
            continue
        label = entry.get("label") or f"Temperature slot {slot + 1}"
        specs.append(
            HelioEntitySpec(
                key=f"temperature_slot_{slot}_c",
                platform="sensor",
                name=str(label),
                native_unit=UnitOfTemperature.CELSIUS,
                device_class="temperature",
                state_class="measurement",
                capability="temperature",
            )
        )
    return specs


def _read_second_channel_from_measurements(
    measurements: dict[str, Any], key: str
) -> Any:
    mapping = _SECOND_CHANNEL_MEASUREMENT_KEYS.get(key)
    if not mapping:
        return None
    section, field = mapping
    block = measurements.get(section) or {}
    if not isinstance(block, dict):
        return None
    return block.get(field)


def read_snapshot_key(data: dict[str, Any], key: str) -> Any:
    snap = _snapshot(data)
    if key in snap:
        return snap[key]
    if key == "device_lifecycle":
        health = _health(data)
        if health.get("device_lifecycle") is not None:
            return health.get("device_lifecycle")
        return _status(data).get("device_lifecycle")
    if key == "regulation_motion":
        return _status(data).get("regulation_motion")
    if key == "output_suspend_reason":
        suspend = _health(data).get("output_suspend")
        if not isinstance(suspend, dict):
            suspend = _status(data).get("output_suspend")
        if isinstance(suspend, dict):
            return suspend.get("reason")
        return None
    if key == "product_profile":
        health = _health(data)
        if health.get("product_profile") is not None:
            return health.get("product_profile")
        return _device_caps(data).get("product_profile")
    if key == "meter_pack":
        return _firmware_capabilities(data).get("meter_pack")
    if key == "safety_lockout_reasons":
        from .safety_lockout import safety_lockout_reasons

        reasons = safety_lockout_reasons(data)
        return ", ".join(reasons) if reasons else None
    if key == "self_test_severity_zc":
        st = _health(data).get("self_test")
        if isinstance(st, dict):
            severity = st.get("severity")
            if isinstance(severity, dict) and severity.get("zc") is not None:
                return severity.get("zc")
        return None
    if key == "self_test_last_run":
        return _self_test_last_run_epoch(data)
    if key in ("grid_net_w", "house_load_w", "pv_production_w"):
        house = _measurements(data).get("house") or {}
        if isinstance(house, dict) and key in house:
            return house.get(key)
        return None
    if key.startswith("temperature_slot_") and key.endswith("_c"):
        try:
            slot = int(key[len("temperature_slot_") : -2])
        except ValueError:
            slot = -1
        if slot >= 0:
            entry = _temperature_sensor_entry(data, slot)
            if entry and entry.get("enabled") and entry.get("valid"):
                return entry.get("temperature_c")
    diag = _diagnostics(data)
    if key in diag:
        return diag[key]
    st = _status(data)
    if key in st:
        return st[key]
    state = _state(data)
    if key in state:
        return state[key]
    m = _measurements(data)
    if key in m:
        return m[key]
    raw = m.get("raw_meter") or {}
    if key in raw:
        return raw[key]
    house = m.get("house") or {}
    if key == "house_net_power_w":
        if raw.get("house_net_power_w") is not None:
            return raw.get("house_net_power_w")
        imp = house.get("active_import_w")
        exp = house.get("active_export_w")
        if imp is not None and exp is not None:
            return imp - exp
        return None
    if key in house:
        return house[key]
    second = m.get("second") or {}
    if key in second:
        return second[key]
    return _read_second_channel_from_measurements(m, key)


_PROBE_LABEL_METRIC_SUFFIX: dict[str, tuple[str, str]] = {
    "house_net_power_w": ("house", "net power"),
    "house_active_import_w": ("house", "active import"),
    "house_active_export_w": ("house", "active export"),
    "house_voltage_v": ("house", "voltage"),
    "house_current_a": ("house", "current"),
    "house_power_factor": ("house", "power factor"),
    "house_energy_import_wh": ("house", "energy import"),
    "house_energy_export_wh": ("house", "energy export"),
    "house_day_energy_import_wh": ("house", "day energy import"),
    "house_day_energy_export_wh": ("house", "day energy export"),
    "house_apparent_import_va": ("house", "apparent import"),
    "house_apparent_export_va": ("house", "apparent export"),
    "second_active_import_w": ("second", "active import"),
    "second_active_export_w": ("second", "active export"),
    "second_voltage_v": ("second", "voltage"),
    "second_current_a": ("second", "current"),
    "second_power_factor": ("second", "power factor"),
    "second_energy_import_wh": ("second", "energy import"),
    "second_energy_export_wh": ("second", "energy export"),
    "second_day_energy_import_wh": ("second", "day energy import"),
    "second_day_energy_export_wh": ("second", "day energy export"),
    "second_apparent_import_va": ("second", "apparent import"),
    "second_apparent_export_va": ("second", "apparent export"),
}

_TRIAC_LABELED_KEYS: dict[str, str] = {
    "triac_open_percent": "open",
    "triac_target": "target opening",
    "triac_auto": "regulation auto",
}


def entity_display_name(data: dict[str, Any], key: str, fallback: str) -> str:
    """Friendly name from live API labels when available."""
    if key == "temperature_c":
        return _primary_temperature_label(data)
    if key.startswith("temperature_slot_") and key.endswith("_c"):
        try:
            slot = int(key[len("temperature_slot_") : -2])
        except ValueError:
            return fallback
        if slot >= 0:
            return _temperature_slot_display_label(data, slot, fallback)
    triac_suffix = _TRIAC_LABELED_KEYS.get(key)
    if triac_suffix:
        title = _action_channel_title(data, 0, default="Triac")
        return f"{title} {triac_suffix}"
    action_idx = _parse_action_index_from_key(key)
    if action_idx is not None and action_idx >= 1:
        title = _action_channel_title(data, action_idx, default=f"Action {action_idx}")
        if key.endswith("_auto"):
            return f"{title} auto"
        if key.endswith("_daily_cap_wh"):
            return f"{title} daily cap"
        return title
    mapping = _PROBE_LABEL_METRIC_SUFFIX.get(key)
    if not mapping:
        return fallback
    channel, suffix = mapping
    m = _measurements(data)
    if channel == "house":
        label = str(m.get("probe_house_name") or "").strip() or "House"
    else:
        label = str(m.get("probe_second_name") or "").strip() or "Second channel"
    return f"{label} {suffix}"


def _triac_channel_present(data: dict[str, Any]) -> bool:
    raw = _measurements(data).get("raw_meter") or {}
    if not isinstance(raw, dict):
        raw = {}
    return (
        _snapshot(data).get("second_voltage_v") is not None
        or (_measurements(data).get("second") or {}).get("active_import_w") is not None
        or raw.get("voltage_second_v") is not None
    )


def _balansun_peer_active(data: dict[str, Any]) -> bool:
    from .source_wires import current_meter_source

    return current_meter_source(data) == "BalansunPeer"


def _firmware_cap(data: dict[str, Any], key: str) -> bool:
    fc = _firmware_capabilities(data)
    return fc.get(key) is True


def _multi_action_cap(data: dict[str, Any]) -> bool:
    return _firmware_cap(data, "multi_action")


def _compiled_meter(data: dict[str, Any], wire: str) -> bool:
    fc = _firmware_capabilities(data)
    meters = fc.get("meters")
    if isinstance(meters, list) and meters:
        return wire in meters
    return True


def _linky_cap(data: dict[str, Any]) -> bool:
    if not _compiled_meter(data, "Linky"):
        return False
    fc = _firmware_capabilities(data)
    meters = fc.get("meters")
    if isinstance(meters, list) and meters:
        return "Linky" in meters
    return (
        _measurements(data).get("linky_tariff") is not None
        or _snapshot(data).get("linky_ltarf") is not None
    )


def _config(data: dict[str, Any]) -> dict[str, Any]:
    cfg = data.get("config")
    return cfg if isinstance(cfg, dict) else {}


def _surplus_regulation_enabled(data: dict[str, Any]) -> bool:
    fc = _firmware_capabilities(data)
    if "surplus_regulation" in fc:
        return fc.get("surplus_regulation") is True
    return _triac_channel_present(data)


def _has_status_led(data: dict[str, Any]) -> bool:
    cfg = data.get("config") or {}
    return isinstance(cfg, dict) and "status_led_mode" in cfg


CAPABILITY_CHECKS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "surplus_regulation": _surplus_regulation_enabled,
    "triac": _surplus_regulation_enabled,
    "triac_channel": _surplus_regulation_enabled,
    "multi_action": _multi_action_cap,
    "temperature": _temperature_sensors_active,
    "linky": lambda d: _linky_cap(d),
    "pmqtt": lambda d: _compiled_meter(d, "Pmqtt"),
    "enphase": lambda d: _compiled_meter(d, "Enphase"),
    "analog": lambda d: _compiled_meter(d, "Analog"),
    "jsy_mk333": lambda d: _compiled_meter(d, "JsyMk333"),
    "tempo": lambda d: _snapshot(d).get("rte_today") is not None,
    "balansun_peer": _balansun_peer_active,
    "status_led": _has_status_led,
    "self_test_triac": lambda d: _firmware_cap(d, "self_test_triac"),
}


def capability_enabled(data: dict[str, Any], cap: str | None) -> bool:
    if not cap:
        return True
    check = CAPABILITY_CHECKS.get(cap)
    return check(data) if check else True


def firmware_capabilities(data: dict[str, Any]) -> dict[str, Any]:
    return _firmware_capabilities(data)


def iter_action_specs(data: dict[str, Any]) -> list[HelioEntitySpec]:
    cfg = data.get("actions_config") or {}
    actions = cfg.get("actions") if isinstance(cfg, dict) else None
    if not isinstance(actions, list):
        return []
    specs: list[HelioEntitySpec] = []
    for idx, ch in enumerate(actions):
        if idx == 0:
            continue
        if not isinstance(ch, dict):
            continue
        title = str(ch.get("title") or ch.get("name") or f"Action {idx}")
        specs.append(
            HelioEntitySpec(
                key=f"action_{idx}",
                platform="switch",
                name=title,
                capability="multi_action",
                action_index=idx,
            )
        )
    return specs


STATIC_ENTITIES: tuple[HelioEntitySpec, ...] = (
    HelioEntitySpec(
        key="republish_discovery",
        platform="button",
        name="Republish MQTT discovery",
        companion_allowed=True,
        entity_category="diagnostic",
        icon="mdi:mqtt",
    ),
    HelioEntitySpec(
        key="device_reboot",
        platform="button",
        name="Reboot device",
        button_action="device_reboot",
        companion_allowed=True,
        entity_category="diagnostic",
        icon="mdi:restart",
    ),
    HelioEntitySpec(
        key="house_net_power_w",
        platform="sensor",
        name="House net power",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_active_import_w",
        platform="sensor",
        name="House active import",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_active_export_w",
        platform="sensor",
        name="House active export",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_voltage_v",
        platform="sensor",
        name="House voltage",
        native_unit=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_current_a",
        platform="sensor",
        name="House current",
        native_unit=UnitOfElectricCurrent.AMPERE,
        device_class="current",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_power_factor",
        platform="sensor",
        name="House power factor",
        device_class="power_factor",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_energy_import_wh",
        platform="sensor",
        name="House energy import",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
    ),
    HelioEntitySpec(
        key="house_energy_export_wh",
        platform="sensor",
        name="House energy export",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
    ),
    HelioEntitySpec(
        key="house_day_energy_import_wh",
        platform="sensor",
        name="House day energy import",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
    ),
    HelioEntitySpec(
        key="house_day_energy_export_wh",
        platform="sensor",
        name="House day energy export",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
    ),
    HelioEntitySpec(
        key="triac_open_percent",
        platform="sensor",
        name="Triac open",
        native_unit="%",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="source_health",
        platform="sensor",
        name="Source health",
        state_class="measurement",
        native_unit="%",
        entity_category="diagnostic",
        icon="mdi:heart-pulse",
    ),
    HelioEntitySpec(
        key="second_active_import_w",
        platform="sensor",
        name="Second active import",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_active_export_w",
        platform="sensor",
        name="Second active export",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_voltage_v",
        platform="sensor",
        name="Second voltage",
        native_unit=UnitOfElectricPotential.VOLT,
        device_class="voltage",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_current_a",
        platform="sensor",
        name="Second current",
        native_unit=UnitOfElectricCurrent.AMPERE,
        device_class="current",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_power_factor",
        platform="sensor",
        name="Second power factor",
        device_class="power_factor",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_energy_import_wh",
        platform="sensor",
        name="Second energy import",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_energy_export_wh",
        platform="sensor",
        name="Second energy export",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_day_energy_import_wh",
        platform="sensor",
        name="Second day energy import",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_day_energy_export_wh",
        platform="sensor",
        name="Second day energy export",
        native_unit=UnitOfEnergy.WATT_HOUR,
        device_class="energy",
        state_class="total_increasing",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="mains_frequency_hz",
        platform="sensor",
        name="Mains frequency",
        native_unit=UnitOfFrequency.HERTZ,
        device_class="frequency",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="tariff_code",
        platform="sensor",
        name="Tariff code",
        capability="linky",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:transmission-tower",
    ),
    HelioEntitySpec(
        key="house_apparent_import_va",
        platform="sensor",
        name="House apparent import",
        native_unit=UnitOfApparentPower.VOLT_AMPERE,
        device_class="apparent_power",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="house_apparent_export_va",
        platform="sensor",
        name="House apparent export",
        native_unit=UnitOfApparentPower.VOLT_AMPERE,
        device_class="apparent_power",
        state_class="measurement",
    ),
    HelioEntitySpec(
        key="second_apparent_import_va",
        platform="sensor",
        name="Second apparent import",
        native_unit=UnitOfApparentPower.VOLT_AMPERE,
        device_class="apparent_power",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="second_apparent_export_va",
        platform="sensor",
        name="Second apparent export",
        native_unit=UnitOfApparentPower.VOLT_AMPERE,
        device_class="apparent_power",
        state_class="measurement",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="source_data",
        platform="sensor",
        name="Effective meter source",
        capability="balansun_peer",
        writable=False,
        entity_category="diagnostic",
        icon="mdi:swap-horizontal",
    ),
    HelioEntitySpec(
        key="linky_ltarf",
        platform="sensor",
        name="Linky tariff option",
        capability="linky",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:transmission-tower",
    ),
    HelioEntitySpec(
        key="rte_today",
        platform="sensor",
        name="RTE today",
        capability="tempo",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:calendar-clock",
    ),
    HelioEntitySpec(
        key="rte_tomorrow",
        platform="sensor",
        name="RTE tomorrow",
        capability="tempo",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:calendar-clock",
    ),
    HelioEntitySpec(
        key="device_lifecycle",
        platform="sensor",
        name="Device lifecycle",
        entity_category="diagnostic",
        icon="mdi:state-machine",
    ),
    HelioEntitySpec(
        key="regulation_motion",
        platform="sensor",
        name="Regulation motion",
        capability="surplus_regulation",
        entity_category="diagnostic",
        icon="mdi:chart-timeline-variant",
    ),
    HelioEntitySpec(
        key="output_suspended",
        platform="binary_sensor",
        name="Output suspended",
        capability="surplus_regulation",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:pause-circle",
    ),
    HelioEntitySpec(
        key="output_suspend_reason",
        platform="sensor",
        name="Output suspend reason",
        capability="surplus_regulation",
        entity_category="diagnostic",
        icon="mdi:information-outline",
    ),
    HelioEntitySpec(
        key="adc_clipping",
        platform="binary_sensor",
        name="ADC clipping",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:chart-bell-curve-cumulative",
    ),
    HelioEntitySpec(
        key="regulation_hunting",
        platform="binary_sensor",
        name="Regulation hunting",
        capability="surplus_regulation",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:sync-alert",
    ),
    HelioEntitySpec(
        key="source_stale",
        platform="binary_sensor",
        name="Source stale",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:connection",
    ),
    HelioEntitySpec(
        key="regulation_active",
        platform="binary_sensor",
        name="Regulation active",
        capability="surplus_regulation",
        entity_category="diagnostic",
        binary_device_class="running",
        icon="mdi:flash",
    ),
    HelioEntitySpec(
        key="mqtt_connected",
        platform="binary_sensor",
        name="MQTT connected",
        entity_category="diagnostic",
        binary_device_class="connectivity",
        icon="mdi:lan-connect",
    ),
    HelioEntitySpec(
        key="site_cap_active",
        platform="binary_sensor",
        name="Site power cap active",
        capability="surplus_regulation",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:speedometer",
    ),
    HelioEntitySpec(
        key="heater_load_backoff_active",
        platform="binary_sensor",
        name="Routed load backoff active",
        capability="surplus_regulation",
        entity_category="diagnostic",
        binary_device_class="running",
        icon="mdi:heating-coil",
    ),
    HelioEntitySpec(
        key="vacation",
        platform="switch",
        name="Vacation mode",
        icon="mdi:palm-tree",
    ),
    HelioEntitySpec(
        key="max_routed_w",
        platform="number",
        name="Max routed power",
        native_unit=UnitOfPower.WATT,
        min_value=0,
        max_value=20000,
        step=100,
        icon="mdi:flash",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="triac_target",
        platform="number",
        name="Target triac opening",
        native_unit="%",
        min_value=0,
        max_value=100,
        step=1,
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="source",
        platform="select",
        name="Meter source",
        config_key="source",
        icon="mdi:electric-switch",
    ),
    HelioEntitySpec(
        key="triac_auto",
        platform="button",
        name="Triac regulation auto",
        button_action="triac_auto",
        icon="mdi:flash-auto",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="product_profile",
        platform="sensor",
        name="Product profile",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:chip",
    ),
    HelioEntitySpec(
        key="meter_pack",
        platform="sensor",
        name="Meter pack",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:meter-electric",
    ),
    HelioEntitySpec(
        key="safety_lockout_active",
        platform="binary_sensor",
        name="Safety lockout",
        entity_category="diagnostic",
        binary_device_class="problem",
        icon="mdi:shield-lock",
    ),
    HelioEntitySpec(
        key="safety_lockout_reasons",
        platform="sensor",
        name="Safety lockout reasons",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:shield-alert",
    ),
    HelioEntitySpec(
        key="self_test_running",
        platform="binary_sensor",
        name="Self-test running",
        entity_category="diagnostic",
        binary_device_class="running",
        icon="mdi:progress-wrench",
    ),
    HelioEntitySpec(
        key="self_test_severity_zc",
        platform="sensor",
        name="Self-test ZC severity",
        entity_category="diagnostic",
        writable=False,
        icon="mdi:waveform",
    ),
    HelioEntitySpec(
        key="self_test_last_run",
        platform="sensor",
        name="Self-test last run",
        entity_category="diagnostic",
        writable=False,
        device_class="timestamp",
        capability="self_test_triac",
        icon="mdi:calendar-clock",
    ),
    HelioEntitySpec(
        key="self_test_run",
        platform="button",
        name="Run self-test",
        button_action="self_test_run",
        capability="self_test_triac",
        companion_allowed=True,
        entity_category="diagnostic",
        icon="mdi:play-circle-outline",
    ),
    HelioEntitySpec(
        key="telemetry_ready",
        platform="binary_sensor",
        name="Telemetry ready",
        entity_category="diagnostic",
        binary_device_class="connectivity",
        icon="mdi:transmission-tower",
    ),
    HelioEntitySpec(
        key="grid_net_w",
        platform="sensor",
        name="Grid net power",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
        enabled_by_default=False,
    ),
    HelioEntitySpec(
        key="house_load_w",
        platform="sensor",
        name="House load",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
        enabled_by_default=False,
    ),
    HelioEntitySpec(
        key="pv_production_w",
        platform="sensor",
        name="PV production",
        native_unit=UnitOfPower.WATT,
        device_class="power",
        state_class="measurement",
        enabled_by_default=False,
    ),
)


def _config_key(spec: HelioEntitySpec) -> str:
    return spec.config_key or spec.key


def read_config_value(data: dict[str, Any], spec: HelioEntitySpec) -> Any:
    cfg = data.get("config") or {}
    if not isinstance(cfg, dict):
        return None
    key = _config_key(spec)
    if spec.daily_cap_index is not None:
        caps = cfg.get("action_daily_cap_wh")
        if isinstance(caps, list) and spec.daily_cap_index < len(caps):
            return caps[spec.daily_cap_index]
        return 0
    if spec.key == "source_data":
        sources = data.get("sources") or {}
        device = data.get("device") or {}
        if isinstance(sources, dict) and sources.get("current_data"):
            return sources.get("current_data")
        if isinstance(device, dict) and device.get("source_data"):
            return device.get("source_data")
        m = data.get("measurements") or {}
        return m.get("source")
    return cfg.get(key)


def entities_for_mode(
    data: dict[str, Any], mode: str, platform: str | None = None
) -> list[HelioEntitySpec]:
    from .config_registry import (
        CONFIG_ENTITIES,
        iter_action_auto_buttons,
        iter_daily_cap_specs,
        status_led_entities,
    )
    from .const import MODE_COMPANION, MODE_REST_ONLY

    candidates: list[HelioEntitySpec] = list(STATIC_ENTITIES)
    if mode == MODE_REST_ONLY:
        candidates.extend(CONFIG_ENTITIES)
        candidates.extend(status_led_entities())
        candidates.extend(iter_daily_cap_specs(data))
        candidates.extend(iter_action_specs(data))
        candidates.extend(iter_temperature_specs(data))
        candidates.extend(iter_action_auto_buttons(data))

    out: list[HelioEntitySpec] = []
    for spec in candidates:
        if platform and spec.platform != platform:
            continue
        if mode == MODE_COMPANION:
            if not spec.companion_allowed:
                continue
        elif not entity_enabled_for_mode(spec.key, mode):
            continue
        if not capability_enabled(data, spec.capability):
            continue
        out.append(spec)
    return out


def read_binary_value(data: dict[str, Any], key: str) -> bool | None:
    if key == "vacation":
        cfg = data.get("config") or {}
        if "vacation_enabled" not in cfg:
            return None
        return bool(cfg.get("vacation_enabled"))
    if key == "safety_lockout_active":
        from .safety_lockout import safety_lockout_active

        return safety_lockout_active(data)
    if key == "self_test_running":
        st = _health(data).get("self_test")
        if isinstance(st, dict) and "running" in st:
            return bool(st.get("running"))
        return None
    if key == "telemetry_ready":
        health = _health(data)
        if "telemetry_ready" in health:
            return bool(health.get("telemetry_ready"))
        return None
    raw = read_snapshot_key(data, key)
    if key == "output_suspended":
        suspend = _health(data).get("output_suspend")
        if not isinstance(suspend, dict):
            suspend = _status(data).get("output_suspend")
        if isinstance(suspend, dict) and "active" in suspend:
            return bool(suspend.get("active"))
        return None
    if key in ("adc_clipping", "regulation_hunting", "source_stale", "regulation_active",
               "mqtt_connected", "site_cap_active", "heater_load_backoff_active"):
        if raw is None:
            raw = _diagnostics(data).get(key)
        return _on_off(raw)
    if key.startswith("action_"):
        return _on_off(raw)
    return _on_off(raw)
