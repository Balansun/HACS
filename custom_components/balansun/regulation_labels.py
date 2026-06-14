"""Human-readable select labels for RouterConfig enums."""

from __future__ import annotations

EXPERT_REGULATION_LABEL_INTEGRAL = "Integral only"
EXPERT_REGULATION_LABEL_PID = "PID (Kp/Ki/Kd)"
EXPERT_REGULATION_LABELS: tuple[str, ...] = (
    EXPERT_REGULATION_LABEL_INTEGRAL,
    EXPERT_REGULATION_LABEL_PID,
)

STATUS_LED_MODE_API_TO_LABEL: dict[str, str] = {
    "off": "Off",
    "dual_gpio": "Dual GPIO",
    "rgb_ws2812": "RGB (WS2812)",
}
STATUS_LED_MODE_LABEL_TO_API: dict[str, str] = {
    label: api for api, label in STATUS_LED_MODE_API_TO_LABEL.items()
}
STATUS_LED_MODE_LABELS: tuple[str, ...] = tuple(STATUS_LED_MODE_API_TO_LABEL.values())


def expert_regulation_label(value: object | None) -> str:
    try:
        v = int(value) if value is not None else 0
    except (TypeError, ValueError):
        return EXPERT_REGULATION_LABEL_INTEGRAL
    return EXPERT_REGULATION_LABEL_PID if v > 0 else EXPERT_REGULATION_LABEL_INTEGRAL


def expert_regulation_value(label: str) -> int:
    return 1 if label == EXPERT_REGULATION_LABEL_PID else 0


def status_led_mode_label(api_value: object | None) -> str | None:
    if api_value is None:
        return None
    return STATUS_LED_MODE_API_TO_LABEL.get(str(api_value))


def status_led_mode_api_value(label: str) -> str:
    return STATUS_LED_MODE_LABEL_TO_API.get(label, label)
