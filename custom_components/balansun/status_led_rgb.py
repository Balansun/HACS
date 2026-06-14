"""RGB hex helpers for status LED config (web parity)."""

from __future__ import annotations

Rgb = tuple[int, int, int]

DEFAULT_HEX = {
    "status_led_color_activity": "#ffb400",
    "status_led_color_regulation": "#00ff00",
    "status_led_color_reboot": "#ff0000",
    "status_led_color_ap": "#6600ff",
}


def rgb_to_hex(rgb: list | tuple | None, fallback: str) -> str:
    if not rgb or len(rgb) < 3:
        return fallback
    try:
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    except (TypeError, ValueError):
        return fallback
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_value: str) -> Rgb:
    v = hex_value.replace("#", "").strip()
    if len(v) != 6:
        return (0, 0, 0)
    n = int(v, 16)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def rgb_list(hex_value: str) -> list[int]:
    r, g, b = hex_to_rgb(hex_value)
    return [r, g, b]
