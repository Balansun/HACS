# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-06-14

### Added

- Home Assistant **2026.3.0** minimum (`hacs.json`; brand icons on 2026.3.x).
- **`rest_only`** mode (default): full REST entity set via `/api/v1/telemetry/snapshot` and extended diagnostics.
- **`companion`** mode: auto-detect MQTT entities; register **republish discovery** button only.
- Options flow: integration mode and **REST refresh interval** (1 second – 5 minutes, applied live).
- **Reconfigure** flow: change router URL or API token after setup (⋮ menu).
- Multiple routers: add the integration again per base URL.
- Entity registry: sensors, binary sensors, switches, numbers, selects, buttons, lights.
- `rest_only` text entities for Linky/Tempo (`linky_ltarf`, `rte_today`, `rte_tomorrow`).
- Triac and action **AUTO** buttons; measurement sensors (`pv_production_w`, apparent VA, `house_load_w`).
- Effective meter **source_data** sensor when `BalansunPeer` is active.
- RouterConfig customisation entities (fail-safes, Tempo API toggle, regulation tuning, vacation end, per-action daily caps).
- Status LED mode/GPIO/colors and preview test buttons when firmware exposes `status_led_mode` in config.
- Device automation triggers in `rest_only` (surplus, source lost, cap hit, safety lockout, etc.) via poll edge detection.
- Firmware **product profile** parity: entity set gated by `firmware_capabilities` (`surplus_regulation`, `multi_action`, meter pack).
- Diagnostic sensors: `product_profile`, `meter_pack`, `device_lifecycle`, `regulation_motion`, output suspend, **safety lockout**, self-test, `telemetry_ready`.
- Optional derived house sensors (`grid_net_w`, `house_load_w`, `pv_production_w`) — disabled by default.
- CI / release: `hacs/action@main`, `hassfest@master`, gated `release.yaml`, `balansun-hacs.zip` (flat zip root for HACS `zip_release`).
- Nightly GitHub releases only (`vX.Y.Z-nightly.<sha>` from main-branch CI).

### Fixed

- Routing writes under safety lockout: entities unavailable + clear `HomeAssistantError` on 403 (`safety_lockout`, `capability_disabled`).
- Boot / `503 not_ready` on `/measurements` keeps last good data when `telemetry_ready` is false.
- Entities flipping to unavailable after every REST action: sequential router polling, debounced refresh, **Configure** availability options applied.
- Device automation triggers registered with Home Assistant.
- Regulation tuning number ranges (`regulation_gain` 1–99, hunting thresholds per firmware).
