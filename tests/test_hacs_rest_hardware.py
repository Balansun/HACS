"""REST contract tests mirroring BalansunCoordinator poll + entity writes."""

from __future__ import annotations

from typing import Any

import aiohttp
import pytest

POLL_PATHS = (
    "/api/v1/measurements",
    "/api/v1/device",
    "/api/v1/state",
    "/api/v1/health",
    "/api/v1/config",
)

COORDINATOR_POLL_PATHS = (
    "/api/v1/measurements",
    "/api/v1/device",
    "/api/v1/state",
    "/api/v1/health",
    "/api/v1/config",
    "/api/v1/telemetry/snapshot",
    "/api/v1/sources",
    "/api/v1/sources/diagnostics",
    "/api/v1/actions/config",
)


def _normalize_config(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    config = body.get("config", body)
    return config if isinstance(config, dict) else {}


async def _get_config(
    session: aiohttp.ClientSession, base_url: str
) -> dict[str, Any]:
    async with session.get(f"{base_url}/api/v1/config") as resp:
        assert resp.status == 200, await resp.text()
        return _normalize_config(await resp.json())


async def _patch_config(
    session: aiohttp.ClientSession, base_url: str, body: dict[str, Any]
) -> None:
    async with session.patch(f"{base_url}/api/v1/config", json=body) as resp:
        resp.raise_for_status()


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_poll_bundle(rest_session: aiohttp.ClientSession, base_url: str) -> None:
    """Sequential GETs on one ClientSession (coordinator poll order)."""
    measurements: dict[str, Any] = {}
    device: dict[str, Any] = {}
    state: dict[str, Any] = {}
    health: dict[str, Any] = {}
    cfg_body: dict[str, Any] = {}

    for path in POLL_PATHS:
        async with rest_session.get(f"{base_url}{path}") as resp:
            if path in ("/api/v1/measurements", "/api/v1/device"):
                resp.raise_for_status()
                payload = await resp.json()
            elif resp.status == 200:
                payload = await resp.json()
            else:
                payload = {}

        if path == "/api/v1/measurements":
            measurements = payload if isinstance(payload, dict) else {}
        elif path == "/api/v1/device":
            device = payload if isinstance(payload, dict) else {}
        elif path == "/api/v1/state":
            state = payload if isinstance(payload, dict) else {}
        elif path == "/api/v1/health":
            health = payload if isinstance(payload, dict) else {}
        else:
            cfg_body = payload if isinstance(payload, dict) else {}

    assert measurements.get("probe_house_name") is not None
    assert measurements.get("probe_second_name") is not None
    house = measurements.get("house") or {}
    raw = measurements.get("raw_meter") or {}
    assert "active_import_w" in house, house
    assert "house_net_power_w" in raw, raw
    assert device.get("router_name"), device
    config = _normalize_config(cfg_body)
    assert isinstance(config, dict)
    assert state is not None
    assert health is not None


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_patch_vacation_restore(
    rest_session: aiohttp.ClientSession, base_url: str
) -> None:
    original = await _get_config(rest_session, base_url)
    orig_vacation = bool(original.get("vacation_enabled"))
    toggled = not orig_vacation

    await _patch_config(rest_session, base_url, {"vacation_enabled": toggled})
    updated = await _get_config(rest_session, base_url)
    assert bool(updated.get("vacation_enabled")) is toggled

    await _patch_config(rest_session, base_url, {"vacation_enabled": orig_vacation})
    restored = await _get_config(rest_session, base_url)
    assert bool(restored.get("vacation_enabled")) is orig_vacation


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_patch_max_routed_restore(
    rest_session: aiohttp.ClientSession, base_url: str
) -> None:
    original = await _get_config(rest_session, base_url)
    orig_max = int(original.get("max_routed_w") or 0)
    candidate = min(orig_max + 100, 20000)
    if candidate == orig_max:
        candidate = max(0, orig_max - 100)

    await _patch_config(rest_session, base_url, {"max_routed_w": candidate})
    updated = await _get_config(rest_session, base_url)
    assert int(updated.get("max_routed_w") or 0) == candidate

    await _patch_config(rest_session, base_url, {"max_routed_w": orig_max})
    restored = await _get_config(rest_session, base_url)
    assert int(restored.get("max_routed_w") or 0) == orig_max


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_post_mqtt_discover(
    rest_session: aiohttp.ClientSession, base_url: str
) -> None:
    async with rest_session.post(f"{base_url}/api/v1/mqtt/discover") as resp:
        assert 200 <= resp.status < 300, await resp.text()


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_poll_bundle_v2(rest_session: aiohttp.ClientSession, base_url: str) -> None:
    """Coordinator parity paths (gather bundle)."""
    import asyncio

    async def _get(path: str) -> tuple[str, dict[str, Any]]:
        async with rest_session.get(f"{base_url}{path}") as resp:
            if path in ("/api/v1/measurements", "/api/v1/device"):
                resp.raise_for_status()
            if resp.status != 200:
                return path, {}
            payload = await resp.json()
            return path, payload if isinstance(payload, dict) else {}

    results = dict(await asyncio.gather(*[_get(p) for p in COORDINATOR_POLL_PATHS]))

    measurements = results.get("/api/v1/measurements", {})
    device = results.get("/api/v1/device", {})
    snapshot = results.get("/api/v1/telemetry/snapshot", {})
    state = results.get("/api/v1/state", {})
    sources = results.get("/api/v1/sources", {})

    raw = measurements.get("raw_meter") or {}
    assert raw.get("house_net_power_w") is not None
    if sources:
        assert "supported" in sources and "current" in sources, sources
    assert device.get("device_uid")
    for key in ("house_net_power_w", "triac_open_percent", "device_uid"):
        assert key in snapshot, snapshot
    diag = measurements.get("diagnostics") or {}
    assert "source_health" in diag, diag
    assert "source_stale" in diag, diag
    status = state.get("status") or {}
    assert "source_health" in status, status


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_second_channel_read_snapshot_key(
    rest_session: aiohttp.ClientSession, base_url: str
) -> None:
    """read_snapshot_key resolves CH2 from nested measurements on the lab bench."""
    from tests.unit.balansun_import import load_entity_registry

    read_snapshot_key = load_entity_registry().read_snapshot_key

    async def _get(path: str) -> dict[str, Any]:
        async with rest_session.get(f"{base_url}{path}") as resp:
            resp.raise_for_status()
            payload = await resp.json()
            return payload if isinstance(payload, dict) else {}

    measurements = await _get("/api/v1/measurements")
    snapshot = await _get("/api/v1/telemetry/snapshot")
    second = measurements.get("second") or {}
    if second.get("active_import_w") is None and (
        (measurements.get("raw_meter") or {}).get("voltage_second_v") is None
    ):
        pytest.skip("bench has no live second-channel metering")

    data = {"measurements": measurements, "snapshot": snapshot}
    assert read_snapshot_key(data, "second_active_import_w") is not None
    assert read_snapshot_key(data, "second_voltage_v") is not None


@pytest.mark.hardware
@pytest.mark.asyncio
async def test_triac_override_auto(
    rest_session: aiohttp.ClientSession, base_url: str
) -> None:
    async with rest_session.post(
        f"{base_url}/api/v1/triac/override",
        json={"command": "AUTO"},
    ) as resp:
        assert resp.status == 200, await resp.text()
        body = await resp.json()
        assert body.get("ok") is True
