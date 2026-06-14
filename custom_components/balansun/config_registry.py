"""RouterConfig and status LED entity specs (rest_only customisations)."""

from __future__ import annotations

from typing import Any

from homeassistant.const import UnitOfEnergy, UnitOfTemperature

from .entity_registry import HelioEntitySpec
from .regulation_labels import EXPERT_REGULATION_LABELS, STATUS_LED_MODE_LABELS
from .source_wires import current_meter_source, source_wire_options
from .status_led_rgb import DEFAULT_HEX

__all__ = ("current_meter_source", "source_wire_options")


def _config(cfg: dict[str, Any], key: str, default: Any = None) -> Any:
    return cfg.get(key, default) if isinstance(cfg, dict) else default


def has_status_led_config(data: dict[str, Any]) -> bool:
    cfg = data.get("config") or {}
    return isinstance(cfg, dict) and "status_led_mode" in cfg


def balansun_peer_active(data: dict[str, Any]) -> bool:
    return current_meter_source(data) == "BalansunPeer"


CONFIG_ENTITIES: tuple[HelioEntitySpec, ...] = (
    HelioEntitySpec(
        key="triac_off_when_source_stale",
        platform="switch",
        name="Triac off when source stale",
        config_key="triac_off_when_source_stale",
        entity_category="config",
        icon="mdi:flash-off",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="triac_backoff_when_heater_idle",
        platform="switch",
        name="Triac backoff when heater idle",
        config_key="triac_backoff_when_heater_idle",
        entity_category="config",
        icon="mdi:heating-coil",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="mqtt_json_commands",
        platform="switch",
        name="MQTT JSON config commands",
        config_key="mqtt_json_commands",
        entity_category="config",
        icon="mdi:code-json",
    ),
    HelioEntitySpec(
        key="tempo_rte_enabled",
        platform="switch",
        name="Tempo colors via API",
        config_key="tempo_rte_enabled",
        entity_category="config",
        icon="mdi:cloud-download",
        capability="linky",
    ),
    HelioEntitySpec(
        key="vacation_end",
        platform="datetime",
        name="Vacation end",
        config_key="vacation_end_epoch",
        entity_category="config",
        icon="mdi:calendar-end",
    ),
    HelioEntitySpec(
        key="triac_override_max_temp_c",
        platform="number",
        name="Triac max temperature cap",
        config_key="triac_override_max_temp_c",
        entity_category="config",
        native_unit=UnitOfTemperature.CELSIUS,
        min_value=0,
        max_value=120,
        step=1,
        number_mode="box",
        icon="mdi:thermometer-high",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="regulation_gain",
        platform="number",
        name="Regulation gain",
        config_key="regulation_gain",
        entity_category="config",
        min_value=1,
        max_value=99,
        step=1,
        number_mode="slider",
        icon="mdi:tune",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="hunting_reversal_threshold",
        platform="number",
        name="Hunting reversal threshold",
        config_key="hunting_reversal_threshold",
        entity_category="config",
        min_value=3,
        max_value=30,
        step=1,
        number_mode="slider",
        icon="mdi:chart-timeline-variant",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="hunting_window_min",
        platform="number",
        name="Hunting window",
        config_key="hunting_window_min",
        entity_category="config",
        min_value=2,
        max_value=30,
        step=1,
        number_mode="slider",
        icon="mdi:target",
        capability="surplus_regulation",
    ),
    HelioEntitySpec(
        key="expert_regulation_mode",
        platform="select",
        name="Expert regulation mode",
        config_key="expert_regulation_mode",
        entity_category="config",
        select_options=EXPERT_REGULATION_LABELS,
        icon="mdi:chart-bell-curve",
        capability="surplus_regulation",
    ),
)


def status_led_entities() -> tuple[HelioEntitySpec, ...]:
    return (
        HelioEntitySpec(
            key="status_led_mode",
            platform="select",
            name="Status LED mode",
            config_key="status_led_mode",
            entity_category="config",
            select_options=STATUS_LED_MODE_LABELS,
            capability="status_led",
            icon="mdi:led-on",
        ),
        HelioEntitySpec(
            key="status_led_gpio_activity",
            platform="number",
            name="Status LED GPIO activity",
            config_key="status_led_gpio_activity",
            entity_category="config",
            min_value=-1,
            max_value=48,
            step=1,
            number_mode="box",
            capability="status_led",
            icon="mdi:gpio",
        ),
        HelioEntitySpec(
            key="status_led_gpio_regulation",
            platform="number",
            name="Status LED GPIO regulation",
            config_key="status_led_gpio_regulation",
            entity_category="config",
            min_value=-1,
            max_value=48,
            step=1,
            number_mode="box",
            capability="status_led",
            icon="mdi:gpio",
        ),
        HelioEntitySpec(
            key="status_led_rgb_gpio",
            platform="number",
            name="Status LED RGB GPIO",
            config_key="status_led_rgb_gpio",
            entity_category="config",
            min_value=-1,
            max_value=48,
            step=1,
            number_mode="box",
            capability="status_led",
            icon="mdi:gpio",
        ),
        HelioEntitySpec(
            key="status_led_active_low",
            platform="switch",
            name="Status LED active low",
            config_key="status_led_active_low",
            entity_category="config",
            capability="status_led",
            icon="mdi:invert-colors",
        ),
        HelioEntitySpec(
            key="status_led_color_activity",
            platform="light",
            name="Status LED color activity",
            config_key="status_led_color_activity",
            entity_category="config",
            capability="status_led",
            icon="mdi:palette",
        ),
        HelioEntitySpec(
            key="status_led_color_regulation",
            platform="light",
            name="Status LED color regulation",
            config_key="status_led_color_regulation",
            entity_category="config",
            capability="status_led",
            icon="mdi:palette",
        ),
        HelioEntitySpec(
            key="status_led_color_reboot",
            platform="light",
            name="Status LED color reboot",
            config_key="status_led_color_reboot",
            entity_category="config",
            capability="status_led",
            icon="mdi:palette",
        ),
        HelioEntitySpec(
            key="status_led_color_ap",
            platform="light",
            name="Status LED color AP",
            config_key="status_led_color_ap",
            entity_category="config",
            capability="status_led",
            icon="mdi:palette",
        ),
        HelioEntitySpec(
            key="status_led_test_activity",
            platform="button",
            name="Test status LED activity",
            button_action="status_led_test",
            status_led_role="activity",
            capability="status_led",
            entity_category="config",
            icon="mdi:gesture-tap-button",
        ),
        HelioEntitySpec(
            key="status_led_test_regulation",
            platform="button",
            name="Test status LED regulation",
            button_action="status_led_test",
            status_led_role="regulation",
            capability="status_led",
            entity_category="config",
            icon="mdi:gesture-tap-button",
        ),
        HelioEntitySpec(
            key="status_led_test_both",
            platform="button",
            name="Test status LED both",
            button_action="status_led_test",
            status_led_role="both",
            capability="status_led",
            entity_category="config",
            icon="mdi:gesture-tap-button",
        ),
        HelioEntitySpec(
            key="status_led_test_reboot",
            platform="button",
            name="Test status LED reboot",
            button_action="status_led_test",
            status_led_role="reboot",
            capability="status_led",
            entity_category="config",
            icon="mdi:gesture-tap-button",
        ),
        HelioEntitySpec(
            key="status_led_test_ap",
            platform="button",
            name="Test status LED AP",
            button_action="status_led_test",
            status_led_role="ap",
            capability="status_led",
            entity_category="config",
            icon="mdi:gesture-tap-button",
        ),
    )


def iter_daily_cap_specs(data: dict[str, Any]) -> list[HelioEntitySpec]:
    cfg = data.get("config") or {}
    caps = cfg.get("action_daily_cap_wh") if isinstance(cfg, dict) else None
    if not isinstance(caps, list):
        actions_cfg = data.get("actions_config") or {}
        nb = actions_cfg.get("nb_actions") if isinstance(actions_cfg, dict) else 0
        try:
            n = int(nb or 0)
        except (TypeError, ValueError):
            n = 0
        caps = [0] * n if n > 0 else []
    specs: list[HelioEntitySpec] = []
    for idx in range(1, len(caps)):
        specs.append(
            HelioEntitySpec(
                key=f"action_{idx}_daily_cap_wh",
                platform="number",
                name=f"Action {idx} daily cap",
                config_key="action_daily_cap_wh",
                entity_category="config",
                native_unit=UnitOfEnergy.WATT_HOUR,
                min_value=0,
                max_value=100000,
                step=100,
                daily_cap_index=idx,
                number_mode="box",
                icon="mdi:lightning-bolt",
            )
        )
    return specs


def iter_action_auto_buttons(data: dict[str, Any]) -> list[HelioEntitySpec]:
    from .entity_registry import iter_action_specs

    specs: list[HelioEntitySpec] = []
    for action in iter_action_specs(data):
        specs.append(
            HelioEntitySpec(
                key=f"{action.key}_auto",
                platform="button",
                name=f"{action.name} auto",
                button_action="action_auto",
                action_index=action.action_index,
                icon="mdi:flash-auto",
            )
        )
    return specs


def default_hex_for_color_key(key: str) -> str:
    return DEFAULT_HEX.get(key, "#000000")
