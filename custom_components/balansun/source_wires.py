"""Meter source wire labels (GET /api/v1/sources + config.source)."""

from __future__ import annotations

from typing import Any

_SKIP_WIRES = frozenset({"", "NotDef"})


def normalize_source_wire(wire: Any) -> str | None:
    """Return canonical wire string; drop NotDef and empty labels."""
    if wire is None:
        return None
    label = str(wire).strip()
    if not label or label in _SKIP_WIRES:
        return None
    return label


def current_meter_source(data: dict[str, Any]) -> str | None:
    """Active source: prefer sources.current, then config.source."""
    sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
    cfg = data.get("config") if isinstance(data.get("config"), dict) else {}
    raw = sources.get("current") or cfg.get("source")
    return normalize_source_wire(raw)


def _firmware_meters(data: dict[str, Any]) -> list[str] | None:
    device = data.get("device") if isinstance(data.get("device"), dict) else {}
    caps = device.get("capabilities") if isinstance(device.get("capabilities"), dict) else {}
    fc = caps.get("firmware_capabilities") if isinstance(caps.get("firmware_capabilities"), dict) else {}
    meters = fc.get("meters")
    if isinstance(meters, list) and meters:
        return [str(m) for m in meters if str(m) not in _SKIP_WIRES]
    return None


def source_wire_options(data: dict[str, Any]) -> list[str]:
    """Select options from firmware meters[] when advertised; else supported[]."""
    meters = _firmware_meters(data)
    if meters:
        return meters
    options: list[str] = []
    sources = data.get("sources") if isinstance(data.get("sources"), dict) else {}
    supported = sources.get("supported")
    if isinstance(supported, list):
        for entry in supported:
            norm = normalize_source_wire(entry)
            if norm and norm not in options:
                options.append(norm)
    current = current_meter_source(data)
    if current and current not in options:
        options.insert(0, current)
    if options:
        return options
    if current:
        return [current]
    return []
