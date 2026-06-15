<p align="center">
  <a href="https://github.com/Balansun/ESP32-router">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/brand/balansun-logo-dark.svg" />
      <img src="assets/brand/balansun-logo-light.svg" alt="Balansun" width="420" />
    </picture>
  </a>
</p>

# Balansun — Home Assistant (HACS)

<p align="center">
  <img src="https://img.shields.io/badge/license-EUPL--1.2-blue" alt="EUPL-1.2" />
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=Balansun&repository=HACS&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_integration.svg" alt="Open in HACS" />
  </a>
</p>

**Requires Home Assistant 2026.3.0 or newer** (inline integration brand images in `brand/`). Lovelace starter dashboards target **2026.4+** (sections view).

Optional [Home Assistant](https://www.home-assistant.io/) custom integration for [Balansun](https://github.com/Balansun/ESP32-router) PV excess routers. Polls the router REST API (`/api/v1/measurements`) when you prefer UI setup over hand-edited MQTT YAML.

**MQTT discovery on the router remains the supported default.**

Source repository: **[HACS](https://github.com/Balansun/HACS)**.

## Brand icons

Integration icons/logos ship in [`custom_components/balansun/brand/`](custom_components/balansun/brand/) (`icon.png`, `logo.png`, `@2x` and `dark_*` variants) for [Home Assistant 2026.3+ inline brand images](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/). Sources: [`assets/brand/`](assets/brand/) (synced from [Balansun Router (ESP32-router)](https://github.com/Balansun/ESP32-router)); regenerate with `npm run prepare:brand` (set `BALANSUN_ROUTER_ROOT` when the firmware tree is not a sibling directory; `BALANSUN_ESP32_ROOT` is a deprecated alias).

## Install

1. In HACS: **Settings → Custom repositories** → add `https://github.com/Balansun/HACS` (category **Integration**). No repository subpath.
2. Install **Balansun** from HACS (**Releases** tab → newest **nightly pre-release**, e.g. `v0.1.0-nightly.<sha>`) and restart Home Assistant.
3. **Settings → Devices & services → Add integration → Balansun**.
4. Enter `http://<router-ip>` and optional API token (router **More → API** permanent access tokens when HTTP API protection is enabled).

**Manual install:** copy [`custom_components/balansun/`](https://github.com/Balansun/HACS/tree/main/custom_components/balansun) into your HA `config/custom_components/` directory, restart, then add the integration as above.

**Multiple routers:** add the integration again for each router base URL; each device is labeled with that router’s `router_name` from the API.

**After setup:**

| Home Assistant action | What it changes |
|---------------------|-----------------|
| **Configure** (integration card) | Integration mode (`companion` / `rest_only`, reloads entities when changed) and **REST refresh interval** (1 s – 5 min, applied immediately) |
| **Reconfigure** (⋮ menu on the integration) | Router base URL (IP/hostname) and API token — leave token empty to keep the current token |

**MQTT pack:** router MQTT discovery remains the default for automations and device triggers. See the [ESP32-router](https://github.com/Balansun/ESP32-router) README and [`integrations/README.md`](https://github.com/Balansun/ESP32-router/blob/main/integrations/README.md).

### Balansun missing from “Add integration”?

1. **Settings → System → Logs** — search for `balansun`. An `ImportError` or version message means the custom component did not load (fix the error, or upgrade Home Assistant to **2026.3+**).
2. Confirm the folder exists: `config/custom_components/balansun/manifest.json` (not `custom_components/balansun/balansun/` — if nested, remove the folder, **Redownload** the latest nightly release, restart).
3. In HACS, open **Balansun →** use **Redownload** and pick the latest **Release** (not a hidden/empty default branch). Restart Home Assistant.
4. If you previously installed a broken release zip, remove `config/custom_components/balansun`, redownload the latest nightly release, restart, then add the integration again.

**Initial release 0.1.0:** per-router `unique_id` (`{config_entry_id}_{key}`), HA brand icons, `issue_tracker` in manifest, and device **Open router UI** link (`configuration_url`).

## Entities

`unique_id` = `{config_entry_id}_{key}` per router. Pick entities from **Developer tools → States** or the device page.

| Mode | Entities |
|------|----------|
| **`rest_only`** (default) | Full MQTT discovery parity via REST (sensors, binary sensors, vacation, triac, actions, …) |
| **`companion`** | Action buttons only when MQTT discovery is active: **Republish MQTT discovery**, **Run self-test** (router profiles), **Reboot device** — no duplicate sensors |

Configure mode and REST refresh interval (1 s – 5 min) under **Settings → Devices & services → Balansun → Configure** (changes apply without restart).

Diagnostics: **Settings → Devices → Diagnostics** (redacted token, effective mode, snapshot keys).

## When to use HACS vs MQTT

| Use MQTT | Use HACS |
|----------|----------|
| Default install | REST-only LAN (`rest_only`) |
| Broker automations & device triggers | UI setup without editing discovery YAML |
| Lowest latency MQTT commands | Full entity surface when no MQTT entities |

**Hybrid:** default is **rest_only** (full HACS entities). If MQTT discovery is already active on the router, open **Configure** and switch to **companion** so HACS does not duplicate MQTT sensors (HACS still adds republish, self-test, and reboot buttons).

**Reboot device** schedules a router restart (~500 ms); the device is briefly unavailable. There is no confirmation dialog in Home Assistant.

## Development

REST poll and entity writes share one Home Assistant `aiohttp` clientsession on the data coordinator (`coordinator.py`). Add new REST platforms via `async_patch_config` / `async_post_mqtt_discover` rather than new `ClientSession()` instances.

**CI (every PR):** `./scripts/test-unit.sh` (compileall, `pytest -m "not hardware"`), `home-assistant/actions/hassfest@master`, and `hacs/action@main`.

**Hardware REST contract (when touching coordinator or REST entities):**

```bash
export BALANSUN_FIELD_URL=http://192.168.2.159
export BALANSUN_API_BEARER_TOKEN=<router PAT>
./scripts/run_hardware_checks.sh
```

PATCH tests restore `vacation_enabled` and `max_routed_w` on the device after each run.

## Releasing

### Nightly builds (CI, `main`)

When a push to `main` changes integration-related paths and **CI** is green, Actions publishes a GitHub **pre-release** tagged `vX.Y.Z-nightly.<short-sha>` (base `version` from `manifest.json` + commit). Install from [GitHub Releases](https://github.com/Balansun/HACS/releases) via HACS (**Releases** tab) — pick the newest nightly.

Dry-run without tagging: **Actions → Release → Run workflow** (artifact only, no GitHub Release).

See [HACS publishing docs](https://www.hacs.xyz/docs/publish/integration/).

## Related

- Firmware & MQTT: [Balansun](https://github.com/Balansun/ESP32-router)
- [HACS publishing docs](https://www.hacs.xyz/docs/publish/integration/)

## License

This repository is **EUPL-1.2** — see [`LICENSE`](LICENSE), same as [Balansun](https://github.com/Balansun/ESP32-router).
